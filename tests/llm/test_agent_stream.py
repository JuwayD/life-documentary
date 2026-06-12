"""Tests for GMAgent streaming (mocked Anthropic client)."""
import json
from unittest.mock import MagicMock, patch

import pytest

from mingrpg.audit.logger import AuditLogger
from mingrpg.core.world import World
from mingrpg.llm.agent import GMAgent
from mingrpg.llm.tools_registry import build_tool_registry
from mingrpg.scenarios.yangzhou_court import seed_yangzhou_court
from mingrpg.scenarios.yangzhou_market import seed_yangzhou_market
from mingrpg.scenarios.yangzhou_inn import seed_yangzhou_inn
from mingrpg.scenarios.yangzhou_districts import seed_yangzhou_districts


class FakeTextBlock:
    type = "text"
    text = ""


class FakeToolUseBlock:
    type = "tool_use"
    name = "get_entity"
    input = {"entity_id": "player"}


class FakeResponse:
    stop_reason = "end_turn"
    content = []


def _make_response(blocks, stop_reason="end_turn"):
    resp = MagicMock()
    resp.content = blocks
    resp.stop_reason = stop_reason
    return resp


def _make_text_block(text):
    block = MagicMock()
    block.type = "text"
    block.text = text
    return block


def _make_tool_use_block(name="get_entity", input_data=None):
    block = MagicMock()
    block.type = "tool_use"
    block.name = name
    block.id = f"tool_001"
    block.input = input_data or {"entity_id": "player"}
    return block


@pytest.fixture
def gm():
    world = World(":memory:")
    seed_yangzhou_court(world)
    audit = AuditLogger(":memory:", dry_run=True)
    agent = GMAgent(
        world=world,
        audit=audit,
        model="test",
        api_key="test-key",
        base_url="http://localhost/test",
    )
    return agent


def test_phase5b_economy_tools_are_registered(gm):
    registry = build_tool_registry(gm.world)
    assert "purchase_item" in registry
    assert "hire_service" in registry
    assert "unit_price_wen" in registry["purchase_item"]["schema"]["input_schema"]["properties"]
    assert "service_id" in registry["hire_service"]["schema"]["input_schema"]["properties"]


def test_phase5bc_story_progress_tools_are_registered(gm):
    registry = build_tool_registry(gm.world)
    assert "record_clue" in registry
    assert "advance_pressure_clock" in registry
    assert "thread_id" in registry["record_clue"]["schema"]["input_schema"]["properties"]
    assert "clock_id" in registry["advance_pressure_clock"]["schema"]["input_schema"]["properties"]


def test_phase6_step2_advisor_tools_are_registered(gm):
    registry = build_tool_registry(gm.world)
    assert "ask_advisor" in registry
    assert "list_advisors" in registry
    assert "advisor_id" in registry["ask_advisor"]["schema"]["input_schema"]["properties"]
    assert "question" in registry["ask_advisor"]["schema"]["input_schema"]["properties"]
    assert "required" in registry["ask_advisor"]["schema"]["input_schema"]
    assert "advisor_id" in registry["ask_advisor"]["schema"]["input_schema"]["required"]
    assert "location_id" in registry["list_advisors"]["schema"]["input_schema"]["properties"]


def test_phase6_step3_observation_tools_are_registered(gm):
    registry = build_tool_registry(gm.world)
    assert "list_observables" in registry
    assert "discover_observation" in registry
    assert "actor_id" in registry["list_observables"]["schema"]["input_schema"]["properties"]
    assert "detail_id" in registry["discover_observation"]["schema"]["input_schema"]["properties"]
    assert "detail_id" in registry["discover_observation"]["schema"]["input_schema"]["required"]


def test_phase6_step4_party_tools_are_registered(gm):
    registry = build_tool_registry(gm.world)
    for name in ["list_party", "join_party", "leave_party", "set_active_actor"]:
        assert name in registry
    assert "entity_id" in registry["join_party"]["schema"]["input_schema"]["properties"]
    assert "entity_id" in registry["leave_party"]["schema"]["input_schema"]["required"]
    assert "entity_id" in registry["set_active_actor"]["schema"]["input_schema"]["required"]


def test_phase6_multi_ending_tools_are_registered(gm):
    registry = build_tool_registry(gm.world)
    assert "list_endings" in registry
    assert "record_ending" in registry
    assert "ending_id" in registry["record_ending"]["schema"]["input_schema"]["required"]
    assert "final" in registry["record_ending"]["schema"]["input_schema"]["properties"]


def test_process_input_stream_can_execute_join_party(gm):
    tool_block = _make_tool_use_block("join_party", {
        "entity_id": "shiye",
        "role": "府衙向导",
        "joined_reason": "临时带路",
    })
    text_block = _make_text_block("刘师爷点头,暂随你同行。")
    response1 = _make_response([tool_block], stop_reason="tool_use")
    response2 = _make_response([text_block])

    with patch.object(gm.client.messages, "create",
                      side_effect=[response1, response2]):
        events = list(gm.process_input_stream("请刘师爷同行"))

    tr = next(e for e in events if e["type"] == "tool_result")
    assert "error" not in tr["output"]
    assert tr["output"]["joined"] is True
    party = gm.world.get_flag("party")
    assert any(m["entity_id"] == "shiye" for m in party["members"])


def test_process_input_stream_can_execute_record_ending(gm):
    tool_block = _make_tool_use_block("record_ending", {
        "ending_id": "official_vindication",
        "title": "公堂昭雪",
        "summary": "证据齐备,王知府正式收案。",
        "outcome": "玩家民望上升",
        "final": True,
    })
    text_block = _make_text_block("堂上惊木一响,案情终得昭雪。")
    response1 = _make_response([tool_block], stop_reason="tool_use")
    response2 = _make_response([text_block])

    with patch.object(gm.client.messages, "create",
                      side_effect=[response1, response2]):
        events = list(gm.process_input_stream("呈上全部证据,请求结案"))

    tr = next(e for e in events if e["type"] == "tool_result")
    assert "error" not in tr["output"]
    assert tr["output"]["final"] is True
    progress = gm.world.get_flag("ending_progress")
    assert progress["final_ending_id"] == "official_vindication"


def test_process_input_stream_can_execute_discover_observation(gm):
    tool_block = _make_tool_use_block("discover_observation", {
        "detail_id": "court_hall_case_table",
        "target_id": "court_hall",
        "actor_id": "player",
    })
    text_block = _make_text_block("你瞧见案角压着状纸。")
    response1 = _make_response([tool_block], stop_reason="tool_use")
    response2 = _make_response([text_block])

    with patch.object(gm.client.messages, "create",
                      side_effect=[response1, response2]):
        events = list(gm.process_input_stream("仔细观察公案"))

    tr = next(e for e in events if e["type"] == "tool_result")
    assert "error" not in tr["output"]
    assert tr["output"]["detail_id"] == "court_hall_case_table"
    observations = gm.world.get_flag("observations")
    assert "location:court_hall:court_hall_case_table" in observations["player"]


def test_process_input_stream_can_execute_ask_advisor(gm):
    """Streaming should execute ask_advisor tool and return results."""
    tool_block = _make_tool_use_block("ask_advisor", {
        "advisor_id": "shiye",
        "question": "我现在该怎么办?",
        "player_id": "player",
    })
    text_block = _make_text_block("刘师爷捻须沉吟,说...")
    response1 = _make_response([tool_block], stop_reason="tool_use")
    response2 = _make_response([text_block])

    with patch.object(gm.client.messages, "create",
                      side_effect=[response1, response2]):
        events = list(gm.process_input_stream("请教刘师爷"))

    types = [e["type"] for e in events]
    assert "tool_call" in types
    assert "tool_result" in types
    tc = next(e for e in events if e["type"] == "tool_call")
    assert tc["name"] == "ask_advisor"
    tr = next(e for e in events if e["type"] == "tool_result")
    assert "error" not in tr["output"]
    assert tr["output"]["advisor_name"] == "刘师爷"

    # Verify memory and event were created
    shiye = gm.world.get_entity("shiye")
    assert len(shiye["attributes"]["memories"]) >= 1
    events_list = gm.world.list_events()
    assert any(e["type"] == "ask_advisor" for e in events_list)


def test_phase5bc_story_materials_in_snapshot_summary():
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)
    audit = AuditLogger(":memory:", dry_run=True)
    agent = GMAgent(
        world=world,
        audit=audit,
        model="test",
        api_key="test-key",
        base_url="http://localhost/test",
    )

    summary = agent._summarize_snapshot(world.snapshot())

    assert "可用剧情素材" in summary
    assert "状告漕帮恶霸" in summary
    assert "藏书楼失书" in summary
    assert "academy_missing_book" in summary


def test_process_input_stream_yields_text_and_done(gm):
    """Streaming should yield text blocks then a done event."""
    text_block = _make_text_block("你向知府深深一揖。")
    response = _make_response([text_block])

    with patch.object(gm.client.messages, "create", return_value=response):
        events = list(gm.process_input_stream("我向知府行礼"))

    types = [e["type"] for e in events]
    assert "text" in types
    assert "done" in types
    # done should have narration and state
    done = next(e for e in events if e["type"] == "done")
    assert "narration" in done
    assert "state" in done
    assert "entities" in done["state"]


def test_process_input_stream_yields_tool_calls(gm):
    """Streaming should yield tool_call events for tool_use blocks."""
    tool_block = _make_tool_use_block("get_entity", {"entity_id": "player"})
    text_block = _make_text_block("叙述文本。")
    response = _make_response([tool_block, text_block])

    with patch.object(gm.client.messages, "create", return_value=response):
        events = list(gm.process_input_stream("看看我是谁"))

    types = [e["type"] for e in events]
    assert "tool_call" in types
    tc = next(e for e in events if e["type"] == "tool_call")
    assert tc["name"] == "get_entity"
    assert tc["input"] == {"entity_id": "player"}


def test_process_input_stream_yields_tool_results(gm):
    """After a tool_call, should yield tool_result events."""
    tool_block = _make_tool_use_block("get_entity", {"entity_id": "player"})
    response1 = _make_response([tool_block], stop_reason="tool_use")

    text_block = _make_text_block("你是无名书生。")
    response2 = _make_response([text_block])

    with patch.object(gm.client.messages, "create",
                      side_effect=[response1, response2]):
        events = list(gm.process_input_stream("看看我是谁"))

    types = [e["type"] for e in events]
    assert "tool_call" in types
    assert "tool_result" in types
    tr = next(e for e in events if e["type"] == "tool_result")
    assert tr["name"] == "get_entity"
    assert "output" in tr


def test_process_input_stream_handles_unknown_tool(gm):
    """Unknown tool should yield error in tool_result."""
    unknown_block = _make_tool_use_block("nonexistent_tool", {})
    text_block = _make_text_block("无法执行。")
    response1 = _make_response([unknown_block], stop_reason="tool_use")
    response2 = _make_response([text_block])

    with patch.object(gm.client.messages, "create",
                      side_effect=[response1, response2]):
        events = list(gm.process_input_stream("做一件怪事"))

    tr = next(e for e in events if e["type"] == "tool_result")
    assert "error" in tr["output"]
    assert "unknown tool" in tr["output"]["error"]


def test_process_input_stream_handles_exception(gm):
    """If LLM call throws, should yield error event."""
    with patch.object(gm.client.messages, "create",
                      side_effect=RuntimeError("API down")):
        events = list(gm.process_input_stream("测试错误"))

    types = [e["type"] for e in events]
    assert "error" in types
    err = next(e for e in events if e["type"] == "error")
    assert "API down" in err["message"]


def test_process_input_stream_defaults_when_no_text(gm):
    """When LLM produces no text, narration should default."""
    response = _make_response([])

    with patch.object(gm.client.messages, "create", return_value=response):
        events = list(gm.process_input_stream("说点什么"))

    done = next(e for e in events if e["type"] == "done")
    assert "沉默" in done["narration"] or done["narration"]
