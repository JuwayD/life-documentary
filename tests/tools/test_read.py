"""Tests for read tools — pure read operations exposed to GM Agent."""
import pytest
from mingrpg.core.world import World
from mingrpg.tools import read as R


@pytest.fixture
def w():
    world = World(":memory:")
    world.save_location({"id": "hall", "name": "扬州府衙大堂",
                         "type": "indoor_official", "size": [10, 10],
                         "exits": {"south": "yard"}, "tags": ["official"]})
    world.save_location({"id": "yard", "name": "府衙院子",
                         "type": "outdoor", "size": [20, 20],
                         "exits": {"north": "hall"}, "tags": ["public"]})
    world.save_entity({"id": "player", "name": "无名书生",
                       "type": "player", "location": "hall", "pos": [3, 5],
                       "attributes": {"hp": 100, "rank": "平民"},
                       "status_effects": [], "inventory": [], "tags": []})
    world.save_entity({"id": "zhifu", "name": "王知府",
                       "type": "npc", "location": "hall", "pos": [3, 7],
                       "attributes": {"hp": 80, "rank": "四品"},
                       "status_effects": [], "inventory": [],
                       "tags": ["official"]})
    world.save_entity({"id": "guard", "name": "衙役甲",
                       "type": "npc", "location": "hall", "pos": [1, 7],
                       "attributes": {"hp": 50},
                       "status_effects": [], "inventory": [],
                       "tags": ["official", "guard"]})
    world.save_entity({"id": "beggar", "name": "乞丐",
                       "type": "npc", "location": "yard", "pos": [10, 10],
                       "attributes": {"hp": 30},
                       "status_effects": [], "inventory": [], "tags": []})
    return world


# ----- get_entity -----

def test_get_entity_returns_full_state(w):
    r = R.get_entity(w, "player")
    assert r["name"] == "无名书生"
    assert r["attributes"]["hp"] == 100


def test_get_entity_unknown_returns_error(w):
    r = R.get_entity(w, "ghost")
    assert "error" in r
    assert "ghost" in r["error"]


# ----- get_location -----

def test_get_location_returns_full(w):
    r = R.get_location(w, "hall")
    assert r["name"] == "扬州府衙大堂"
    assert "south" in r["exits"]


def test_get_location_unknown_returns_error(w):
    r = R.get_location(w, "void")
    assert "error" in r


# ----- list_entities_nearby -----

def test_list_entities_nearby_default_radius(w):
    """玩家在 (3,5),hall 内的 zhifu(3,7)/guard(1,7) 都在 5 格以内"""
    r = R.list_entities_nearby(w, "player")
    ids = sorted(e["id"] for e in r["entities"])
    assert ids == ["guard", "zhifu"]  # player 自己不返回


def test_list_entities_nearby_small_radius(w):
    """半径 2 时,只有 zhifu (距离 2) 算近"""
    r = R.list_entities_nearby(w, "player", radius=2)
    ids = [e["id"] for e in r["entities"]]
    assert "zhifu" in ids
    assert "guard" not in ids  # guard 距离是 sqrt(4+4)=2.83


def test_list_entities_nearby_excludes_other_locations(w):
    r = R.list_entities_nearby(w, "player", radius=100)
    ids = [e["id"] for e in r["entities"]]
    assert "beggar" not in ids


def test_list_entities_nearby_unknown_actor(w):
    r = R.list_entities_nearby(w, "nobody")
    assert "error" in r


# ----- query_laws -----

def test_query_laws_returns_empty_when_no_data(w, tmp_path, monkeypatch):
    monkeypatch.setattr(R, "_LAW_DIR", str(tmp_path))
    R._reset_laws_cache()
    r = R.query_laws(["打人"])
    assert r["laws"] == []


def test_query_laws_matches_by_keyword(w, tmp_path, monkeypatch):
    """关键词匹配能找到对应法条"""
    law_file = tmp_path / "test.yaml"
    law_file.write_text(
        "- id: test.law.1\n"
        "  category: 斗殴\n"
        "  text: 凡殴打官员者杖一百\n"
        "  keywords: [打, 殴, 官员]\n",
        encoding="utf-8")
    monkeypatch.setattr(R, "_LAW_DIR", str(tmp_path))
    R._reset_laws_cache()
    r = R.query_laws(["殴打", "官员"])
    assert len(r["laws"]) == 1
    assert r["laws"][0]["id"] == "test.law.1"


def test_query_laws_top_k(w, tmp_path, monkeypatch):
    law_file = tmp_path / "many.yaml"
    entries = "".join(
        f"- id: law.{i}\n  category: 斗殴\n  text: t{i}\n"
        f"  keywords: [打]\n" for i in range(5))
    law_file.write_text(entries, encoding="utf-8")
    monkeypatch.setattr(R, "_LAW_DIR", str(tmp_path))
    R._reset_laws_cache()
    r = R.query_laws(["打"], top_k=3)
    assert len(r["laws"]) == 3


def test_query_laws_loads_real_data(monkeypatch):
    """Ensure the real law YAML files in data/laws/ can be loaded."""
    from pathlib import Path
    # tests/tools/test_read.py → 3 levels up = project root
    real_dir = str(Path(__file__).parent.parent.parent / "data" / "laws")
    monkeypatch.setattr(R, "_LAW_DIR", real_dir)
    R._reset_laws_cache()
    laws = R._load_laws()
    # 01_criminal(6) + 02_curfew(4) + 03_commerce(5) + 04_combat(5) +
    # 05_household(5) + 06_official(5) + 07_gambling(2) + 08_poison(2) +
    # 09_trespass(2) + 10_witness_tampering(2) = 38
    assert len(laws) == 38, f"Expected 38 laws, got {len(laws)}"


def test_query_laws_covers_new_categories(monkeypatch):
    """Query laws by new Phase 5C category keywords."""
    from pathlib import Path
    real_dir = str(Path(__file__).parent.parent.parent / "data" / "laws")
    monkeypatch.setattr(R, "_LAW_DIR", real_dir)
    R._reset_laws_cache()
    r1 = R.query_laws(["贿赂", "贪赃"])
    assert len(r1["laws"]) >= 1
    ids1 = [law["id"] for law in r1["laws"]]
    assert any("受赃" in lid for lid in ids1), f"贿赂 should match 受赃: {ids1}"

    r2 = R.query_laws(["田产", "典卖"])
    assert len(r2["laws"]) >= 1
    ids2 = [law["id"] for law in r2["laws"]]
    assert any("田宅" in lid for lid in ids2), f"田产 should match 田宅: {ids2}"

    r3 = R.query_laws(["婚姻", "婚书"])
    assert len(r3["laws"]) >= 1
    ids3 = [law["id"] for law in r3["laws"]]
    assert any("婚姻" in lid for lid in ids3), f"婚姻 should match: {ids3}"

    r4 = R.query_laws(["泄密", "军情"])
    assert len(r4["laws"]) >= 1
    ids4 = [law["id"] for law in r4["laws"]]
    assert any("漏泄" in lid for lid in ids4), f"泄密 should match: {ids4}"


# ----- query_laws vector retrieval -----

def test_query_laws_vector_mode(w, tmp_path, monkeypatch):
    """Natural language query uses vector retrieval."""
    law_file = tmp_path / "test.yaml"
    law_file.write_text(
        "- id: test.law.1\n"
        "  category: 斗殴\n"
        "  text: 凡殴打官员者杖一百\n"
        "  keywords: [打, 殴, 官员]\n"
        "- id: test.law.2\n"
        "  category: 贼盗\n"
        "  text: 凡窃盗已行而不得财者笞五十\n"
        "  keywords: [偷, 窃, 盗]\n",
        encoding="utf-8")
    monkeypatch.setattr(R, "_LAW_DIR", str(tmp_path))
    R._reset_laws_cache()
    r = R.query_laws(query="平民殴打知府大人")
    assert r["mode"] == "vector"
    assert len(r["laws"]) >= 1
    assert r["laws"][0]["id"] == "test.law.1"


def test_query_laws_hybrid_mode(w, tmp_path, monkeypatch):
    """Both keywords and query produces hybrid results."""
    law_file = tmp_path / "test.yaml"
    law_file.write_text(
        "- id: test.law.1\n"
        "  category: 斗殴\n"
        "  text: 凡殴打官员者杖一百\n"
        "  keywords: [打, 殴, 官员]\n"
        "- id: test.law.2\n"
        "  category: 贼盗\n"
        "  text: 凡窃盗已行而不得财者笞五十\n"
        "  keywords: [偷, 窃, 盗]\n",
        encoding="utf-8")
    monkeypatch.setattr(R, "_LAW_DIR", str(tmp_path))
    R._reset_laws_cache()
    r = R.query_laws(keywords=["殴打"], query="平民攻击官员")
    assert r["mode"] == "hybrid"
    assert len(r["laws"]) >= 1


def test_query_laws_vector_with_real_data(monkeypatch):
    """Vector retrieval works with real law data."""
    from pathlib import Path
    real_dir = str(Path(__file__).parent.parent.parent / "data" / "laws")
    monkeypatch.setattr(R, "_LAW_DIR", real_dir)
    R._reset_laws_cache()
    r = R.query_laws(query="有人在夜里偷偷翻墙进别人家")
    assert r["mode"] == "vector"
    assert len(r["laws"]) >= 1
    ids = [law["id"] for law in r["laws"]]
    assert any("擅入" in lid or "越墙" in lid for lid in ids), \
        f"翻墙入室 should match trespass law: {ids}"


def test_query_laws_backward_compat_keywords_only(w, tmp_path, monkeypatch):
    """Existing keyword-only calls still work unchanged."""
    law_file = tmp_path / "test.yaml"
    law_file.write_text(
        "- id: test.law.1\n"
        "  category: 斗殴\n"
        "  text: 凡殴打官员者杖一百\n"
        "  keywords: [打, 殴, 官员]\n",
        encoding="utf-8")
    monkeypatch.setattr(R, "_LAW_DIR", str(tmp_path))
    R._reset_laws_cache()
    r = R.query_laws(keywords=["殴打", "官员"])
    assert r["mode"] == "keyword"
    assert len(r["laws"]) == 1
    assert r["laws"][0]["id"] == "test.law.1"


# ----- get_world_time -----

def test_get_world_time(w):
    r = R.get_world_time(w)
    assert "year" in r
    assert "time_of_day" in r


# ----- get_recent_events -----

def test_get_recent_events(w):
    w.append_event({"actor": "player", "summary": "进入大堂"})
    w.append_event({"actor": "player", "summary": "向知府行礼"})
    r = R.get_recent_events(w, limit=10)
    assert len(r["events"]) == 2
    assert r["events"][-1]["summary"] == "向知府行礼"


# ----- list_locations -----

def test_list_locations_returns_all(w):
    r = R.list_locations(w)
    locs = r["locations"]
    ids = sorted(l["id"] for l in locs)
    assert ids == ["hall", "yard"]


def test_list_locations_empty_world():
    world = World(":memory:")
    r = R.list_locations(world)
    assert r["locations"] == []


# ----- Phase 6 Step 2: list_advisors -----

def test_list_advisors_returns_marked_npcs(w):
    w.save_entity({"id": "shiye", "name": "刘师爷", "type": "npc",
                   "location": "hall", "pos": [4, 6],
                   "attributes": {"hp": 50, "personality": "圆滑",
                                  "is_advisor": True,
                                  "advisor_topics": ["府衙程序"],
                                  "advisor_style": "谨慎",
                                  "occupation": "幕僚",
                                  "memories": []},
                   "status_effects": [], "inventory": [], "tags": []})
    r = R.list_advisors(w)
    assert len(r["advisors"]) == 1
    a = r["advisors"][0]
    assert a["id"] == "shiye"
    assert a["name"] == "刘师爷"
    assert "府衙程序" in a["advisor_topics"]


def test_list_advisors_filters_by_location(w):
    w.save_entity({"id": "shiye", "name": "刘师爷", "type": "npc",
                   "location": "hall", "pos": [4, 6],
                   "attributes": {"hp": 50, "personality": "圆滑",
                                  "is_advisor": True,
                                  "advisor_topics": ["府衙程序"],
                                  "advisor_style": "谨慎",
                                  "occupation": "幕僚",
                                  "memories": []},
                   "status_effects": [], "inventory": [], "tags": []})
    w.save_entity({"id": "teahouse_owner", "name": "陈掌柜", "type": "npc",
                   "location": "teahouse", "pos": [5, 3],
                   "attributes": {"hp": 60, "personality": "消息灵通",
                                  "is_advisor": True,
                                  "advisor_topics": ["街市传闻"],
                                  "advisor_style": "热心",
                                  "occupation": "茶馆老板",
                                  "memories": []},
                   "status_effects": [], "inventory": [], "tags": []})
    r = R.list_advisors(w, location_id="hall")
    assert len(r["advisors"]) == 1
    assert r["advisors"][0]["id"] == "shiye"


def test_list_advisors_empty_world(w):
    r = R.list_advisors(w)
    assert r["advisors"] == []


# ----- Phase 6 Step 4: list_party -----


def test_list_party_defaults_to_player_only(w):
    r = R.list_party(w)
    assert r["leader_id"] == "player"
    assert r["active_actor_id"] == "player"
    assert len(r["members"]) == 1
    assert r["members"][0]["id"] == "player"
    assert r["members"][0]["is_active"] is True


def test_list_party_returns_joined_members(w):
    w.set_flag("party", {
        "leader_id": "player",
        "active_actor_id": "zhifu",
        "members": [
            {"entity_id": "player", "role": "主角", "joined_reason": "初始队伍"},
            {"entity_id": "zhifu", "role": "官府向导", "joined_reason": "带路"},
        ],
    })
    r = R.list_party(w)
    ids = [m["id"] for m in r["members"]]
    assert ids == ["player", "zhifu"]
    zhifu = next(m for m in r["members"] if m["id"] == "zhifu")
    assert zhifu["role"] == "官府向导"
    assert zhifu["is_active"] is True


def test_list_party_rejects_unknown_leader(w):
    r = R.list_party(w, leader_id="ghost")
    assert "error" in r


# ----- Phase 6 Step 3: list_observables -----


def test_list_observables_returns_visible_location_and_entity_details(w):
    loc = w.get_location("hall")
    loc["observable_details"] = [
        {"id": "case_table", "text": "案上压着状纸", "discovery_value": 8},
        {"id": "hidden_screen", "text": "屏风后有人", "discovery_value": 15},
    ]
    w.save_location(loc)
    guard = w.get_entity("guard")
    guard["attributes"]["observable_details"] = [
        {"id": "guard_stick", "text": "水火棍有新裂痕", "discovery_value": 10},
    ]
    w.save_entity(guard)

    r = R.list_observables(w, "player")

    ids = [d["id"] for d in r["details"]]
    assert "case_table" in ids
    assert "guard_stick" in ids
    assert "hidden_screen" not in ids
    assert r["observation_score"] == 10


def test_list_observables_includes_previously_discovered_hard_detail(w):
    loc = w.get_location("hall")
    loc["observable_details"] = [
        {"id": "hidden_screen", "text": "屏风后有人", "discovery_value": 15},
    ]
    w.save_location(loc)
    w.set_flag("observations", {"player": {
        "location:hall:hidden_screen": {"detail_id": "hidden_screen"}
    }})

    r = R.list_observables(w, "player")

    assert r["details"][0]["id"] == "hidden_screen"
    assert r["details"][0]["discovered"] is True


def test_list_observables_rejects_unknown_actor(w):
    r = R.list_observables(w, "ghost")
    assert "error" in r


# ----- list_skills -----

class TestListSkills:
    def test_returns_entity_skills(self, w):
        e = w.get_entity("player")
        e["attributes"]["skills"] = {
            "litigation": {"name": "讼学", "xp": 12, "level": 1},
            "calligraphy": {"name": "书法", "xp": 3, "level": 0},
        }
        w.save_entity(e)
        r = R.list_skills(w, "player")
        assert r["entity_id"] == "player"
        assert r["entity_name"] == "无名书生"
        assert "litigation" in r["skills"]
        assert r["skills"]["litigation"]["xp"] == 12
        assert r["skills"]["calligraphy"]["level"] == 0

    def test_empty_when_no_skills(self, w):
        r = R.list_skills(w, "player")
        assert r["entity_id"] == "player"
        assert r["skills"] == {}

    def test_unknown_entity_returns_error(self, w):
        r = R.list_skills(w, "ghost")
        assert "error" in r
        assert "ghost" in r["error"]


# ----- list_endings -----

def test_list_endings_returns_seeds_and_progress(w):
    w.set_flag("ending_seeds", [{"id": "official_vindication", "title": "公堂昭雪"}])
    w.set_flag("ending_progress", {"endings": [{"id": "official_vindication"}]})
    r = R.list_endings(w)
    assert r["ending_seeds"][0]["id"] == "official_vindication"
    assert r["ending_progress"]["endings"][0]["id"] == "official_vindication"


def test_list_endings_defaults_empty(w):
    r = R.list_endings(w)
    assert r["ending_seeds"] == []
    assert r["ending_progress"] == {"endings": []}


def test_list_endings_returns_steps(w):
    w.set_flag("ending_steps", {"ending_a": [
        {"id": "s1", "label": "步骤一", "completed": True},
        {"id": "s2", "label": "步骤二", "completed": False},
    ]})
    r = R.list_endings(w)
    assert "ending_steps" in r
    assert len(r["ending_steps"]["ending_a"]) == 2
    assert r["ending_steps"]["ending_a"][0]["completed"] is True


# ----- list_evolutions -----

class TestListEvolutions:
    def test_returns_registered_entities(self, w):
        w.set_flag("evolution_registry", [
            {"entity_id": "zhifu", "frequency": "every_turn",
             "last_evolved_turn": 5, "reason": "玩家在府衙"},
            {"entity_id": "beggar", "frequency": "every_2_turns",
             "last_evolved_turn": 3, "reason": "街市常驻"},
        ])
        r = R.list_evolutions(w)
        assert r["count"] == 2
        assert r["evolutions"][0]["entity_id"] == "zhifu"
        assert r["evolutions"][0]["entity_name"] == "王知府"
        assert r["evolutions"][1]["entity_id"] == "beggar"
        assert r["evolutions"][1]["entity_name"] == "乞丐"

    def test_defaults_empty(self, w):
        r = R.list_evolutions(w)
        assert r["evolutions"] == []
        assert r["count"] == 0

    def test_includes_turns_since_evolution(self, w):
        w.set_flag("evolution_registry", [
            {"entity_id": "zhifu", "frequency": "every_turn",
             "last_evolved_turn": 5, "reason": ""},
        ])
        w.set_flag("turn_index", 10)
        r = R.list_evolutions(w)
        assert r["evolutions"][0]["turns_since_evolution"] == 5
        assert r["current_turn"] == 10

    def test_handles_nonexistent_entity(self, w):
        w.set_flag("evolution_registry", [
            {"entity_id": "ghost", "frequency": "dormant",
             "last_evolved_turn": 0, "reason": ""},
        ])
        r = R.list_evolutions(w)
        assert r["evolutions"][0]["entity_name"] == "ghost"
        assert r["evolutions"][0]["entity_location"] is None


# ----- list_quest_log -----

class TestListQuestLog:
    def test_returns_entries(self, w):
        w.set_flag("quest_log", {"entries": [
            {"id": "q1", "title": "测试一", "status": "active"},
            {"id": "q2", "title": "测试二", "status": "completed"},
        ]})
        r = R.list_quest_log(w)
        assert r["total"] == 2
        assert len(r["entries"]) == 2

    def test_filters_by_status(self, w):
        w.set_flag("quest_log", {"entries": [
            {"id": "q1", "title": "A", "status": "active"},
            {"id": "q2", "title": "B", "status": "completed"},
            {"id": "q3", "title": "C", "status": "locked"},
        ]})
        r = R.list_quest_log(w, status="active")
        assert len(r["entries"]) == 1
        assert r["entries"][0]["id"] == "q1"

    def test_counts_statuses(self, w):
        w.set_flag("quest_log", {"entries": [
            {"id": "q1", "title": "A", "status": "active"},
            {"id": "q2", "title": "B", "status": "completed"},
            {"id": "q3", "title": "C", "status": "locked"},
            {"id": "q4", "title": "D", "status": "active"},
        ]})
        r = R.list_quest_log(w)
        assert r["active"] == 2
        assert r["completed"] == 1
        assert r["locked"] == 1

    def test_defaults_empty(self, w):
        r = R.list_quest_log(w)
        assert r["entries"] == []
        assert r["total"] == 0
        assert r["active"] == 0

    def test_filter_returns_correct_counts(self, w):
        w.set_flag("quest_log", {"entries": [
            {"id": "q1", "title": "A", "status": "active"},
            {"id": "q2", "title": "B", "status": "completed"},
        ]})
        r = R.list_quest_log(w, status="completed")
        assert len(r["entries"]) == 1
        # Totals reflect full log, not filtered
        assert r["total"] == 2
        assert r["active"] == 1
        assert r["completed"] == 1


# ----- get_npc_dialogue (Phase 28) -----

def _make_dialogue_world():
    """Helper: world with an NPC that has dialogue_lines."""
    world = World(":memory:")
    world.save_location({"id": "hall", "name": "大厅", "type": "indoor",
                         "size": [10, 10], "exits": {}, "tags": []})
    world.save_entity({"id": "player", "name": "书生", "type": "player",
                       "location": "hall", "pos": [3, 5],
                       "attributes": {"hp": 100}, "status_effects": [],
                       "inventory": [], "tags": []})
    world.save_entity({"id": "npc", "name": "王知府", "type": "npc",
                       "location": "hall", "pos": [3, 7],
                       "attributes": {
                           "hp": 80, "memories": [],
                           "attitude": {"player": 10},
                           "dialogue_lines": {
                               "greetings": [
                                   {"text": "你好", "min_attitude": -100, "max_attitude": 100},
                                   {"text": "贵客来了", "min_attitude": 20, "max_attitude": 100},
                               ],
                               "topics": [
                                   {"id": "weather", "label": "天气", "unlock_attitude": -100,
                                    "lines": [{"text": "今日天晴", "min_attitude": -100, "max_attitude": 100}]},
                                   {"id": "secrets", "label": "秘闻", "unlock_attitude": 30,
                                    "lines": [{"text": "有个秘密", "min_attitude": 30, "max_attitude": 100}]},
                               ],
                               "farewells": [
                                   {"text": "慢走", "min_attitude": -100, "max_attitude": 100},
                               ],
                               "special": [
                                   {"trigger": "first_meeting", "text": "初次见面"},
                                   {"trigger": "high_attitude", "text": "信任你了", "min_attitude": 50},
                               ],
                           },
                       },
                       "status_effects": [], "inventory": [], "tags": []})
    return world


def test_get_npc_dialogue_returns_greetings_filtered_by_attitude():
    w = _make_dialogue_world()
    r = R.get_npc_dialogue(w, "npc", "player")
    assert r["npc_name"] == "王知府"
    assert r["attitude"] == 10
    # attitude=10, so only greeting with min<=10<=max
    assert "你好" in r["greetings"]
    assert "贵客来了" not in r["greetings"]  # requires att>=20


def test_get_npc_dialogue_returns_topics_by_unlock():
    w = _make_dialogue_world()
    r = R.get_npc_dialogue(w, "npc", "player")
    topic_ids = [t["id"] for t in r["topics"]]
    assert "weather" in topic_ids
    assert "secrets" not in topic_ids  # requires att>=30


def test_get_npc_dialogue_specials_first_meeting():
    w = _make_dialogue_world()
    r = R.get_npc_dialogue(w, "npc", "player")
    triggers = [s["trigger"] for s in r["specials"]]
    assert "first_meeting" in triggers  # no memories = first meeting


def test_get_npc_dialogue_specials_high_attitude_hidden():
    w = _make_dialogue_world()
    r = R.get_npc_dialogue(w, "npc", "player")
    triggers = [s["trigger"] for s in r["specials"]]
    assert "high_attitude" not in triggers  # att=10 < 50


def test_get_npc_dialogue_high_attitude_shows_more():
    w = _make_dialogue_world()
    # Boost attitude to 50
    npc = w.get_entity("npc")
    npc["attributes"]["attitude"]["player"] = 50
    w.save_entity(npc)
    r = R.get_npc_dialogue(w, "npc", "player")
    assert "贵客来了" in r["greetings"]
    topic_ids = [t["id"] for t in r["topics"]]
    assert "secrets" in topic_ids
    triggers = [s["trigger"] for s in r["specials"]]
    assert "high_attitude" in triggers


def test_get_npc_dialogue_error_not_npc():
    w = _make_dialogue_world()
    r = R.get_npc_dialogue(w, "player")
    assert "error" in r


def test_get_npc_dialogue_error_not_found():
    w = _make_dialogue_world()
    r = R.get_npc_dialogue(w, "ghost")
    assert "error" in r


def test_get_npc_dialogue_no_dialogue_lines():
    w = World(":memory:")
    w.save_location({"id": "h", "name": "h", "type": "indoor",
                     "size": [1, 1], "exits": {}, "tags": []})
    w.save_entity({"id": "p", "name": "p", "type": "player",
                   "location": "h", "pos": [0, 0], "attributes": {},
                   "status_effects": [], "inventory": [], "tags": []})
    w.save_entity({"id": "n", "name": "n", "type": "npc",
                   "location": "h", "pos": [0, 0], "attributes": {},
                   "status_effects": [], "inventory": [], "tags": []})
    r = R.get_npc_dialogue(w, "n", "p")
    assert r["greetings"] == []
    assert r["topics"] == []


# ----- get_weather (Phase 31) -----

class TestGetWeather:
    def test_returns_stored_weather(self, w):
        w.set_flag("weather", {
            "condition": "rain", "intensity": "moderate",
            "text": "秋雨绵绵,街道泥泞。",
        })
        r = R.get_weather(w)
        assert r["condition"] == "rain"
        assert r["intensity"] == "moderate"
        assert "雨" in r["text"]

    def test_default_autumn(self, w):
        """Default weather for 秋 season."""
        r = R.get_weather(w)
        assert r["condition"] == "clear"
        assert r["intensity"] == "light"
        assert "秋" in r["text"]

    def test_default_spring(self, w):
        t = w.get_world_time()
        t["season"] = "春"
        w.set_world_time(t)
        r = R.get_weather(w)
        assert r["condition"] == "cloudy"
        assert "春" in r["text"]

    def test_default_summer(self, w):
        t = w.get_world_time()
        t["season"] = "夏"
        w.set_world_time(t)
        r = R.get_weather(w)
        assert r["condition"] == "clear"
        assert "夏" in r["text"]

    def test_default_winter(self, w):
        t = w.get_world_time()
        t["season"] = "冬"
        w.set_world_time(t)
        r = R.get_weather(w)
        assert r["condition"] == "cloudy"
        assert "冬" in r["text"]
