"""Tests for the FastAPI web layer.

Uses a fake GMAgent so tests are fast and deterministic.
"""
import json

import pytest
from fastapi.testclient import TestClient
from mingrpg.web.server import create_app


class FakeAgent:
    """Deterministic stand-in for GMAgent."""

    def __init__(self, world, audit, **_):
        self.world = world
        self.audit = audit
        self.calls: list[str] = []

    def process_input(self, text: str) -> str:
        self.calls.append(text)
        snapshot = self.world.snapshot()
        self.audit.start_turn(player_input=text, snapshot=snapshot)
        # Mutate the world a little so we can verify state propagation
        from mingrpg.tools.write import log_event, discover_observation, join_party, record_ending
        log_result = log_event(self.world, {"actor": "player", "type": "test",
                                             "summary": f"echo: {text}"})
        if "观察" in text:
            result = discover_observation(self.world, "court_hall_case_table",
                                          target_id="court_hall")
            self.audit.record_tool_call("discover_observation",
                                        {"detail_id": "court_hall_case_table"},
                                        result)
        if "同行" in text or "队伍" in text:
            join_party(self.world, "shiye", role="府衙向导", joined_reason="测试同行")
        if "结局" in text or "结案" in text:
            record_ending(self.world, "official_vindication", "公堂昭雪",
                          "证据齐备,府衙正式收案。", outcome="民望上升", final=True)
        self.audit.record_tool_call("log_event",
                                     {"event": {"summary": f"echo: {text}"}},
                                     log_result)
        narration = f"(GM 模拟响应) 你说了: {text}"
        self.audit.end_turn(narration=narration,
                             final_snapshot=self.world.snapshot())
        return narration

    def process_input_stream(self, text: str):
        """Streaming variant for WebSocket tests."""
        narration = self.process_input(text)
        yield {"type": "text", "content": narration}
        yield {"type": "done", "narration": narration,
               "state": self.world.snapshot()}


@pytest.fixture
def client(tmp_path):
    app = create_app(agent_factory=FakeAgent,
                      audit_dir=tmp_path,
                      db_path=":memory:")
    return TestClient(app)


# ----- Health & basic routes -----

def test_index_returns_html(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "人生纪实" in r.text


def test_state_endpoint_returns_snapshot(client):
    r = client.get("/api/state")
    assert r.status_code == 200
    body = r.json()
    assert "entities" in body
    assert "locations" in body
    assert "time" in body
    # 验证默认场景已加载
    ids = [e["id"] for e in body["entities"]]
    assert "player" in ids
    assert "zhifu_wang" in ids


# ----- Birth templates -----


def test_birth_templates_endpoint_lists_defaults(client):
    r = client.get("/api/birth/templates")

    assert r.status_code == 200
    ids = {t["id"] for t in r.json()["templates"]}
    assert {"scholar", "merchant_son", "military_heir", "beggar"} <= ids


def test_birth_template_detail_endpoint_returns_template(client):
    r = client.get("/api/birth/templates/scholar")

    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "落第书生"
    assert body["attributes"]["skills"]["litigation"]["name"] == "讼学"


def test_birth_template_detail_endpoint_404_for_unknown(client):
    r = client.get("/api/birth/templates/ghost")

    assert r.status_code == 404


def test_birth_apply_endpoint_updates_current_world(client):
    r = client.post("/api/birth/apply", json={"template_id": "merchant_son"})

    assert r.status_code == 200
    state = r.json()["state"]
    player = next(e for e in state["entities"] if e["id"] == "player")
    assert player["name"] == "商人之子"
    assert player["location"] == "market_main"
    assert player["attributes"]["money_wen"] == 180
    assert player["attributes"]["skills"]["commerce"]["name"] == "商贸"
    assert state["flags"]["birth_setting"]["template_id"] == "merchant_son"


def test_birth_apply_endpoint_404_for_unknown(client):
    r = client.post("/api/birth/apply", json={"template_id": "ghost"})

    assert r.status_code == 404


# ----- Turn endpoint -----

def test_turn_endpoint_processes_input(client):
    r = client.post("/api/turn", json={"input": "我向知府行礼"})
    assert r.status_code == 200
    body = r.json()
    assert "narration" in body
    assert "我向知府行礼" in body["narration"]
    assert "state" in body  # 应返回新快照


def test_turn_endpoint_rejects_empty_input(client):
    r = client.post("/api/turn", json={"input": "  "})
    assert r.status_code == 400


def test_turn_endpoint_persists_event(client):
    """连续两次回合,事件日志应累积。"""
    client.post("/api/turn", json={"input": "动作1"})
    client.post("/api/turn", json={"input": "动作2"})
    state = client.get("/api/state").json()
    summaries = [e.get("summary", "") for e in state["events"]]
    assert any("动作1" in s for s in summaries)
    assert any("动作2" in s for s in summaries)


def test_state_endpoint_includes_recent_events_for_timeline(client):
    for i in range(12):
        client.post("/api/turn", json={"input": f"时间线动作{i}"})

    state = client.get("/api/state").json()

    assert len(state["events"]) == 10
    summaries = [e.get("summary", "") for e in state["events"]]
    assert not any("时间线动作0" in s for s in summaries)
    assert any("时间线动作11" in s for s in summaries)
    assert all("id" in e for e in state["events"])


# ----- Audit endpoint -----

def test_audit_endpoint_returns_recent_turns(client):
    client.post("/api/turn", json={"input": "测试动作"})
    r = client.get("/api/audit?limit=5")
    assert r.status_code == 200
    body = r.json()
    assert "turns" in body
    assert len(body["turns"]) >= 1
    last = body["turns"][-1]
    assert last["player_input"] == "测试动作"


def test_audit_endpoint_returns_pagination_fields(client):
    for i in range(3):
        client.post("/api/turn", json={"input": f"动作{i}"})
    r = client.get("/api/audit?limit=2")
    assert r.status_code == 200
    body = r.json()
    assert "total" in body
    assert "offset" in body
    assert "has_more" in body
    assert body["total"] >= 3
    assert body["offset"] == 0
    assert len(body["turns"]) == 2


def test_audit_endpoint_offset_skips_recent_turns(client):
    for i in range(3):
        client.post("/api/turn", json={"input": f"偏移动作{i}"})
    r_all = client.get("/api/audit?limit=50")
    r_offset = client.get("/api/audit?limit=50&offset=1")
    assert r_offset.status_code == 200
    body = r_offset.json()
    assert len(body["turns"]) == len(r_all.json()["turns"]) - 1


def test_audit_endpoint_limit_cap_is_500(client):
    r = client.get("/api/audit?limit=1000")
    assert r.status_code == 200
    # Should not error, just cap at 500


# ----- Debug console endpoint -----


def test_debug_console_endpoint_returns_world_audit_and_performance(client):
    client.post("/api/turn", json={"input": "调试动作"})

    r = client.get("/api/debug/console?limit=5")

    assert r.status_code == 200
    body = r.json()
    assert body["world"]["entity_count"] >= 1
    assert body["world"]["location_count"] >= 1
    assert body["world"]["player"]["id"] == "player"
    assert body["world"]["current_location"]["id"] == body["world"]["player"]["location"]
    assert any(e["id"] == "zhifu_wang" for e in body["world"]["entities"])
    assert "story_seeds" in body["world"]["flags"]
    assert body["audit"]["turn_count"] >= 1
    assert body["audit"]["recent_tool_calls"][-1]["name"] == "log_event"
    assert body["audit"]["recent_tool_calls"][-1]["output"]["event"]["summary"] == "echo: 调试动作"
    assert "log_event" in body["audit"]["tool_names"]
    assert body["audit"]["filtered_tool_count"] >= 1
    assert body["performance"]["audit_bytes"] > 0
    assert body["performance"]["snapshot_event_window"] == len(client.get("/api/state").json()["events"])


def test_debug_console_export_returns_filtered_debug_bundle(client):
    client.post("/api/turn", json={"input": "调试观察动作"})

    r = client.get("/api/debug/export?limit=5&tool=discover_observation&q=court_hall_case_table")

    assert r.status_code == 200
    body = r.json()
    assert body["format"] == "mingrpg.debug-bundle"
    assert body["version"] == 1
    assert body["exported_at"].endswith("Z")
    assert body["audit"]["tool_filter"] == "discover_observation"
    assert body["audit"]["query"] == "court_hall_case_table"
    assert body["audit"]["filtered_tool_count"] == 1
    assert body["audit"]["recent_tool_calls"][0]["name"] == "discover_observation"
    assert body["world"]["player"]["id"] == "player"
    assert body["performance"]["audit_bytes"] > 0


def test_debug_console_endpoint_filters_tool_calls(client):
    client.post("/api/turn", json={"input": "调试观察动作"})

    by_name = client.get("/api/debug/console?limit=5&tool=discover_observation")

    assert by_name.status_code == 200
    body = by_name.json()
    assert body["audit"]["tool_filter"] == "discover_observation"
    assert body["audit"]["filtered_tool_count"] == 1
    assert body["audit"]["recent_tool_calls"][0]["name"] == "discover_observation"
    assert {"log_event", "discover_observation"} <= set(body["audit"]["tool_names"])

    by_query = client.get("/api/debug/console?limit=5&q=court_hall_case_table")

    assert by_query.status_code == 200
    calls = by_query.json()["audit"]["recent_tool_calls"]
    assert len(calls) == 1
    assert calls[0]["name"] == "discover_observation"

    empty = client.get("/api/debug/console?limit=5&tool=discover_observation&q=notfound")
    assert empty.status_code == 200
    assert empty.json()["audit"]["recent_tool_calls"] == []


# ----- Reset endpoint -----

def test_reset_endpoint_resets_world(client):
    client.post("/api/turn", json={"input": "搞乱世界"})
    r = client.post("/api/reset")
    assert r.status_code == 200
    state = client.get("/api/state").json()
    # 重置后 player hp 应当满血
    player = next(e for e in state["entities"] if e["id"] == "player")
    assert player["attributes"]["hp"] == player["attributes"]["max_hp"]


def test_reset_endpoint_applies_birth_template(client):
    r = client.post("/api/reset?template_id=beggar")

    assert r.status_code == 200
    state = r.json()["state"]
    player = next(e for e in state["entities"] if e["id"] == "player")
    assert player["name"] == "城中乞儿"
    assert player["location"] == "market_main"
    assert player["attributes"]["money_wen"] == 3
    assert player["attributes"]["skills"]["streetwise"]["name"] == "市井"
    assert state["flags"]["birth_setting"]["template_id"] == "beggar"


def test_reset_endpoint_unknown_template_does_not_reset_current_world(client):
    client.post("/api/birth/apply", json={"template_id": "merchant_son"})

    r = client.post("/api/reset?template_id=ghost")

    assert r.status_code == 404
    state = client.get("/api/state").json()
    player = next(e for e in state["entities"] if e["id"] == "player")
    assert player["name"] == "商人之子"
    assert player["location"] == "market_main"
    assert state["flags"]["birth_setting"]["template_id"] == "merchant_son"


def test_reset_endpoint_birth_template_uses_existing_location(client):
    r = client.post("/api/reset?template_id=military_heir")

    assert r.status_code == 200
    state = r.json()["state"]
    player = next(e for e in state["entities"] if e["id"] == "player")
    locations = {loc["id"] for loc in state["locations"]}
    assert player["location"] == "court_yard"
    assert player["location"] in locations


# ----- WebSocket streaming -----

def test_websocket_turn_streams_events(client):
    with client.websocket_connect("/ws/turn") as ws:
        ws.send_text(json.dumps({"input": "我向知府行礼"}))
        events = []
        for _ in range(20):
            try:
                data = ws.receive_text()
                events.append(json.loads(data))
                if events[-1]["type"] == "done":
                    break
            except Exception:
                break

        types = [e["type"] for e in events]
        assert "text" in types
        assert "done" in types
        # Verify done event has narration and state
        done = next(e for e in events if e["type"] == "done")
        assert "我向知府行礼" in done["narration"]
        assert "entities" in done["state"]


def test_websocket_rejects_empty_input(client):
    with client.websocket_connect("/ws/turn") as ws:
        ws.send_text(json.dumps({"input": "  "}))
        data = ws.receive_text()
        event = json.loads(data)
        assert event["type"] == "error"
        assert "empty" in event["message"]


# ----- Story panel data in snapshot -----

def test_story_seeds_flag_in_snapshot(client):
    """快照应包含 story_seeds flag(主线和支线)。"""
    state = client.get("/api/state").json()
    assert "story_seeds" in state["flags"]
    seeds = state["flags"]["story_seeds"]
    assert "main_thread" in seeds
    assert "side_threads" in seeds
    assert "title" in seeds["main_thread"]


def test_story_progress_and_pressure_clocks_in_snapshot(client):
    """record_clue 和 advance_pressure_clock 后的数据应在快照中。"""
    from mingrpg.tools.write import record_clue, advance_pressure_clock
    from mingrpg.core.world import World

    # 直接操作 world 写入剧情数据
    world = client.app.state.world
    record_clue(world, "main_thread", "测试线索",
                source_entity="王知府", location_id="court_hall")
    advance_pressure_clock(world, "test_clock", amount=1,
                           reason="test", danger_at=3)

    state = client.get("/api/state").json()
    flags = state["flags"]
    assert "story_progress" in flags
    assert flags["story_progress"]["main_thread"]["clues"][0]["clue"] == "测试线索"
    assert "pressure_clocks" in flags
    assert flags["pressure_clocks"]["test_clock"]["value"] == 1


def test_observable_details_present_in_state_snapshot(client):
    state = client.get("/api/state").json()
    hall = next(l for l in state["locations"] if l["id"] == "court_hall")
    detail_ids = [d["id"] for d in hall["observable_details"]]
    assert "court_hall_case_table" in detail_ids
    player = next(e for e in state["entities"] if e["id"] == "player")
    assert player["attributes"]["observation"] == 10


def test_observations_flag_updates_after_observation_turn(client):
    client.post("/api/turn", json={"input": "我仔细观察四周"})
    state = client.get("/api/state").json()
    observations = state["flags"]["observations"]["player"]
    assert "location:court_hall:court_hall_case_table" in observations


def test_advisors_present_in_state_snapshot(client):
    """快照应包含顾问 NPC 的 is_advisor 属性。"""
    state = client.get("/api/state").json()
    advisors = [e for e in state["entities"]
                if (e["attributes"] or {}).get("is_advisor")]
    advisor_ids = {a["id"] for a in advisors}
    assert "shiye" in advisor_ids
    assert "teahouse_owner" in advisor_ids
    assert "teacher_gu" in advisor_ids
    for a in advisors:
        assert len(a["attributes"]["advisor_topics"]) > 0
        assert len(a["attributes"]["advisor_style"]) > 0


def test_party_flag_updates_after_join_turn(client):
    client.post("/api/turn", json={"input": "请刘师爷同行加入队伍"})
    state = client.get("/api/state").json()
    party = state["flags"]["party"]
    assert party["leader_id"] == "player"
    assert any(m["entity_id"] == "shiye" and m["role"] == "府衙向导"
               for m in party["members"])


def test_ending_seeds_present_in_state_snapshot(client):
    state = client.get("/api/state").json()
    seeds = state["flags"]["ending_seeds"]
    assert any(e["id"] == "official_vindication" for e in seeds)


def test_ending_progress_updates_after_ending_turn(client):
    client.post("/api/turn", json={"input": "请求结案并达成结局"})
    state = client.get("/api/state").json()
    progress = state["flags"]["ending_progress"]
    assert progress["final_ending_id"] == "official_vindication"
    assert progress["endings"][0]["title"] == "公堂昭雪"


# ----- Shareable saves -----

def test_save_endpoint_exports_current_world(client):
    client.post("/api/turn", json={"input": "保存前动作"})

    r = client.get("/api/save")

    assert r.status_code == 200
    save = r.json()
    assert save["format"] == "mingrpg.save"
    assert save["version"] == 1
    summaries = [e["summary"] for e in save["world"]["events"]]
    assert any("保存前动作" in s for s in summaries)
    assert any(e["id"] == "player" for e in save["world"]["entities"])


def test_save_import_endpoint_restores_state(client):
    save = client.get("/api/save").json()
    player = next(e for e in save["world"]["entities"] if e["id"] == "player")
    player["attributes"]["hp"] = 42
    save["world"]["flags"]["share_test"] = {"ok": True}

    r = client.post("/api/save/import", json={"save": save})

    assert r.status_code == 200
    state = r.json()["state"]
    imported_player = next(e for e in state["entities"] if e["id"] == "player")
    assert imported_player["attributes"]["hp"] == 42
    assert state["flags"]["share_test"] == {"ok": True}


def test_save_import_endpoint_rejects_bad_save(client):
    r = client.post("/api/save/import", json={"save": {"format": "bad"}})

    assert r.status_code == 400
    assert "unsupported save format" in r.json()["detail"]


# ----- Test scenario snapshots -----


def test_debug_test_snapshots_save_list_and_load_current_world(client):
    client.post("/api/turn", json={"input": "快照前动作"})

    created = client.post("/api/debug/test-snapshots", json={
        "name": "府衙冒烟测试",
        "note": "用于回归验证",
    })

    assert created.status_code == 200
    snapshot = created.json()["snapshot"]
    assert snapshot["name"] == "府衙冒烟测试"
    assert snapshot["note"] == "用于回归验证"
    assert snapshot["id"]

    listing = client.get("/api/debug/test-snapshots")
    assert listing.status_code == 200
    listing_body = listing.json()
    snapshots = listing_body["snapshots"]
    assert snapshots[0]["id"] == snapshot["id"]
    assert snapshots[0]["entity_count"] >= 1
    assert snapshots[0]["flag_count"] >= 1
    assert listing_body["summary"]["snapshot_count"] == 1
    assert listing_body["summary"]["latest_updated_at"] == snapshots[0]["created_at"]
    assert listing_body["summary"]["totals"]["entities"] == snapshots[0]["entity_count"]

    client.post("/api/turn", json={"input": "快照后动作"})
    changed = client.get("/api/state").json()
    assert any("快照后动作" in e.get("summary", "") for e in changed["events"])

    loaded = client.post("/api/debug/test-snapshots/load", json={"snapshot_id": snapshot["id"]})

    assert loaded.status_code == 200
    loaded_snapshot = loaded.json()["snapshot"]
    assert loaded_snapshot["last_loaded_at"].endswith("Z")
    restored = loaded.json()["state"]
    summaries = [e.get("summary", "") for e in restored["events"]]
    assert any("快照前动作" in s for s in summaries)
    assert not any("快照后动作" in s for s in summaries)
    listing_after_load = client.get("/api/debug/test-snapshots").json()["snapshots"][0]
    assert listing_after_load["last_loaded_at"] == loaded_snapshot["last_loaded_at"]


def test_debug_test_snapshot_detail_previews_saved_world(client):
    client.post("/api/debug/test-presets/load", json={"preset_id": "court_clue_pressure"})
    created = client.post("/api/debug/test-snapshots", json={
        "name": "详情快照",
        "note": "查看前确认",
    })
    snapshot_id = created.json()["snapshot"]["id"]

    r = client.get(f"/api/debug/test-snapshots/{snapshot_id}")

    assert r.status_code == 200
    body = r.json()["snapshot"]
    assert body["id"] == snapshot_id
    assert body["name"] == "详情快照"
    assert body["note"] == "查看前确认"
    assert body["entity_count"] >= 1
    assert body["location_count"] >= 1
    assert body["event_count"] >= 2
    assert body["flag_count"] >= 1
    assert body["player"]["id"] == "player"
    assert body["current_location"]["id"] == body["player"]["location"]
    assert "test_preset" in body["flag_keys"]
    assert any("证人压力" in event.get("summary", "") for event in body["recent_events"])



def test_debug_test_snapshot_detail_404_for_unknown(client):
    r = client.get("/api/debug/test-snapshots/missing")

    assert r.status_code == 404



def test_debug_test_snapshot_export_returns_shareable_snapshot_file(client):
    client.post("/api/turn", json={"input": "单个快照导出动作"})
    created = client.post("/api/debug/test-snapshots", json={
        "name": "可导出快照",
        "note": "单文件分享",
    })
    snapshot_id = created.json()["snapshot"]["id"]

    r = client.get(f"/api/debug/test-snapshots/{snapshot_id}/export")

    assert r.status_code == 200
    body = r.json()
    assert body["format"] == "mingrpg.test-snapshot"
    assert body["version"] == 1
    assert body["exported_at"].endswith("Z")
    assert body["id"] == snapshot_id
    assert body["name"] == "可导出快照"
    assert body["note"] == "单文件分享"
    assert body["last_exported_at"] == body["exported_at"]
    assert body["save"]["format"] == "mingrpg.save"
    summaries = [e.get("summary", "") for e in body["save"]["world"]["events"]]
    assert any("单个快照导出动作" in s for s in summaries)
    listing = client.get("/api/debug/test-snapshots").json()["snapshots"][0]
    assert listing["last_exported_at"] == body["exported_at"]



def test_debug_test_snapshot_export_404_for_unknown(client):
    r = client.get("/api/debug/test-snapshots/missing/export")

    assert r.status_code == 404



def test_debug_test_snapshot_duplicate_copies_saved_world_and_metadata(client):
    client.post("/api/turn", json={"input": "复制来源动作"})
    created = client.post("/api/debug/test-snapshots", json={
        "name": "原始快照",
        "note": "原始备注",
        "tags": ["府衙", "回归"],
    }).json()["snapshot"]
    client.post("/api/turn", json={"input": "复制后当前世界动作"})

    r = client.post(f"/api/debug/test-snapshots/{created['id']}/duplicate", json={})

    assert r.status_code == 200
    duplicate = r.json()["snapshot"]
    assert duplicate["id"] != created["id"]
    assert duplicate["name"] == "原始快照 副本"
    assert duplicate["note"] == "原始备注"
    assert duplicate["tags"] == ["府衙", "回归"]
    assert duplicate["duplicated_from"] == created["id"]
    listing = client.get("/api/debug/test-snapshots").json()["snapshots"]
    assert {snapshot["id"] for snapshot in listing} == {created["id"], duplicate["id"]}
    exported = client.get(f"/api/debug/test-snapshots/{duplicate['id']}/export").json()
    summaries = [event.get("summary", "") for event in exported["save"]["world"]["events"]]
    assert any("复制来源动作" in summary for summary in summaries)
    assert not any("复制后当前世界动作" in summary for summary in summaries)



def test_debug_test_snapshot_duplicate_accepts_metadata_overrides(client):
    created = client.post("/api/debug/test-snapshots", json={
        "name": "原始快照",
        "note": "原始备注",
        "tags": ["府衙"],
    }).json()["snapshot"]

    r = client.post(f"/api/debug/test-snapshots/{created['id']}/duplicate", json={
        "name": "派生快照",
        "note": "派生备注",
        "tags": ["街市", "回归", "街市"],
    })

    assert r.status_code == 200
    duplicate = r.json()["snapshot"]
    assert duplicate["name"] == "派生快照"
    assert duplicate["note"] == "派生备注"
    assert duplicate["tags"] == ["街市", "回归"]



def test_debug_test_snapshot_duplicate_rejects_empty_name(client):
    created = client.post("/api/debug/test-snapshots", json={"name": "原始快照"}).json()["snapshot"]

    r = client.post(f"/api/debug/test-snapshots/{created['id']}/duplicate", json={"name": "   "})

    assert r.status_code == 400
    assert "snapshot name cannot be empty" in r.json()["detail"]



def test_debug_test_snapshot_duplicate_404_for_unknown(client):
    r = client.post("/api/debug/test-snapshots/missing/duplicate", json={})

    assert r.status_code == 404



def test_debug_test_snapshot_health_reports_ok_and_problem_snapshots(client):
    first = client.post("/api/debug/test-snapshots", json={"name": "健康快照"}).json()["snapshot"]
    second = client.post("/api/debug/test-snapshots", json={"name": "健康快照"}).json()["snapshot"]
    broken_path = client.app.state.test_snapshots_dir / "broken.json"
    broken_path.write_text(json.dumps({"id": "broken", "name": "坏快照", "save": {"format": "bad"}}, ensure_ascii=False), encoding="utf-8")

    r = client.get("/api/debug/test-snapshots/health")

    assert r.status_code == 200
    body = r.json()
    assert body["snapshot_count"] == 3
    assert body["ok_count"] == 0
    assert body["issue_count"] == 3
    by_id = {snapshot["id"]: snapshot for snapshot in body["issues"]}
    assert "duplicate_name" in by_id[first["id"]]["issues"]
    assert "duplicate_name" in by_id[second["id"]]["issues"]
    assert "unsupported save format" in by_id["broken"]["issues"]



def test_debug_test_snapshot_health_reports_all_clear(client):
    client.post("/api/debug/test-snapshots", json={"name": "唯一快照"})

    r = client.get("/api/debug/test-snapshots/health")

    assert r.status_code == 200
    body = r.json()
    assert body["snapshot_count"] == 1
    assert body["ok_count"] == 1
    assert body["issue_count"] == 0
    assert body["issues"] == []



def test_debug_test_snapshot_health_export_returns_shareable_report(client):
    client.post("/api/debug/test-snapshots", json={"name": "重复快照"})
    client.post("/api/debug/test-snapshots", json={"name": "重复快照"})

    r = client.get("/api/debug/test-snapshots/health/export")

    assert r.status_code == 200
    body = r.json()
    assert body["format"] == "mingrpg.test-snapshot-health"
    assert body["version"] == 1
    assert body["exported_at"].endswith("Z")
    assert body["snapshot_count"] == 2
    assert body["issue_count"] == 2
    assert all("duplicate_name" in snapshot["issues"] for snapshot in body["issues"])



def test_debug_test_snapshot_index_export_lists_all_snapshot_summaries(client):
    client.post("/api/turn", json={"input": "索引导出动作一"})
    first = client.post("/api/debug/test-snapshots", json={"name": "索引快照甲", "note": "第一份"}).json()["snapshot"]
    client.post("/api/turn", json={"input": "索引导出动作二"})
    second = client.post("/api/debug/test-snapshots", json={"name": "索引快照乙", "note": "第二份"}).json()["snapshot"]

    r = client.get("/api/debug/test-snapshots/export-index")

    assert r.status_code == 200
    body = r.json()
    assert body["format"] == "mingrpg.test-snapshot-index"
    assert body["version"] == 1
    assert body["exported_at"].endswith("Z")
    assert body["snapshot_count"] == 2
    assert body["latest_updated_at"] == max(snapshot["created_at"] for snapshot in body["snapshots"])
    assert {snapshot["id"] for snapshot in body["snapshots"]} == {first["id"], second["id"]}
    assert {snapshot["name"] for snapshot in body["snapshots"]} == {"索引快照甲", "索引快照乙"}
    assert body["totals"]["entities"] == sum(snapshot["entity_count"] for snapshot in body["snapshots"])
    assert all("save" not in snapshot for snapshot in body["snapshots"])



def test_debug_test_snapshot_import_restores_exported_snapshot(client):
    client.post("/api/turn", json={"input": "导入前动作"})
    created = client.post("/api/debug/test-snapshots", json={"name": "可导入快照", "note": "单文件恢复"})
    snapshot_id = created.json()["snapshot"]["id"]
    exported = client.get(f"/api/debug/test-snapshots/{snapshot_id}/export").json()
    client.post("/api/turn", json={"input": "导入后动作"})

    r = client.post("/api/debug/test-snapshots/import", json={"snapshot": exported})

    assert r.status_code == 200
    body = r.json()
    assert body["snapshot"]["id"] == snapshot_id
    assert body["snapshot"]["name"] == "可导入快照"
    assert body["snapshot"]["note"] == "单文件恢复"
    summaries = [e.get("summary", "") for e in body["state"]["events"]]
    assert any("导入前动作" in s for s in summaries)
    assert not any("导入后动作" in s for s in summaries)



def test_debug_test_snapshot_import_rejects_bad_snapshot(client):
    r = client.post("/api/debug/test-snapshots/import", json={"snapshot": {"format": "bad"}})

    assert r.status_code == 400
    assert "unsupported test snapshot format" in r.json()["detail"]



def test_debug_test_snapshot_update_edits_metadata_without_changing_save(client):
    created = client.post("/api/debug/test-snapshots", json={
        "name": "旧名",
        "note": "旧备注",
    })
    snapshot_id = created.json()["snapshot"]["id"]
    before = client.get(f"/api/debug/test-snapshots/{snapshot_id}/diff").json()

    r = client.patch(f"/api/debug/test-snapshots/{snapshot_id}", json={
        "name": "新名",
        "note": "新备注",
    })

    assert r.status_code == 200
    snapshot = r.json()["snapshot"]
    assert snapshot["name"] == "新名"
    assert snapshot["note"] == "新备注"
    assert snapshot["updated_at"].endswith("Z")
    listing = client.get("/api/debug/test-snapshots").json()["snapshots"][0]
    assert listing["name"] == "新名"
    assert listing["note"] == "新备注"
    assert listing["updated_at"] == snapshot["updated_at"]
    after = client.get(f"/api/debug/test-snapshots/{snapshot_id}/diff").json()
    assert after["summary"] == before["summary"]



def test_debug_test_snapshot_pinning_sorts_first_and_exports_metadata(client):
    first = client.post("/api/debug/test-snapshots", json={"name": "普通快照"}).json()["snapshot"]
    second = client.post("/api/debug/test-snapshots", json={"name": "置顶快照"}).json()["snapshot"]

    r = client.patch(f"/api/debug/test-snapshots/{second['id']}", json={"pinned": True})

    assert r.status_code == 200
    assert r.json()["snapshot"]["pinned"] is True
    listing = client.get("/api/debug/test-snapshots").json()["snapshots"]
    assert listing[0]["id"] == second["id"]
    assert listing[0]["pinned"] is True
    assert listing[1]["id"] == first["id"]
    detail = client.get(f"/api/debug/test-snapshots/{second['id']}").json()["snapshot"]
    assert detail["pinned"] is True
    exported = client.get(f"/api/debug/test-snapshots/{second['id']}/export").json()
    assert exported["pinned"] is True
    duplicate = client.post(f"/api/debug/test-snapshots/{second['id']}/duplicate", json={}).json()["snapshot"]
    assert duplicate["pinned"] is True
    index = client.get("/api/debug/test-snapshots/export-index").json()
    assert next(snapshot for snapshot in index["snapshots"] if snapshot["id"] == second["id"])["pinned"] is True

    unpinned = client.patch(f"/api/debug/test-snapshots/{second['id']}", json={"pinned": False})

    assert unpinned.status_code == 200
    assert unpinned.json()["snapshot"]["pinned"] is False



def test_debug_test_snapshot_archive_updates_metadata_and_exports(client):
    created = client.post("/api/debug/test-snapshots", json={"name": "待归档快照"}).json()["snapshot"]
    assert created["archived"] is False

    archived = client.patch(f"/api/debug/test-snapshots/{created['id']}", json={"archived": True})

    assert archived.status_code == 200
    assert archived.json()["snapshot"]["archived"] is True
    listing = client.get("/api/debug/test-snapshots").json()["snapshots"]
    assert listing[0]["archived"] is True
    detail = client.get(f"/api/debug/test-snapshots/{created['id']}").json()["snapshot"]
    assert detail["archived"] is True
    exported = client.get(f"/api/debug/test-snapshots/{created['id']}/export").json()
    assert exported["archived"] is True
    index = client.get("/api/debug/test-snapshots/export-index").json()
    assert index["snapshots"][0]["archived"] is True

    restored = client.patch(f"/api/debug/test-snapshots/{created['id']}", json={"archived": False})

    assert restored.status_code == 200
    assert restored.json()["snapshot"]["archived"] is False



def test_debug_test_snapshot_archive_preserved_by_duplicate_and_bundle_import(client):
    created = client.post("/api/debug/test-snapshots", json={"name": "归档来源"}).json()["snapshot"]
    client.patch(f"/api/debug/test-snapshots/{created['id']}", json={"archived": True})

    duplicate = client.post(f"/api/debug/test-snapshots/{created['id']}/duplicate", json={}).json()["snapshot"]
    bundle = client.post("/api/debug/test-snapshots/bulk-export", json={"snapshot_ids": [created["id"]]}).json()
    client.post("/api/debug/test-snapshots/bulk-delete", json={"snapshot_ids": [created["id"], duplicate["id"]]})
    preview = client.post("/api/debug/test-snapshots/bulk-import/preview", json={"bundle": bundle}).json()
    imported = client.post("/api/debug/test-snapshots/bulk-import", json={"bundle": bundle}).json()

    assert duplicate["archived"] is True
    assert preview["snapshots"][0]["archived"] is True
    assert imported["imported"][0]["archived"] is True
    listing = client.get("/api/debug/test-snapshots").json()["snapshots"]
    assert listing[0]["archived"] is True



def test_debug_test_snapshot_tags_are_saved_updated_and_exported(client):
    created = client.post("/api/debug/test-snapshots", json={
        "name": "标签快照",
        "note": "标签回归",
        "tags": ["府衙", "回归", "府衙", ""],
    })

    assert created.status_code == 200
    snapshot = created.json()["snapshot"]
    assert snapshot["tags"] == ["府衙", "回归"]
    snapshot_id = snapshot["id"]
    listing = client.get("/api/debug/test-snapshots").json()["snapshots"][0]
    assert listing["tags"] == ["府衙", "回归"]

    updated = client.patch(f"/api/debug/test-snapshots/{snapshot_id}", json={"tags": ["街市", "回归"]})

    assert updated.status_code == 200
    assert updated.json()["snapshot"]["tags"] == ["街市", "回归"]
    detail = client.get(f"/api/debug/test-snapshots/{snapshot_id}").json()["snapshot"]
    assert detail["tags"] == ["街市", "回归"]
    exported = client.get(f"/api/debug/test-snapshots/{snapshot_id}/export").json()
    assert exported["tags"] == ["街市", "回归"]
    index = client.get("/api/debug/test-snapshots/export-index").json()
    assert index["snapshots"][0]["tags"] == ["街市", "回归"]



def test_debug_test_snapshot_update_rejects_empty_name(client):
    created = client.post("/api/debug/test-snapshots", json={"name": "可编辑快照"})
    snapshot_id = created.json()["snapshot"]["id"]

    r = client.patch(f"/api/debug/test-snapshots/{snapshot_id}", json={"name": "   "})

    assert r.status_code == 400
    assert "snapshot name cannot be empty" in r.json()["detail"]



def test_debug_test_snapshot_update_404_for_unknown(client):
    r = client.patch("/api/debug/test-snapshots/missing", json={"name": "新名"})

    assert r.status_code == 404



def test_debug_test_snapshot_delete_removes_snapshot(client):
    created = client.post("/api/debug/test-snapshots", json={"name": "待删除快照", "note": "临时"})
    snapshot_id = created.json()["snapshot"]["id"]

    r = client.delete(f"/api/debug/test-snapshots/{snapshot_id}")

    assert r.status_code == 200
    assert r.json()["snapshot"]["name"] == "待删除快照"
    listing = client.get("/api/debug/test-snapshots").json()["snapshots"]
    assert all(snapshot["id"] != snapshot_id for snapshot in listing)
    assert client.get(f"/api/debug/test-snapshots/{snapshot_id}/diff").status_code == 404
    assert client.post("/api/debug/test-snapshots/load", json={"snapshot_id": snapshot_id}).status_code == 404



def test_debug_test_snapshot_delete_404_for_unknown(client):
    r = client.delete("/api/debug/test-snapshots/missing")

    assert r.status_code == 404



def test_debug_test_snapshot_bulk_export_returns_selected_snapshot_bundle(client):
    client.post("/api/turn", json={"input": "批量导出动作一"})
    first = client.post("/api/debug/test-snapshots", json={"name": "批量导出甲"}).json()["snapshot"]
    client.post("/api/turn", json={"input": "批量导出动作二"})
    second = client.post("/api/debug/test-snapshots", json={"name": "批量导出乙"}).json()["snapshot"]
    keep = client.post("/api/debug/test-snapshots", json={"name": "不导出"}).json()["snapshot"]

    r = client.post("/api/debug/test-snapshots/bulk-export", json={
        "snapshot_ids": [first["id"], second["id"], first["id"]],
    })

    assert r.status_code == 200
    body = r.json()
    assert body["format"] == "mingrpg.test-snapshot-bundle"
    assert body["version"] == 1
    assert body["exported_at"].endswith("Z")
    assert body["snapshot_count"] == 2
    assert {snapshot["id"] for snapshot in body["snapshots"]} == {first["id"], second["id"]}
    assert keep["id"] not in {snapshot["id"] for snapshot in body["snapshots"]}
    assert all(snapshot["format"] == "mingrpg.test-snapshot" for snapshot in body["snapshots"])
    assert all(snapshot["save"]["format"] == "mingrpg.save" for snapshot in body["snapshots"])
    listing = client.get("/api/debug/test-snapshots").json()["snapshots"]
    assert {snapshot["id"] for snapshot in listing} == {first["id"], second["id"], keep["id"]}



def test_debug_test_snapshot_bulk_export_rejects_empty_selection(client):
    r = client.post("/api/debug/test-snapshots/bulk-export", json={"snapshot_ids": []})

    assert r.status_code == 400
    assert "snapshot ids cannot be empty" in r.json()["detail"]



def test_debug_test_snapshot_bulk_export_404_for_unknown(client):
    r = client.post("/api/debug/test-snapshots/bulk-export", json={"snapshot_ids": ["missing"]})

    assert r.status_code == 404



def test_debug_test_snapshot_bulk_import_preview_summarizes_bundle_without_importing(client):
    client.post("/api/turn", json={"input": "批量预览动作一"})
    first = client.post("/api/debug/test-snapshots", json={"name": "预览包甲", "note": "第一份"}).json()["snapshot"]
    client.post("/api/turn", json={"input": "批量预览动作二"})
    second = client.post("/api/debug/test-snapshots", json={"name": "预览包乙", "note": "第二份"}).json()["snapshot"]
    bundle = client.post("/api/debug/test-snapshots/bulk-export", json={"snapshot_ids": [first["id"], second["id"]]}).json()
    client.post("/api/debug/test-snapshots/bulk-delete", json={"snapshot_ids": [first["id"], second["id"]]})

    r = client.post("/api/debug/test-snapshots/bulk-import/preview", json={"bundle": bundle})

    assert r.status_code == 200
    body = r.json()
    assert body["snapshot_count"] == 2
    assert {snapshot["name"] for snapshot in body["snapshots"]} == {"预览包甲", "预览包乙"}
    assert body["totals"]["entities"] == sum(snapshot["entity_count"] for snapshot in body["snapshots"])
    assert client.get("/api/debug/test-snapshots").json()["snapshots"] == []



def test_debug_test_snapshot_bulk_import_adds_bundle_snapshots_without_loading_world(client):
    client.post("/api/turn", json={"input": "批量导入动作一"})
    first = client.post("/api/debug/test-snapshots", json={"name": "导入包甲", "note": "第一份"}).json()["snapshot"]
    client.post("/api/turn", json={"input": "批量导入动作二"})
    second = client.post("/api/debug/test-snapshots", json={"name": "导入包乙", "note": "第二份"}).json()["snapshot"]
    bundle = client.post("/api/debug/test-snapshots/bulk-export", json={"snapshot_ids": [first["id"], second["id"]]}).json()
    client.post("/api/debug/test-snapshots/bulk-delete", json={"snapshot_ids": [first["id"], second["id"]]})
    client.post("/api/turn", json={"input": "导入后当前世界动作"})

    r = client.post("/api/debug/test-snapshots/bulk-import", json={"bundle": bundle})

    assert r.status_code == 200
    body = r.json()
    assert len(body["imported"]) == 2
    assert {snapshot["name"] for snapshot in body["imported"]} == {"导入包甲", "导入包乙"}
    assert body["summary"]["snapshot_count"] == 2
    listing = client.get("/api/debug/test-snapshots").json()["snapshots"]
    assert {snapshot["name"] for snapshot in listing} == {"导入包甲", "导入包乙"}
    assert {snapshot["id"] for snapshot in listing}.isdisjoint({first["id"], second["id"]})
    state = client.get("/api/state").json()
    assert any("导入后当前世界动作" in e.get("summary", "") for e in state["events"])



def test_debug_test_snapshot_bulk_import_rejects_bad_bundle(client):
    r = client.post("/api/debug/test-snapshots/bulk-import", json={"bundle": {"format": "bad"}})

    assert r.status_code == 400
    assert "unsupported test snapshot bundle format" in r.json()["detail"]



def test_debug_test_snapshot_bulk_import_rejects_empty_bundle(client):
    r = client.post("/api/debug/test-snapshots/bulk-import", json={
        "bundle": {"format": "mingrpg.test-snapshot-bundle", "version": 1, "snapshots": []},
    })

    assert r.status_code == 400
    assert "snapshot bundle cannot be empty" in r.json()["detail"]



def test_debug_test_snapshot_bulk_import_rejects_bad_snapshot_in_bundle(client):
    r = client.post("/api/debug/test-snapshots/bulk-import", json={
        "bundle": {"format": "mingrpg.test-snapshot-bundle", "version": 1, "snapshots": [{"format": "bad"}]},
    })

    assert r.status_code == 400
    assert "unsupported test snapshot format" in r.json()["detail"]



def test_debug_test_snapshot_bulk_archive_updates_selected_snapshots(client):
    first = client.post("/api/debug/test-snapshots", json={"name": "批量归档甲"}).json()["snapshot"]
    second = client.post("/api/debug/test-snapshots", json={"name": "批量归档乙"}).json()["snapshot"]
    keep = client.post("/api/debug/test-snapshots", json={"name": "保留"}).json()["snapshot"]

    archived = client.post("/api/debug/test-snapshots/bulk-archive", json={
        "snapshot_ids": [first["id"], second["id"], first["id"]],
        "archived": True,
    })

    assert archived.status_code == 200
    body = archived.json()
    assert {snapshot["id"] for snapshot in body["archived"]} == {first["id"], second["id"]}
    assert all(snapshot["archived"] is True for snapshot in body["archived"])
    listing = client.get("/api/debug/test-snapshots").json()["snapshots"]
    by_id = {snapshot["id"]: snapshot for snapshot in listing}
    assert by_id[first["id"]]["archived"] is True
    assert by_id[second["id"]]["archived"] is True
    assert by_id[keep["id"]]["archived"] is False
    assert body["summary"]["snapshot_count"] == 3

    restored = client.post("/api/debug/test-snapshots/bulk-archive", json={
        "snapshot_ids": [first["id"]],
        "archived": False,
    })

    assert restored.status_code == 200
    assert restored.json()["archived"][0]["archived"] is False
    listing = client.get("/api/debug/test-snapshots").json()["snapshots"]
    by_id = {snapshot["id"]: snapshot for snapshot in listing}
    assert by_id[first["id"]]["archived"] is False
    assert by_id[second["id"]]["archived"] is True



def test_debug_test_snapshot_bulk_archive_rejects_empty_selection(client):
    r = client.post("/api/debug/test-snapshots/bulk-archive", json={"snapshot_ids": []})

    assert r.status_code == 400
    assert "snapshot ids cannot be empty" in r.json()["detail"]



def test_debug_test_snapshot_bulk_archive_404_for_unknown(client):
    r = client.post("/api/debug/test-snapshots/bulk-archive", json={"snapshot_ids": ["missing"]})

    assert r.status_code == 404



def test_debug_test_snapshot_bulk_delete_removes_selected_snapshots(client):
    first = client.post("/api/debug/test-snapshots", json={"name": "批量甲"}).json()["snapshot"]
    second = client.post("/api/debug/test-snapshots", json={"name": "批量乙"}).json()["snapshot"]
    keep = client.post("/api/debug/test-snapshots", json={"name": "保留"}).json()["snapshot"]

    r = client.post("/api/debug/test-snapshots/bulk-delete", json={
        "snapshot_ids": [first["id"], second["id"], first["id"]],
    })

    assert r.status_code == 200
    body = r.json()
    assert {snapshot["id"] for snapshot in body["deleted"]} == {first["id"], second["id"]}
    assert body["summary"]["snapshot_count"] == 1
    listing = client.get("/api/debug/test-snapshots").json()["snapshots"]
    assert [snapshot["id"] for snapshot in listing] == [keep["id"]]



def test_debug_test_snapshot_bulk_delete_rejects_empty_selection(client):
    r = client.post("/api/debug/test-snapshots/bulk-delete", json={"snapshot_ids": []})

    assert r.status_code == 400
    assert "snapshot ids cannot be empty" in r.json()["detail"]



def test_debug_test_snapshot_bulk_delete_404_for_unknown(client):
    r = client.post("/api/debug/test-snapshots/bulk-delete", json={"snapshot_ids": ["missing"]})

    assert r.status_code == 404



def test_debug_test_snapshot_diff_previews_changes_before_load(client):
    created = client.post("/api/debug/test-snapshots", json={"name": "初始府衙"})
    snapshot_id = created.json()["snapshot"]["id"]
    client.post("/api/birth/apply", json={"template_id": "merchant_son"})

    r = client.get(f"/api/debug/test-snapshots/{snapshot_id}/diff")

    assert r.status_code == 200
    body = r.json()
    assert body["snapshot"]["id"] == snapshot_id
    assert body["summary"]["total_changes"] >= 2
    assert "player" in body["entities"]["changed"]
    assert "birth_setting" in body["flags"]["removed"]
    assert body["current_counts"]["entities"] == body["snapshot_counts"]["entities"]



def test_debug_test_snapshot_diff_404_for_unknown(client):
    r = client.get("/api/debug/test-snapshots/missing/diff")

    assert r.status_code == 404



def test_debug_test_snapshots_reject_empty_name(client):
    r = client.post("/api/debug/test-snapshots", json={"name": "   "})

    assert r.status_code == 400
    assert "snapshot name cannot be empty" in r.json()["detail"]


def test_debug_test_snapshots_load_404_for_unknown(client):
    r = client.post("/api/debug/test-snapshots/load", json={"snapshot_id": "missing"})

    assert r.status_code == 404


# ----- Test scenario presets -----


def test_debug_test_presets_list_defaults(client):
    r = client.get("/api/debug/test-presets")

    assert r.status_code == 200
    presets = r.json()["presets"]
    ids = {preset["id"] for preset in presets}
    assert {"court_clue_pressure", "advisor_party_observation"} <= ids
    assert all("apply" not in preset for preset in presets)


def test_debug_test_preset_load_resets_and_applies_clue_pressure_state(client):
    client.post("/api/turn", json={"input": "预设前动作"})

    r = client.post("/api/debug/test-presets/load", json={"preset_id": "court_clue_pressure"})

    assert r.status_code == 200
    body = r.json()
    state = body["state"]
    assert body["preset"]["name"] == "府衙线索压力局"
    assert state["flags"]["test_preset"]["id"] == "court_clue_pressure"
    assert state["flags"]["pressure_clocks"]["witness_pressure"] == {"value": 2, "danger_at": 3}
    clues = state["flags"]["story_progress"]["main_thread"]["clues"]
    assert clues[0]["source_entity"] == "shiye"
    summaries = [e.get("summary", "") for e in state["events"]]
    assert any("状纸曾被刘师爷压下" in s for s in summaries)
    assert not any("预设前动作" in s for s in summaries)


def test_debug_test_preset_load_applies_party_observation_state(client):
    r = client.post("/api/debug/test-presets/load", json={"preset_id": "advisor_party_observation"})

    assert r.status_code == 200
    state = r.json()["state"]
    party = state["flags"]["party"]
    assert party["active_actor_id"] == "shiye"
    assert any(member["entity_id"] == "shiye" for member in party["members"])
    observations = state["flags"]["observations"]["player"]
    assert "location:court_hall:court_hall_case_table" in observations
    assert state["flags"]["test_preset"]["id"] == "advisor_party_observation"


def test_debug_test_preset_load_404_for_unknown(client):
    r = client.post("/api/debug/test-presets/load", json={"preset_id": "missing"})

    assert r.status_code == 404


# ----- Quest log / investigation panel data -----

def test_quest_log_data_in_snapshot(client):
    """update_quest_log 后的调查数据应在快照 flags.quest_log 中。"""
    from mingrpg.tools.write import update_quest_log

    world = client.app.state.world
    base_count = len((world.get_flag("quest_log") or {}).get("entries", []))
    update_quest_log(world, "test_investigation", "测试调查里程碑",
                     description="测试描述", region="测试地区", status="active")
    update_quest_log(world, "test_completed", "已完成里程碑",
                     description="已完成描述", region="测试地区", status="completed")

    state = client.get("/api/state").json()
    quest_log = state["flags"]["quest_log"]
    assert "entries" in quest_log
    entries = quest_log["entries"]
    assert len(entries) == base_count + 2
    test_entries = [e for e in entries if e["id"].startswith("test_")]
    assert len(test_entries) == 2
    assert any(e["status"] == "active" for e in test_entries)
    assert any(e["status"] == "completed" for e in test_entries)
    assert any(e.get("region") == "测试地区" for e in test_entries)


def test_quest_timeline_events_include_region_and_status(client):
    """调查时间线事件应包含地区和状态字段。"""
    from mingrpg.tools.write import update_quest_log

    world = client.app.state.world
    update_quest_log(world, "timeline_test_1", "时间线测试1",
                     description="测试", region="yangzhou", status="active")
    update_quest_log(world, "timeline_test_2", "时间线测试2",
                     description="测试", region="suzhou", status="completed")

    state = client.get("/api/state").json()
    quest_events = [ev for ev in state["events"] if ev.get("type") == "quest_log"]
    assert len(quest_events) >= 2

    # Check that events have region and status fields
    for ev in quest_events:
        assert "region" in ev
        assert "status" in ev
        assert ev["type"] == "quest_log"

    # Verify specific regions exist
    regions = {ev.get("region") for ev in quest_events}
    assert "yangzhou" in regions
    assert "suzhou" in regions


def test_quest_flow_data_includes_all_regions(client):
    """调查流程图应能正确识别所有地区。"""
    from mingrpg.tools.write import update_quest_log

    world = client.app.state.world
    # Add entries for multiple regions
    regions = ["yangzhou", "guazhou", "nanjing", "suzhou", "hangzhou", "huaian", "xuzhou"]
    for i, region in enumerate(regions):
        update_quest_log(world, f"flow_test_{region}", f"流程测试{region}",
                         description="测试", region=region, status="active")

    state = client.get("/api/state").json()
    quest_log = state["flags"]["quest_log"]
    entries = quest_log.get("entries", [])

    # Verify all regions are present
    entry_regions = {e.get("region") for e in entries if e.get("region")}
    for region in regions:
        assert region in entry_regions, f"Region {region} not found in quest entries"


def test_quest_entry_has_required_fields(client):
    """调查条目应包含必需字段。"""
    from mingrpg.tools.write import update_quest_log

    world = client.app.state.world
    update_quest_log(world, "field_test", "字段测试",
                     description="测试描述", region="yangzhou", status="active")

    state = client.get("/api/state").json()
    quest_log = state["flags"]["quest_log"]
    entries = quest_log.get("entries", [])

    test_entry = next((e for e in entries if e["id"] == "field_test"), None)
    assert test_entry is not None
    assert "id" in test_entry
    assert "title" in test_entry
    assert "status" in test_entry
    assert test_entry["title"] == "字段测试"
    assert test_entry["description"] == "测试描述"
    assert test_entry["region"] == "yangzhou"


# ----- Dialogue history data (Phase 34) -----

def test_dialogue_events_in_state(client):
    """对话事件应包含在 state 中供前端渲染。"""
    from mingrpg.tools.write import record_dialogue

    world = client.app.state.world
    # Record several dialogues with different NPCs and topics
    record_dialogue(world, "zhifu_wang", "player", topic="天气",
                    player_line="今天天气不错", npc_response="确实如此",
                    attitude_delta=5)
    record_dialogue(world, "zhifu_wang", "player", topic="案情",
                    player_line="案情如何", npc_response="尚在调查",
                    attitude_delta=-3)
    record_dialogue(world, "shiye", "player", topic="秘闻",
                    player_line="有何消息", npc_response="风声紧",
                    attitude_delta=2)

    state = client.get("/api/state").json()
    dialogue_events = [e for e in state["events"] if e.get("type") == "dialogue"]
    assert len(dialogue_events) >= 3

    # Verify each event has fields needed for filtering
    for ev in dialogue_events:
        assert "target" in ev
        assert "target_name" in ev
        assert "topic" in ev
        assert "player_line" in ev
        assert "npc_response" in ev
        assert "attitude_delta" in ev


def test_dialogue_events_unique_npcs(client):
    """对话事件应能正确区分不同 NPC。"""
    from mingrpg.tools.write import record_dialogue

    world = client.app.state.world
    record_dialogue(world, "zhifu_wang", "player", topic="天气")
    record_dialogue(world, "shiye", "player", topic="秘闻")
    record_dialogue(world, "merchant_wu", "player", topic="买卖")

    state = client.get("/api/state").json()
    dialogue_events = [e for e in state["events"] if e.get("type") == "dialogue"]
    npc_ids = {e["target"] for e in dialogue_events if e.get("target")}
    assert len(npc_ids) >= 3


def test_dialogue_events_unique_topics(client):
    """对话事件应能正确区分不同话题。"""
    from mingrpg.tools.write import record_dialogue

    world = client.app.state.world
    record_dialogue(world, "zhifu_wang", "player", topic="天气")
    record_dialogue(world, "zhifu_wang", "player", topic="案情")
    record_dialogue(world, "zhifu_wang", "player", topic="家常")

    state = client.get("/api/state").json()
    dialogue_events = [e for e in state["events"] if e.get("type") == "dialogue"]
    topics = {e["topic"] for e in dialogue_events if e.get("topic")}
    assert len(topics) >= 3


# ----- Phase 34: Dialogue panel enhancements -----

def test_dialogue_events_have_searchable_text(client):
    """对话事件应包含可搜索的玩家台词和NPC回应。"""
    from mingrpg.tools.write import record_dialogue

    world = client.app.state.world
    record_dialogue(world, "zhifu_wang", "player", topic="案情",
                    player_line="知府大人，案情如何",
                    npc_response="尚在调查之中", attitude_delta=3)

    state = client.get("/api/state").json()
    dialogue_events = [e for e in state["events"] if e.get("type") == "dialogue"]
    assert len(dialogue_events) >= 1
    ev = dialogue_events[-1]
    assert "player_line" in ev
    assert "npc_response" in ev
    assert "知府" in ev["player_line"]
    assert "调查" in ev["npc_response"]


def test_dialogue_attitude_distribution_data(client):
    """对话事件应能用于计算态度分布。"""
    from mingrpg.tools.write import record_dialogue

    world = client.app.state.world
    # NPC with positive attitude
    record_dialogue(world, "zhifu_wang", "player", topic="天气",
                    attitude_delta=15)
    # NPC with neutral attitude
    record_dialogue(world, "shiye", "player", topic="案情",
                    attitude_delta=2)
    # NPC with negative attitude
    record_dialogue(world, "merchant_wu", "player", topic="买卖",
                    attitude_delta=-15)

    state = client.get("/api/state").json()
    dialogue_events = [e for e in state["events"] if e.get("type") == "dialogue"]

    # Build attitude sums per NPC
    att_sums = {}
    for ev in dialogue_events:
        npc = ev.get("target")
        if npc:
            att_sums[npc] = att_sums.get(npc, 0) + (ev.get("attitude_delta") or 0)

    # Should have at least one NPC in each category
    positive = any(v >= 10 for v in att_sums.values())
    negative = any(v <= -10 for v in att_sums.values())
    assert positive
    assert negative


def test_dialogue_topic_statistics(client):
    """对话事件应能用于计算话题统计。"""
    from mingrpg.tools.write import record_dialogue

    world = client.app.state.world
    record_dialogue(world, "zhifu_wang", "player", topic="天气")
    record_dialogue(world, "zhifu_wang", "player", topic="天气")
    record_dialogue(world, "zhifu_wang", "player", topic="案情")
    record_dialogue(world, "shiye", "player", topic="天气")

    state = client.get("/api/state").json()
    dialogue_events = [e for e in state["events"] if e.get("type") == "dialogue"]
    topic_counts = {}
    for ev in dialogue_events:
        t = ev.get("topic") or "(无话题)"
        topic_counts[t] = topic_counts.get(t, 0) + 1

    assert topic_counts.get("天气", 0) >= 3
    assert topic_counts.get("案情", 0) >= 1


def test_dialogue_attitude_delta_present(client):
    """对话事件应包含态度变化值用于导出。"""
    from mingrpg.tools.write import record_dialogue

    world = client.app.state.world
    record_dialogue(world, "zhifu_wang", "player", topic="案情",
                    player_line="知府大人辛苦了",
                    npc_response="份内之事",
                    attitude_delta=5)

    state = client.get("/api/state").json()
    dialogue_events = [e for e in state["events"] if e.get("type") == "dialogue"]
    ev = dialogue_events[-1]
    assert ev["attitude_delta"] == 5
    assert ev["player_line"] == "知府大人辛苦了"
    assert ev["npc_response"] == "份内之事"
