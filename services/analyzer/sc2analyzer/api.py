from __future__ import annotations

import ctypes
import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import SCHEMA
from .db import SessionLocal
from .importer import import_folder
from .migrations import applied_versions, run_migrations


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def rows(result: Any) -> list[dict[str, Any]]:
    return [dict(row._mapping) for row in result]


@dataclass
class ImportJob:
    id: str
    path: str
    status: str = "queued"
    phase: str = "queued"
    total: int = 0
    processed: int = 0
    current_file: str | None = None
    imported: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=now_iso)
    started_at: str | None = None
    finished_at: str | None = None
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        progress = 0.0
        if self.total:
            progress = min(100.0, round(self.processed * 100.0 / self.total, 1))
        return {
            "id": self.id,
            "path": self.path,
            "status": self.status,
            "phase": self.phase,
            "total": self.total,
            "processed": self.processed,
            "progress": progress,
            "current_file": self.current_file,
            "imported": self.imported,
            "skipped": self.skipped,
            "errors": self.errors,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "message": self.message,
        }


_jobs: dict[str, ImportJob] = {}
_jobs_lock = threading.Lock()
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="sc2-import")


def _update_job(job_id: str, **changes: Any) -> None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            return
        for key, value in changes.items():
            if key == "error" and value:
                job.errors.append(str(value))
            else:
                setattr(job, key, value)


def _progress(job_id: str, payload: dict[str, Any]) -> None:
    changes: dict[str, Any] = {"phase": payload.get("phase", "running")}
    if payload.get("total") is not None:
        changes["total"] = int(payload["total"])
    if payload.get("index") is not None:
        changes["processed"] = int(payload["index"])
    if payload.get("file") is not None:
        changes["current_file"] = payload["file"]
    if payload.get("message"):
        changes["error"] = payload["message"]
    _update_job(job_id, **changes)


def _run_import(job_id: str, path: str) -> None:
    _update_job(job_id, status="running", started_at=now_iso(), phase="scanning")
    session = SessionLocal()
    try:
        result = import_folder(session, path, progress=lambda payload: _progress(job_id, payload))
        _update_job(
            job_id,
            status="done",
            phase="done",
            finished_at=now_iso(),
            imported=len(result.imported),
            skipped=len(result.skipped),
            errors=[f"{error.file}: {error.message}" for error in result.errors],
        )
    except Exception as exc:  # noqa: BLE001 - job failure is reported through the API
        _update_job(
            job_id,
            status="failed",
            phase="failed",
            finished_at=now_iso(),
            message=str(exc),
        )
    finally:
        session.close()


def _pid_alive(pid: int) -> bool:
    if os.name == "nt":
        process_query_limited_information = 0x1000
        still_active = 259
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
        if not handle:
            return False
        try:
            exit_code = ctypes.c_ulong()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return False
            return exit_code.value == still_active
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _watch_parent(pid: int) -> None:
    while True:
        time.sleep(2)
        if not _pid_alive(pid):
            os._exit(0)


@asynccontextmanager
async def lifespan(app: FastAPI):

    parent_pid = int(os.environ.get("SC2_PARENT_PID", "0") or 0)
    if parent_pid:
        threading.Thread(target=_watch_parent, args=(parent_pid,), daemon=True).start()

    applied = run_migrations()
    app.state.applied_migrations = applied
    yield
    _executor.shutdown(wait=False, cancel_futures=True)


app = FastAPI(title="SC2 Build Analyzer", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ImportRequest(BaseModel):
    path: str


@app.get("/api/health")
def health() -> dict[str, Any]:
    with SessionLocal() as session:
        session.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "schema": SCHEMA,
        "migrations": applied_versions(),
    }


@app.get("/api/imports")
def list_imports() -> list[dict[str, Any]]:
    with _jobs_lock:
        jobs = sorted(_jobs.values(), key=lambda job: job.created_at, reverse=True)
    return [job.to_dict() for job in jobs]


@app.post("/api/imports", status_code=202)
def create_import(request: ImportRequest) -> dict[str, Any]:
    path = Path(request.path).resolve()
    if not path.is_dir():
        raise HTTPException(status_code=400, detail=f"not a directory: {path}")

    job = ImportJob(id=uuid.uuid4().hex[:12], path=str(path))
    with _jobs_lock:
        _jobs[job.id] = job
    _executor.submit(_run_import, job.id, str(path))
    return job.to_dict()


@app.get("/api/imports/{job_id}")
def get_import(job_id: str) -> dict[str, Any]:
    with _jobs_lock:
        job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="import job not found")
    return job.to_dict()


@app.get("/api/folders")
def list_folders(session: Session = Depends(get_session)) -> list[dict[str, Any]]:
    return rows(
        session.execute(
            text(
                """
                SELECT
                    f.id,
                    f.path,
                    f.name,
                    f.created_at,
                    count(g.id) AS game_count,
                    max(g.played_at) AS last_played
                FROM folders f
                LEFT JOIN games g ON g.folder_id = f.id
                GROUP BY f.id
                ORDER BY f.name
                """
            )
        )
    )


@app.get("/api/games")
def list_games(
    folder_id: int | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> list[dict[str, Any]]:
    where = "WHERE folder_id = :folder_id" if folder_id is not None else ""
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if folder_id is not None:
        params["folder_id"] = folder_id
    return rows(
        session.execute(
            text(
                f"""
                SELECT *
                FROM v_game_summary
                {where}
                ORDER BY played_at DESC NULLS LAST, game_id DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            params,
        )
    )


@app.get("/api/folders/{folder_id}/replays")
def list_folder_replays(
    folder_id: int,
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> list[dict[str, Any]]:
    games = rows(
        session.execute(
            text(
                """
                SELECT *
                FROM v_game_summary
                WHERE folder_id = :folder_id
                ORDER BY played_at DESC NULLS LAST, game_id DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {"folder_id": folder_id, "limit": limit, "offset": offset},
        )
    )
    if not games:
        return []

    game_ids = [game["game_id"] for game in games]
    players = rows(
        session.execute(
            text(
                """
                SELECT id, game_id, pid, name, race, result, is_winner
                FROM game_players
                WHERE game_id = ANY(:ids)
                ORDER BY game_id, pid
                """
            ),
            {"ids": game_ids},
        )
    )
    units = rows(
        session.execute(
            text(
                """
                SELECT game_id, player_id, name AS unit, count(*) AS count
                FROM events
                WHERE game_id = ANY(:ids)
                  AND kind = 'unit_born'
                  AND COALESCE((payload->>'is_worker')::boolean, false) = false
                  AND COALESCE((payload->>'is_building')::boolean, false) = false
                GROUP BY game_id, player_id, name
                ORDER BY count(*) DESC
                """
            ),
            {"ids": game_ids},
        )
    )
    tech = rows(
        session.execute(
            text(
                """
                SELECT game_id, player_id, name AS tech, min(t_sec) AS t_sec
                FROM events
                WHERE game_id = ANY(:ids) AND kind = 'upgrade_done'
                GROUP BY game_id, player_id, name
                ORDER BY min(t_sec)
                """
            ),
            {"ids": game_ids},
        )
    )

    units_by_player: dict[int, list[dict[str, Any]]] = {}
    for row in units:
        units_by_player.setdefault(row["player_id"], []).append(
            {"unit": row["unit"], "count": row["count"]}
        )
    for items in units_by_player.values():
        items.sort(key=lambda item: (-item["count"], item["unit"]))

    def phase_for(t_sec: float) -> str:
        if t_sec < 360:
            return "early"
        if t_sec < 840:
            return "mid"
        return "late"

    tech_by_player: dict[int, dict[str, list[dict[str, Any]]]] = {}
    for row in tech:
        phases = tech_by_player.setdefault(
            row["player_id"], {"early": [], "mid": [], "late": []}
        )
        phases[phase_for(float(row["t_sec"]))].append(
            {"tech": row["tech"], "t_sec": row["t_sec"]}
        )

    players_by_game: dict[int, list[dict[str, Any]]] = {}
    for player in players:
        player["units"] = units_by_player.get(player["id"], [])
        player["tech"] = tech_by_player.get(
            player["id"], {"early": [], "mid": [], "late": []}
        )
        players_by_game.setdefault(player["game_id"], []).append(player)

    for game in games:
        game["player_details"] = players_by_game.get(game["game_id"], [])
    return games


@app.get("/api/games/{game_id}")
def get_game(game_id: int, session: Session = Depends(get_session)) -> dict[str, Any]:
    game = session.execute(
        text("SELECT * FROM v_game_summary WHERE game_id = :game_id"),
        {"game_id": game_id},
    ).mappings().first()
    if game is None:
        raise HTTPException(status_code=404, detail="game not found")

    players = rows(
        session.execute(
            text(
                """
                SELECT id, pid, name, race, team, result, is_winner, is_human, uid, color
                FROM game_players
                WHERE game_id = :game_id
                ORDER BY pid
                """
            ),
            {"game_id": game_id},
        )
    )

    event_counts = rows(
        session.execute(
            text(
                """
                SELECT kind, count(*) AS count
                FROM events
                WHERE game_id = :game_id
                GROUP BY kind
                ORDER BY kind
                """
            ),
            {"game_id": game_id},
        )
    )
    return {
        "game": dict(game),
        "players": players,
        "event_counts": event_counts,
    }


@app.get("/api/games/{game_id}/timeline")
def get_timeline(
    game_id: int,
    player_id: int | None = None,
    from_sec: float | None = None,
    to_sec: float | None = None,
    kinds: str | None = None,
    limit: int = Query(default=10000, ge=1, le=50000),
    session: Session = Depends(get_session),
) -> list[dict[str, Any]]:
    conditions = ["game_id = :game_id"]
    params: dict[str, Any] = {"game_id": game_id, "limit": limit}
    if player_id is not None:
        conditions.append("player_id = :player_id")
        params["player_id"] = player_id
    if from_sec is not None:
        conditions.append("t_sec >= :from_sec")
        params["from_sec"] = from_sec
    if to_sec is not None:
        conditions.append("t_sec <= :to_sec")
        params["to_sec"] = to_sec
    if kinds:
        kind_list = [kind.strip() for kind in kinds.split(",") if kind.strip()]
        if kind_list:
            placeholders = ", ".join(f":kind_{index}" for index in range(len(kind_list)))
            conditions.append(f"kind IN ({placeholders})")
            params.update({f"kind_{index}": kind for index, kind in enumerate(kind_list)})

    return rows(
        session.execute(
            text(
                f"""
                SELECT *
                FROM v_player_events
                WHERE {' AND '.join(conditions)}
                ORDER BY t_sec, frame, kind, name
                LIMIT :limit
                """
            ),
            params,
        )
    )


@app.get("/api/games/{game_id}/tech")
def get_tech(game_id: int, session: Session = Depends(get_session)) -> list[dict[str, Any]]:
    return rows(
        session.execute(
            text(
                """
                SELECT *
                FROM v_player_tech_timings
                WHERE game_id = :game_id
                ORDER BY t_sec
                """
            ),
            {"game_id": game_id},
        )
    )


@app.get("/api/games/{game_id}/units")
def get_units(game_id: int, session: Session = Depends(get_session)) -> list[dict[str, Any]]:
    return rows(
        session.execute(
            text(
                """
                SELECT *
                FROM v_player_units
                WHERE game_id = :game_id
                ORDER BY player_id, born_t_sec, unit_id
                """
            ),
            {"game_id": game_id},
        )
    )


@app.get("/api/games/{game_id}/buildings")
def get_buildings(game_id: int, session: Session = Depends(get_session)) -> list[dict[str, Any]]:
    return rows(
        session.execute(
            text(
                """
                SELECT *
                FROM v_player_events
                WHERE game_id = :game_id
                  AND (
                    kind IN ('build_start', 'build_done')
                    OR (kind IN ('unit_born', 'unit_died', 'unit_morph')
                        AND COALESCE((payload->>'is_building')::boolean, false))
                  )
                ORDER BY t_sec, frame, kind
                """
            ),
            {"game_id": game_id},
        )
    )


@app.get("/api/games/{game_id}/units/alive")
def get_alive_units(
    game_id: int,
    t_sec: float = Query(default=0, ge=0),
    player_id: int | None = None,
    include_workers: bool = False,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    conditions = [
        "game_id = :game_id",
        "born_t_sec <= :t_sec",
        "(died_t_sec IS NULL OR died_t_sec > :t_sec)",
        "NOT is_building",
    ]
    params: dict[str, Any] = {"game_id": game_id, "t_sec": t_sec}
    if player_id is not None:
        conditions.append("player_id = :player_id")
        params["player_id"] = player_id
    if not include_workers:
        conditions.append("NOT is_worker")

    units = rows(
        session.execute(
            text(
                f"""
                SELECT unit_type AS unit, count(*) AS count
                FROM units
                WHERE {' AND '.join(conditions)}
                GROUP BY unit_type
                ORDER BY count(*) DESC, unit_type
                """
            ),
            params,
        )
    )
    return {"t_sec": t_sec, "total": sum(item["count"] for item in units), "units": units}


@app.get("/api/games/{game_id}/units/production")
def get_unit_production(
    game_id: int,
    until_sec: float | None = None,
    player_id: int | None = None,
    include_workers: bool = False,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    conditions = ["game_id = :game_id", "kind = 'unit_born'"]
    params: dict[str, Any] = {"game_id": game_id}
    if until_sec is not None:
        conditions.append("t_sec <= :until_sec")
        params["until_sec"] = until_sec
    if player_id is not None:
        conditions.append("player_id = :player_id")
        params["player_id"] = player_id
    if not include_workers:
        conditions.append("COALESCE((payload->>'is_worker')::boolean, false) = false")
    conditions.append("COALESCE((payload->>'is_building')::boolean, false) = false")

    born = rows(
        session.execute(
            text(
                f"""
                SELECT name AS unit, count(*) AS produced
                FROM events
                WHERE {' AND '.join(conditions)}
                GROUP BY name
                ORDER BY count(*) DESC, name
                """
            ),
            params,
        )
    )

    morph_conditions = ["game_id = :game_id", "kind = 'unit_morph'"]
    morph_params: dict[str, Any] = {"game_id": game_id}
    if until_sec is not None:
        morph_conditions.append("t_sec <= :until_sec")
        morph_params["until_sec"] = until_sec
    if player_id is not None:
        morph_conditions.append("player_id = :player_id")
        morph_params["player_id"] = player_id
    morph_conditions.append("COALESCE((payload->>'is_building')::boolean, false) = false")
    morphed = rows(
        session.execute(
            text(
                f"""
                SELECT name AS unit, count(*) AS produced
                FROM events
                WHERE {' AND '.join(morph_conditions)}
                GROUP BY name
                ORDER BY count(*) DESC, name
                """
            ),
            morph_params,
        )
    )
    return {"born": born, "morphed": morphed}


@app.get("/api/games/{game_id}/stats")
def get_stats(
    game_id: int,
    player_id: int | None = None,
    session: Session = Depends(get_session),
) -> list[dict[str, Any]]:
    where = "AND player_id = :player_id" if player_id is not None else ""
    params: dict[str, Any] = {"game_id": game_id}
    if player_id is not None:
        params["player_id"] = player_id
    return rows(
        session.execute(
            text(
                f"""
                SELECT *
                FROM v_player_stats
                WHERE game_id = :game_id {where}
                ORDER BY player_id, t_sec
                """
            ),
            params,
        )
    )


@app.get("/api/games/{game_id}/features")
def get_features(game_id: int, session: Session = Depends(get_session)) -> dict[str, Any]:
    row = session.execute(
        text("SELECT * FROM v_game_features WHERE game_id = :game_id"),
        {"game_id": game_id},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="game not found")
    return dict(row)


def main() -> None:
    import uvicorn

    uvicorn.run(
        "sc2analyzer.api:app",
        host=os.environ.get("SC2_API_HOST", "127.0.0.1"),
        port=int(os.environ.get("SC2_API_PORT", "8765")),
        reload=False,
    )


if __name__ == "__main__":
    main()
