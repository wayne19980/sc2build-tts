from __future__ import annotations

from pathlib import Path

from sc2analyzer.parser import canonical_unit_name, parse_replay

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
    assert 620 < parsed.duration_sec < 621
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
