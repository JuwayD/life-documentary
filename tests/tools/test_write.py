"""Tests for write tools — mutation operations exposed to GM Agent."""
import pytest
from mingrpg.core.world import World
from mingrpg.tools import write as W


@pytest.fixture
def w():
    world = World(":memory:")
    world.save_entity({"id": "player", "name": "无名书生", "type": "player",
                       "location": "hall", "pos": [3, 5],
                       "attributes": {"hp": 100, "max_hp": 100,
                                       "rank": "平民"},
                       "status_effects": [], "inventory": [], "tags": []})
    world.save_entity({"id": "zhifu", "name": "王知府", "type": "npc",
                       "location": "hall", "pos": [3, 7],
                       "attributes": {"hp": 80, "rank": "四品"},
                       "status_effects": [], "inventory": [],
                       "tags": ["official"]})
    world.save_location({"id": "hall", "name": "府衙大堂", "type": "indoor",
                         "size": [10, 10], "exits": {}, "tags": []})
    world.save_location({"id": "jail", "name": "县衙大牢", "type": "indoor",
                         "size": [5, 5], "exits": {}, "tags": []})
    world.save_location({"id": "teahouse", "name": "茶楼", "type": "indoor",
                         "size": [8, 8], "exits": {}, "tags": []})
    return world


# ----- set_attribute -----

def test_set_attribute_updates_value_and_returns_diff(w):
    r = W.set_attribute(w, "player", "hp", 80)
    assert r["entity"] == "player"
    assert r["attr"] == "hp"
    assert r["old"] == 100
    assert r["new"] == 80
    assert w.get_entity("player")["attributes"]["hp"] == 80


def test_set_attribute_creates_new_key(w):
    r = W.set_attribute(w, "player", "mood", "angry")
    assert r["old"] is None
    assert r["new"] == "angry"
    assert w.get_entity("player")["attributes"]["mood"] == "angry"


def test_set_attribute_unknown_entity_returns_error(w):
    r = W.set_attribute(w, "ghost", "hp", 10)
    assert "error" in r


# ----- move_entity -----

def test_move_entity_within_same_location(w):
    r = W.move_entity(w, "player", to_pos=[5, 5])
    assert r["from_pos"] == [3, 5]
    assert r["to_pos"] == [5, 5]
    assert r["location_changed"] is False
    assert w.get_entity("player")["pos"] == [5, 5]


def test_move_entity_change_location(w):
    r = W.move_entity(w, "player", to_location="jail", to_pos=[1, 1])
    assert r["from_location"] == "hall"
    assert r["to_location"] == "jail"
    assert r["location_changed"] is True
    assert w.get_entity("player")["location"] == "jail"
    assert w.get_entity("player")["pos"] == [1, 1]


def test_move_entity_unknown_location_returns_error(w):
    r = W.move_entity(w, "player", to_location="atlantis")
    assert "error" in r


def test_move_entity_unknown_entity_returns_error(w):
    r = W.move_entity(w, "ghost", to_pos=[0, 0])
    assert "error" in r


# ----- add_status / remove_status -----

def test_add_status_effect(w):
    r = W.add_status(w, "player", "通缉", duration=-1,
                     reason="公堂袭官")
    assert r["entity"] == "player"
    assert r["status"] == "通缉"
    statuses = w.get_entity("player")["status_effects"]
    assert any(s["name"] == "通缉" for s in statuses)


def test_remove_status_effect(w):
    W.add_status(w, "player", "中毒", duration=3)
    r = W.remove_status(w, "player", "中毒")
    assert r["removed"] is True
    assert all(s["name"] != "中毒"
                for s in w.get_entity("player")["status_effects"])


def test_remove_nonexistent_status(w):
    r = W.remove_status(w, "player", "不存在")
    assert r["removed"] is False


# ----- add_item / remove_item -----

def test_add_item(w):
    r = W.add_item(w, "player",
                    {"id": "scroll_1", "name": "状纸", "qty": 1})
    assert r["added"]["name"] == "状纸"
    assert len(w.get_entity("player")["inventory"]) == 1


def test_remove_item(w):
    W.add_item(w, "player", {"id": "coin", "name": "铜钱", "qty": 5})
    r = W.remove_item(w, "player", "coin")
    assert r["removed"] is True
    assert len(w.get_entity("player")["inventory"]) == 0


# ----- log_event -----

def test_log_event_writes_to_world(w):
    r = W.log_event(w, {"actor": "player", "type": "attack",
                         "target": "zhifu", "summary": "玩家殴打知府"})
    assert "event_id" in r
    events = w.list_events()
    assert any(e.get("summary") == "玩家殴打知府" for e in events)


# ----- set_flag -----

def test_set_flag_writes_value(w):
    r = W.set_flag(w, "公堂袭官", True)
    assert r["key"] == "公堂袭官"
    assert r["new"] is True
    assert w.get_flag("公堂袭官") is True


def test_set_flag_overwrite_records_old(w):
    W.set_flag(w, "count", 1)
    r = W.set_flag(w, "count", 5)
    assert r["old"] == 1
    assert r["new"] == 5


# ----- add_memory -----

def test_add_memory_to_npc(w):
    r = W.add_memory(w, "zhifu",
                      "被一刁民当堂殴打,记恨在心",
                      importance=9)
    assert r["entity"] == "zhifu"
    memories = w.get_entity("zhifu")["attributes"].get("memories", [])
    assert any("记恨" in m["text"] for m in memories)


# ----- advance_time (enhanced) -----

def test_advance_time_default_day_index_is_zero(w):
    r = W.advance_time(w, units="shichen", amount=1)
    t = w.get_world_time()
    assert "day_index" in t
    assert t["day_index"] == 0


def test_advance_time_by_day_increments_day_index(w):
    r = W.advance_time(w, units="day", amount=1)
    assert r["units"] == "day"
    assert r["amount"] == 1
    t = w.get_world_time()
    assert t["day_index"] == 1
    # time_of_day should NOT change when advancing by day
    assert t["time_of_day"] == r["from"]


def test_advance_time_by_multiple_days(w):
    r = W.advance_time(w, units="day", amount=3)
    t = w.get_world_time()
    assert t["day_index"] == 3


def test_advance_time_shichen_wrap_increments_day(w):
    # Set time to 亥时 (last shichen), advance 1 → wraps to 子时, day_index +1
    w.set_world_time({"year": "万历十年", "season": "秋",
                       "time_of_day": "亥时", "day_index": 0})
    r = W.advance_time(w, units="shichen", amount=1)
    assert r["to"] == "子时"
    t = w.get_world_time()
    assert t["day_index"] == 1
    assert r["day_wrapped"] is True


def test_advance_time_shichen_no_wrap_no_day_change(w):
    r = W.advance_time(w, units="shichen", amount=1)
    # default is 巳时 → 午时, no wrap
    assert r["day_wrapped"] is False
    t = w.get_world_time()
    assert t["day_index"] == 0


def test_advance_time_shichen_multiple_wraps(w):
    w.set_world_time({"year": "万历十年", "season": "秋",
                       "time_of_day": "亥时", "day_index": 0})
    r = W.advance_time(w, units="shichen", amount=25)
    # 25 时辰 = 2 full wraps + 1 more → 子时, day_index +3
    assert r["to"] == "子时"
    t = w.get_world_time()
    assert t["day_index"] == 3
    assert r["day_wrapped"] is True


def test_tick_npc_schedules_moves_matching_npc(w):
    W.set_attribute(w, "zhifu", "schedule", {
        "午时": {"location": "teahouse", "pos": [4, 4], "activity": "去茶楼听消息"}
    })
    w.set_world_time({"year": "万历十年", "season": "秋",
                      "time_of_day": "午时", "day_index": 0})

    r = W.tick_npc_schedules(w)

    assert r["time_of_day"] == "午时"
    assert r["moved"][0]["entity"] == "zhifu"
    assert w.get_entity("zhifu")["location"] == "teahouse"
    assert w.get_entity("zhifu")["pos"] == [4, 4]
    assert any(e["type"] == "schedule_move" and e["actor"] == "zhifu"
               for e in w.list_events())


def test_tick_npc_schedules_skips_missing_location(w):
    W.set_attribute(w, "zhifu", "schedule", {
        "午时": {"location": "missing", "pos": [4, 4], "activity": "去不存在之地"}
    })
    w.set_world_time({"year": "万历十年", "season": "秋",
                      "time_of_day": "午时", "day_index": 0})

    r = W.tick_npc_schedules(w)

    assert r["moved"] == []
    assert w.get_entity("zhifu")["location"] == "hall"


def test_advance_time_triggers_schedule_tick(w):
    W.set_attribute(w, "zhifu", "schedule", {
        "午时": {"location": "teahouse", "pos": [4, 4], "activity": "去茶楼听消息"}
    })

    r = W.advance_time(w, units="shichen", amount=1)

    assert r["to"] == "午时"
    assert r["schedule_tick"]["moved"][0]["entity"] == "zhifu"
    assert w.get_entity("zhifu")["location"] == "teahouse"


# ----- transfer_money -----

def test_transfer_money_successful(w):
    # player has no money_wen in test fixture, so give some first
    W.set_attribute(w, "player", "money_wen", 100)
    W.set_attribute(w, "zhifu", "money_wen", 50)
    r = W.transfer_money(w, "player", "zhifu", 30, "买消息")
    assert r["from_entity"] == "player"
    assert r["to_entity"] == "zhifu"
    assert r["amount"] == 30
    assert r["from_balance_after"] == 70
    assert r["to_balance_after"] == 80
    assert r["reason"] == "买消息"
    assert w.get_entity("player")["attributes"]["money_wen"] == 70
    assert w.get_entity("zhifu")["attributes"]["money_wen"] == 80


def test_transfer_money_insufficient_funds(w):
    W.set_attribute(w, "player", "money_wen", 10)
    W.set_attribute(w, "zhifu", "money_wen", 50)
    r = W.transfer_money(w, "player", "zhifu", 100)
    assert "error" in r
    assert w.get_entity("player")["attributes"]["money_wen"] == 10
    assert w.get_entity("zhifu")["attributes"]["money_wen"] == 50


def test_transfer_money_from_entity_not_found(w):
    r = W.transfer_money(w, "ghost", "zhifu", 10)
    assert "error" in r
    assert "ghost" in r["error"]


def test_transfer_money_to_entity_not_found(w):
    W.set_attribute(w, "player", "money_wen", 100)
    r = W.transfer_money(w, "player", "ghost", 10)
    assert "error" in r


def test_transfer_money_to_entity_creates_money_wen(w):
    W.set_attribute(w, "player", "money_wen", 100)
    # zhifu has no money_wen in fixture
    r = W.transfer_money(w, "player", "zhifu", 50)
    assert "error" not in r
    assert r["to_balance_after"] == 50


def test_transfer_money_negative_amount(w):
    r = W.transfer_money(w, "player", "zhifu", -10)
    assert "error" in r


def test_transfer_money_zero_amount(w):
    r = W.transfer_money(w, "player", "zhifu", 0)
    assert "error" in r


def test_transfer_money_same_entity(w):
    W.set_attribute(w, "player", "money_wen", 100)
    r = W.transfer_money(w, "player", "player", 10)
    assert "error" in r


# ----- purchase_item -----

def test_purchase_item_transfers_money_and_item(w):
    W.set_attribute(w, "player", "money_wen", 100)
    W.set_attribute(w, "zhifu", "money_wen", 50)
    W.set_attribute(w, "zhifu", "price_list", {"tea": 8})
    W.add_item(w, "zhifu", {"id": "tea", "name": "清茶", "qty": 3})

    r = W.purchase_item(w, "player", "zhifu", "tea", qty=2, reason="买茶")

    assert r["buyer"] == "player"
    assert r["seller"] == "zhifu"
    assert r["item_id"] == "tea"
    assert r["qty"] == 2
    assert r["total_price_wen"] == 16
    assert w.get_entity("player")["attributes"]["money_wen"] == 84
    assert w.get_entity("zhifu")["attributes"]["money_wen"] == 66
    assert any(i["id"] == "tea" and i["qty"] == 2
               for i in w.get_entity("player")["inventory"])
    assert any(i["id"] == "tea" and i["qty"] == 1
               for i in w.get_entity("zhifu")["inventory"])


def test_purchase_item_uses_explicit_unit_price(w):
    W.set_attribute(w, "player", "money_wen", 100)
    W.add_item(w, "zhifu", {"id": "bun", "name": "包子", "qty": 2})

    r = W.purchase_item(w, "player", "zhifu", "bun", qty=1,
                        unit_price_wen=5)

    assert "error" not in r
    assert r["total_price_wen"] == 5


def test_purchase_item_requires_stock(w):
    W.set_attribute(w, "player", "money_wen", 100)
    W.set_attribute(w, "zhifu", "price_list", {"tea": 8})
    W.add_item(w, "zhifu", {"id": "tea", "name": "清茶", "qty": 1})

    r = W.purchase_item(w, "player", "zhifu", "tea", qty=2)

    assert "error" in r
    assert w.get_entity("player")["inventory"] == []


def test_purchase_item_requires_price(w):
    W.set_attribute(w, "player", "money_wen", 100)
    W.add_item(w, "zhifu", {"id": "tea", "name": "清茶", "qty": 1})

    r = W.purchase_item(w, "player", "zhifu", "tea", qty=1)

    assert "error" in r
    assert "price" in r["error"]


# ----- hire_service -----

def test_hire_service_transfers_money_and_marks_provider(w):
    W.set_attribute(w, "player", "money_wen", 100)
    W.set_attribute(w, "zhifu", "money_wen", 50)
    W.set_attribute(w, "zhifu", "service_catalog", {
        "guide": {"name": "带路", "price_wen": 20}
    })

    r = W.hire_service(w, "player", "zhifu", "guide",
                       duration=2, reason="请人带路")

    assert r["payer"] == "player"
    assert r["provider"] == "zhifu"
    assert r["service_id"] == "guide"
    assert r["price_wen"] == 20
    provider = w.get_entity("zhifu")
    assert provider["attributes"]["money_wen"] == 70
    assert provider["attributes"]["current_contract"]["hired_by"] == "player"
    assert provider["attributes"]["current_contract"]["service_id"] == "guide"
    assert any(e["type"] == "hire_service" and e["actor"] == "player"
               for e in w.list_events())


def test_hire_service_uses_explicit_price(w):
    W.set_attribute(w, "player", "money_wen", 100)

    r = W.hire_service(w, "player", "zhifu", "guide", price_wen=12)

    assert "error" not in r
    assert r["price_wen"] == 12


def test_hire_service_requires_catalog_or_price(w):
    W.set_attribute(w, "player", "money_wen", 100)

    r = W.hire_service(w, "player", "zhifu", "guide")

    assert "error" in r
    assert "service" in r["error"]


# ----- story progress -----


def test_record_clue_appends_story_progress_and_event(w):
    r = W.record_clue(
        w,
        thread_id="petition_against_bully",
        clue="乞丐老刘见过赵三夜会货栈伙计",
        source_entity="beggar_liu",
        location_id="market_gate",
        evidence_item="证词",
    )

    assert r["thread_id"] == "petition_against_bully"
    assert r["clue_count"] == 1
    progress = w.get_flag("story_progress")
    assert progress["petition_against_bully"]["clues"][0]["clue"] == "乞丐老刘见过赵三夜会货栈伙计"
    assert any(e["type"] == "record_clue" for e in w.list_events())


def test_record_clue_deduplicates_same_clue(w):
    W.record_clue(w, "petition_against_bully", "同一条线索", source_entity="shiye")
    r = W.record_clue(w, "petition_against_bully", "同一条线索", source_entity="shiye")

    assert r["added"] is False
    assert r["clue_count"] == 1


def test_advance_pressure_clock_creates_and_increments_clock(w):
    r = W.advance_pressure_clock(
        w,
        clock_id="witness_pressure",
        amount=2,
        reason="玩家当众追问证人",
        danger_at=3,
    )

    assert r["clock_id"] == "witness_pressure"
    assert r["old"] == 0
    assert r["new"] == 2
    assert r["danger_reached"] is False
    clocks = w.get_flag("pressure_clocks")
    assert clocks["witness_pressure"]["value"] == 2
    assert clocks["witness_pressure"]["danger_at"] == 3


def test_advance_pressure_clock_reports_danger_reached(w):
    W.advance_pressure_clock(w, "official_patience", amount=2, danger_at=3)
    r = W.advance_pressure_clock(w, "official_patience", amount=1, reason="再闹公堂")

    assert r["old"] == 2
    assert r["new"] == 3
    assert r["danger_reached"] is True
    assert any(e["type"] == "pressure_clock" and e["danger_reached"] is True
               for e in w.list_events())


def test_advance_pressure_clock_tracks_history(w):
    W.advance_pressure_clock(w, "witness_pressure", amount=1, danger_at=5)
    W.advance_pressure_clock(w, "witness_pressure", amount=2, danger_at=5)
    W.advance_pressure_clock(w, "witness_pressure", amount=1, danger_at=5)

    clocks = w.get_flag("pressure_clocks")
    assert clocks["witness_pressure"]["history"] == [1, 3, 4]


# ----- Phase 6 Step 3: discover_observation -----


def test_discover_observation_records_flag_and_event(w):
    loc = w.get_location("hall")
    loc["observable_details"] = [
        {"id": "case_table", "text": "案上压着状纸", "discovery_value": 8},
    ]
    w.save_location(loc)

    r = W.discover_observation(w, "case_table", target_id="hall")

    assert "error" not in r
    assert r["discovered"] is True
    observations = w.get_flag("observations")
    assert "location:hall:case_table" in observations["player"]
    assert any(e["type"] == "discover_observation" for e in w.list_events())


def test_discover_observation_deduplicates_same_detail(w):
    loc = w.get_location("hall")
    loc["observable_details"] = [
        {"id": "case_table", "text": "案上压着状纸", "discovery_value": 8},
    ]
    w.save_location(loc)
    W.discover_observation(w, "case_table")
    r = W.discover_observation(w, "case_table")

    assert r["discovered"] is False
    events = [e for e in w.list_events() if e.get("type") == "discover_observation"]
    assert len(events) == 1


def test_discover_observation_rejects_missing_detail(w):
    r = W.discover_observation(w, "missing")
    assert "error" in r


# ----- Phase 6 Step 2: ask_advisor -----

def test_ask_advisor_records_event_and_memory(w):
    w.save_entity({"id": "shiye", "name": "刘师爷", "type": "npc",
                   "location": "hall", "pos": [4, 6],
                   "attributes": {"hp": 50, "personality": "圆滑",
                                  "is_advisor": True,
                                  "advisor_topics": ["府衙程序", "状纸策略"],
                                  "advisor_style": "谨慎提醒风险",
                                  "memories": []},
                   "status_effects": [], "inventory": [], "tags": []})
    r = W.ask_advisor(w, advisor_id="shiye",
                      question="我现在该做什么?", player_id="player")
    assert "error" not in r
    assert r["advisor_id"] == "shiye"
    assert r["advisor_name"] == "刘师爷"
    assert r["question"] == "我现在该做什么?"
    assert "府衙程序" in r["advisor_topics"]
    assert r["advisor_style"] == "谨慎提醒风险"
    assert "personality" in r
    assert r["memories_count"] == 1
    assert "event_id" in r

    # Verify event was logged
    events = w.list_events()
    assert any(e["type"] == "ask_advisor" and e["advisor_id"] == "shiye"
               for e in events)

    # Verify memory was added to advisor
    shiye = w.get_entity("shiye")
    assert len(shiye["attributes"]["memories"]) == 1
    assert "我现在该做什么" in shiye["attributes"]["memories"][0]["text"]


def test_ask_advisor_rejects_unknown_advisor(w):
    r = W.ask_advisor(w, advisor_id="ghost",
                      question="test", player_id="player")
    assert "error" in r


def test_ask_advisor_rejects_non_advisor(w):
    r = W.ask_advisor(w, advisor_id="zhifu",
                      question="test", player_id="player")
    assert "error" in r


def test_ask_advisor_rejects_empty_question(w):
    w.save_entity({"id": "shiye", "name": "刘师爷", "type": "npc",
                   "location": "hall", "pos": [4, 6],
                   "attributes": {"hp": 50, "personality": "圆滑",
                                  "is_advisor": True,
                                  "advisor_topics": ["府衙程序"],
                                  "advisor_style": "谨慎",
                                  "memories": []},
                   "status_effects": [], "inventory": [], "tags": []})
    r = W.ask_advisor(w, advisor_id="shiye",
                      question="  ", player_id="player")
    assert "error" in r


# ----- Phase 6 Step 4: party tools -----


def test_join_party_adds_member_memory_and_event(w):
    r = W.join_party(w, "zhifu", role="临时同伴", joined_reason="带路去后堂")
    assert r["joined"] is True
    assert r["member_count"] == 2
    party = w.get_flag("party")
    assert party["leader_id"] == "player"
    assert any(m["entity_id"] == "zhifu" and m["role"] == "临时同伴"
               for m in party["members"])
    zhifu = w.get_entity("zhifu")
    assert any("加入" in m["text"] for m in zhifu["attributes"]["memories"])
    assert any(e["type"] == "join_party" and e["actor"] == "zhifu"
               for e in w.list_events())


def test_join_party_is_idempotent(w):
    W.join_party(w, "zhifu")
    r = W.join_party(w, "zhifu")
    assert r["joined"] is False
    assert r["member_count"] == 2


def test_join_party_rejects_missing_entity(w):
    r = W.join_party(w, "ghost")
    assert "error" in r


def test_leave_party_removes_member_and_resets_active_actor(w):
    W.join_party(w, "zhifu")
    W.set_active_actor(w, "zhifu")
    r = W.leave_party(w, "zhifu", reason="不愿涉险")
    assert r["removed"] is True
    assert r["active_actor_id"] == "player"
    assert all(m["entity_id"] != "zhifu" for m in w.get_flag("party")["members"])
    assert any(e["type"] == "leave_party" and e["actor"] == "zhifu"
               for e in w.list_events())


def test_leave_party_rejects_leader(w):
    r = W.leave_party(w, "player")
    assert "error" in r


def test_set_active_actor_requires_party_member(w):
    r = W.set_active_actor(w, "zhifu")
    assert "error" in r


def test_set_active_actor_updates_party_flag(w):
    W.join_party(w, "zhifu")
    r = W.set_active_actor(w, "zhifu", reason="由知府出面")
    assert r["old_active_actor_id"] == "player"
    assert r["active_actor_id"] == "zhifu"
    assert w.get_flag("party")["active_actor_id"] == "zhifu"
    assert any(e["type"] == "set_active_actor" and e["to_actor"] == "zhifu"
               for e in w.list_events())


# ----- train_skill -----

class TestTrainSkill:
    def test_grants_xp_and_logs_event(self, w):
        e = w.get_entity("player")
        e["attributes"]["skills"] = {
            "litigation": {"name": "讼学", "xp": 0, "level": 0},
        }
        w.save_entity(e)
        r = W.train_skill(w, "player", "litigation", xp_granted=5,
                           name="讼学", reason="研读状纸范本")
        assert r["entity"] == "player"
        assert r["skill_id"] == "litigation"
        assert r["old_xp"] == 0
        assert r["new_xp"] == 5
        assert w.get_entity("player")["attributes"]["skills"]["litigation"]["xp"] == 5
        assert any(e["type"] == "train_skill" for e in w.list_events())

    def test_creates_skill_if_absent(self, w):
        r = W.train_skill(w, "player", "calligraphy", xp_granted=3,
                           name="书法", reason="临帖练字")
        assert r["old_xp"] == 0
        assert r["new_xp"] == 3
        skills = w.get_entity("player")["attributes"]["skills"]
        assert "calligraphy" in skills
        assert skills["calligraphy"]["name"] == "书法"

    def test_unknown_entity_returns_error(self, w):
        r = W.train_skill(w, "ghost", "litigation", xp_granted=5)
        assert "error" in r

    def test_empty_skill_id_returns_error(self, w):
        r = W.train_skill(w, "player", "", xp_granted=5)
        assert "error" in r


# ----- learn_from_npc -----

class TestLearnFromNpc:
    def _setup(self, w):
        """Add skills to player and teacher NPC."""
        e = w.get_entity("player")
        e["attributes"]["skills"] = {
            "litigation": {"name": "讼学", "xp": 0, "level": 0},
        }
        w.save_entity(e)
        w.save_entity({"id": "teacher", "name": "顾先生", "type": "npc",
                        "location": "hall", "pos": [5, 5],
                        "attributes": {"hp": 55, "rank": "生员",
                                       "personality": "循循善诱",
                                       "skills_taught": ["litigation", "calligraphy"],
                                       "memories": []},
                        "status_effects": [], "inventory": [], "tags": []})

    def test_grants_xp_and_records_memory(self, w):
        self._setup(w)
        r = W.learn_from_npc(w, "player", "teacher", "litigation",
                              name="讼学", reason="顾先生讲解律例")
        assert r["entity"] == "player"
        assert r["teacher_id"] == "teacher"
        assert r["skill_id"] == "litigation"
        assert r["new_xp"] >= r["old_xp"]
        # memory recorded on teacher
        teacher = w.get_entity("teacher")
        assert len(teacher["attributes"]["memories"]) > 0
        assert any(e["type"] == "learn_from_npc" for e in w.list_events())

    def test_unknown_teacher_returns_error(self, w):
        self._setup(w)
        r = W.learn_from_npc(w, "player", "ghost", "litigation")
        assert "error" in r

    def test_non_npc_returns_error(self, w):
        self._setup(w)
        r = W.learn_from_npc(w, "player", "player", "litigation")
        assert "error" in r

    def test_empty_skill_id_returns_error(self, w):
        self._setup(w)
        r = W.learn_from_npc(w, "player", "teacher", "")
        assert "error" in r


# ----- record_ending -----

class TestRecordEnding:
    def test_records_final_ending_and_event(self, w):
        r = W.record_ending(
            w, "official_vindication", "公堂昭雪",
            "王知府正式收案,赵三伏法。", outcome="民望上升", final=True)
        assert r["ending_id"] == "official_vindication"
        assert r["recorded"] is True
        assert r["final"] is True
        progress = w.get_flag("ending_progress")
        assert progress["final_ending_id"] == "official_vindication"
        assert progress["endings"][0]["title"] == "公堂昭雪"
        assert any(e["type"] == "record_ending" and e["final"] is True
                   for e in w.list_events())

    def test_updates_existing_ending(self, w):
        W.record_ending(w, "private_settlement", "私下和解", "初稿")
        r = W.record_ending(w, "private_settlement", "私下和解", "更新后摘要")
        assert r["recorded"] is False
        endings = w.get_flag("ending_progress")["endings"]
        assert len(endings) == 1
        assert endings[0]["summary"] == "更新后摘要"

    def test_rejects_unknown_actor(self, w):
        r = W.record_ending(w, "x", "标题", "摘要", actor_id="ghost")
        assert "error" in r

    def test_rejects_empty_required_fields(self, w):
        assert "error" in W.record_ending(w, "", "标题", "摘要")
        assert "error" in W.record_ending(w, "ending", "", "摘要")
        assert "error" in W.record_ending(w, "ending", "标题", "")


# ----- register_evolution -----

class TestRegisterEvolution:
    def test_registers_entity_and_logs_event(self, w):
        r = W.register_evolution(w, "zhifu", frequency="every_turn",
                                 reason="玩家在府衙附近活动")
        assert r["entity_id"] == "zhifu"
        assert r["registered"] is True
        assert r["frequency"] == "every_turn"
        registry = w.get_flag("evolution_registry")
        assert len(registry) == 1
        assert registry[0]["entity_id"] == "zhifu"
        assert any(e["type"] == "register_evolution" for e in w.list_events())

    def test_rejects_duplicate_registration(self, w):
        W.register_evolution(w, "zhifu")
        r = W.register_evolution(w, "zhifu")
        assert r["registered"] is False
        assert "already registered" in r["reason"]

    def test_default_frequency(self, w):
        r = W.register_evolution(w, "zhifu")
        assert r["frequency"] == "every_2_turns"

    def test_rejects_empty_entity_id(self, w):
        r = W.register_evolution(w, "")
        assert "error" in r

    def test_registers_nonexistent_entity(self, w):
        r = W.register_evolution(w, "ghost", reason="test")
        assert r["registered"] is True
        assert r["entity_id"] == "ghost"


# ----- update_evolution -----

class TestUpdateEvolution:
    def test_updates_frequency(self, w):
        W.register_evolution(w, "zhifu", frequency="every_turn")
        r = W.update_evolution(w, "zhifu", frequency="every_5_turns")
        assert r["updated"] is True
        assert r["old_frequency"] == "every_turn"
        assert r["new_frequency"] == "every_5_turns"
        registry = w.get_flag("evolution_registry")
        assert registry[0]["frequency"] == "every_5_turns"

    def test_updates_reason(self, w):
        W.register_evolution(w, "zhifu", reason="old reason")
        r = W.update_evolution(w, "zhifu", reason="new reason")
        assert r["reason"] == "new reason"

    def test_rejects_unregistered_entity(self, w):
        r = W.update_evolution(w, "zhifu", frequency="dormant")
        assert "error" in r
        assert "not in evolution registry" in r["error"]

    def test_rejects_empty_entity_id(self, w):
        r = W.update_evolution(w, "")
        assert "error" in r


# ----- remove_evolution -----

class TestRemoveEvolution:
    def test_removes_entity(self, w):
        W.register_evolution(w, "zhifu")
        r = W.remove_evolution(w, "zhifu")
        assert r["removed"] is True
        assert r["registry_size"] == 0
        assert w.get_flag("evolution_registry") == []
        assert any(e["type"] == "remove_evolution" for e in w.list_events())

    def test_returns_not_found_for_unregistered(self, w):
        r = W.remove_evolution(w, "zhifu")
        assert r["removed"] is False

    def test_rejects_empty_entity_id(self, w):
        r = W.remove_evolution(w, "")
        assert "error" in r


# ----- update_ending_progress -----

class TestUpdateEndingProgress:
    def test_adds_step(self, w):
        r = W.update_ending_progress(w, "ending_cleared", "step_clues", "收集全部线索")
        assert r["added"] is True
        assert r["completed"] is True
        assert r["completed_count"] == 1
        assert r["total_steps"] == 1
        steps = w.get_flag("ending_steps")
        assert steps["ending_cleared"][0]["id"] == "step_clues"
        assert steps["ending_cleared"][0]["completed"] is True

    def test_updates_existing_step(self, w):
        W.update_ending_progress(w, "ending_cleared", "step_clues", "收集线索", completed=False)
        r = W.update_ending_progress(w, "ending_cleared", "step_clues", "收集全部线索", completed=True)
        assert r["added"] is False
        assert r["completed"] is True
        steps = w.get_flag("ending_steps")
        assert len(steps["ending_cleared"]) == 1
        assert steps["ending_cleared"][0]["label"] == "收集全部线索"

    def test_multiple_steps(self, w):
        W.update_ending_progress(w, "ending_cleared", "step1", "步骤一")
        W.update_ending_progress(w, "ending_cleared", "step2", "步骤二", completed=False)
        r = W.update_ending_progress(w, "ending_cleared", "step3", "步骤三")
        assert r["total_steps"] == 3
        assert r["completed_count"] == 2

    def test_different_endings_independent(self, w):
        W.update_ending_progress(w, "ending_a", "s1", "A步骤")
        W.update_ending_progress(w, "ending_b", "s1", "B步骤")
        steps = w.get_flag("ending_steps")
        assert len(steps["ending_a"]) == 1
        assert len(steps["ending_b"]) == 1

    def test_appends_event(self, w):
        W.update_ending_progress(w, "ending_cleared", "step1", "步骤一")
        events = w.list_events()
        assert any(e["type"] == "ending_progress" for e in events)

    def test_rejects_empty_ending_id(self, w):
        r = W.update_ending_progress(w, "", "step1", "步骤")
        assert "error" in r

    def test_rejects_empty_step_id(self, w):
        r = W.update_ending_progress(w, "ending_cleared", "", "步骤")
        assert "error" in r

    def test_rejects_empty_step_label(self, w):
        r = W.update_ending_progress(w, "ending_cleared", "step1", "")
        assert "error" in r


# ----- update_quest_log -----

class TestUpdateQuestLog:
    def test_adds_new_entry(self, w):
        r = W.update_quest_log(w, "test_quest", "测试里程碑",
                               description="测试描述", region="yangzhou")
        assert r["added"] is True
        assert r["entry_id"] == "test_quest"
        assert r["title"] == "测试里程碑"
        assert r["status"] == "active"
        assert r["total"] == 1

    def test_updates_existing_entry(self, w):
        W.update_quest_log(w, "q1", "里程碑一", status="active")
        r = W.update_quest_log(w, "q1", "里程碑一", status="completed")
        assert r["added"] is False
        assert r["status"] == "completed"

    def test_persists_to_flag(self, w):
        W.update_quest_log(w, "q1", "测试")
        log = w.get_flag("quest_log")
        assert log is not None
        assert len(log["entries"]) == 1
        assert log["entries"][0]["id"] == "q1"

    def test_counts_by_status(self, w):
        W.update_quest_log(w, "q1", "A", status="active")
        W.update_quest_log(w, "q2", "B", status="completed")
        W.update_quest_log(w, "q3", "C", status="locked")
        r = W.update_quest_log(w, "q4", "D", status="active")
        assert r["active_count"] == 2
        assert r["completed_count"] == 1

    def test_appends_event(self, w):
        W.update_quest_log(w, "q1", "测试")
        events = w.list_events()
        assert any(e["type"] == "quest_log" for e in events)

    def test_rejects_empty_entry_id(self, w):
        r = W.update_quest_log(w, "", "测试")
        assert "error" in r

    def test_rejects_empty_title(self, w):
        r = W.update_quest_log(w, "q1", "")
        assert "error" in r

    def test_default_status_is_active(self, w):
        r = W.update_quest_log(w, "q1", "测试")
        assert r["status"] == "active"

    def test_new_entry_has_timestamps(self, w):
        r = W.update_quest_log(w, "q1", "测试")
        log = w.get_flag("quest_log")
        entry = log["entries"][0]
        assert "created_at" in entry
        assert "updated_at" in entry
        assert entry["created_at"] == entry["updated_at"]

    def test_update_changes_updated_at(self, w):
        W.update_quest_log(w, "q1", "里程碑一", status="active")
        log1 = w.get_flag("quest_log")
        t1 = log1["entries"][0]["updated_at"]
        W.update_quest_log(w, "q1", "里程碑一", status="completed")
        log2 = w.get_flag("quest_log")
        t2 = log2["entries"][0]["updated_at"]
        assert t2 >= t1
        assert log2["entries"][0]["created_at"] == t1


# ----- record_dialogue (Phase 28) -----

class TestRecordDialogue:
    def test_records_dialogue_event(self, w):
        r = W.record_dialogue(w, "zhifu", "player", topic="天气",
                              player_line="今天天气不错", npc_response="是啊",
                              attitude_delta=5)
        assert r["npc_id"] == "zhifu"
        assert r["dialogue_recorded"] is True
        assert r["attitude_delta"] == 5
        assert r["old_attitude"] == 0
        assert r["new_attitude"] == 5

    def test_adds_memory_to_npc(self, w):
        W.record_dialogue(w, "zhifu", "player", topic="打听",
                          player_line="你认识赵三吗")
        npc = w.get_entity("zhifu")
        memories = npc["attributes"].get("memories", [])
        assert len(memories) >= 1
        assert any("打听" in m.get("text", "") for m in memories)

    def test_adjusts_attitude(self, w):
        W.record_dialogue(w, "zhifu", "player", attitude_delta=10)
        npc = w.get_entity("zhifu")
        assert npc["attributes"]["attitude"]["player"] == 10

    def test_negative_attitude(self, w):
        W.record_dialogue(w, "zhifu", "player", attitude_delta=-15)
        npc = w.get_entity("zhifu")
        assert npc["attributes"]["attitude"]["player"] == -15

    def test_no_attitude_change_when_zero(self, w):
        r = W.record_dialogue(w, "zhifu", "player")
        assert "attitude_delta" not in r

    def test_error_not_npc(self, w):
        r = W.record_dialogue(w, "player")
        assert "error" in r

    def test_error_not_found(self, w):
        r = W.record_dialogue(w, "ghost")
        assert "error" in r

    def test_revealed_rumor_in_result(self, w):
        r = W.record_dialogue(w, "zhifu", "player",
                              revealed_rumor="码头有夜船")
        assert r["revealed_rumor"] == "码头有夜船"

    def test_dialogue_logged_as_event(self, w):
        W.record_dialogue(w, "zhifu", "player", topic="秘闻",
                          player_line="告诉我真相")
        events = w.list_events(limit=10)
        dialogue_events = [e for e in events if e.get("type") == "dialogue"]
        assert len(dialogue_events) >= 1
        ev = dialogue_events[-1]
        assert ev["target"] == "zhifu"
        assert ev["topic"] == "秘闻"


# ----- set_weather (Phase 31) -----

class TestSetWeather:
    def test_sets_weather_and_logs_event(self, w):
        r = W.set_weather(w, condition="rain", intensity="moderate",
                          text="秋雨绵绵", reason="季节变化")
        assert r["new"]["condition"] == "rain"
        assert r["new"]["intensity"] == "moderate"
        assert r["new"]["text"] == "秋雨绵绵"
        stored = w.get_flag("weather")
        assert stored["condition"] == "rain"
        assert any(e["type"] == "weather_change" for e in w.list_events())

    def test_preserves_unset_fields(self, w):
        W.set_weather(w, condition="fog", intensity="heavy", text="大雾弥漫")
        r = W.set_weather(w, condition="clear")
        assert r["new"]["condition"] == "clear"
        assert r["new"]["intensity"] == "heavy"  # preserved
        assert r["new"]["text"] == "大雾弥漫"  # preserved

    def test_rejects_invalid_condition(self, w):
        r = W.set_weather(w, condition="tornado")
        assert "error" in r
        assert "invalid condition" in r["error"]

    def test_rejects_invalid_intensity(self, w):
        r = W.set_weather(w, condition="rain", intensity="extreme")
        assert "error" in r
        assert "invalid intensity" in r["error"]

    def test_returns_old_and_new(self, w):
        W.set_weather(w, condition="clear", text="晴天")
        r = W.set_weather(w, condition="cloudy", text="阴天")
        assert r["old"]["condition"] == "clear"
        assert r["new"]["condition"] == "cloudy"

    def test_default_intensity_light(self, w):
        r = W.set_weather(w, condition="snow")
        assert r["new"]["intensity"] == "light"

    def test_empty_condition_preserves_old(self, w):
        W.set_weather(w, condition="storm", intensity="heavy", text="暴风雨")
        r = W.set_weather(w, text="暴风雨加剧")
        assert r["new"]["condition"] == "storm"
        assert r["new"]["text"] == "暴风雨加剧"
