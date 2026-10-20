from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import delete, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import Event, Folder, Game, GamePlayer, StatsTimeline, Unit
from .parser import ParsedReplay, parse_replay, sha256_file

ProgressCallback = Callable[[dict[str, Any]], None]


def _emit(progress: ProgressCallback | None, **payload: Any) -> None:
    if progress is not None:
        progress(payload)


@dataclass
class ImportError:
    file: str
    message: str


@dataclass
class ImportResult:
    folder_id: int
    folder_path: str
    imported: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[ImportError] = field(default_factory=list)
    game_ids: list[int] = field(default_factory=list)


def _replay_files(folder: Path) -> list[Path]:
    return sorted(
        (path for path in folder.rglob("*") if path.is_file() and path.suffix.lower() == ".sc2replay"),
        key=lambda path: str(path).lower(),
    )


def get_or_create_folder(session: Session, folder_path: Path) -> Folder:
    path = str(folder_path.resolve())
    folder = session.scalar(select(Folder).where(Folder.path == path))
    if folder is None:
        folder = Folder(path=path, name=folder_path.resolve().name)
        session.add(folder)
        session.flush()
    return folder


def delete_game(session: Session, game_id: int) -> None:
    session.execute(delete(Game).where(Game.id == game_id))


def _insert_parsed_replay(session: Session, folder_id: int, parsed: ParsedReplay) -> Game:
    game = Game(
        folder_id=folder_id,
        file_path=parsed.file_path,
        file_name=parsed.file_name,
        file_hash=parsed.file_hash,
        file_size=parsed.file_size,
        map_name=parsed.map_name,
        duration_sec=parsed.duration_sec,
        game_version=parsed.game_version,
        region=parsed.region,
        played_at=parsed.played_at,
        frames=parsed.frames,
        frames_per_second=parsed.frames_per_second,
        speed=parsed.speed,
        game_type=parsed.game_type,
        raw=parsed.raw,
    )
    session.add(game)
    session.flush()

    player_rows: list[GamePlayer] = []
    for player in parsed.players:
        row = GamePlayer(
            game_id=game.id,
            pid=player.pid,
            name=player.name,
            race=player.race,
            team=player.team,
            result=player.result,
            is_winner=player.is_winner,
            is_human=player.is_human,
            uid=player.uid,
            color=player.color,
        )
        session.add(row)
        player_rows.append(row)
    session.flush()

    player_ids = {row.pid: row.id for row in player_rows}

    if parsed.events:
        session.execute(
            insert(Event),
            [
                {
                    "game_id": game.id,
                    "player_id": player_ids.get(event.player_pid),
                    "frame": event.frame,
                    "t_sec": event.t_sec,
                    "kind": event.kind,
                    "name": event.name,
                    "display_name": event.display_name,
                    "supply": event.supply,
                    "is_worker": event.is_worker,
                    "payload": event.payload,
                }
                for event in parsed.events
            ],
        )

    if parsed.units:
        session.execute(
            insert(Unit),
            [
                {
                    "game_id": game.id,
                    "player_id": player_ids[unit.player_pid],
                    "unit_id": unit.unit_id,
                    "first_type": unit.first_type,
                    "unit_type": unit.unit_type,
                    "born_t_sec": unit.born_t_sec,
                    "died_t_sec": unit.died_t_sec,
                    "is_worker": unit.is_worker,
                    "is_army": unit.is_army,
                    "is_building": unit.is_building,
                    "morphs": unit.morphs,
                    "payload": unit.payload,
                }
                for unit in parsed.units
            ],
        )

    if parsed.stats:
        session.execute(
            insert(StatsTimeline),
            [
                {
                    "game_id": game.id,
                    "player_id": player_ids[stat.player_pid],
                    "frame": stat.frame,
                    "t_sec": stat.t_sec,
                    "minerals": stat.minerals,
                    "vespene": stat.vespene,
                    "workers": stat.workers,
                    "supply_used": stat.supply_used,
                    "supply_made": stat.supply_made,
                    "army_value": stat.army_value,
                    "minerals_collection_rate": stat.minerals_collection_rate,
                    "vespene_collection_rate": stat.vespene_collection_rate,
                    "resources_lost": stat.resources_lost,
                    "resources_killed": stat.resources_killed,
                    "payload": stat.payload,
                }
                for stat in parsed.stats
            ],
        )

    return game


def _import_worker(path: str, folder_id: int, file_hash: str) -> tuple[str, str, int | None, str | None]:
    """Parse and store one replay in a worker process."""
    session = SessionLocal()
    try:
        existing = session.scalar(select(Game.id).where(Game.file_hash == file_hash))
        if existing is not None:
            return path, "skipped", existing, None
        parsed = parse_replay(path, file_hash=file_hash)
        game = _insert_parsed_replay(session, folder_id, parsed)
        session.commit()
        return path, "imported", game.id, None
    except IntegrityError:
        session.rollback()
        existing = session.scalar(select(Game.id).where(Game.file_hash == file_hash))
        if existing is not None:
            return path, "skipped", existing, None
        return path, "error", None, "duplicate replay hash conflict"
    except Exception as exc:  # noqa: BLE001 - report the file and continue
        session.rollback()
        return path, "error", None, str(exc)
    finally:
        session.close()


def _worker_count() -> int:
    configured = os.environ.get("SC2_IMPORT_WORKERS", "").strip()
    if configured.isdigit():
        return max(1, int(configured))
    return max(2, min(8, (os.cpu_count() or 4) // 2))


def _existing_hashes(session: Session, hashes: list[str]) -> set[str]:
    found: set[str] = set()
    for start in range(0, len(hashes), 500):
        chunk = hashes[start : start + 500]
        found.update(session.scalars(select(Game.file_hash).where(Game.file_hash.in_(chunk))))
    return found


def import_folder(
    session: Session,
    folder_path: str | Path,
    progress: ProgressCallback | None = None,
) -> ImportResult:
    folder = Path(folder_path).resolve()
    if not folder.is_dir():
        raise NotADirectoryError(folder)

    folder_row = get_or_create_folder(session, folder)
    session.commit()

    files = _replay_files(folder)
    result = ImportResult(folder_id=folder_row.id, folder_path=folder_row.path)
    processed = 0
    _emit(progress, phase="scan", total=len(files))

    def record(path: str, status: str, game_id: int | None, message: str | None) -> None:
        nonlocal processed
        processed += 1
        if status == "imported":
            result.imported.append(path)
            if game_id is not None:
                result.game_ids.append(game_id)
        elif status == "skipped":
            result.skipped.append(path)
        else:
            result.errors.append(ImportError(file=path, message=message or "unknown error"))
        _emit(
            progress,
            phase=f"file_{status}",
            index=processed,
            total=len(files),
            file=path,
            message=message or "",
        )

    hashed: list[tuple[Path, str]] = []
    for replay_file in files:
        try:
            hashed.append((replay_file, sha256_file(replay_file)))
        except Exception as exc:  # noqa: BLE001 - report unreadable files and continue
            record(str(replay_file), "error", None, str(exc))

    existing = _existing_hashes(session, [file_hash for _, file_hash in hashed])
    pending: list[tuple[Path, str]] = []
    scheduled: set[str] = set()
    for replay_file, file_hash in hashed:
        if file_hash in existing or file_hash in scheduled:
            record(str(replay_file), "skipped", None, None)
            continue
        scheduled.add(file_hash)
        pending.append((replay_file, file_hash))

    workers = min(_worker_count(), len(pending)) if pending else 1
    if workers <= 1:
        for replay_file, file_hash in pending:
            path, status, game_id, message = _import_worker(
                str(replay_file), folder_row.id, file_hash
            )
            record(path, status, game_id, message)
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(_import_worker, str(replay_file), folder_row.id, file_hash): replay_file
                for replay_file, file_hash in pending
            }
            for future in as_completed(futures):
                replay_file = futures[future]
                try:
                    path, status, game_id, message = future.result()
                except Exception as exc:  # noqa: BLE001 - a crashed worker should not kill the import
                    path, status, game_id, message = str(replay_file), "error", None, str(exc)
                record(path, status, game_id, message)

    _emit(
        progress,
        phase="done",
        total=len(files),
        imported=len(result.imported),
        skipped=len(result.skipped),
        errors=len(result.errors),
    )
    return result


def import_replay(session: Session, replay_path: str | Path, folder_path: str | Path | None = None) -> ImportResult:
    replay = Path(replay_path).resolve()
    if not replay.is_file():
        raise FileNotFoundError(replay)

    file_hash = sha256_file(replay)
    existing = session.scalar(select(Game).where(Game.file_hash == file_hash))
    if existing is not None:
        result = ImportResult(folder_id=existing.folder_id, folder_path=str(replay.parent))
        result.skipped.append(str(replay))
        result.game_ids.append(existing.id)
        return result

    parsed = parse_replay(replay, file_hash=file_hash)
    folder = Path(folder_path).resolve() if folder_path else replay.parent
    folder_row = get_or_create_folder(session, folder)
    session.commit()

    result = ImportResult(folder_id=folder_row.id, folder_path=folder_row.path)
    try:
        game = _insert_parsed_replay(session, folder_row.id, parsed)
        session.commit()
        result.imported.append(str(replay))
        result.game_ids.append(game.id)
    except Exception as exc:  # noqa: BLE001
        session.rollback()
        result.errors.append(ImportError(file=str(replay), message=str(exc)))

    return result
