from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from sc2analyzer.parser import canonical_unit_name, display_fps, parse_replay

REPLAY = (
    Path(__file__).resolve().parents[3]
    / "test"
    / "clem(w) vs classic g1 old republic.SC2Replay"
)


def test_parse_test_replay() -> None:
    parsed = parse_replay(REPLAY)

    assert parsed.map_name == "Old Republic LE"
    assert parsed.frames_per_second == 22.4
    assert parsed.duration_sec is not None
    # The replay keeps running after GG; duration is the last stats tick.
    assert 601 < parsed.duration_sec < 602
    assert {player.name for player in parsed.players} == {"Clem", "Classic"}

    upgrades = {
        (event.player_pid, event.name, round(event.t_sec, 1))
        for event in parsed.events
        if event.kind == "upgrade_done"
    }
    assert (2, "Stimpack", 319.4) in upgrades
    assert (1, "WarpGateResearch", 220.8) in upgrades

    gateway_completions = [
        event
        for event in parsed.events
        if event.kind == "build_done" and event.name == "Gateway"
    ]
    warp_gate_morphs = [
        event
        for event in parsed.events
        if event.kind == "unit_morph" and event.name == "WarpGate"
    ]
    assert len(gateway_completions) == 8
    assert len(warp_gate_morphs) == 8

    zealot_births = [
        event
        for event in parsed.events
        if event.kind == "unit_born" and event.name == "Zealot"
    ]
    assert len(zealot_births) == 42

    army_units = [
        unit
        for unit in parsed.units
        if not unit.is_worker and not unit.is_building
    ]
    assert len(army_units) > 100


def test_alive_army_at_five_minutes() -> None:
    parsed = parse_replay(REPLAY)
    at_five_minutes = [
        unit
        for unit in parsed.units
        if unit.born_t_sec <= 300
        and (unit.died_t_sec is None or unit.died_t_sec > 300)
        and not unit.is_worker
        and not unit.is_building
    ]
    assert len(at_five_minutes) > 0
    assert any(unit.unit_type == "Marine" for unit in at_five_minutes)


def test_zerg_variant_names_are_canonicalized() -> None:
    assert canonical_unit_name("LurkerMP") == "Lurker"
    assert canonical_unit_name("LurkerMPBurrowed") == "Lurker"
    assert canonical_unit_name("LurkerMPEgg") == "Lurker"
    assert canonical_unit_name("LurkerDenMP") == "LurkerDen"
    assert canonical_unit_name("BroodLordCocoon") == "BroodLord"
    assert canonical_unit_name("OverlordCocoon") == "Overseer"
    assert canonical_unit_name("BanelingCocoon") == "Baneling"
    assert canonical_unit_name("RavagerCocoon") == "Ravager"


def test_display_fps_ignores_cooperative_bit_for_ai_games() -> None:
    replay = SimpleNamespace(
        game_fps=16.0,
        build=98370,
        players=[SimpleNamespace(commander="")],
    )
    st_data = {"frames_per_second": 16, "cooperative": True}

    assert display_fps(replay, st_data) == pytest.approx(22.4)


def test_display_fps_uses_coop_rate_for_real_coop_replays() -> None:
    replay = SimpleNamespace(
        game_fps=16.0,
        build=98370,
        players=[SimpleNamespace(commander="Raynor")],
    )

    assert display_fps(replay, {"frames_per_second": 16}) == 16
