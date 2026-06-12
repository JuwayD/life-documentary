"""Tests for the event-sourced replay engine."""
import json
import tempfile
from pathlib import Path

import pytest

from mingrpg.audit.logger import AuditLogger
from mingrpg.core.replay import (
    REPLAY_FORMAT, REPLAY_VERSION,
    export_replay_log, replay_from_log,
)
from mingrpg.core.world import World


@pytest.fixture
def world():
    return World(":memory:")


def _seed_world(w: World):
    """Seed a minimal world for testing."""
    w.save_entity({
        "id": "player", "name": "书生", "type": "player",
        "location": "court_hall", "pos": [3, 5],
        "attributes": {"hp": 100, "money_wen": 50},
        "status_effects": [], "inventory": [], "tags": [],
    })
    w.save_entity({
        "id": "zhifu", "name": "王知府", "type": "npc",
        "location": "court_hall", "pos": [5, 5],
        "attributes": {"hp": 80}, "status_effects": [],
        "inventory": [], "tags": [],
    })
    w.save_location({
        "id": "court_hall", "name": "府衙大堂", "type": "indoor",
        "size": [10, 10], "exits": {"south": "court_yard"}, "tags": [],
    })


def _make_audit(world: World, tmp_path: Path) -> Path:
    """Create an audit logger, run a turn, return the audit path."""
    audit_path = tmp_path / "audit.jsonl"
    audit = AuditLogger(str(audit_path))

    snap = world.snapshot()
    audit.start_turn("我向知府行礼", snap)
    # Simulate a write tool call
    audit.record_tool_call("set_attribute", {
        "entity_id": "player", "attr": "mood", "value": "恭敬",
    }, {"ok": True})
    audit.record_tool_call("move_entity", {
        "entity_id": "player", "to_pos": [5, 4],
    }, {"ok": True})
    final_snap = world.snapshot()
    # Apply the actual writes so snapshot_after differs
    from mingrpg.tools.write import set_attribute, move_entity
    set_attribute(world, entity_id="player", attr="mood", value="恭敬")
    move_entity(world, entity_id="player", to_pos=[5, 4])
    final_snap = world.snapshot()
    audit.end_turn("你向王知府深深一揖。", final_snap)

    return audit_path


# ---- export_replay_log ----

def test_export_replay_log_format(world, tmp_path):
    _seed_world(world)
    audit_path = _make_audit(world, tmp_path)

    replay = export_replay_log(world, audit_path)

    assert replay["format"] == REPLAY_FORMAT
    assert replay["version"] == REPLAY_VERSION
    assert "initial_world" in replay
    assert "turns" in replay
    assert len(replay["turns"]) == 1


def test_export_replay_log_turn_structure(world, tmp_path):
    _seed_world(world)
    audit_path = _make_audit(world, tmp_path)

    replay = export_replay_log(world, audit_path)
    turn = replay["turns"][0]

    assert turn["player_input"] == "我向知府行礼"
    assert turn["narration"] == "你向王知府深深一揖。"
    assert len(turn["writes"]) == 2
    assert turn["writes"][0]["tool"] == "set_attribute"
    assert turn["writes"][0]["args"]["entity_id"] == "player"
    assert turn["writes"][1]["tool"] == "move_entity"


def test_export_replay_log_empty_audit(world, tmp_path):
    _seed_world(world)
    audit_path = tmp_path / "empty.jsonl"

    replay = export_replay_log(world, audit_path)

    assert replay["format"] == REPLAY_FORMAT
    assert len(replay["turns"]) == 0
    assert "entities" in replay["initial_world"]


def test_export_replay_log_no_audit_file(world):
    _seed_world(world)

    replay = export_replay_log(world, "/nonexistent/path/audit.jsonl")

    assert replay["format"] == REPLAY_FORMAT
    assert len(replay["turns"]) == 0


def test_export_replay_log_filters_non_replayable(world, tmp_path):
    """Read-only tool calls should not appear in replay writes."""
    _seed_world(world)
    audit_path = tmp_path / "audit.jsonl"
    audit = AuditLogger(str(audit_path))

    snap = world.snapshot()
    audit.start_turn("看看周围", snap)
    # Read tool — should be filtered out
    audit.record_tool_call("get_entity", {"entity_id": "player"}, {"id": "player"})
    # Write tool — should be included
    audit.record_tool_call("set_flag", {"key": "looked_around", "value": True}, {"ok": True})
    audit.end_turn("你环顾四周。", world.snapshot())

    replay = export_replay_log(world, audit_path)
    turn = replay["turns"][0]

    assert len(turn["writes"]) == 1
    assert turn["writes"][0]["tool"] == "set_flag"


# ---- replay_from_log ----

def test_replay_round_trip(world, tmp_path):
    """Export then import should reconstruct equivalent world state."""
    _seed_world(world)
    audit_path = _make_audit(world, tmp_path)

    replay = export_replay_log(world, audit_path)

    # Replay into a fresh world
    world2 = replay_from_log(replay)

    # Check entities were reconstructed
    player = world2.get_entity("player")
    assert player is not None
    assert player["name"] == "书生"
    # The mood attribute was set during the turn
    assert player["attributes"].get("mood") == "恭敬"

    # Check locations survived
    loc = world2.get_location("court_hall")
    assert loc is not None
    assert loc["name"] == "府衙大堂"


def test_replay_empty_log(world):
    """Replaying a log with zero turns should produce the seed state."""
    seed = world.snapshot()
    replay = {
        "format": REPLAY_FORMAT,
        "version": REPLAY_VERSION,
        "initial_world": seed,
        "turns": [],
    }

    world2 = replay_from_log(replay)
    # Default time should be present
    t = world2.get_world_time()
    assert "year" in t


def test_replay_preserves_set_flag(world, tmp_path):
    """set_flag calls should be replayed."""
    _seed_world(world)
    audit_path = tmp_path / "audit.jsonl"
    audit = AuditLogger(str(audit_path))

    snap = world.snapshot()
    audit.start_turn("我大喊冤枉", snap)
    from mingrpg.tools.write import set_flag
    set_flag(world, key="shouted_injustice", value=True)
    audit.record_tool_call("set_flag", {"key": "shouted_injustice", "value": True}, {"ok": True})
    audit.end_turn("你在公堂上大喊冤枉。", world.snapshot())

    replay = export_replay_log(world, audit_path)
    world2 = replay_from_log(replay)

    assert world2.get_flag("shouted_injustice") is True


def test_replay_preserves_multiple_turns(world, tmp_path):
    """Multiple turns should be replayed in order."""
    _seed_world(world)
    audit_path = tmp_path / "audit.jsonl"
    audit = AuditLogger(str(audit_path))

    # Turn 1
    snap = world.snapshot()
    audit.start_turn("行礼", snap)
    from mingrpg.tools.write import set_attribute
    set_attribute(world, entity_id="player", attr="reputation", value=10)
    audit.record_tool_call("set_attribute", {
        "entity_id": "player", "attr": "reputation", "value": 10,
    }, {"ok": True})
    audit.end_turn("你行了一礼。", world.snapshot())

    # Turn 2
    snap = world.snapshot()
    audit.start_turn("递状纸", snap)
    set_attribute(world, entity_id="player", attr="reputation", value=20)
    audit.record_tool_call("set_attribute", {
        "entity_id": "player", "attr": "reputation", "value": 20,
    }, {"ok": True})
    audit.end_turn("你递上状纸。", world.snapshot())

    replay = export_replay_log(world, audit_path)
    world2 = replay_from_log(replay)

    player = world2.get_entity("player")
    # Last write wins
    assert player["attributes"]["reputation"] == 20


def test_replay_invalid_format(world):
    with pytest.raises(ValueError, match="unsupported replay format"):
        replay_from_log({"format": "other", "version": 2, "initial_world": {}, "turns": []})


def test_replay_invalid_version(world):
    with pytest.raises(ValueError, match="unsupported replay version"):
        replay_from_log({"format": REPLAY_FORMAT, "version": 99, "initial_world": {}, "turns": []})


def test_replay_missing_initial_world(world):
    with pytest.raises(ValueError, match="missing initial_world"):
        replay_from_log({"format": REPLAY_FORMAT, "version": 2, "turns": []})


# ---- World.import_replay_log ----

def test_world_import_replay_log(world, tmp_path):
    """World.import_replay_log delegates correctly."""
    _seed_world(world)
    audit_path = _make_audit(world, tmp_path)

    replay = export_replay_log(world, audit_path)

    world2 = World(":memory:")
    world2.import_replay_log(replay)

    player = world2.get_entity("player")
    assert player["attributes"].get("mood") == "恭敬"
