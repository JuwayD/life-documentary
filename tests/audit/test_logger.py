"""Tests for the audit log — JSONL append-only logger."""
import json
from pathlib import Path
import pytest
from mingrpg.audit.logger import AuditLogger


@pytest.fixture
def logger(tmp_path):
    return AuditLogger(tmp_path / "audit.jsonl")


def test_start_and_end_turn_writes_jsonl(logger, tmp_path):
    logger.start_turn(player_input="我打知府",
                       snapshot={"entities": [], "time": {}})
    logger.record_tool_call("get_entity", {"entity_id": "player"},
                             {"id": "player"})
    logger.record_thinking("玩家要打人,我得查法律")
    logger.end_turn(narration="衙役按住了你。", final_snapshot={"flag": True})

    log_path = tmp_path / "audit.jsonl"
    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1  # one turn = one JSON record
    rec = json.loads(lines[0])
    assert rec["player_input"] == "我打知府"
    assert rec["narration"] == "衙役按住了你。"
    assert len(rec["agent_trace"]) == 2  # tool + thinking
    assert rec["agent_trace"][0]["type"] == "tool_use"
    assert rec["agent_trace"][1]["type"] == "thinking"


def test_multiple_turns_append_distinct_records(logger, tmp_path):
    for i in range(3):
        logger.start_turn(player_input=f"action {i}",
                           snapshot={})
        logger.end_turn(narration=f"result {i}",
                         final_snapshot={})

    log_path = tmp_path / "audit.jsonl"
    lines = log_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 3
    for i, line in enumerate(lines):
        rec = json.loads(line)
        assert rec["player_input"] == f"action {i}"
        assert rec["turn"] == i + 1


def test_audit_captures_cited_laws(logger, tmp_path):
    logger.start_turn(player_input="x", snapshot={})
    logger.record_tool_call("query_laws", {"keywords": ["打"]},
                             {"laws": [{"id": "law.x", "text": "..."}]})
    logger.end_turn(narration="y", final_snapshot={})

    rec = json.loads((tmp_path / "audit.jsonl").read_text().strip())
    assert "law.x" in rec["cited_laws"]


def test_audit_dry_run_doesnt_write(tmp_path):
    """Dry-run mode buffers but doesn't persist."""
    logger = AuditLogger(tmp_path / "audit.jsonl", dry_run=True)
    logger.start_turn(player_input="x", snapshot={})
    logger.end_turn(narration="y", final_snapshot={})
    assert not (tmp_path / "audit.jsonl").exists()
    assert logger.last_record() is not None
