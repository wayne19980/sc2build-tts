from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sc2reader
import spawningtool.parser
from sc2reader.events.message import ChatEvent
from sc2reader.events.tracker import (
    UnitBornEvent,
    UnitDiedEvent,
    UnitDoneEvent,
    UnitInitEvent,
    UnitTypeChangeEvent,
    UpgradeCompleteEvent,
)
from sc2reader.events.tracker import PlayerStatsEvent

SPEED_FACTOR = {
    "Slower": 0.6,
    "Slow": 0.8,
    "Normal": 1.0,
    "Fast": 1.2,
    "Faster": 1.4,
}

UNIT_VARIANTS = {
    "AdeptPhaseShift": "AdeptPhaseShift",
    "BattleHellion": "Hellbat",
    "Hellbat": "Hellbat",
    "SiegeTankSieged": "SiegeTank",
    "WidowMineBurrowed": "WidowMine",
    "VikingAssault": "Viking",
    "VikingFighter": "Viking",
    "LiberatorAG": "Liberator",
    "ThorAP": "Thor",
    "OverseerSiegeMode": "Overseer",
    "ObserverSiegeMode": "Observer",
    "WarpPrismPhasing": "WarpPrism",
    "DroneBurrowed": "Drone",
    "ZerglingBurrowed": "Zergling",
    "BanelingBurrowed": "Baneling",
    "RoachBurrowed": "Roach",
    "RavagerBurrowed": "Ravager",
    "HydraliskBurrowed": "Hydralisk",
    "LurkerBurrowed": "Lurker",
    "LurkerMP": "Lurker",
    "LurkerMPBurrowed": "Lurker",
    "LurkerMPEgg": "Lurker",
    "LurkerDenMP": "LurkerDen",
    "BroodLordCocoon": "BroodLord",
    "OverlordCocoon": "Overseer",
    "BanelingCocoon": "Baneling",
    "RavagerCocoon": "Ravager",
    "InfestorBurrowed": "Infestor",
    "UltraliskBurrowed": "Ultralisk",
    "SwarmHostBurrowed": "SwarmHost",
    "QueenBurrowed": "Queen",
    "SupplyDepotLowered": "SupplyDepot",
    "SpineCrawlerUprooted": "SpineCrawler",
    "SporeCrawlerUprooted": "SporeCrawler",
    "CreepTumorBurrowed": "CreepTumor",
    "CreepTumorQueen": "CreepTumor",
    "RefineryRich": "Refinery",
    "ExtractorRich": "Extractor",
}

IGNORED_UPGRADES = {"GameHeartActive"}
IGNORED_UNITS = {"AdeptPhaseShift"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_unit_name(name: str) -> str:
    return UNIT_VARIANTS.get(name, name)


def display_fps(replay: Any, st_data: dict[str, Any]) -> float:
    fps = st_data.get("frames_per_second")
    if fps:
        return float(fps)
    return float(replay.game_fps) * SPEED_FACTOR.get(replay.speed, 1.0)


@dataclass
class ParsedPlayer:
    pid: int
    name: str
    race: str | None
    team: int | None
    result: str | None
    is_winner: bool
    is_human: bool
    uid: int | None
    color: str | None
    build_order: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ParsedEvent:
    player_pid: int | None
    frame: float
    t_sec: float
    kind: str
    name: str
    display_name: str | None = None
    supply: float | None = None
    is_worker: bool = False
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedUnit:
    player_pid: int
    unit_id: int
    first_type: str
    unit_type: str
    born_t_sec: float
    died_t_sec: float | None
    is_worker: bool
    is_army: bool
    is_building: bool
    morphs: list[dict[str, Any]] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedStats:
    player_pid: int
    frame: float
    t_sec: float
    minerals: int | None
    vespene: int | None
    workers: int | None
    supply_used: float | None
    supply_made: float | None
    army_value: int | None
    minerals_collection_rate: int | None
    vespene_collection_rate: int | None
    resources_lost: int | None
    resources_killed: int | None
    payload: dict[str, Any]


@dataclass
class ParsedReplay:
    file_path: str
    file_name: str
    file_size: int
    file_hash: str
    map_name: str | None
    duration_sec: float | None
    game_version: str | None
    region: str | None
    played_at: datetime | None
    frames: int | None
    frames_per_second: float | None
    speed: str | None
    game_type: str | None
    raw: dict[str, Any]
    players: list[ParsedPlayer]
    events: list[ParsedEvent]
    units: list[ParsedUnit]
    stats: list[ParsedStats]


def _pid_of(unit_event: Any, fallback: int | None = None) -> int | None:
    owner = getattr(getattr(unit_event, "unit", None), "owner", None)
    if owner is not None:
        return int(owner.pid)
    control_pid = getattr(unit_event, "control_pid", None)
    if control_pid:
        return int(control_pid)
    return fallback


def _event_name(event: Any, *, prefer_type: bool = True) -> str | None:
    if prefer_type:
        name = getattr(event, "unit_type_name", None)
        if name:
            return str(name)
    unit = getattr(event, "unit", None)
    if unit is not None:
        return str(unit.name)
    return None


def _unit_type_at(unit: Any, frame: float) -> str | None:
    history = getattr(unit, "type_history", None)
    if history:
        name = None
        for history_frame, unit_type in history.items():
            if history_frame <= frame:
                name = getattr(unit_type, "name", None) or str(unit_type)
            else:
                break
        if name:
            return str(name)
    return str(unit.name) if unit is not None else None


def _unit_id(event: Any) -> int | None:
    value = getattr(event, "unit_id", None)
    return int(value) if value is not None else None


def _stat_payload(stats: dict[Any, Any]) -> dict[str, Any]:
    return {str(key): value for key, value in stats.items()}


def parse_replay(path: str | Path, file_hash: str | None = None) -> ParsedReplay:
    replay_path = Path(path).resolve()
    if not replay_path.is_file():
        raise FileNotFoundError(replay_path)

    # Keep spawningtool's build order keys stable instead of using display names.
    def patched_get_display_name(self: Any, unit_name: str, player: Any) -> str:
        return unit_name

    spawningtool.parser.GameParser.get_display_name = patched_get_display_name

    parser = spawningtool.parser.GameParser(str(replay_path))
    st_data = parser.get_parsed_data()
    replay = parser.replay

    fps = display_fps(replay, st_data)
    players: list[ParsedPlayer] = []

    for player in replay.players:
        st_player = st_data.get("players", {}).get(player.pid, {})
        players.append(
            ParsedPlayer(
                pid=int(player.pid),
                name=str(player.name),
                race=str(getattr(player, "play_race", None) or getattr(player, "pick_race", None) or ""),
                team=int(st_player.get("team")) if st_player.get("team") is not None else None,
                result=st_player.get("result"),
                is_winner=bool(st_player.get("is_winner", False)),
                is_human=bool(getattr(player, "is_human", False)),
                uid=int(st_player["uid"]) if st_player.get("uid") is not None else None,
                color=st_player.get("color"),
                build_order=list(st_player.get("buildOrder", [])),
            )
        )

    parsed_events: list[ParsedEvent] = []
    seen_stats: set[tuple[int, float]] = set()
    parsed_stats: list[ParsedStats] = []

    def add_event(event: ParsedEvent) -> None:
        parsed_events.append(event)

    for event in replay.events:
        frame = float(getattr(event, "frame", 0))
        t_sec = frame / fps if fps else 0.0

        if isinstance(event, UnitInitEvent):
            name = _event_name(event, prefer_type=True)
            pid = _pid_of(event)
            if not name or pid is None:
                continue
            unit = getattr(event, "unit", None)
            is_army = bool(getattr(unit, "is_army", False))
            is_building = bool(getattr(unit, "is_building", False))
            canonical = canonical_unit_name(name)
            add_event(
                ParsedEvent(
                    player_pid=pid,
                    frame=frame,
                    t_sec=t_sec,
                    kind="unit_training_start" if is_army else "build_start",
                    name=canonical,
                    display_name=name,
                    payload={
                        "unit_id": _unit_id(event),
                        "is_building": is_building,
                        "is_army": is_army,
                        "unit_type": name,
                    },
                )
            )

        elif isinstance(event, UnitDoneEvent):
            unit = getattr(event, "unit", None)
            name = _unit_type_at(unit, frame) if unit is not None else None
            pid = _pid_of(event)
            if not name or pid is None:
                continue
            is_army = bool(getattr(unit, "is_army", False))
            is_worker = bool(getattr(unit, "is_worker", False))
            is_building = bool(getattr(unit, "is_building", False))
            canonical = canonical_unit_name(name)
            # Warp-in units and Archon merges use UnitInit/UnitDone instead of
            # UnitBorn. Treat their completion as a unit birth.
            kind = "unit_born" if (is_army or is_worker) else "build_done"
            add_event(
                ParsedEvent(
                    player_pid=pid,
                    frame=frame,
                    t_sec=t_sec,
                    kind=kind,
                    name=canonical,
                    display_name=name,
                    is_worker=is_worker,
                    payload={
                        "unit_id": _unit_id(event),
                        "is_building": is_building,
                        "is_army": is_army,
                        "is_worker": is_worker,
                        "unit_type": name,
                    },
                )
            )

        elif isinstance(event, UnitBornEvent):
            name = _event_name(event, prefer_type=True)
            pid = _pid_of(event)
            if not name or pid is None:
                continue
            if name in IGNORED_UNITS:
                continue
            unit = getattr(event, "unit", None)
            is_army = bool(getattr(unit, "is_army", False))
            is_worker = bool(getattr(unit, "is_worker", False))
            is_building = bool(getattr(unit, "is_building", False))
            # Beacons, mineral fields and other map props are reported as owned
            # UnitBorn events but are not part of a player's army.
            if not (is_army or is_worker or is_building):
                continue
            canonical = canonical_unit_name(name)
            add_event(
                ParsedEvent(
                    player_pid=pid,
                    frame=frame,
                    t_sec=t_sec,
                    kind="unit_born",
                    name=canonical,
                    display_name=name,
                    is_worker=is_worker,
                    payload={
                        "unit_id": _unit_id(event),
                        "unit_type": name,
                        "is_army": is_army,
                        "is_worker": is_worker,
                        "is_building": is_building,
                    },
                )
            )

        elif isinstance(event, UnitDiedEvent):
            unit = getattr(event, "unit", None)
            name = _unit_type_at(unit, frame) if unit is not None else None
            pid = _pid_of(event)
            if not name or pid is None:
                continue
            is_army = bool(getattr(unit, "is_army", False))
            is_worker = bool(getattr(unit, "is_worker", False))
            is_building = bool(getattr(unit, "is_building", False))
            if not (is_army or is_worker or is_building):
                continue
            canonical = canonical_unit_name(name)
            add_event(
                ParsedEvent(
                    player_pid=pid,
                    frame=frame,
                    t_sec=t_sec,
                    kind="unit_died",
                    name=canonical,
                    display_name=name,
                    is_worker=is_worker,
                    payload={
                        "unit_id": _unit_id(event),
                        "unit_type": name,
                        "is_army": is_army,
                        "is_worker": is_worker,
                        "is_building": is_building,
                    },
                )
            )

        elif isinstance(event, UnitTypeChangeEvent):
            name = _event_name(event, prefer_type=True)
            pid = _pid_of(event)
            if not name or pid is None:
                continue
            unit = getattr(event, "unit", None)
            is_army = bool(getattr(unit, "is_army", False))
            is_worker = bool(getattr(unit, "is_worker", False))
            is_building = bool(getattr(unit, "is_building", False))
            if not (is_army or is_worker or is_building):
                continue
            canonical = canonical_unit_name(name)
            add_event(
                ParsedEvent(
                    player_pid=pid,
                    frame=frame,
                    t_sec=t_sec,
                    kind="unit_morph",
                    name=canonical,
                    display_name=name,
                    payload={
                        "unit_id": _unit_id(event),
                        "unit_type": name,
                        "is_army": is_army,
                        "is_worker": is_worker,
                        "is_building": is_building,
                    },
                )
            )

        elif isinstance(event, UpgradeCompleteEvent):
            name = str(getattr(event, "upgrade_type_name", "") or "")
            if not name or name in IGNORED_UPGRADES or name.startswith("Spray"):
                continue
            pid = getattr(event, "pid", None)
            if pid is None:
                player = getattr(event, "player", None)
                pid = getattr(player, "pid", None)
            if pid is None:
                continue
            add_event(
                ParsedEvent(
                    player_pid=int(pid),
                    frame=frame,
                    t_sec=t_sec,
                    kind="upgrade_done",
                    name=name,
                    display_name=name,
                    payload={"upgrade": name},
                )
            )

        elif isinstance(event, PlayerStatsEvent):
            pid = int(event.pid)
            stat_key = (pid, frame)
            if stat_key in seen_stats:
                continue
            seen_stats.add(stat_key)
            army_value = int(
                (getattr(event, "minerals_used_current_army", 0) or 0)
                + (getattr(event, "vespene_used_current_army", 0) or 0)
            )
            parsed_stats.append(
                ParsedStats(
                    player_pid=pid,
                    frame=frame,
                    t_sec=t_sec,
                    minerals=getattr(event, "minerals_current", None),
                    vespene=getattr(event, "vespene_current", None),
                    workers=getattr(event, "workers_active_count", None),
                    supply_used=float(getattr(event, "food_used", 0) or 0),
                    supply_made=float(getattr(event, "food_made", 0) or 0),
                    army_value=army_value,
                    minerals_collection_rate=getattr(event, "minerals_collection_rate", None),
                    vespene_collection_rate=getattr(event, "vespene_collection_rate", None),
                    resources_lost=getattr(event, "resources_lost", None),
                    resources_killed=getattr(event, "resources_killed", None),
                    payload=_stat_payload(getattr(event, "stats", {})),
                )
            )

        elif isinstance(event, ChatEvent):
            # Chat is not part of the tech-tree dataset, but keep it out of events.
            continue

    # Build-order events are order timestamps, not completion timestamps.
    for player in players:
        st_player = st_data.get("players", {}).get(player.pid, {})
        for item in player.build_order:
            frame = item.get("frame")
            if frame is None:
                continue
            name = str(item.get("name", ""))
            if not name:
                continue
            canonical = canonical_unit_name(name)
            payload = {
                "is_chronoboosted": bool(item.get("is_chronoboosted", False)),
                "time": item.get("time"),
            }
            parsed_events.append(
                ParsedEvent(
                    player_pid=player.pid,
                    frame=float(frame),
                    t_sec=float(frame) / fps if fps else 0.0,
                    kind="order",
                    name=canonical,
                    display_name=name,
                    supply=float(item["supply"]) if item.get("supply") is not None else None,
                    is_worker=bool(item.get("is_worker", False)),
                    payload=payload,
                )
            )

        for ability in st_player.get("abilities", []) or []:
            frame = ability.get("frame")
            name = ability.get("name")
            if frame is None or not name:
                continue
            parsed_events.append(
                ParsedEvent(
                    player_pid=player.pid,
                    frame=float(frame),
                    t_sec=float(frame) / fps if fps else 0.0,
                    kind="ability",
                    name=str(name),
                    display_name=str(name),
                    payload={"time": ability.get("time")},
                )
            )

    parsed_events.sort(key=lambda item: (item.t_sec, item.kind, item.name))
    parsed_stats.sort(key=lambda item: (item.player_pid, item.t_sec))

    # Build a lifecycle record for every unit. This makes both cumulative
    # production and "alive at time T" queries straightforward.
    unit_states: dict[tuple[int, int], dict[str, Any]] = {}
    for item in parsed_events:
        if item.player_pid is None:
            continue
        unit_id = item.payload.get("unit_id")
        if unit_id is None:
            continue
        key = (item.player_pid, int(unit_id))

        if item.kind == "unit_born":
            if item.payload.get("is_building"):
                continue
            unit_states.setdefault(
                key,
                {
                    "player_pid": item.player_pid,
                    "unit_id": int(unit_id),
                    "first_type": item.name,
                    "unit_type": item.name,
                    "born_t_sec": item.t_sec,
                    "died_t_sec": None,
                    "is_worker": bool(item.payload.get("is_worker", item.is_worker)),
                    "is_army": bool(item.payload.get("is_army", False)),
                    "is_building": False,
                    "morphs": [],
                    "payload": {"unit_type": item.payload.get("unit_type", item.name)},
                },
            )
            continue

        state = unit_states.get(key)
        if state is None:
            if item.kind == "unit_died" and not item.payload.get("is_building"):
                state = {
                    "player_pid": item.player_pid,
                    "unit_id": int(unit_id),
                    "first_type": item.name,
                    "unit_type": item.name,
                    "born_t_sec": 0.0,
                    "died_t_sec": item.t_sec,
                    "is_worker": bool(item.payload.get("is_worker", item.is_worker)),
                    "is_army": bool(item.payload.get("is_army", False)),
                    "is_building": False,
                    "morphs": [],
                    "payload": {"unit_type": item.payload.get("unit_type", item.name)},
                }
                unit_states[key] = state
            continue

        if item.kind == "unit_died":
            state["died_t_sec"] = item.t_sec
        elif item.kind == "unit_morph":
            previous = state["unit_type"]
            if previous != item.name:
                state["morphs"].append(
                    {"t_sec": item.t_sec, "from": previous, "to": item.name}
                )
                state["unit_type"] = item.name

    parsed_units = [
        ParsedUnit(
            player_pid=state["player_pid"],
            unit_id=state["unit_id"],
            first_type=state["first_type"],
            unit_type=state["unit_type"],
            born_t_sec=state["born_t_sec"],
            died_t_sec=state["died_t_sec"],
            is_worker=state["is_worker"],
            is_army=state["is_army"],
            is_building=state["is_building"],
            morphs=state["morphs"],
            payload=state["payload"],
        )
        for state in sorted(unit_states.values(), key=lambda value: (value["player_pid"], value["born_t_sec"], value["unit_id"]))
    ]

    played_at = None
    unix_timestamp = st_data.get("unix_timestamp")
    if unix_timestamp:
        played_at = datetime.fromtimestamp(int(unix_timestamp), tz=timezone.utc)

    raw = {
        "map": st_data.get("map"),
        "frames": st_data.get("frames"),
        "frames_per_second": st_data.get("frames_per_second"),
        "build": st_data.get("build"),
        "base_build": st_data.get("baseBuild"),
        "expansion": st_data.get("expansion"),
        "category": st_data.get("category"),
        "region": st_data.get("region"),
        "unix_timestamp": st_data.get("unix_timestamp"),
        "game_type": st_data.get("game_type"),
        "map_hash": st_data.get("map_hash"),
        "speed": replay.speed,
    }

    return ParsedReplay(
        file_path=str(replay_path),
        file_name=replay_path.name,
        file_size=replay_path.stat().st_size,
        file_hash=file_hash or sha256_file(replay_path),
        map_name=st_data.get("map"),
        duration_sec=(float(st_data["frames"]) / fps) if st_data.get("frames") and fps else None,
        game_version=str(st_data.get("build")) if st_data.get("build") is not None else None,
        region=st_data.get("region"),
        played_at=played_at,
        frames=st_data.get("frames"),
        frames_per_second=fps,
        speed=replay.speed,
        game_type=st_data.get("game_type"),
        raw=raw,
        players=players,
        events=parsed_events,
        units=parsed_units,
        stats=parsed_stats,
    )
