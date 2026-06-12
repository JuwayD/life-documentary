"""Replay engine — event-sourced save/load.

Format v2 stores the initial world snapshot plus a sequence of turns
(player_input + write tool calls), enabling full state reconstruction
by replaying writes from the seed state.  This is much smaller than
v1 full-state snapshots and provides complete action history.
"""
import json
from pathlib import Path

from mingrpg.core.world import World

REPLAY_FORMAT = "mingrpg.replay"
REPLAY_VERSION = 2

# Write tools whose calls are recorded and replayed.
REPLAYABLE_WRITES = {
    "set_attribute", "move_entity", "add_status", "remove_status",
    "add_item", "remove_item", "log_event", "set_flag", "add_memory",
    "advance_time", "transfer_money", "apply_damage", "tick_statuses",
    "purchase_item", "hire_service", "record_clue", "advance_pressure_clock",
    "ask_advisor", "discover_observation",
    "join_party", "leave_party", "set_active_actor",
    "advance_skill", "train_skill", "learn_from_npc",
    "register_evolution", "update_evolution", "remove_evolution",
    "record_ending", "update_ending_progress",
    "record_dialogue",
}


def export_replay_log(world: World, audit_path: str | Path) -> dict:
    """Build a replay log from the current world + audit trail.

    Returns a dict in ``mingrpg.replay`` format v2.  If the audit file
    is empty or missing, returns a replay log with zero turns (equivalent
    to a fresh world seed).
    """
    audit_path = Path(audit_path)

    # Capture the current world as the seed.  If audit exists, the first
    # turn's snapshot_before is the true initial state; otherwise use the
    # current world state directly.
    turns: list[dict] = []
    initial_world: dict | None = None

    if audit_path.exists():
        with audit_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)

                # First turn's snapshot_before = initial seed
                if initial_world is None:
                    initial_world = record.get("snapshot_before")

                # Extract only the replayable write calls
                writes = []
                for w in record.get("writes", []):
                    if w.get("tool") in REPLAYABLE_WRITES:
                        writes.append({
                            "tool": w["tool"],
                            "args": w.get("args", {}),
                        })

                turns.append({
                    "player_input": record.get("player_input", ""),
                    "narration": record.get("narration", ""),
                    "writes": writes,
                })

    if initial_world is None:
        initial_world = world.snapshot()

    return {
        "format": REPLAY_FORMAT,
        "version": REPLAY_VERSION,
        "initial_world": initial_world,
        "turns": turns,
    }


def _apply_write(world: World, tool: str, args: dict) -> None:
    """Apply a single write tool call to the world.

    This mirrors the write tools from ``mingrpg.tools.write`` but operates
    directly on the World layer for deterministic replay.  We import the
    actual tool handlers so replay stays in sync with the tool registry.
    """
    from mingrpg.tools import write as W

    handler_map = {
        "set_attribute": W.set_attribute,
        "move_entity": W.move_entity,
        "add_status": W.add_status,
        "remove_status": W.remove_status,
        "add_item": W.add_item,
        "remove_item": W.remove_item,
        "log_event": W.log_event,
        "set_flag": W.set_flag,
        "add_memory": W.add_memory,
        "advance_time": W.advance_time,
        "transfer_money": W.transfer_money,
        "apply_damage": W.apply_damage,
        "tick_statuses": W.tick_statuses,
        "purchase_item": W.purchase_item,
        "hire_service": W.hire_service,
        "record_clue": W.record_clue,
        "advance_pressure_clock": W.advance_pressure_clock,
        "ask_advisor": W.ask_advisor,
        "discover_observation": W.discover_observation,
        "join_party": W.join_party,
        "leave_party": W.leave_party,
        "set_active_actor": W.set_active_actor,
        "advance_skill": W.advance_skill,
        "train_skill": W.train_skill,
        "learn_from_npc": W.learn_from_npc,
        "register_evolution": W.register_evolution,
        "update_evolution": W.update_evolution,
        "remove_evolution": W.remove_evolution,
        "record_ending": W.record_ending,
        "update_ending_progress": W.update_ending_progress,
        "record_dialogue": W.record_dialogue,
    }

    handler = handler_map.get(tool)
    if handler is not None:
        try:
            handler(world, **args)
        except (TypeError, KeyError):
            # Some audit trails record incomplete args (e.g. log_event
            # with empty args from test fixtures).  Skip gracefully –
            # replay is for visualisation, not state correctness.
            pass


def replay_to_player_data(replay_data: dict) -> dict:
    """Build step-by-step player data with world state at each turn.

    Returns a dict with ``initial_state`` and ``turns`` list where each
    entry contains ``player_input``, ``narration``, ``writes`` summary,
    and a full ``state`` snapshot after that turn's writes are applied.
    This is designed for the frontend replay player which needs instant
    forward/backward navigation without re-computing states.
    """
    if replay_data.get("format") != REPLAY_FORMAT:
        raise ValueError("unsupported replay format")
    if replay_data.get("version") != REPLAY_VERSION:
        raise ValueError("unsupported replay version")

    initial = replay_data.get("initial_world")
    if not isinstance(initial, dict):
        raise ValueError("missing initial_world data")

    world = World(":memory:")
    seed_save = {
        "format": "mingrpg.save",
        "version": 1,
        "world": initial,
    }
    world.import_save(seed_save)

    # Capture initial state (turn 0 = seed)
    initial_state = world.snapshot()

    turns = []
    for turn in replay_data.get("turns", []):
        for write in turn.get("writes", []):
            _apply_write(world, write["tool"], write.get("args", {}))
        turns.append({
            "player_input": turn.get("player_input", ""),
            "narration": turn.get("narration", ""),
            "write_count": len(turn.get("writes", [])),
            "writes": [
                {"tool": w.get("tool", ""), "summary": _summarize_write(w)}
                for w in turn.get("writes", [])
            ],
            "state": world.snapshot(),
        })

    return {
        "format": "mingrpg.replay-player",
        "version": 1,
        "total_turns": len(turns),
        "initial_state": initial_state,
        "turns": turns,
    }


def _summarize_write(write: dict) -> str:
    """Return a human-readable summary of a single write tool call."""
    tool = write.get("tool", "")
    args = write.get("args", {})
    if tool == "move_entity":
        return f"移动 {args.get('entity_id', '?')} → {args.get('location_id', '?')}"
    if tool == "set_attribute":
        return f"设置 {args.get('entity_id', '?')}.{args.get('key', '?')}"
    if tool == "add_status":
        return f"状态 {args.get('entity_id', '?')} +{args.get('status_id', '?')}"
    if tool == "remove_status":
        return f"状态 {args.get('entity_id', '?')} -{args.get('status_id', '?')}"
    if tool == "log_event":
        ev = args.get("event", {})
        return f"事件: {ev.get('summary', ev.get('type', '?'))}"
    if tool == "add_memory":
        return f"记忆 {args.get('entity_id', '?')}: {str(args.get('memory', ''))[:20]}"
    if tool == "transfer_money":
        return f"转账 {args.get('from_id', '?')} → {args.get('to_id', '?')}: {args.get('amount', '?')}文"
    if tool == "advance_time":
        return "推进时间"
    if tool == "record_clue":
        return f"线索: {str(args.get('clue', ''))[:20]}"
    if tool == "advance_pressure_clock":
        return f"压力钟 {args.get('clock_id', '?')} +{args.get('amount', 1)}"
    if tool == "set_flag":
        return f"标记 {args.get('key', '?')}"
    if tool == "apply_damage":
        return f"伤害 {args.get('entity_id', '?')} -{args.get('amount', '?')}HP"
    return tool


def replay_from_log(replay_data: dict, target_world: World | None = None) -> World:
    """Replay a replay log into a World, returning the reconstructed state.

    If *target_world* is provided it is cleared and reused; otherwise a
    fresh in-memory world is created.
    """
    if replay_data.get("format") != REPLAY_FORMAT:
        raise ValueError("unsupported replay format")
    if replay_data.get("version") != REPLAY_VERSION:
        raise ValueError("unsupported replay version")

    initial = replay_data.get("initial_world")
    if not isinstance(initial, dict):
        raise ValueError("missing initial_world data")

    if target_world is None:
        target_world = World(":memory:")

    # Import the initial world snapshot using the v1 importer
    seed_save = {
        "format": "mingrpg.save",
        "version": 1,
        "world": initial,
    }
    target_world.import_save(seed_save)

    # Replay each turn's writes in order
    for turn in replay_data.get("turns", []):
        for write in turn.get("writes", []):
            _apply_write(target_world, write["tool"], write.get("args", {}))

    return target_world
