"""Audit logger — JSONL append-only record of every agent turn.

Each turn = one JSON line containing:
  - player input
  - snapshot before
  - full agent trace (tool calls, thinking)
  - cited laws (extracted from query_laws results)
  - all writes performed
  - narration produced
  - snapshot after
"""
import json
from pathlib import Path
from datetime import datetime


WRITE_TOOL_NAMES = {
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


class AuditLogger:
    """Append-only audit logger writing one JSON record per turn."""

    def __init__(self, path: str | Path, dry_run: bool = False):
        self.path = Path(path)
        self.dry_run = dry_run
        self._turn_counter = 0
        self._current: dict | None = None
        self._last: dict | None = None
        if not dry_run:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            # count existing turns to keep monotonic numbering
            if self.path.exists():
                with self.path.open("r", encoding="utf-8") as f:
                    self._turn_counter = sum(1 for _ in f)

    # ------------------------------------------------------------------
    def start_turn(self, player_input: str, snapshot: dict) -> None:
        self._turn_counter += 1
        self._current = {
            "turn": self._turn_counter,
            "timestamp": datetime.now().isoformat(),
            "player_input": player_input,
            "snapshot_before": snapshot,
            "agent_trace": [],
            "cited_laws": [],
            "writes": [],
            "narration": None,
            "snapshot_after": None,
        }

    def record_tool_call(self, name: str, args: dict, result: dict) -> None:
        if self._current is None:
            return
        step = {
            "type": "tool_use",
            "name": name,
            "input": args,
            "output": result,
        }
        self._current["agent_trace"].append(step)

        if name == "query_laws" and isinstance(result, dict):
            for law in result.get("laws", []):
                lid = law.get("id")
                if lid and lid not in self._current["cited_laws"]:
                    self._current["cited_laws"].append(lid)

        if name in WRITE_TOOL_NAMES:
            self._current["writes"].append({"tool": name, "args": args,
                                             "result": result})

    def record_thinking(self, text: str) -> None:
        if self._current is None:
            return
        self._current["agent_trace"].append({
            "type": "thinking", "text": text,
        })

    def end_turn(self, narration: str, final_snapshot: dict) -> dict:
        if self._current is None:
            raise RuntimeError("end_turn called without start_turn")
        self._current["narration"] = narration
        self._current["snapshot_after"] = final_snapshot
        rec = self._current
        self._last = rec
        if not self.dry_run:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self._current = None
        return rec

    def last_record(self) -> dict | None:
        return self._last
