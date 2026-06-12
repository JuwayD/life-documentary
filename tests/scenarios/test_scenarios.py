"""Tests for scenario seed functions."""
import json

import pytest
from mingrpg.core.world import World
from mingrpg.scenarios.yangzhou_court import seed_yangzhou_court
from mingrpg.scenarios.yangzhou_market import seed_yangzhou_market
from mingrpg.scenarios.yangzhou_inn import seed_yangzhou_inn
from mingrpg.scenarios.yangzhou_districts import seed_yangzhou_districts
from mingrpg.scenarios.yangzhou_phase11 import seed_yangzhou_phase11
from mingrpg.scenarios.yangzhou_phase12 import seed_yangzhou_phase12
from mingrpg.scenarios.yangzhou_phase13 import seed_yangzhou_phase13
from mingrpg.scenarios.guazhou import seed_guazhou
from mingrpg.scenarios.nanjing import seed_nanjing
from mingrpg.scenarios.suzhou import seed_suzhou
from mingrpg.scenarios.hangzhou import seed_hangzhou
from mingrpg.scenarios.zhenjiang import seed_zhenjiang
from mingrpg.scenarios.huaian import seed_huaian
from mingrpg.scenarios.xuzhou import seed_xuzhou
from mingrpg.scenarios.phase23_main_story import seed_phase23_main_story


# ----- Market scenario -----

def test_seed_market_creates_locations():
    world = World(":memory:")
    seed_yangzhou_market(world)
    locs = {l["id"]: l for l in world.list_locations()}
    assert "market_gate" in locs
    assert "market_street" in locs
    assert "market_stall_food" in locs
    assert "market_stall_fabric" in locs
    assert "teahouse" in locs
    assert locs["market_gate"]["name"] == "街市入口"
    assert locs["market_street"]["name"] == "街市中心"


def test_seed_market_creates_npcs():
    world = World(":memory:")
    seed_yangzhou_market(world)
    e = world.get_entity("vendor_food")
    assert e is not None
    assert e["name"] == "孙老四"
    assert e["location"] == "market_stall_food"

    e = world.get_entity("vendor_fabric")
    assert e is not None
    assert e["name"] == "周掌柜"

    e = world.get_entity("teahouse_owner")
    assert e is not None
    assert e["name"] == "陈掌柜"

    e = world.get_entity("beggar_liu")
    assert e is not None
    assert e["name"] == "乞丐老刘"
    assert e["location"] == "market_gate"

    e = world.get_entity("constable")
    assert e is not None
    assert e["name"] == "李捕快"


def test_seed_market_npcs_have_money():
    world = World(":memory:")
    seed_yangzhou_market(world)
    assert world.get_entity("vendor_food")["attributes"]["money_wen"] == 200
    assert world.get_entity("vendor_fabric")["attributes"]["money_wen"] == 500
    assert world.get_entity("teahouse_owner")["attributes"]["money_wen"] == 300
    assert world.get_entity("beggar_liu")["attributes"]["money_wen"] == 5
    assert world.get_entity("constable")["attributes"]["money_wen"] == 100


def test_seed_market_merchants_have_price_lists_and_services():
    world = World(":memory:")
    seed_yangzhou_market(world)
    food = world.get_entity("vendor_food")
    fabric = world.get_entity("vendor_fabric")
    tea = world.get_entity("teahouse_owner")
    assert food["attributes"]["price_list"]["baozi"] == 4
    assert fabric["attributes"]["price_list"]["cotton_cloth"] == 50
    assert tea["attributes"]["service_catalog"]["tea_seat"]["price_wen"] == 8


def test_seed_market_npcs_have_personality():
    world = World(":memory:")
    seed_yangzhou_market(world)
    for eid in ["vendor_food", "vendor_fabric", "teahouse_owner",
                "beggar_liu", "constable"]:
        e = world.get_entity(eid)
        assert "personality" in e["attributes"]
        assert "memories" in e["attributes"]
        assert e["attributes"]["memories"] == []


# ----- Inn scenario -----

def test_seed_inn_creates_locations():
    world = World(":memory:")
    seed_yangzhou_inn(world)
    locs = {l["id"]: l for l in world.list_locations()}
    assert "inn_front" in locs
    assert "inn_hall" in locs
    assert "inn_room" in locs
    assert locs["inn_hall"]["name"] == "客栈大堂"


def test_seed_inn_creates_npcs():
    world = World(":memory:")
    seed_yangzhou_inn(world)
    e = world.get_entity("innkeeper")
    assert e is not None
    assert e["name"] == "赵掌柜"

    e = world.get_entity("inn_waiter")
    assert e is not None
    assert e["name"] == "店小二"

    e = world.get_entity("traveling_merchant")
    assert e is not None
    assert e["name"] == "马行商"


def test_seed_inn_npcs_have_money():
    world = World(":memory:")
    seed_yangzhou_inn(world)
    assert world.get_entity("innkeeper")["attributes"]["money_wen"] == 800
    assert world.get_entity("inn_waiter")["attributes"]["money_wen"] == 30
    assert world.get_entity("traveling_merchant")["attributes"]["money_wen"] == 300


def test_innkeeper_has_service_catalog():
    world = World(":memory:")
    seed_yangzhou_inn(world)
    services = world.get_entity("innkeeper")["attributes"]["service_catalog"]
    assert services["common_room"]["price_wen"] == 10
    assert services["private_room"]["price_wen"] == 20
    assert services["meal"]["price_wen"] == 6


# ----- All scenarios together -----

def test_all_scenarios_connected():
    """When all three seeds are loaded, exits connect properly."""
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)

    locs = {l["id"]: l for l in world.list_locations()}

    # street_main south → market_gate
    assert "south" in locs["street_main"]["exits"]
    assert locs["street_main"]["exits"]["south"] == "market_gate"

    # market_gate north → street_main, south → market_street
    assert locs["market_gate"]["exits"]["north"] == "street_main"
    assert locs["market_gate"]["exits"]["south"] == "market_street"

    # market_street → inn_front
    assert "east" in locs["market_street"]["exits"]
    assert "west" in locs["inn_front"]["exits"]
    assert locs["inn_front"]["exits"]["west"] == "market_street"

    # inn_front east → inn_hall
    assert locs["inn_front"]["exits"]["east"] == "inn_hall"
    assert locs["inn_hall"]["exits"]["west"] == "inn_front"


def test_all_scenarios_entity_count():
    """When all seeds loaded, total entities should be correct."""
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)

    entities = [json.loads(r[0]) for r in
                world._conn.execute("SELECT json_data FROM entities").fetchall()]
    # 1 player + 4 court NPCs + 5 market NPCs + 3 inn NPCs + 8 district NPCs = 21
    # (Phase 11 adds 6 more NPCs in a separate seed, not counted here)
    assert len(entities) == 21
    # Verify no duplicates (should have saved player only once from court)
    player_count = sum(1 for e in entities if e["id"] == "player")
    assert player_count == 1


def test_all_scenarios_location_count():
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)

    assert len(world.list_locations()) >= 20


def test_yangzhou_districts_add_phase5a_locations_and_exits():
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)

    locs = {l["id"]: l for l in world.list_locations()}
    for loc_id in ["academy_gate", "academy_hall", "academy_library",
                   "clinic_front", "clinic_hall", "river_dock",
                   "ferry_pier", "warehouse", "temple_gate", "temple_hall"]:
        assert loc_id in locs

    assert locs["street_main"]["exits"]["east"] == "academy_gate"
    assert locs["academy_gate"]["exits"]["west"] == "street_main"
    assert locs["street_main"]["exits"]["west"] == "temple_gate"
    assert locs["temple_gate"]["exits"]["east"] == "street_main"
    assert locs["market_gate"]["exits"]["west"] == "clinic_front"
    assert locs["clinic_front"]["exits"]["east"] == "market_gate"
    assert locs["market_gate"]["exits"]["east"] == "river_dock"
    assert locs["river_dock"]["exits"]["west"] == "market_gate"
    assert locs["river_dock"]["exits"]["east"] == "warehouse"
    assert locs["warehouse"]["exits"]["west"] == "river_dock"


def test_yangzhou_district_npcs_follow_existing_contract():
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)

    loc_ids = {l["id"] for l in world.list_locations()}
    for eid in ["teacher_gu", "student_lin", "doctor_he", "herb_apprentice",
                "dock_boss_qian", "porter_niu", "boatman_zhou", "temple_keeper"]:
        e = world.get_entity(eid)
        assert e is not None
        assert e["location"] in loc_ids
        assert "personality" in e["attributes"]
        assert e["attributes"]["memories"] == []
        assert "money_wen" in e["attributes"]
        assert e["attributes"]["attack"] >= 1
        assert e["attributes"]["defense"] >= 8


def test_yangzhou_districts_have_phase5b_economy_hooks():
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)

    doctor = world.get_entity("doctor_he")
    boatman = world.get_entity("boatman_zhou")
    dock_boss = world.get_entity("dock_boss_qian")
    assert doctor["attributes"]["price_list"]["herb_bundle"] == 12
    assert doctor["attributes"]["service_catalog"]["diagnosis"]["price_wen"] == 15
    assert boatman["attributes"]["service_catalog"]["ferry_crossing"]["price_wen"] == 5
    assert dock_boss["attributes"]["service_catalog"]["hire_porter"]["price_wen"] == 15


def test_phase5bc_npc_rumor_hooks_attached():
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)

    # Main thread leads should be in NPC rumor_hooks
    shiye = world.get_entity("shiye")
    hooks = shiye["attributes"].get("rumor_hooks", [])
    assert any("状纸" in h for h in hooks), f"shiye missing main thread hook: {hooks}"

    # Side thread entities should have their hooks
    student = world.get_entity("student_lin")
    sh = student["attributes"].get("rumor_hooks", [])
    assert any("失书" in h or "藏书楼" in h for h in sh), f"student_lin missing hook: {sh}"

    doctor = world.get_entity("doctor_he")
    dh = doctor["attributes"].get("rumor_hooks", [])
    assert any("欠账" in h or "涨价" in h for h in dh), f"doctor_he missing hook: {dh}"

    beggar = world.get_entity("beggar_liu")
    bh = beggar["attributes"].get("rumor_hooks", [])
    assert any("恶霸" in h or "货栈" in h for h in bh), f"beggar_liu missing hook: {bh}"


def test_phase5bc_location_story_threads_attached():
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)

    lib = world.get_location("academy_library")
    st = lib.get("story_threads", [])
    assert any(t["id"] == "academy_missing_book" for t in st), f"library missing thread: {st}"

    teahouse = world.get_location("teahouse")
    st2 = teahouse.get("story_threads", [])
    assert any(t["id"] == "teahouse_storyteller" for t in st2)

    hall = world.get_location("clinic_hall")
    st3 = hall.get("story_threads", [])
    assert any(t["id"] == "clinic_debtors" for t in st3)

    warehouse = world.get_location("warehouse")
    st4 = warehouse.get("story_threads", [])
    assert any(t["id"] == "warehouse_shortage" for t in st4)


def test_phase5bc_story_seeds_flag_set():
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)

    assert world.get_flag("phase5bc_story_materials") is True
    seeds = world.get_flag("story_seeds")
    assert seeds is not None
    assert "main_thread" in seeds
    assert "side_threads" in seeds
    assert len(seeds["side_threads"]) == 12
    assert seeds["main_thread"]["title"] == "状告漕帮恶霸"


def test_phase6_ending_seeds_flag_set():
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)

    seeds = world.get_flag("ending_seeds")
    assert len(seeds) == 3
    ids = {s["id"] for s in seeds}
    assert "official_vindication" in ids
    assert "private_settlement" in ids
    assert "exile_from_yangzhou" in ids


def test_phase5bc_no_duplicate_hooks():
    """Seeding twice should not duplicate hooks or threads."""
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)
    seed_yangzhou_districts(world)

    # Rumor hooks should not duplicate
    shiye = world.get_entity("shiye")
    hooks = shiye["attributes"].get("rumor_hooks", [])
    unique = set(hooks)
    assert len(hooks) == len(unique), f"duplicate hooks: {hooks}"

    # Location threads should not duplicate
    lib = world.get_location("academy_library")
    st = lib.get("story_threads", [])
    thread_ids = [t["id"] for t in st]
    assert len(thread_ids) == len(set(thread_ids)), f"duplicate threads: {thread_ids}"

    # Flag should still be present
    assert world.get_flag("phase5bc_story_materials") is True


def test_all_scenarios_npcs_have_memories():
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)

    entities = [json.loads(r[0]) for r in
                world._conn.execute("SELECT json_data FROM entities").fetchall()]
    for e in entities:
        if e["type"] == "npc":
            assert "memories" in e["attributes"], (
                f"NPC {e['id']} missing 'memories' attribute"
            )
            assert e["attributes"]["memories"] == []


# ----- Combat attributes -----

def test_guards_have_combat_attributes():
    world = World(":memory:")
    seed_yangzhou_court(world)
    for eid in ["guard_a", "guard_b"]:
        e = world.get_entity(eid)
        assert e["attributes"]["attack"] == 4
        assert e["attributes"]["defense"] == 12
        assert e["attributes"]["weapon_damage"] == "1d6"
        assert e["attributes"]["weapon_name"] == "水火棍"


def test_constable_has_combat_attributes():
    world = World(":memory:")
    seed_yangzhou_market(world)
    e = world.get_entity("constable")
    assert e["attributes"]["attack"] == 5
    assert e["attributes"]["defense"] == 13
    assert e["attributes"]["weapon_damage"] == "1d6"
    assert e["attributes"]["weapon_name"] == "腰刀"


def test_civilians_have_base_combat_attributes():
    world = World(":memory:")
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    for eid in ["vendor_food", "vendor_fabric", "teahouse_owner",
                "beggar_liu", "innkeeper", "inn_waiter", "traveling_merchant"]:
        e = world.get_entity(eid)
        assert e["attributes"]["attack"] >= 1, f"{eid} missing attack"
        assert e["attributes"]["defense"] >= 8, f"{eid} missing defense"


def test_zhifu_and_shiye_have_base_combat_attributes():
    world = World(":memory:")
    seed_yangzhou_court(world)
    for eid in ["zhifu_wang", "shiye"]:
        e = world.get_entity(eid)
        assert e["attributes"]["attack"] >= 1, f"{eid} missing attack"
        assert e["attributes"]["defense"] >= 9, f"{eid} missing defense"


# ----- Phase 5C: new side threads and commercial details -----

def test_phase5c_new_side_threads():
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)

    seeds = world.get_flag("story_seeds")
    side_ids = [s["id"] for s in seeds["side_threads"]]
    assert "court_yard_secret" in side_ids
    assert "street_main_rumor" in side_ids


def test_phase5c_commercial_details_teacher_gu():
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)

    teacher = world.get_entity("teacher_gu")
    assert teacher["attributes"]["price_list"]["copy_service"] == 30
    assert teacher["attributes"]["service_catalog"]["copy_writing"]["price_wen"] == 50
    assert teacher["attributes"]["service_catalog"]["tutoring"]["price_wen"] == 20


def test_phase5c_commercial_details_temple_keeper():
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)

    keeper = world.get_entity("temple_keeper")
    assert keeper["attributes"]["price_list"]["incense"] == 3
    assert keeper["attributes"]["service_catalog"]["blessing"]["price_wen"] == 30
    assert keeper["attributes"]["service_catalog"]["fortune_sticks"]["price_wen"] == 10


# ----- Phase 6 Step 2: Advisor NPCs -----

def test_phase6_step2_advisors_seeded():
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)

    for eid, expected_topics in [
        ("shiye", ["府衙程序", "状纸策略", "官场风险"]),
        ("teahouse_owner", ["街市传闻", "人情世故", "找证人"]),
        ("teacher_gu", ["讼状", "旧案", "读书人关系"]),
    ]:
        e = world.get_entity(eid)
        assert e["attributes"]["is_advisor"] is True, f"{eid} not advisor"
        assert e["attributes"]["advisor_topics"] == expected_topics, (
            f"{eid} topics mismatch: {e['attributes'].get('advisor_topics')}"
        )
        assert len(e["attributes"]["advisor_style"]) > 0, f"{eid} missing style"


def test_phase6_step3_observables_seeded():
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)

    player = world.get_entity("player")
    assert player["attributes"]["observation"] == 10

    hall = world.get_location("court_hall")
    detail_ids = [d["id"] for d in hall["observable_details"]]
    assert "court_hall_case_table" in detail_ids
    assert "court_hall_side_screen" in detail_ids

    shiye = world.get_entity("shiye")
    entity_detail_ids = [d["id"] for d in shiye["attributes"]["observable_details"]]
    assert "shiye_ink_stain" in entity_detail_ids
    assert "shiye_hidden_note" in entity_detail_ids


def test_phase6_step2_advisors_retain_existing_contract():
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)

    for eid in ["shiye", "teahouse_owner", "teacher_gu"]:
        e = world.get_entity(eid)
        assert "personality" in e["attributes"]
        assert "memories" in e["attributes"]
        assert e["attributes"]["memories"] == []
        assert e["location"] is not None


def test_phase5c_commercial_details_beggar_liu():
    world = World(":memory:")
    seed_yangzhou_market(world)

    beggar = world.get_entity("beggar_liu")
    svc = beggar["attributes"]["service_catalog"]["street_info"]
    assert svc["name"] == "打听街头消息"
    assert svc["price_wen"] == 10


# ----- Phase 11: World Content Deepening -----

def _seed_all_plus_phase11():
    """Helper: seed base scenarios + phase 11, return world."""
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)
    seed_yangzhou_phase11(world)
    return world


def test_phase11_antagonist_npcs_created():
    world = _seed_all_plus_phase11()

    bully = world.get_entity("bully_zhao")
    assert bully is not None
    assert bully["name"] == "赵三"
    assert bully["location"] == "river_dock"
    assert bully["attributes"]["occupation"] == "漕帮打手"
    assert bully["attributes"]["hp"] == 70
    assert bully["attributes"]["attack"] == 6
    assert bully["attributes"]["defense"] == 12
    assert "antagonist" in bully["tags"]

    merchant = world.get_entity("merchant_wu")
    assert merchant is not None
    assert merchant["name"] == "吴员外"
    assert merchant["location"] == "warehouse"
    assert merchant["attributes"]["occupation"] == "绸缎商人"
    assert merchant["attributes"]["money_wen"] == 5000
    assert "antagonist" in merchant["tags"]


def test_phase11_female_npcs_created():
    world = _seed_all_plus_phase11()

    singer = world.get_entity("teahouse_singer")
    assert singer is not None
    assert singer["name"] == "柳姑娘"
    assert singer["attributes"]["occupation"] == "茶楼歌伎"
    assert singer["location"] == "teahouse"

    herb = world.get_entity("herb_woman")
    assert herb is not None
    assert herb["name"] == "宋婶"
    assert herb["attributes"]["occupation"] == "药婆"
    assert herb["location"] == "clinic_front"

    widow = world.get_entity("temple_widow")
    assert widow is not None
    assert widow["name"] == "周寡妇"
    assert widow["attributes"]["occupation"] == "绣娘"
    assert widow["location"] == "temple_gate"

    maid = world.get_entity("inn_maid")
    assert maid is not None
    assert maid["name"] == "阿杏"
    assert maid["attributes"]["occupation"] == "客栈丫鬟"
    assert maid["location"] == "inn_hall"


def test_phase11_npcs_have_combat_attributes():
    world = _seed_all_plus_phase11()

    for eid in ["bully_zhao", "merchant_wu", "teahouse_singer",
                "herb_woman", "temple_widow", "inn_maid"]:
        e = world.get_entity(eid)
        assert "attack" in e["attributes"], f"{eid} missing attack"
        assert "defense" in e["attributes"], f"{eid} missing defense"


def test_phase11_npcs_have_memories():
    world = _seed_all_plus_phase11()

    for eid in ["bully_zhao", "merchant_wu", "teahouse_singer",
                "herb_woman", "temple_widow", "inn_maid"]:
        e = world.get_entity(eid)
        assert "memories" in e["attributes"], f"{eid} missing memories"
        assert e["attributes"]["memories"] == []


def test_phase11_npcs_have_schedules():
    world = _seed_all_plus_phase11()

    for eid in ["bully_zhao", "teahouse_singer", "temple_widow", "inn_maid"]:
        e = world.get_entity(eid)
        assert "schedule" in e["attributes"], f"{eid} missing schedule"
        assert len(e["attributes"]["schedule"]) >= 3


def test_phase11_merchant_wu_has_economy():
    world = _seed_all_plus_phase11()

    merchant = world.get_entity("merchant_wu")
    assert merchant["attributes"]["price_list"]["silk_wholesale"] == 100
    assert merchant["attributes"]["service_catalog"]["bulk_purchase"]["price_wen"] == 500


def test_phase11_herb_woman_has_services():
    world = _seed_all_plus_phase11()

    herb = world.get_entity("herb_woman")
    assert herb["attributes"]["service_catalog"]["herb_consult"]["price_wen"] == 5
    assert herb["attributes"]["service_catalog"]["midwifery"]["price_wen"] == 30


def test_phase11_jail_connectivity_fixed():
    world = _seed_all_plus_phase11()

    jail = world.get_location("jail")
    assert jail is not None
    assert "north" in jail["exits"]
    assert jail["exits"]["north"] == "court_yard"

    court_yard = world.get_location("court_yard")
    assert court_yard is not None
    assert "south_jail" in court_yard["exits"]
    assert court_yard["exits"]["south_jail"] == "jail"


def test_phase11_evolution_registry_entries():
    world = _seed_all_plus_phase11()

    registry = world.get_flag("evolution_registry")
    assert registry is not None
    reg_ids = {e["entity_id"] for e in registry}
    for eid in ["bully_zhao", "merchant_wu", "teahouse_singer",
                "herb_woman", "temple_widow", "inn_maid"]:
        assert eid in reg_ids, f"{eid} missing from evolution registry"


def test_phase11_antagonists_evolve_more_frequently():
    world = _seed_all_plus_phase11()

    registry = world.get_flag("evolution_registry")
    reg_by_id = {e["entity_id"]: e for e in registry}
    assert reg_by_id["bully_zhao"]["frequency"] == "every_2_turns"
    assert reg_by_id["merchant_wu"]["frequency"] == "every_2_turns"
    assert reg_by_id["teahouse_singer"]["frequency"] == "every_5_turns"


def test_phase11_side_threads_attached():
    world = _seed_all_plus_phase11()

    seeds = world.get_flag("story_seeds")
    assert seeds is not None
    side_ids = [s["id"] for s in seeds["side_threads"]]
    assert "dock_gambling_den" in side_ids
    assert "widow_husband_death" in side_ids
    assert "merchant_ledger" in side_ids
    assert "singer_secret" in side_ids


def test_phase11_location_story_threads():
    world = _seed_all_plus_phase11()

    warehouse = world.get_location("warehouse")
    wh_threads = [t["id"] for t in warehouse.get("story_threads", [])]
    assert "dock_gambling_den" in wh_threads
    assert "merchant_ledger" in wh_threads

    temple = world.get_location("temple_gate")
    tp_threads = [t["id"] for t in temple.get("story_threads", [])]
    assert "widow_husband_death" in tp_threads

    teahouse = world.get_location("teahouse")
    th_threads = [t["id"] for t in teahouse.get("story_threads", [])]
    assert "singer_secret" in th_threads


def test_phase11_rumor_hooks_attached():
    world = _seed_all_plus_phase11()

    # Antagonist main thread hooks
    bully = world.get_entity("bully_zhao")
    hooks = bully["attributes"].get("rumor_hooks", [])
    assert any("状纸上控告的恶霸" in h for h in hooks), f"bully_zhao missing main hook: {hooks}"

    merchant = world.get_entity("merchant_wu")
    mhooks = merchant["attributes"].get("rumor_hooks", [])
    assert any("豪商" in h for h in mhooks), f"merchant_wu missing main hook: {mhooks}"

    # Side thread hooks attached to entities
    widow = world.get_entity("temple_widow")
    wh = widow["attributes"].get("rumor_hooks", [])
    assert any("码头溺亡" in h or "赵三" in h for h in wh), f"temple_widow missing side hook: {wh}"

    singer = world.get_entity("teahouse_singer")
    sh = singer["attributes"].get("rumor_hooks", [])
    assert any("密谈" in h for h in sh), f"teahouse_singer missing side hook: {sh}"


def test_phase11_flag_set():
    world = _seed_all_plus_phase11()
    assert world.get_flag("phase11_world_deepened") is True


def test_phase11_no_duplicate_seeding():
    """Seeding phase 11 twice should not duplicate hooks or threads."""
    world = _seed_all_plus_phase11()
    seed_yangzhou_phase11(world)  # seed again

    # No duplicate side threads
    seeds = world.get_flag("story_seeds")
    side_ids = [s["id"] for s in seeds["side_threads"]]
    assert len(side_ids) == len(set(side_ids))

    # No duplicate evolution entries
    registry = world.get_flag("evolution_registry")
    reg_ids = [e["entity_id"] for e in registry]
    assert len(reg_ids) == len(set(reg_ids))

    # No duplicate rumor hooks
    bully = world.get_entity("bully_zhao")
    hooks = bully["attributes"].get("rumor_hooks", [])
    assert len(hooks) == len(set(hooks))


def test_phase11_total_entity_count():
    """After all seeds + phase 11, total entities should be 21 + 6 = 27."""
    world = _seed_all_plus_phase11()

    entities = [json.loads(r[0]) for r in
                world._conn.execute("SELECT json_data FROM entities").fetchall()]
    # 21 base + 6 phase 11 = 27
    assert len(entities) == 27


def test_phase11_npc_inventory():
    world = _seed_all_plus_phase11()

    bully = world.get_entity("bully_zhao")
    inv_ids = [i["id"] for i in bully["inventory"]]
    assert "iron_ring" in inv_ids

    merchant = world.get_entity("merchant_wu")
    minv = [i["id"] for i in merchant["inventory"]]
    assert "account_book_wu" in minv
    assert "jade_pendant" in minv

    singer = world.get_entity("teahouse_singer")
    sinv = [i["id"] for i in singer["inventory"]]
    assert "pipa" in sinv


# ----- Phase 12: NPC Expansion -----

def _seed_all_plus_phase12():
    """Helper: seed base scenarios + phase 11 + phase 12, return world."""
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)
    seed_yangzhou_phase11(world)
    seed_yangzhou_phase12(world)
    return world


def test_phase12_new_npcs_created():
    world = _seed_all_plus_phase12()

    storyteller = world.get_entity("storyteller_sun")
    assert storyteller is not None
    assert storyteller["name"] == "孙说书"
    assert storyteller["location"] == "teahouse"
    assert storyteller["attributes"]["occupation"] == "茶楼说书人"

    fortune = world.get_entity("fortune_yao")
    assert fortune is not None
    assert fortune["name"] == "姚半仙"
    assert fortune["location"] == "temple_gate"
    assert fortune["attributes"]["occupation"] == "算命先生"

    porter = world.get_entity("porter_chen")
    assert porter is not None
    assert porter["name"] == "陈脚夫"
    assert porter["location"] == "street_main"
    assert porter["attributes"]["occupation"] == "街头挑夫"

    jailer = world.get_entity("jailer_zhang")
    assert jailer is not None
    assert jailer["name"] == "张牢头"
    assert jailer["location"] == "jail"
    assert jailer["attributes"]["occupation"] == "大牢牢头"


def test_phase12_npcs_follow_contract():
    """All Phase 12 NPCs must have required attributes."""
    world = _seed_all_plus_phase12()
    loc_ids = {l["id"] for l in world.list_locations()}

    for eid in ["storyteller_sun", "fortune_yao", "porter_chen", "jailer_zhang"]:
        e = world.get_entity(eid)
        assert e is not None
        assert e["type"] == "npc"
        assert e["location"] in loc_ids, f"{eid} location {e['location']} not in locations"
        assert "personality" in e["attributes"], f"{eid} missing personality"
        assert "memories" in e["attributes"], f"{eid} missing memories"
        assert e["attributes"]["memories"] == [], f"{eid} memories not empty"
        assert "money_wen" in e["attributes"], f"{eid} missing money_wen"
        assert e["attributes"]["attack"] >= 1, f"{eid} missing attack"
        assert e["attributes"]["defense"] >= 8, f"{eid} missing defense"
        assert "hp" in e["attributes"], f"{eid} missing hp"
        assert "max_hp" in e["attributes"], f"{eid} missing max_hp"


def test_phase12_npcs_have_schedules():
    world = _seed_all_plus_phase12()

    for eid in ["storyteller_sun", "fortune_yao", "porter_chen", "jailer_zhang"]:
        e = world.get_entity(eid)
        assert "schedule" in e["attributes"], f"{eid} missing schedule"
        assert len(e["attributes"]["schedule"]) >= 2, (
            f"{eid} schedule too short: {len(e['attributes']['schedule'])}"
        )


def test_phase12_npcs_have_rumor_hooks():
    world = _seed_all_plus_phase12()

    for eid in ["storyteller_sun", "fortune_yao", "porter_chen", "jailer_zhang"]:
        e = world.get_entity(eid)
        hooks = e["attributes"].get("rumor_hooks", [])
        assert len(hooks) >= 1, f"{eid} missing rumor_hooks"


def test_phase12_npcs_have_inventory():
    world = _seed_all_plus_phase12()

    for eid in ["storyteller_sun", "fortune_yao", "porter_chen", "jailer_zhang"]:
        e = world.get_entity(eid)
        assert len(e["inventory"]) >= 1, f"{eid} missing inventory"


def test_phase12_fortune_yao_has_services():
    world = _seed_all_plus_phase12()

    fortune = world.get_entity("fortune_yao")
    svc = fortune["attributes"]["service_catalog"]
    assert svc["face_reading"]["price_wen"] == 10
    assert svc["palm_reading"]["price_wen"] == 8
    assert svc["divination"]["price_wen"] == 15


def test_phase12_jailer_has_combat_weapon():
    world = _seed_all_plus_phase12()

    jailer = world.get_entity("jailer_zhang")
    assert jailer["attributes"]["weapon_damage"] == "1d4"
    assert jailer["attributes"]["weapon_name"] == "铁尺"


def test_phase12_evolution_registry_entries():
    world = _seed_all_plus_phase12()

    registry = world.get_flag("evolution_registry")
    assert registry is not None
    reg_ids = {e["entity_id"] for e in registry}
    for eid in ["storyteller_sun", "fortune_yao", "porter_chen", "jailer_zhang"]:
        assert eid in reg_ids, f"{eid} missing from evolution registry"


def test_phase12_side_threads_attached():
    world = _seed_all_plus_phase12()

    seeds = world.get_flag("story_seeds")
    assert seeds is not None
    side_ids = [s["id"] for s in seeds["side_threads"]]
    assert "storyteller_lawsuit" in side_ids
    assert "fortune_teller_secrets" in side_ids


def test_phase12_location_story_threads():
    world = _seed_all_plus_phase12()

    teahouse = world.get_location("teahouse")
    th_threads = [t["id"] for t in teahouse.get("story_threads", [])]
    assert "storyteller_lawsuit" in th_threads

    temple = world.get_location("temple_gate")
    tp_threads = [t["id"] for t in temple.get("story_threads", [])]
    assert "fortune_teller_secrets" in tp_threads


def test_phase12_rumor_hooks_attached():
    world = _seed_all_plus_phase12()

    # Side thread hooks should be attached to anchor entities
    fortune = world.get_entity("fortune_yao")
    hooks = fortune["attributes"].get("rumor_hooks", [])
    assert any("周寡妇" in h or "黄泥" in h for h in hooks), (
        f"fortune_yao missing side thread hook: {hooks}"
    )

    storyteller = world.get_entity("storyteller_sun")
    shooks = storyteller["attributes"].get("rumor_hooks", [])
    assert any("官司" in h or "段子" in h for h in shooks), (
        f"storyteller_sun missing side thread hook: {shooks}"
    )


def test_phase12_flag_set():
    world = _seed_all_plus_phase12()
    assert world.get_flag("phase12_npc_expanded") is True


def test_phase12_no_duplicate_seeding():
    """Seeding phase 12 twice should not duplicate hooks or threads."""
    world = _seed_all_plus_phase12()
    seed_yangzhou_phase12(world)  # seed again

    # No duplicate side threads
    seeds = world.get_flag("story_seeds")
    side_ids = [s["id"] for s in seeds["side_threads"]]
    assert len(side_ids) == len(set(side_ids))

    # No duplicate evolution entries
    registry = world.get_flag("evolution_registry")
    reg_ids = [e["entity_id"] for e in registry]
    assert len(reg_ids) == len(set(reg_ids))

    # No duplicate rumor hooks
    fortune = world.get_entity("fortune_yao")
    hooks = fortune["attributes"].get("rumor_hooks", [])
    assert len(hooks) == len(set(hooks))


def test_phase12_total_entity_count():
    """After all seeds + phase 11 + phase 12, total entities should be 27 + 4 = 31."""
    world = _seed_all_plus_phase12()

    entities = [json.loads(r[0]) for r in
                world._conn.execute("SELECT json_data FROM entities").fetchall()]
    # 21 base + 6 phase 11 + 4 phase 12 = 31
    assert len(entities) == 31


# ----- Phase 13: NPC Extension -----

def _seed_all_plus_phase13():
    """Helper: seed base scenarios + phase 11 + phase 12 + phase 13, return world."""
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)
    seed_yangzhou_phase11(world)
    seed_yangzhou_phase12(world)
    seed_yangzhou_phase13(world)
    return world


def test_phase13_new_npcs_created():
    world = _seed_all_plus_phase13()

    mei = world.get_entity("flower_girl_mei")
    assert mei is not None
    assert mei["name"] == "梅儿"
    assert mei["location"] == "street_main"
    assert mei["attributes"]["occupation"] == "卖花女"

    huang = world.get_entity("scholar_huang")
    assert huang is not None
    assert huang["name"] == "黄老秀才"
    assert huang["location"] == "academy_gate"
    assert huang["attributes"]["rank"] == "秀才"

    liu = world.get_entity("washerwoman_liu")
    assert liu is not None
    assert liu["name"] == "刘婶"
    assert liu["location"] == "ferry_pier"

    wu = world.get_entity("gatekeeper_wu")
    assert wu is not None
    assert wu["name"] == "吴门子"
    assert wu["location"] == "court_yard"
    assert wu["attributes"]["rank"] == "差役"


def test_phase13_npc_schedules():
    world = _seed_all_plus_phase13()

    mei = world.get_entity("flower_girl_mei")
    schedule = mei["attributes"]["schedule"]
    assert "卯时" in schedule
    assert schedule["卯时"]["location"] == "market_stall_food"
    assert "activity" in schedule["卯时"]

    huang = world.get_entity("scholar_huang")
    assert "午时" in huang["attributes"]["schedule"]
    assert huang["attributes"]["schedule"]["午时"]["location"] == "teahouse"


def test_phase13_npc_inventory():
    world = _seed_all_plus_phase13()

    mei = world.get_entity("flower_girl_mei")
    inv_ids = [i["id"] for i in mei["inventory"]]
    assert "flower_basket" in inv_ids

    wu = world.get_entity("gatekeeper_wu")
    inv_ids = [i["id"] for i in wu["inventory"]]
    assert "court_keys" in inv_ids
    assert "visitor_log" in inv_ids


def test_phase13_evolution_registry():
    world = _seed_all_plus_phase13()
    registry = world.get_flag("evolution_registry")
    reg_ids = [e["entity_id"] for e in registry]

    assert "flower_girl_mei" in reg_ids
    assert "scholar_huang" in reg_ids
    assert "washerwoman_liu" in reg_ids
    assert "gatekeeper_wu" in reg_ids


def test_phase13_side_threads():
    world = _seed_all_plus_phase13()
    seeds = world.get_flag("story_seeds")
    side_ids = [s["id"] for s in seeds["side_threads"]]

    assert "gatekeeper_visitors" in side_ids
    assert "washerwoman_midnight_cargo" in side_ids


def test_phase13_flag_set():
    world = _seed_all_plus_phase13()
    assert world.get_flag("phase13_npc_expanded") is True


def test_phase13_no_duplicate_seeding():
    """Seeding phase 13 twice should not duplicate hooks or threads."""
    world = _seed_all_plus_phase13()
    seed_yangzhou_phase13(world)  # seed again

    # No duplicate side threads
    seeds = world.get_flag("story_seeds")
    side_ids = [s["id"] for s in seeds["side_threads"]]
    assert len(side_ids) == len(set(side_ids))

    # No duplicate evolution entries
    registry = world.get_flag("evolution_registry")
    reg_ids = [e["entity_id"] for e in registry]
    assert len(reg_ids) == len(set(reg_ids))

    # No duplicate rumor hooks
    huang = world.get_entity("scholar_huang")
    hooks = huang["attributes"].get("rumor_hooks", [])
    assert len(hooks) == len(set(hooks))


def test_phase13_total_entity_count():
    """After all seeds + phase 13, total entities should be 31 + 4 = 35."""
    world = _seed_all_plus_phase13()

    entities = [json.loads(r[0]) for r in
                world._conn.execute("SELECT json_data FROM entities").fetchall()]
    # 21 base + 6 phase 11 + 4 phase 12 + 4 phase 13 = 35
    assert len(entities) == 35


def test_phase13_npc_tags():
    world = _seed_all_plus_phase13()

    mei = world.get_entity("flower_girl_mei")
    assert "informant" in mei["tags"]

    huang = world.get_entity("scholar_huang")
    assert "scholar" in huang["tags"]

    wu = world.get_entity("gatekeeper_wu")
    assert "official" in wu["tags"]


def test_phase13_npc_skills_taught():
    world = _seed_all_plus_phase13()

    huang = world.get_entity("scholar_huang")
    assert "classical_chinese" in huang["attributes"]["skills_taught"]
    assert "calligraphy" in huang["attributes"]["skills_taught"]


def test_phase13_npc_observable_details():
    world = _seed_all_plus_phase13()

    huang = world.get_entity("scholar_huang")
    assert len(huang["attributes"]["observable_details"]) == 2

    wu = world.get_entity("gatekeeper_wu")
    assert len(wu["attributes"]["observable_details"]) == 2


# ----- Phase 17: Guazhou Ferry (新地域) -----

def _seed_all_plus_guazhou():
    """Helper: seed all Yangzhou scenarios + Guazhou, return world."""
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)
    seed_yangzhou_phase11(world)
    seed_yangzhou_phase12(world)
    seed_yangzhou_phase13(world)
    seed_guazhou(world)
    return world


def test_guazhou_creates_locations():
    world = _seed_all_plus_guazhou()
    locs = {l["id"]: l for l in world.list_locations()}

    assert "guazhou_ferry" in locs
    assert "guazhou_town" in locs
    assert "guazhou_inn" in locs

    assert locs["guazhou_ferry"]["name"] == "瓜洲渡口"
    assert locs["guazhou_town"]["name"] == "瓜洲镇街"
    assert locs["guazhou_inn"]["name"] == "瓜洲客栈"


def test_guazhou_creates_npcs():
    world = _seed_all_plus_guazhou()

    chen = world.get_entity("ferryman_chen")
    assert chen is not None
    assert chen["name"] == "陈老渡"
    assert chen["location"] == "guazhou_ferry"
    assert chen["attributes"]["occupation"] == "渡夫"

    clerk = world.get_entity("guazhou_clerk")
    assert clerk is not None
    assert clerk["name"] == "郑书办"
    assert clerk["location"] == "guazhou_town"
    assert clerk["attributes"]["rank"] == "书办"

    traveler = world.get_entity("traveler_li")
    assert traveler is not None
    assert traveler["name"] == "李行客"
    assert traveler["location"] == "guazhou_inn"
    assert traveler["attributes"]["occupation"] == "行商"


def test_guazhou_npcs_follow_contract():
    """All Guazhou NPCs must have required attributes."""
    world = _seed_all_plus_guazhou()
    loc_ids = {l["id"] for l in world.list_locations()}

    for eid in ["ferryman_chen", "guazhou_clerk", "traveler_li"]:
        e = world.get_entity(eid)
        assert e is not None
        assert e["type"] == "npc"
        assert e["location"] in loc_ids, f"{eid} location {e['location']} not in locations"
        assert "personality" in e["attributes"], f"{eid} missing personality"
        assert "memories" in e["attributes"], f"{eid} missing memories"
        assert e["attributes"]["memories"] == [], f"{eid} memories not empty"
        assert "money_wen" in e["attributes"], f"{eid} missing money_wen"
        assert e["attributes"]["attack"] >= 1, f"{eid} missing attack"
        assert e["attributes"]["defense"] >= 8, f"{eid} missing defense"
        assert "hp" in e["attributes"], f"{eid} missing hp"
        assert "max_hp" in e["attributes"], f"{eid} missing max_hp"


def test_guazhou_npcs_have_schedules():
    world = _seed_all_plus_guazhou()

    for eid in ["ferryman_chen", "guazhou_clerk", "traveler_li"]:
        e = world.get_entity(eid)
        assert "schedule" in e["attributes"], f"{eid} missing schedule"
        assert len(e["attributes"]["schedule"]) >= 3, (
            f"{eid} schedule too short: {len(e['attributes']['schedule'])}"
        )


def test_guazhou_npcs_have_rumor_hooks():
    world = _seed_all_plus_guazhou()

    for eid in ["ferryman_chen", "guazhou_clerk", "traveler_li"]:
        e = world.get_entity(eid)
        hooks = e["attributes"].get("rumor_hooks", [])
        assert len(hooks) >= 1, f"{eid} missing rumor_hooks"


def test_guazhou_npcs_have_inventory():
    world = _seed_all_plus_guazhou()

    for eid in ["ferryman_chen", "guazhou_clerk", "traveler_li"]:
        e = world.get_entity(eid)
        assert len(e["inventory"]) >= 1, f"{eid} missing inventory"


def test_guazhou_npcs_have_observable_details():
    world = _seed_all_plus_guazhou()

    for eid in ["ferryman_chen", "guazhou_clerk", "traveler_li"]:
        e = world.get_entity(eid)
        details = e["attributes"].get("observable_details", [])
        assert len(details) >= 1, f"{eid} missing observable_details"


def test_guazhou_ferryman_has_services():
    world = _seed_all_plus_guazhou()

    chen = world.get_entity("ferryman_chen")
    svc = chen["attributes"]["service_catalog"]
    assert svc["cross_river"]["price_wen"] == 5
    assert svc["night_crossing"]["price_wen"] == 15


def test_guazhou_ferryman_has_price_list():
    world = _seed_all_plus_guazhou()

    chen = world.get_entity("ferryman_chen")
    assert chen["attributes"]["price_list"]["ferry_crossing"] == 5


def test_guazhou_connects_to_ferry_pier():
    """ferry_pier should have exit to guazhou_ferry, and vice versa."""
    world = _seed_all_plus_guazhou()

    ferry_pier = world.get_location("ferry_pier")
    assert "south_guazhou" in ferry_pier["exits"]
    assert ferry_pier["exits"]["south_guazhou"] == "guazhou_ferry"

    guazhou_ferry = world.get_location("guazhou_ferry")
    assert "north" in guazhou_ferry["exits"]
    assert guazhou_ferry["exits"]["north"] == "ferry_pier"


def test_guazhou_locations_connected():
    """Guazhou locations should connect to each other."""
    world = _seed_all_plus_guazhou()

    locs = {l["id"]: l for l in world.list_locations()}

    assert locs["guazhou_ferry"]["exits"]["south"] == "guazhou_town"
    assert locs["guazhou_town"]["exits"]["north"] == "guazhou_ferry"
    assert locs["guazhou_town"]["exits"]["east"] == "guazhou_inn"
    assert locs["guazhou_inn"]["exits"]["west"] == "guazhou_town"


def test_guazhou_evolution_registry():
    world = _seed_all_plus_guazhou()
    registry = world.get_flag("evolution_registry")
    reg_ids = {e["entity_id"] for e in registry}

    assert "ferryman_chen" in reg_ids
    assert "guazhou_clerk" in reg_ids
    assert "traveler_li" in reg_ids


def test_guazhou_side_thread_attached():
    world = _seed_all_plus_guazhou()
    seeds = world.get_flag("story_seeds")
    side_ids = [s["id"] for s in seeds["side_threads"]]
    assert "guazhou_night_crossing" in side_ids


def test_guazhou_location_story_threads():
    world = _seed_all_plus_guazhou()

    ferry = world.get_location("guazhou_ferry")
    threads = [t["id"] for t in ferry.get("story_threads", [])]
    assert "guazhou_night_crossing" in threads


def test_guazhou_rumor_hooks_attached():
    world = _seed_all_plus_guazhou()

    chen = world.get_entity("ferryman_chen")
    hooks = chen["attributes"].get("rumor_hooks", [])
    assert any("夜渡" in h or "半夜" in h or "芦苇荡" in h for h in hooks), (
        f"ferryman_chen missing side thread hook: {hooks}"
    )


def test_guazhou_flag_set():
    world = _seed_all_plus_guazhou()
    assert world.get_flag("guazhou_seeded") is True


def test_guazhou_no_duplicate_seeding():
    """Seeding Guazhou twice should not duplicate hooks or threads."""
    world = _seed_all_plus_guazhou()
    seed_guazhou(world)  # seed again

    # No duplicate side threads
    seeds = world.get_flag("story_seeds")
    side_ids = [s["id"] for s in seeds["side_threads"]]
    assert len(side_ids) == len(set(side_ids))

    # No duplicate evolution entries
    registry = world.get_flag("evolution_registry")
    reg_ids = [e["entity_id"] for e in registry]
    assert len(reg_ids) == len(set(reg_ids))

    # No duplicate rumor hooks
    chen = world.get_entity("ferryman_chen")
    hooks = chen["attributes"].get("rumor_hooks", [])
    assert len(hooks) == len(set(hooks))


def test_guazhou_total_entity_count():
    """After all seeds + Guazhou, total entities should be 35 + 3 = 38."""
    world = _seed_all_plus_guazhou()

    entities = [json.loads(r[0]) for r in
                world._conn.execute("SELECT json_data FROM entities").fetchall()]
    # 21 base + 6 phase 11 + 4 phase 12 + 4 phase 13 + 3 guazhou = 38
    assert len(entities) == 38


def test_guazhou_total_location_count():
    """After all seeds + Guazhou, total locations should increase by 3."""
    world = _seed_all_plus_guazhou()
    locs = world.list_locations()
    # Should have at least 22 Yangzhou + 3 Guazhou = 25
    assert len(locs) >= 25


def test_guazhou_npc_tags():
    world = _seed_all_plus_guazhou()

    chen = world.get_entity("ferryman_chen")
    assert "ferryman" in chen["tags"]
    assert "informant" in chen["tags"]

    clerk = world.get_entity("guazhou_clerk")
    assert "official" in clerk["tags"]
    assert "informant" in clerk["tags"]

    traveler = world.get_entity("traveler_li")
    assert "merchant" in traveler["tags"]
    assert "informant" in traveler["tags"]


def test_guazhou_npc_inventory_items():
    world = _seed_all_plus_guazhou()

    chen = world.get_entity("ferryman_chen")
    inv_ids = [i["id"] for i in chen["inventory"]]
    assert "ferry_boat" in inv_ids
    assert "copper_whistle" in inv_ids

    clerk = world.get_entity("guazhou_clerk")
    inv_ids = [i["id"] for i in clerk["inventory"]]
    assert "tax_book" in inv_ids

    traveler = world.get_entity("traveler_li")
    inv_ids = [i["id"] for i in traveler["inventory"]]
    assert "fake_permit" in inv_ids


# ----- Phase 20: Nanjing (南京) -----

def _seed_all_plus_nanjing():
    """Helper: seed all scenarios + Guazhou + Nanjing, return world."""
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)
    seed_yangzhou_phase11(world)
    seed_yangzhou_phase12(world)
    seed_yangzhou_phase13(world)
    seed_guazhou(world)
    seed_nanjing(world)
    return world


def test_nanjing_creates_locations():
    world = _seed_all_plus_nanjing()
    locs = {l["id"]: l for l in world.list_locations()}

    assert "nanjing_confucius" in locs
    assert "nanjing_qinhuai" in locs
    assert "nanjing_jubaomen" in locs
    assert "nanjing_jiming" in locs

    assert locs["nanjing_confucius"]["name"] == "夫子庙贡院"
    assert locs["nanjing_qinhuai"]["name"] == "秦淮河畔"
    assert locs["nanjing_jubaomen"]["name"] == "聚宝门大街"
    assert locs["nanjing_jiming"]["name"] == "鸡鸣寺"


def test_nanjing_creates_npcs():
    world = _seed_all_plus_nanjing()

    scholar = world.get_entity("scholar_zhou")
    assert scholar is not None
    assert scholar["name"] == "周举子"
    assert scholar["location"] == "nanjing_confucius"
    assert scholar["attributes"]["occupation"] == "赴考举子"
    assert scholar["attributes"]["rank"] == "举人"

    madam = world.get_entity("qinhuai_madam")
    assert madam is not None
    assert madam["name"] == "秦淮鸨母"
    assert madam["location"] == "nanjing_qinhuai"
    assert madam["attributes"]["occupation"] == "画舫管事"

    officer = world.get_entity("gate_officer_sun")
    assert officer is not None
    assert officer["name"] == "孙守备"
    assert officer["location"] == "nanjing_jubaomen"
    assert officer["attributes"]["occupation"] == "聚宝门守备"
    assert officer["attributes"]["rank"] == "守备"

    monk = world.get_entity("monk_huiyuan")
    assert monk is not None
    assert monk["name"] == "慧远禅师"
    assert monk["location"] == "nanjing_jiming"
    assert monk["attributes"]["occupation"] == "鸡鸣寺住持"
    assert monk["attributes"]["rank"] == "僧侣"


def test_nanjing_npcs_follow_contract():
    """All Nanjing NPCs must have required attributes."""
    world = _seed_all_plus_nanjing()
    loc_ids = {l["id"] for l in world.list_locations()}

    for eid in ["scholar_zhou", "qinhuai_madam", "gate_officer_sun", "monk_huiyuan"]:
        e = world.get_entity(eid)
        assert e is not None
        assert e["type"] == "npc"
        assert e["location"] in loc_ids, f"{eid} location {e['location']} not in locations"
        assert "personality" in e["attributes"], f"{eid} missing personality"
        assert "memories" in e["attributes"], f"{eid} missing memories"
        assert e["attributes"]["memories"] == [], f"{eid} memories not empty"
        assert "money_wen" in e["attributes"], f"{eid} missing money_wen"
        assert e["attributes"]["attack"] >= 1, f"{eid} missing attack"
        assert e["attributes"]["defense"] >= 7, f"{eid} missing defense"
        assert "hp" in e["attributes"], f"{eid} missing hp"
        assert "max_hp" in e["attributes"], f"{eid} missing max_hp"


def test_nanjing_npcs_have_schedules():
    world = _seed_all_plus_nanjing()

    for eid in ["scholar_zhou", "qinhuai_madam", "gate_officer_sun", "monk_huiyuan"]:
        e = world.get_entity(eid)
        assert "schedule" in e["attributes"], f"{eid} missing schedule"
        assert len(e["attributes"]["schedule"]) >= 3, (
            f"{eid} schedule too short: {len(e['attributes']['schedule'])}"
        )


def test_nanjing_npcs_have_rumor_hooks():
    world = _seed_all_plus_nanjing()

    for eid in ["scholar_zhou", "qinhuai_madam", "gate_officer_sun", "monk_huiyuan"]:
        e = world.get_entity(eid)
        hooks = e["attributes"].get("rumor_hooks", [])
        assert len(hooks) >= 1, f"{eid} missing rumor_hooks"


def test_nanjing_npcs_have_inventory():
    world = _seed_all_plus_nanjing()

    for eid in ["scholar_zhou", "qinhuai_madam", "gate_officer_sun", "monk_huiyuan"]:
        e = world.get_entity(eid)
        assert len(e["inventory"]) >= 1, f"{eid} missing inventory"


def test_nanjing_npcs_have_observable_details():
    world = _seed_all_plus_nanjing()

    for eid in ["scholar_zhou", "qinhuai_madam", "gate_officer_sun", "monk_huiyuan"]:
        e = world.get_entity(eid)
        details = e["attributes"].get("observable_details", [])
        assert len(details) >= 1, f"{eid} missing observable_details"


def test_nanjing_qinhuai_madam_has_services():
    world = _seed_all_plus_nanjing()

    madam = world.get_entity("qinhuai_madam")
    svc = madam["attributes"]["service_catalog"]
    assert svc["listen_rumor"]["price_wen"] == 20
    assert svc["meet_guest"]["price_wen"] == 50


def test_nanjing_gate_officer_has_services():
    world = _seed_all_plus_nanjing()

    officer = world.get_entity("gate_officer_sun")
    svc = officer["attributes"]["service_catalog"]
    assert svc["quick_pass"]["price_wen"] == 30
    assert svc["check_records"]["price_wen"] == 15


def test_nanjing_connects_to_guazhou():
    """guazhou_ferry should have exit to nanjing_jubaomen, and vice versa."""
    world = _seed_all_plus_nanjing()

    guazhou_ferry = world.get_location("guazhou_ferry")
    assert "north_nanjing" in guazhou_ferry["exits"]
    assert guazhou_ferry["exits"]["north_nanjing"] == "nanjing_jubaomen"

    jubaomen = world.get_location("nanjing_jubaomen")
    assert "north_gate" in jubaomen["exits"]
    assert jubaomen["exits"]["north_gate"] == "guazhou_ferry"


def test_nanjing_locations_connected():
    """Nanjing locations should connect to each other."""
    world = _seed_all_plus_nanjing()

    locs = {l["id"]: l for l in world.list_locations()}

    assert locs["nanjing_confucius"]["exits"]["south"] == "nanjing_qinhuai"
    assert locs["nanjing_qinhuai"]["exits"]["north"] == "nanjing_confucius"
    assert locs["nanjing_qinhuai"]["exits"]["west"] == "nanjing_jubaomen"
    assert locs["nanjing_jubaomen"]["exits"]["east"] == "nanjing_qinhuai"
    assert locs["nanjing_confucius"]["exits"]["east"] == "nanjing_jiming"
    assert locs["nanjing_jiming"]["exits"]["west"] == "nanjing_confucius"


def test_nanjing_evolution_registry():
    world = _seed_all_plus_nanjing()
    registry = world.get_flag("evolution_registry")
    reg_ids = {e["entity_id"] for e in registry}

    assert "scholar_zhou" in reg_ids
    assert "qinhuai_madam" in reg_ids
    assert "gate_officer_sun" in reg_ids
    assert "monk_huiyuan" in reg_ids


def test_nanjing_side_threads_attached():
    world = _seed_all_plus_nanjing()
    seeds = world.get_flag("story_seeds")
    side_ids = [s["id"] for s in seeds["side_threads"]]
    assert "nanjing_exam_scandal" in side_ids
    assert "nanjing_salt_investigation" in side_ids


def test_nanjing_location_story_threads():
    world = _seed_all_plus_nanjing()

    confucius = world.get_location("nanjing_confucius")
    threads = [t["id"] for t in confucius.get("story_threads", [])]
    assert "nanjing_exam_scandal" in threads

    qinhuai = world.get_location("nanjing_qinhuai")
    qh_threads = [t["id"] for t in qinhuai.get("story_threads", [])]
    assert "nanjing_salt_investigation" in qh_threads

    jubaomen = world.get_location("nanjing_jubaomen")
    jb_threads = [t["id"] for t in jubaomen.get("story_threads", [])]
    assert "nanjing_salt_investigation" in jb_threads


def test_nanjing_rumor_hooks_attached():
    world = _seed_all_plus_nanjing()

    scholar = world.get_entity("scholar_zhou")
    hooks = scholar["attributes"].get("rumor_hooks", [])
    assert any("科场弊案" in h or "考题" in h for h in hooks), (
        f"scholar_zhou missing side thread hook: {hooks}"
    )

    madam = world.get_entity("qinhuai_madam")
    mhooks = madam["attributes"].get("rumor_hooks", [])
    assert any("盐税" in h or "扬州" in h for h in mhooks), (
        f"qinhuai_madam missing side thread hook: {mhooks}"
    )


def test_nanjing_flag_set():
    world = _seed_all_plus_nanjing()
    assert world.get_flag("nanjing_seeded") is True


def test_nanjing_no_duplicate_seeding():
    """Seeding Nanjing twice should not duplicate hooks or threads."""
    world = _seed_all_plus_nanjing()
    seed_nanjing(world)  # seed again

    # No duplicate side threads
    seeds = world.get_flag("story_seeds")
    side_ids = [s["id"] for s in seeds["side_threads"]]
    assert len(side_ids) == len(set(side_ids))

    # No duplicate evolution entries
    registry = world.get_flag("evolution_registry")
    reg_ids = [e["entity_id"] for e in registry]
    assert len(reg_ids) == len(set(reg_ids))

    # No duplicate rumor hooks
    scholar = world.get_entity("scholar_zhou")
    hooks = scholar["attributes"].get("rumor_hooks", [])
    assert len(hooks) == len(set(hooks))


def test_nanjing_total_entity_count():
    """After all seeds + Nanjing, total entities should be 38 + 4 = 42."""
    world = _seed_all_plus_nanjing()

    entities = [json.loads(r[0]) for r in
                world._conn.execute("SELECT json_data FROM entities").fetchall()]
    # 21 base + 6 phase 11 + 4 phase 12 + 4 phase 13 + 3 guazhou + 4 nanjing = 42
    assert len(entities) == 42


def test_nanjing_total_location_count():
    """After all seeds + Nanjing, total locations should increase by 4."""
    world = _seed_all_plus_nanjing()
    locs = world.list_locations()
    # Should have at least 22 Yangzhou + 3 Guazhou + 4 Nanjing = 29
    assert len(locs) >= 29


def test_nanjing_npc_tags():
    world = _seed_all_plus_nanjing()

    scholar = world.get_entity("scholar_zhou")
    assert "scholar" in scholar["tags"]
    assert "informant" in scholar["tags"]
    assert "examinee" in scholar["tags"]

    madam = world.get_entity("qinhuai_madam")
    assert "entertainer" in madam["tags"]
    assert "informant" in madam["tags"]
    assert "broker" in madam["tags"]

    officer = world.get_entity("gate_officer_sun")
    assert "official" in officer["tags"]
    assert "military" in officer["tags"]
    assert "gatekeeper" in officer["tags"]

    monk = world.get_entity("monk_huiyuan")
    assert "religious" in monk["tags"]
    assert "scholar" in monk["tags"]
    assert "informant" in monk["tags"]


def test_nanjing_npc_inventory_items():
    world = _seed_all_plus_nanjing()

    scholar = world.get_entity("scholar_zhou")
    inv_ids = [i["id"] for i in scholar["inventory"]]
    assert "exam_notes" in inv_ids
    assert "travel_permit" in inv_ids

    madam = world.get_entity("qinhuai_madam")
    inv_ids = [i["id"] for i in madam["inventory"]]
    assert "guest_book" in inv_ids
    assert "jade_bracelet" in inv_ids

    officer = world.get_entity("gate_officer_sun")
    inv_ids = [i["id"] for i in officer["inventory"]]
    assert "gate_keys" in inv_ids
    assert "pass_records" in inv_ids

    monk = world.get_entity("monk_huiyuan")
    inv_ids = [i["id"] for i in monk["inventory"]]
    assert "prayer_beads" in inv_ids
    assert "forbidden_book" in inv_ids


# ----- Suzhou scenario (Phase 21) -----

def _seed_all_plus_suzhou():
    """Helper: seed all scenarios + Suzhou, return world."""
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)
    seed_yangzhou_phase11(world)
    seed_yangzhou_phase12(world)
    seed_yangzhou_phase13(world)
    seed_guazhou(world)
    seed_nanjing(world)
    seed_suzhou(world)
    return world


def test_suzhou_creates_locations():
    world = _seed_all_plus_suzhou()
    locs = {l["id"]: l for l in world.list_locations()}

    assert "suzhou_silk_market" in locs
    assert "suzhou_garden" in locs
    assert "suzhou_canal_bridge" in locs

    assert locs["suzhou_silk_market"]["name"] == "阊门丝市"
    assert locs["suzhou_garden"]["name"] == "拙政园"
    assert locs["suzhou_canal_bridge"]["name"] == "枫桥"


def test_suzhou_creates_npcs():
    world = _seed_all_plus_suzhou()

    merchant = world.get_entity("silk_merchant_qian")
    assert merchant is not None
    assert merchant["name"] == "钱掌柜"
    assert merchant["type"] == "npc"
    assert merchant["location"] == "suzhou_silk_market"

    keeper = world.get_entity("garden_keeper_shen")
    assert keeper is not None
    assert keeper["name"] == "沈园丁"
    assert keeper["location"] == "suzhou_garden"

    boatman = world.get_entity("canal_boatman_feng")
    assert boatman is not None
    assert boatman["name"] == "冯船家"
    assert boatman["location"] == "suzhou_canal_bridge"


def test_suzhou_npcs_follow_contract():
    """Every Suzhou NPC must have hp, attack, defense, money_wen, memories."""
    world = _seed_all_plus_suzhou()

    for eid in ["silk_merchant_qian", "garden_keeper_shen", "canal_boatman_feng"]:
        e = world.get_entity(eid)
        attrs = e["attributes"]
        assert "hp" in attrs, f"{eid} missing hp"
        assert "attack" in attrs, f"{eid} missing attack"
        assert "defense" in attrs, f"{eid} missing defense"
        assert "money_wen" in attrs, f"{eid} missing money_wen"
        assert isinstance(attrs.get("memories"), list), f"{eid} memories not list"
        assert "personality" in attrs, f"{eid} missing personality"


def test_suzhou_npcs_have_schedules():
    world = _seed_all_plus_suzhou()

    for eid in ["silk_merchant_qian", "garden_keeper_shen", "canal_boatman_feng"]:
        e = world.get_entity(eid)
        sched = e["attributes"].get("schedule", {})
        assert len(sched) >= 3, f"{eid} has < 3 schedule entries"


def test_suzhou_npcs_have_rumor_hooks():
    world = _seed_all_plus_suzhou()

    for eid in ["silk_merchant_qian", "garden_keeper_shen", "canal_boatman_feng"]:
        e = world.get_entity(eid)
        hooks = e["attributes"].get("rumor_hooks", [])
        assert len(hooks) >= 2, f"{eid} has < 2 rumor hooks"


def test_suzhou_npcs_have_inventory():
    world = _seed_all_plus_suzhou()

    for eid in ["silk_merchant_qian", "garden_keeper_shen", "canal_boatman_feng"]:
        e = world.get_entity(eid)
        assert len(e.get("inventory", [])) >= 1, f"{eid} has no inventory"


def test_suzhou_npcs_have_observable_details():
    world = _seed_all_plus_suzhou()

    for eid in ["silk_merchant_qian", "garden_keeper_shen", "canal_boatman_feng"]:
        e = world.get_entity(eid)
        details = e["attributes"].get("observable_details", [])
        assert len(details) >= 1, f"{eid} has no observable_details"


def test_suzhou_merchant_has_services():
    world = _seed_all_plus_suzhou()

    merchant = world.get_entity("silk_merchant_qian")
    catalog = merchant["attributes"].get("service_catalog", {})
    assert len(catalog) >= 1, "silk_merchant_qian has no service_catalog"

    prices = merchant["attributes"].get("price_list", {})
    assert len(prices) >= 1, "silk_merchant_qian has no price_list"


def test_suzhou_boatman_has_services():
    world = _seed_all_plus_suzhou()

    boatman = world.get_entity("canal_boatman_feng")
    catalog = boatman["attributes"].get("service_catalog", {})
    assert len(catalog) >= 2, "canal_boatman_feng has < 2 services"

    prices = boatman["attributes"].get("price_list", {})
    assert len(prices) >= 1, "canal_boatman_feng has no price_list"


def test_suzhou_connects_to_yangzhou():
    """river_dock should have exit to suzhou_canal_bridge, and vice versa."""
    world = _seed_all_plus_suzhou()

    river_dock = world.get_location("river_dock")
    assert "south_suzhou" in river_dock["exits"]
    assert river_dock["exits"]["south_suzhou"] == "suzhou_canal_bridge"

    bridge = world.get_location("suzhou_canal_bridge")
    assert "north_canal" in bridge["exits"]
    assert bridge["exits"]["north_canal"] == "river_dock"


def test_suzhou_locations_connected():
    """Suzhou locations should be internally connected."""
    world = _seed_all_plus_suzhou()
    locs = {l["id"]: l for l in world.list_locations()}

    assert locs["suzhou_silk_market"]["exits"]["east"] == "suzhou_garden"
    assert locs["suzhou_garden"]["exits"]["west"] == "suzhou_silk_market"
    assert locs["suzhou_silk_market"]["exits"]["south"] == "suzhou_canal_bridge"
    assert locs["suzhou_canal_bridge"]["exits"]["north"] == "suzhou_silk_market"


def test_suzhou_evolution_registry():
    world = _seed_all_plus_suzhou()
    registry = world.get_flag("evolution_registry")
    reg_ids = {e["entity_id"] for e in registry}

    assert "silk_merchant_qian" in reg_ids
    assert "garden_keeper_shen" in reg_ids
    assert "canal_boatman_feng" in reg_ids


def test_suzhou_side_thread_attached():
    world = _seed_all_plus_suzhou()
    seeds = world.get_flag("story_seeds")
    side_ids = [s["id"] for s in seeds["side_threads"]]
    assert "suzhou_silk_conspiracy" in side_ids


def test_suzhou_location_story_threads():
    world = _seed_all_plus_suzhou()

    market = world.get_location("suzhou_silk_market")
    threads = [t["id"] for t in market.get("story_threads", [])]
    assert "suzhou_silk_conspiracy" in threads

    bridge = world.get_location("suzhou_canal_bridge")
    b_threads = [t["id"] for t in bridge.get("story_threads", [])]
    assert "suzhou_silk_conspiracy" in b_threads


def test_suzhou_rumor_hooks_attached():
    world = _seed_all_plus_suzhou()

    merchant = world.get_entity("silk_merchant_qian")
    hooks = merchant["attributes"].get("rumor_hooks", [])
    assert any("丝税" in h or "商帮" in h for h in hooks), (
        f"silk_merchant_qian missing side thread hook: {hooks}"
    )

    boatman = world.get_entity("canal_boatman_feng")
    bhooks = boatman["attributes"].get("rumor_hooks", [])
    assert any("暗舱" in h or "扬州" in h for h in bhooks), (
        f"canal_boatman_feng missing side thread hook: {bhooks}"
    )


def test_suzhou_flag_set():
    world = _seed_all_plus_suzhou()
    assert world.get_flag("suzhou_seeded") is True


def test_suzhou_no_duplicate_seeding():
    """Seeding Suzhou twice should not duplicate hooks or threads."""
    world = _seed_all_plus_suzhou()
    seed_suzhou(world)  # seed again

    # No duplicate side threads
    seeds = world.get_flag("story_seeds")
    side_ids = [s["id"] for s in seeds["side_threads"]]
    assert len(side_ids) == len(set(side_ids))

    # No duplicate evolution entries
    registry = world.get_flag("evolution_registry")
    reg_ids = [e["entity_id"] for e in registry]
    assert len(reg_ids) == len(set(reg_ids))

    # No duplicate rumor hooks
    merchant = world.get_entity("silk_merchant_qian")
    hooks = merchant["attributes"].get("rumor_hooks", [])
    assert len(hooks) == len(set(hooks))


def test_suzhou_total_entity_count():
    """After all seeds + Suzhou, total entities should be 42 + 3 = 45."""
    world = _seed_all_plus_suzhou()

    entities = [json.loads(r[0]) for r in
                world._conn.execute("SELECT json_data FROM entities").fetchall()]
    # 21 base + 6 phase 11 + 4 phase 12 + 4 phase 13 + 3 guazhou + 4 nanjing + 3 suzhou = 45
    assert len(entities) == 45


def test_suzhou_total_location_count():
    """After all seeds + Suzhou, total locations should increase by 3."""
    world = _seed_all_plus_suzhou()
    locs = world.list_locations()
    # 22 Yangzhou + 3 Guazhou + 4 Nanjing + 3 Suzhou = 32
    assert len(locs) >= 32


def test_suzhou_npc_tags():
    world = _seed_all_plus_suzhou()

    merchant = world.get_entity("silk_merchant_qian")
    assert "merchant" in merchant["tags"]
    assert "informant" in merchant["tags"]
    assert "broker" in merchant["tags"]

    keeper = world.get_entity("garden_keeper_shen")
    assert "commoner" in keeper["tags"]
    assert "informant" in keeper["tags"]
    assert "servant" in keeper["tags"]

    boatman = world.get_entity("canal_boatman_feng")
    assert "commoner" in boatman["tags"]
    assert "ferryman" in boatman["tags"]
    assert "informant" in boatman["tags"]


def test_suzhou_npc_inventory_items():
    world = _seed_all_plus_suzhou()

    merchant = world.get_entity("silk_merchant_qian")
    inv_ids = [i["id"] for i in merchant["inventory"]]
    assert "silk_samples" in inv_ids
    assert "trade_ledger" in inv_ids

    keeper = world.get_entity("garden_keeper_shen")
    inv_ids = [i["id"] for i in keeper["inventory"]]
    assert "garden_keys" in inv_ids
    assert "flower_seeds" in inv_ids

    boatman = world.get_entity("canal_boatman_feng")
    inv_ids = [i["id"] for i in boatman["inventory"]]
    assert "canal_boat" in inv_ids
    assert "waterproof_cloth" in inv_ids


# ----- Hangzhou scenario (Phase 22) -----

def _seed_all_plus_hangzhou():
    """Helper: seed all scenarios + Hangzhou, return world."""
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)
    seed_yangzhou_phase11(world)
    seed_yangzhou_phase12(world)
    seed_yangzhou_phase13(world)
    seed_guazhou(world)
    seed_nanjing(world)
    seed_suzhou(world)
    seed_hangzhou(world)
    return world


def test_hangzhou_creates_locations():
    world = _seed_all_plus_hangzhou()
    locs = {l["id"]: l for l in world.list_locations()}

    assert "hangzhou_west_lake" in locs
    assert "hangzhou_lingyin_temple" in locs
    assert "hangzhou_canal_dock" in locs

    assert locs["hangzhou_west_lake"]["name"] == "西湖"
    assert locs["hangzhou_lingyin_temple"]["name"] == "灵隐寺"
    assert locs["hangzhou_canal_dock"]["name"] == "拱宸桥码头"


def test_hangzhou_creates_npcs():
    world = _seed_all_plus_hangzhou()

    merchant = world.get_entity("tea_merchant_fang")
    assert merchant is not None
    assert merchant["name"] == "方掌柜"
    assert merchant["type"] == "npc"
    assert merchant["location"] == "hangzhou_west_lake"

    abbot = world.get_entity("abbot_mingkong")
    assert abbot is not None
    assert abbot["name"] == "明空方丈"
    assert abbot["location"] == "hangzhou_lingyin_temple"

    captain = world.get_entity("canal_captain_sun")
    assert captain is not None
    assert captain["name"] == "孙船老大"
    assert captain["location"] == "hangzhou_canal_dock"


def test_hangzhou_npcs_follow_contract():
    """Every Hangzhou NPC must have hp, attack, defense, money_wen, memories."""
    world = _seed_all_plus_hangzhou()

    for eid in ["tea_merchant_fang", "abbot_mingkong", "canal_captain_sun"]:
        e = world.get_entity(eid)
        attrs = e["attributes"]
        assert "hp" in attrs, f"{eid} missing hp"
        assert "attack" in attrs, f"{eid} missing attack"
        assert "defense" in attrs, f"{eid} missing defense"
        assert "money_wen" in attrs, f"{eid} missing money_wen"
        assert isinstance(attrs.get("memories"), list), f"{eid} memories not list"
        assert "personality" in attrs, f"{eid} missing personality"


def test_hangzhou_npcs_have_schedules():
    world = _seed_all_plus_hangzhou()

    for eid in ["tea_merchant_fang", "abbot_mingkong", "canal_captain_sun"]:
        e = world.get_entity(eid)
        sched = e["attributes"].get("schedule", {})
        assert len(sched) >= 3, f"{eid} has < 3 schedule entries"


def test_hangzhou_npcs_have_rumor_hooks():
    world = _seed_all_plus_hangzhou()

    for eid in ["tea_merchant_fang", "abbot_mingkong", "canal_captain_sun"]:
        e = world.get_entity(eid)
        hooks = e["attributes"].get("rumor_hooks", [])
        assert len(hooks) >= 2, f"{eid} has < 2 rumor hooks"


def test_hangzhou_npcs_have_inventory():
    world = _seed_all_plus_hangzhou()

    for eid in ["tea_merchant_fang", "abbot_mingkong", "canal_captain_sun"]:
        e = world.get_entity(eid)
        assert len(e.get("inventory", [])) >= 1, f"{eid} has no inventory"


def test_hangzhou_npcs_have_observable_details():
    world = _seed_all_plus_hangzhou()

    for eid in ["tea_merchant_fang", "abbot_mingkong", "canal_captain_sun"]:
        e = world.get_entity(eid)
        details = e["attributes"].get("observable_details", [])
        assert len(details) >= 1, f"{eid} has no observable_details"


def test_hangzhou_merchant_has_services():
    world = _seed_all_plus_hangzhou()

    merchant = world.get_entity("tea_merchant_fang")
    catalog = merchant["attributes"].get("service_catalog", {})
    assert len(catalog) >= 1, "tea_merchant_fang has no service_catalog"

    prices = merchant["attributes"].get("price_list", {})
    assert len(prices) >= 1, "tea_merchant_fang has no price_list"


def test_hangzhou_captain_has_services():
    world = _seed_all_plus_hangzhou()

    captain = world.get_entity("canal_captain_sun")
    catalog = captain["attributes"].get("service_catalog", {})
    assert len(catalog) >= 2, "canal_captain_sun has < 2 services"

    prices = captain["attributes"].get("price_list", {})
    assert len(prices) >= 1, "canal_captain_sun has no price_list"


def test_hangzhou_connects_to_suzhou():
    """suzhou_canal_bridge should have exit to hangzhou_canal_dock, and vice versa."""
    world = _seed_all_plus_hangzhou()

    bridge = world.get_location("suzhou_canal_bridge")
    assert "south_hangzhou" in bridge["exits"]
    assert bridge["exits"]["south_hangzhou"] == "hangzhou_canal_dock"

    dock = world.get_location("hangzhou_canal_dock")
    assert "north_suzhou" in dock["exits"]
    assert dock["exits"]["north_suzhou"] == "suzhou_canal_bridge"


def test_hangzhou_locations_connected():
    """Hangzhou locations should be internally connected."""
    world = _seed_all_plus_hangzhou()
    locs = {l["id"]: l for l in world.list_locations()}

    assert locs["hangzhou_canal_dock"]["exits"]["east"] == "hangzhou_west_lake"
    assert locs["hangzhou_west_lake"]["exits"]["west"] == "hangzhou_canal_dock"
    assert locs["hangzhou_west_lake"]["exits"]["south"] == "hangzhou_lingyin_temple"
    assert locs["hangzhou_lingyin_temple"]["exits"]["north"] == "hangzhou_west_lake"


def test_hangzhou_evolution_registry():
    world = _seed_all_plus_hangzhou()
    registry = world.get_flag("evolution_registry")
    reg_ids = {e["entity_id"] for e in registry}

    assert "tea_merchant_fang" in reg_ids
    assert "abbot_mingkong" in reg_ids
    assert "canal_captain_sun" in reg_ids


def test_hangzhou_side_thread_attached():
    world = _seed_all_plus_hangzhou()
    seeds = world.get_flag("story_seeds")
    side_ids = [s["id"] for s in seeds["side_threads"]]
    assert "hangzhou_tea_smuggling" in side_ids


def test_hangzhou_location_story_threads():
    world = _seed_all_plus_hangzhou()

    lake = world.get_location("hangzhou_west_lake")
    threads = [t["id"] for t in lake.get("story_threads", [])]
    assert "hangzhou_tea_smuggling" in threads

    dock = world.get_location("hangzhou_canal_dock")
    d_threads = [t["id"] for t in dock.get("story_threads", [])]
    assert "hangzhou_tea_smuggling" in d_threads


def test_hangzhou_rumor_hooks_attached():
    world = _seed_all_plus_hangzhou()

    merchant = world.get_entity("tea_merchant_fang")
    hooks = merchant["attributes"].get("rumor_hooks", [])
    assert any("龙井" in h or "茶" in h for h in hooks), (
        f"tea_merchant_fang missing side thread hook: {hooks}"
    )

    captain = world.get_entity("canal_captain_sun")
    chooks = captain["attributes"].get("rumor_hooks", [])
    assert any("暗舱" in h or "运河" in h for h in chooks), (
        f"canal_captain_sun missing side thread hook: {chooks}"
    )


def test_hangzhou_flag_set():
    world = _seed_all_plus_hangzhou()
    assert world.get_flag("hangzhou_seeded") is True


def test_hangzhou_no_duplicate_seeding():
    """Seeding Hangzhou twice should not duplicate hooks or threads."""
    world = _seed_all_plus_hangzhou()
    seed_hangzhou(world)  # seed again

    # No duplicate side threads
    seeds = world.get_flag("story_seeds")
    side_ids = [s["id"] for s in seeds["side_threads"]]
    assert len(side_ids) == len(set(side_ids))

    # No duplicate evolution entries
    registry = world.get_flag("evolution_registry")
    reg_ids = [e["entity_id"] for e in registry]
    assert len(reg_ids) == len(set(reg_ids))

    # No duplicate rumor hooks
    merchant = world.get_entity("tea_merchant_fang")
    hooks = merchant["attributes"].get("rumor_hooks", [])
    assert len(hooks) == len(set(hooks))


def test_hangzhou_total_entity_count():
    """After all seeds + Hangzhou, total entities should be 45 + 3 = 48."""
    world = _seed_all_plus_hangzhou()

    entities = [json.loads(r[0]) for r in
                world._conn.execute("SELECT json_data FROM entities").fetchall()]
    # 21 base + 6 phase 11 + 4 phase 12 + 4 phase 13 + 3 guazhou + 4 nanjing + 3 suzhou + 3 hangzhou = 48
    assert len(entities) == 48


def test_hangzhou_total_location_count():
    """After all seeds + Hangzhou, total locations should increase by 3."""
    world = _seed_all_plus_hangzhou()
    locs = world.list_locations()
    # 22 Yangzhou + 3 Guazhou + 4 Nanjing + 3 Suzhou + 3 Hangzhou = 35
    assert len(locs) >= 35


def test_hangzhou_npc_tags():
    world = _seed_all_plus_hangzhou()

    merchant = world.get_entity("tea_merchant_fang")
    assert "merchant" in merchant["tags"]
    assert "informant" in merchant["tags"]
    assert "broker" in merchant["tags"]

    abbot = world.get_entity("abbot_mingkong")
    assert "religious" in abbot["tags"]
    assert "informant" in abbot["tags"]
    assert "advisor" in abbot["tags"]

    captain = world.get_entity("canal_captain_sun")
    assert "commoner" in captain["tags"]
    assert "ferryman" in captain["tags"]
    assert "informant" in captain["tags"]


def test_hangzhou_npc_inventory_items():
    world = _seed_all_plus_hangzhou()

    merchant = world.get_entity("tea_merchant_fang")
    inv_ids = [i["id"] for i in merchant["inventory"]]
    assert "longjing_samples" in inv_ids
    assert "tea_trade_ledger" in inv_ids

    abbot = world.get_entity("abbot_mingkong")
    inv_ids = [i["id"] for i in abbot["inventory"]]
    assert "prayer_beads" in inv_ids
    assert "buddhist_scripture" in inv_ids

    captain = world.get_entity("canal_captain_sun")
    inv_ids = [i["id"] for i in captain["inventory"]]
    assert "cargo_boat" in inv_ids
    assert "manifest_book" in inv_ids


# ===== Phase 23: Main Story Progression =====

def _seed_all_plus_phase23():
    world = World(":memory:")
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)
    seed_yangzhou_phase11(world)
    seed_yangzhou_phase12(world)
    seed_yangzhou_phase13(world)
    seed_guazhou(world)
    seed_nanjing(world)
    seed_suzhou(world)
    seed_hangzhou(world)
    seed_phase23_main_story(world)
    return world


def test_phase23_cross_region_thread_attached():
    world = _seed_all_plus_phase23()
    seeds = world.get_flag("story_seeds")
    side_ids = [s["id"] for s in seeds["side_threads"]]
    assert "jiangnan_network" in side_ids


def test_phase23_quest_log_seeded():
    world = _seed_all_plus_phase23()
    quest_log = world.get_flag("quest_log")
    assert quest_log is not None
    entries = quest_log["entries"]
    assert len(entries) == 9

    entry_ids = [e["id"] for e in entries]
    assert "yz_petition_filed" in entry_ids
    assert "gz_night_cargo" in entry_ids
    assert "nj_exam_clue" in entry_ids
    assert "nj_salt_trail" in entry_ids
    assert "sz_silk_evidence" in entry_ids
    assert "hz_tea_cargo" in entry_ids
    assert "confrontation" in entry_ids
    assert "ha_grain_trail" in entry_ids
    assert "xz_iron_route" in entry_ids


def test_phase23_quest_log_initial_statuses():
    world = _seed_all_plus_phase23()
    quest_log = world.get_flag("quest_log")
    entries = {e["id"]: e for e in quest_log["entries"]}

    assert entries["yz_petition_filed"]["status"] == "active"
    assert entries["gz_night_cargo"]["status"] == "locked"
    assert entries["confrontation"]["status"] == "locked"


def test_phase23_court_wind_clock_seeded():
    world = _seed_all_plus_phase23()
    clocks = world.get_flag("pressure_clocks")
    assert "court_wind" in clocks
    assert clocks["court_wind"]["value"] == 0
    assert clocks["court_wind"]["danger_at"] == 5


def test_phase23_expanded_endings():
    world = _seed_all_plus_phase23()
    endings = world.get_flag("ending_seeds")
    ending_ids = [e["id"] for e in endings]

    # Original endings
    assert "official_vindication" in ending_ids
    assert "private_settlement" in ending_ids
    assert "exile_from_yangzhou" in ending_ids
    # New cross-region endings
    assert "network_dismantled" in ending_ids
    assert "partial_exposure" in ending_ids
    assert "network_retaliation" in ending_ids


def test_phase23_merchant_wu_marked():
    world = _seed_all_plus_phase23()
    wu = world.get_entity("merchant_wu")
    assert wu is not None
    assert wu["attributes"]["is_investigation_target"] is True
    assert "yangzhou" in wu["attributes"]["network_regions"]
    assert "nanjing" in wu["attributes"]["network_regions"]


def test_phase23_rumor_hooks_attached():
    world = _seed_all_plus_phase23()

    # Check hooks on key NPCs across regions
    wu = world.get_entity("merchant_wu")
    hooks = wu["attributes"].get("rumor_hooks", [])
    assert any("暗网" in h or "吴员外" in h for h in hooks), (
        f"merchant_wu missing cross-region hook: {hooks}"
    )

    ferryman = world.get_entity("ferryman_chen")
    fhooks = ferryman["attributes"].get("rumor_hooks", [])
    assert any("暗网" in h or "各地" in h for h in fhooks), (
        f"ferryman_chen missing cross-region hook: {fhooks}"
    )


def test_phase23_location_story_threads():
    world = _seed_all_plus_phase23()

    warehouse = world.get_location("warehouse")
    threads = [t["id"] for t in warehouse.get("story_threads", [])]
    assert "jiangnan_network" in threads

    lake = world.get_location("hangzhou_west_lake")
    lake_threads = [t["id"] for t in lake.get("story_threads", [])]
    assert "jiangnan_network" in lake_threads


def test_phase23_flag_set():
    world = _seed_all_plus_phase23()
    assert world.get_flag("phase23_main_story") is True


def test_phase23_no_duplicate_seeding():
    """Seeding phase23 twice should not duplicate entries."""
    world = _seed_all_plus_phase23()
    seed_phase23_main_story(world)  # seed again

    # No duplicate side threads
    seeds = world.get_flag("story_seeds")
    side_ids = [s["id"] for s in seeds["side_threads"]]
    assert len(side_ids) == len(set(side_ids))

    # No duplicate quest log entries
    quest_log = world.get_flag("quest_log")
    entry_ids = [e["id"] for e in quest_log["entries"]]
    assert len(entry_ids) == len(set(entry_ids))

    # No duplicate endings
    endings = world.get_flag("ending_seeds")
    ending_ids = [e["id"] for e in endings]
    assert len(ending_ids) == len(set(ending_ids))

    # No duplicate rumor hooks
    wu = world.get_entity("merchant_wu")
    hooks = wu["attributes"].get("rumor_hooks", [])
    assert len(hooks) == len(set(hooks))


# ----- Zhenjiang (Phase 24) -----

def test_seed_zhenjiang_creates_locations():
    world = World(":memory:")
    seed_zhenjiang(world)
    locs = {l["id"]: l for l in world.list_locations()}
    assert "zhenjiang_xijin" in locs
    assert "zhenjiang_fortress" in locs
    assert "zhenjiang_jinshan" in locs
    assert locs["zhenjiang_xijin"]["name"] == "西津渡口"
    assert locs["zhenjiang_fortress"]["name"] == "镇江卫所"
    assert locs["zhenjiang_jinshan"]["name"] == "金山寺"


def test_seed_zhenjiang_creates_npcs():
    world = World(":memory:")
    seed_zhenjiang(world)
    e = world.get_entity("fortress_commander_liu")
    assert e is not None
    assert e["name"] == "刘指挥使"
    assert e["location"] == "zhenjiang_fortress"

    e = world.get_entity("jinshan_monk")
    assert e is not None
    assert e["name"] == "了凡禅师"
    assert e["location"] == "zhenjiang_jinshan"

    e = world.get_entity("xijin_ferryman")
    assert e is not None
    assert e["name"] == "马渡子"
    assert e["location"] == "zhenjiang_xijin"


def test_seed_zhenjiang_npcs_have_attributes():
    world = World(":memory:")
    seed_zhenjiang(world)

    commander = world.get_entity("fortress_commander_liu")
    assert commander["attributes"]["hp"] == 80
    assert commander["attributes"]["attack"] == 12
    assert commander["attributes"]["defense"] == 18
    assert commander["attributes"]["money_wen"] == 300
    assert "personality" in commander["attributes"]
    assert commander["attributes"]["memories"] == []

    monk = world.get_entity("jinshan_monk")
    assert monk["attributes"]["hp"] == 40
    assert monk["attributes"]["attack"] == 1
    assert monk["attributes"]["defense"] == 12
    assert monk["attributes"]["money_wen"] == 150

    ferryman = world.get_entity("xijin_ferryman")
    assert ferryman["attributes"]["hp"] == 50
    assert ferryman["attributes"]["attack"] == 3
    assert ferryman["attributes"]["defense"] == 9
    assert ferryman["attributes"]["money_wen"] == 40


def test_seed_zhenjiang_commander_has_services():
    world = World(":memory:")
    seed_zhenjiang(world)
    commander = world.get_entity("fortress_commander_liu")
    services = commander["attributes"]["service_catalog"]
    assert services["military_escort"]["price_wen"] == 100
    assert services["check_cargo"]["price_wen"] == 30


def test_seed_zhenjiang_ferryman_has_services():
    world = World(":memory:")
    seed_zhenjiang(world)
    ferryman = world.get_entity("xijin_ferryman")
    services = ferryman["attributes"]["service_catalog"]
    assert services["cross_to_guazhou"]["price_wen"] == 8
    assert services["night_crossing"]["price_wen"] == 20


def test_seed_zhenjiang_wires_guazhou_exit():
    world = World(":memory:")
    seed_guazhou(world)
    seed_zhenjiang(world)
    guazhou_ferry = world.get_location("guazhou_ferry")
    assert "south_zhenjiang" in guazhou_ferry["exits"]
    assert guazhou_ferry["exits"]["south_zhenjiang"] == "zhenjiang_xijin"


def test_seed_zhenjiang_side_thread_created():
    world = World(":memory:")
    seed_yangzhou_districts(world)  # initialize story_seeds
    seed_zhenjiang(world)
    seeds = world.get_flag("story_seeds")
    assert seeds is not None
    side_ids = [s["id"] for s in seeds.get("side_threads", [])]
    assert "zhenjiang_seized_cargo" in side_ids


def test_seed_zhenjiang_flag_set():
    world = World(":memory:")
    seed_zhenjiang(world)
    assert world.get_flag("zhenjiang_seeded") is True


def test_seed_zhenjiang_no_duplicate_seeding():
    world = World(":memory:")
    seed_yangzhou_districts(world)  # initialize story_seeds
    seed_zhenjiang(world)
    seed_zhenjiang(world)  # seed again

    # No duplicate side threads
    seeds = world.get_flag("story_seeds")
    side_ids = [s["id"] for s in seeds.get("side_threads", [])]
    assert len(side_ids) == len(set(side_ids))

    # No duplicate rumor hooks
    commander = world.get_entity("fortress_commander_liu")
    hooks = commander["attributes"].get("rumor_hooks", [])
    assert len(hooks) == len(set(hooks))


def test_seed_zhenjiang_rumor_hooks_attached():
    world = World(":memory:")
    seed_zhenjiang(world)

    commander = world.get_entity("fortress_commander_liu")
    hooks = commander["attributes"].get("rumor_hooks", [])
    assert any("卫所扣货" in h or "扬州" in h for h in hooks)

    monk = world.get_entity("jinshan_monk")
    hooks = monk["attributes"].get("rumor_hooks", [])
    assert any("卫所扣货" in h or "扬州" in h for h in hooks)

    ferryman = world.get_entity("xijin_ferryman")
    hooks = ferryman["attributes"].get("rumor_hooks", [])
    assert any("卫所扣货" in h or "扬州" in h for h in hooks)


# ----- Huai'an (Phase 27) -----

def test_seed_huaian_creates_locations():
    world = World(":memory:")
    seed_huaian(world)
    locs = {l["id"]: l for l in world.list_locations()}
    assert "huaian_qingjiangpu" in locs
    assert "huaian_grain_yamen" in locs
    assert "huaian_xuanmiao" in locs
    assert locs["huaian_qingjiangpu"]["name"] == "清江浦"
    assert locs["huaian_grain_yamen"]["name"] == "漕运总督府"
    assert locs["huaian_xuanmiao"]["name"] == "玄妙观"


def test_seed_huaian_creates_npcs():
    world = World(":memory:")
    seed_huaian(world)
    e = world.get_entity("grain_governor_he")
    assert e is not None
    assert e["name"] == "何总督"
    assert e["location"] == "huaian_grain_yamen"

    e = world.get_entity("canal_broker_zhao")
    assert e is not None
    assert e["name"] == "赵牙人"
    assert e["location"] == "huaian_qingjiangpu"

    e = world.get_entity("daoist_qingxu")
    assert e is not None
    assert e["name"] == "清虚子"
    assert e["location"] == "huaian_xuanmiao"


def test_seed_huaian_npcs_have_attributes():
    world = World(":memory:")
    seed_huaian(world)

    governor = world.get_entity("grain_governor_he")
    assert governor["attributes"]["hp"] == 70
    assert governor["attributes"]["attack"] == 8
    assert governor["attributes"]["defense"] == 16
    assert governor["attributes"]["money_wen"] == 500
    assert "personality" in governor["attributes"]
    assert governor["attributes"]["memories"] == []

    broker = world.get_entity("canal_broker_zhao")
    assert broker["attributes"]["hp"] == 45
    assert broker["attributes"]["attack"] == 3
    assert broker["attributes"]["defense"] == 9
    assert broker["attributes"]["money_wen"] == 200

    daoist = world.get_entity("daoist_qingxu")
    assert daoist["attributes"]["hp"] == 35
    assert daoist["attributes"]["attack"] == 2
    assert daoist["attributes"]["defense"] == 10
    assert daoist["attributes"]["money_wen"] == 100


def test_seed_huaian_governor_has_services():
    world = World(":memory:")
    seed_huaian(world)
    governor = world.get_entity("grain_governor_he")
    services = governor["attributes"]["service_catalog"]
    assert services["cargo_inquiry"]["price_wen"] == 50
    assert services["official_letter"]["price_wen"] == 200


def test_seed_huaian_broker_has_services():
    world = World(":memory:")
    seed_huaian(world)
    broker = world.get_entity("canal_broker_zhao")
    services = broker["attributes"]["service_catalog"]
    assert services["find_cargo_ship"]["price_wen"] == 40
    assert services["market_intel"]["price_wen"] == 15


def test_seed_huaian_broker_has_price_list():
    world = World(":memory:")
    seed_huaian(world)
    broker = world.get_entity("canal_broker_zhao")
    prices = broker["attributes"]["price_list"]
    assert prices["market_info"] == 15
    assert prices["ship_arrangement"] == 40


def test_seed_huaian_wires_river_dock_exit():
    world = World(":memory:")
    seed_yangzhou_districts(world)
    seed_huaian(world)
    river_dock = world.get_location("river_dock")
    assert "north_huaian" in river_dock["exits"]
    assert river_dock["exits"]["north_huaian"] == "huaian_qingjiangpu"


def test_seed_huaian_locations_connected():
    world = World(":memory:")
    seed_huaian(world)
    locs = {l["id"]: l for l in world.list_locations()}
    assert locs["huaian_qingjiangpu"]["exits"]["north"] == "huaian_grain_yamen"
    assert locs["huaian_qingjiangpu"]["exits"]["east"] == "huaian_xuanmiao"
    assert locs["huaian_grain_yamen"]["exits"]["south"] == "huaian_qingjiangpu"
    assert locs["huaian_xuanmiao"]["exits"]["west"] == "huaian_qingjiangpu"


def test_seed_huaian_evolution_registry():
    world = World(":memory:")
    seed_huaian(world)
    registry = world.get_flag("evolution_registry") or []
    reg_ids = {e["entity_id"] for e in registry}
    assert "grain_governor_he" in reg_ids
    assert "canal_broker_zhao" in reg_ids
    assert "daoist_qingxu" in reg_ids


def test_seed_huaian_side_thread_created():
    world = World(":memory:")
    seed_yangzhou_districts(world)  # initialize story_seeds
    seed_huaian(world)
    seeds = world.get_flag("story_seeds")
    assert seeds is not None
    side_ids = [s["id"] for s in seeds.get("side_threads", [])]
    assert "huaian_grain_corruption" in side_ids


def test_seed_huaian_location_story_threads():
    world = World(":memory:")
    seed_yangzhou_districts(world)
    seed_huaian(world)
    grain_yamen = world.get_location("huaian_grain_yamen")
    thread_ids = [t["id"] for t in grain_yamen.get("story_threads", [])]
    assert "huaian_grain_corruption" in thread_ids


def test_seed_huaian_rumor_hooks_attached():
    world = World(":memory:")
    seed_huaian(world)

    governor = world.get_entity("grain_governor_he")
    hooks = governor["attributes"].get("rumor_hooks", [])
    assert any("漕运暗流" in h or "扬州" in h for h in hooks)

    broker = world.get_entity("canal_broker_zhao")
    hooks = broker["attributes"].get("rumor_hooks", [])
    assert any("漕运暗流" in h or "扬州" in h for h in hooks)

    daoist = world.get_entity("daoist_qingxu")
    hooks = daoist["attributes"].get("rumor_hooks", [])
    assert any("漕运暗流" in h or "扬州" in h for h in hooks)


def test_seed_huaian_flag_set():
    world = World(":memory:")
    seed_huaian(world)
    assert world.get_flag("huaian_seeded") is True


def test_seed_huaian_no_duplicate_seeding():
    world = World(":memory:")
    seed_yangzhou_districts(world)  # initialize story_seeds
    seed_huaian(world)
    seed_huaian(world)  # seed again

    # No duplicate side threads
    seeds = world.get_flag("story_seeds")
    side_ids = [s["id"] for s in seeds.get("side_threads", [])]
    assert len(side_ids) == len(set(side_ids))

    # No duplicate rumor hooks
    governor = world.get_entity("grain_governor_he")
    hooks = governor["attributes"].get("rumor_hooks", [])
    assert len(hooks) == len(set(hooks))


def test_seed_huaian_npcs_have_schedules():
    world = World(":memory:")
    seed_huaian(world)
    for npc_id in ("grain_governor_he", "canal_broker_zhao", "daoist_qingxu"):
        e = world.get_entity(npc_id)
        assert "schedule" in e["attributes"], f"{npc_id} missing schedule"
        assert len(e["attributes"]["schedule"]) >= 3, f"{npc_id} schedule too short"


def test_seed_huaian_npcs_have_inventory():
    world = World(":memory:")
    seed_huaian(world)
    for npc_id in ("grain_governor_he", "canal_broker_zhao", "daoist_qingxu"):
        e = world.get_entity(npc_id)
        assert len(e.get("inventory", [])) >= 1, f"{npc_id} missing inventory"


def test_seed_huaian_npcs_have_observable_details():
    world = World(":memory:")
    seed_huaian(world)
    for npc_id in ("grain_governor_he", "canal_broker_zhao", "daoist_qingxu"):
        e = world.get_entity(npc_id)
        assert len(e["attributes"].get("observable_details", [])) >= 1, (
            f"{npc_id} missing observable_details"
        )


def test_seed_huaian_npc_tags():
    world = World(":memory:")
    seed_huaian(world)
    governor = world.get_entity("grain_governor_he")
    assert "official" in governor["tags"]
    broker = world.get_entity("canal_broker_zhao")
    assert "commoner" in broker["tags"]
    daoist = world.get_entity("daoist_qingxu")
    assert "religious" in daoist["tags"]


# ----- Xuzhou (Phase 29) -----

def test_seed_xuzhou_creates_locations():
    world = World(":memory:")
    seed_xuzhou(world)
    locs = {l["id"]: l for l in world.list_locations()}
    assert "xuzhou_city_gate" in locs
    assert "xuzhou_yamen" in locs
    assert "xuzhou_inn" in locs
    assert locs["xuzhou_city_gate"]["name"] == "徐州城门"
    assert locs["xuzhou_yamen"]["name"] == "徐州府衙"
    assert locs["xuzhou_inn"]["name"] == "徐州驿站"


def test_seed_xuzhou_creates_npcs():
    world = World(":memory:")
    seed_xuzhou(world)
    e = world.get_entity("xuzhou_magistrate")
    assert e is not None
    assert e["name"] == "钱知府"
    assert e["location"] == "xuzhou_yamen"

    e = world.get_entity("xuzhou_innkeeper")
    assert e is not None
    assert e["name"] == "周老五"
    assert e["location"] == "xuzhou_inn"

    e = world.get_entity("xuzhou_iron_merchant")
    assert e is not None
    assert e["name"] == "孙铁商"
    assert e["location"] == "xuzhou_city_gate"


def test_seed_xuzhou_npcs_have_attributes():
    world = World(":memory:")
    seed_xuzhou(world)

    magistrate = world.get_entity("xuzhou_magistrate")
    assert magistrate["attributes"]["hp"] == 60
    assert magistrate["attributes"]["attack"] == 6
    assert magistrate["attributes"]["defense"] == 14
    assert magistrate["attributes"]["money_wen"] == 400
    assert "personality" in magistrate["attributes"]
    assert magistrate["attributes"]["memories"] == []

    innkeeper = world.get_entity("xuzhou_innkeeper")
    assert innkeeper["attributes"]["hp"] == 40
    assert innkeeper["attributes"]["attack"] == 2
    assert innkeeper["attributes"]["defense"] == 9
    assert innkeeper["attributes"]["money_wen"] == 250

    merchant = world.get_entity("xuzhou_iron_merchant")
    assert merchant["attributes"]["hp"] == 55
    assert merchant["attributes"]["attack"] == 4
    assert merchant["attributes"]["defense"] == 12
    assert merchant["attributes"]["money_wen"] == 600


def test_seed_xuzhou_magistrate_has_services():
    world = World(":memory:")
    seed_xuzhou(world)
    magistrate = world.get_entity("xuzhou_magistrate")
    services = magistrate["attributes"]["service_catalog"]
    assert services["file_complaint"]["price_wen"] == 30
    assert services["check_records"]["price_wen"] == 50


def test_seed_xuzhou_innkeeper_has_services():
    world = World(":memory:")
    seed_xuzhou(world)
    innkeeper = world.get_entity("xuzhou_innkeeper")
    services = innkeeper["attributes"]["service_catalog"]
    assert services["room_night"]["price_wen"] == 8
    assert services["private_room"]["price_wen"] == 15
    assert services["meal"]["price_wen"] == 5
    assert services["news"]["price_wen"] == 10


def test_seed_xuzhou_innkeeper_has_price_list():
    world = World(":memory:")
    seed_xuzhou(world)
    innkeeper = world.get_entity("xuzhou_innkeeper")
    prices = innkeeper["attributes"]["price_list"]
    assert prices["common_room"] == 8
    assert prices["private_room"] == 15
    assert prices["meal"] == 5


def test_seed_xuzhou_iron_merchant_has_services():
    world = World(":memory:")
    seed_xuzhou(world)
    merchant = world.get_entity("xuzhou_iron_merchant")
    services = merchant["attributes"]["service_catalog"]
    assert services["buy_iron"]["price_wen"] == 30
    assert services["custom_order"]["price_wen"] == 100


def test_seed_xuzhou_wires_huaian_exit():
    world = World(":memory:")
    seed_huaian(world)
    seed_xuzhou(world)
    huaian_qingjiangpu = world.get_location("huaian_qingjiangpu")
    assert "west_xuzhou" in huaian_qingjiangpu["exits"]
    assert huaian_qingjiangpu["exits"]["west_xuzhou"] == "xuzhou_city_gate"


def test_seed_xuzhou_locations_connected():
    world = World(":memory:")
    seed_xuzhou(world)
    locs = {l["id"]: l for l in world.list_locations()}
    assert locs["xuzhou_city_gate"]["exits"]["north"] == "xuzhou_yamen"
    assert locs["xuzhou_city_gate"]["exits"]["east"] == "xuzhou_inn"
    assert locs["xuzhou_yamen"]["exits"]["south"] == "xuzhou_city_gate"
    assert locs["xuzhou_inn"]["exits"]["west"] == "xuzhou_city_gate"


def test_seed_xuzhou_evolution_registry():
    world = World(":memory:")
    seed_xuzhou(world)
    registry = world.get_flag("evolution_registry") or []
    reg_ids = {e["entity_id"] for e in registry}
    assert "xuzhou_magistrate" in reg_ids
    assert "xuzhou_innkeeper" in reg_ids
    assert "xuzhou_iron_merchant" in reg_ids


def test_seed_xuzhou_side_thread_created():
    world = World(":memory:")
    seed_yangzhou_districts(world)  # initialize story_seeds
    seed_xuzhou(world)
    seeds = world.get_flag("story_seeds")
    assert seeds is not None
    side_ids = [s["id"] for s in seeds.get("side_threads", [])]
    assert "xuzhou_iron_route" in side_ids


def test_seed_xuzhou_location_story_threads():
    world = World(":memory:")
    seed_yangzhou_districts(world)
    seed_xuzhou(world)
    gate = world.get_location("xuzhou_city_gate")
    thread_ids = [t["id"] for t in gate.get("story_threads", [])]
    assert "xuzhou_iron_route" in thread_ids


def test_seed_xuzhou_rumor_hooks_attached():
    world = World(":memory:")
    seed_xuzhou(world)

    magistrate = world.get_entity("xuzhou_magistrate")
    hooks = magistrate["attributes"].get("rumor_hooks", [])
    assert any("铁器暗运" in h or "扬州" in h for h in hooks)

    innkeeper = world.get_entity("xuzhou_innkeeper")
    hooks = innkeeper["attributes"].get("rumor_hooks", [])
    assert any("铁器暗运" in h or "扬州" in h for h in hooks)

    merchant = world.get_entity("xuzhou_iron_merchant")
    hooks = merchant["attributes"].get("rumor_hooks", [])
    assert any("铁器暗运" in h or "扬州" in h for h in hooks)


def test_seed_xuzhou_flag_set():
    world = World(":memory:")
    seed_xuzhou(world)
    assert world.get_flag("xuzhou_seeded") is True


def test_seed_xuzhou_no_duplicate_seeding():
    world = World(":memory:")
    seed_yangzhou_districts(world)  # initialize story_seeds
    seed_xuzhou(world)
    seed_xuzhou(world)  # seed again

    # No duplicate side threads
    seeds = world.get_flag("story_seeds")
    side_ids = [s["id"] for s in seeds.get("side_threads", [])]
    assert len(side_ids) == len(set(side_ids))

    # No duplicate rumor hooks
    magistrate = world.get_entity("xuzhou_magistrate")
    hooks = magistrate["attributes"].get("rumor_hooks", [])
    assert len(hooks) == len(set(hooks))


def test_seed_xuzhou_npcs_have_schedules():
    world = World(":memory:")
    seed_xuzhou(world)
    for npc_id in ("xuzhou_magistrate", "xuzhou_innkeeper", "xuzhou_iron_merchant"):
        e = world.get_entity(npc_id)
        assert "schedule" in e["attributes"], f"{npc_id} missing schedule"
        assert len(e["attributes"]["schedule"]) >= 3, f"{npc_id} schedule too short"


def test_seed_xuzhou_npcs_have_inventory():
    world = World(":memory:")
    seed_xuzhou(world)
    for npc_id in ("xuzhou_magistrate", "xuzhou_innkeeper", "xuzhou_iron_merchant"):
        e = world.get_entity(npc_id)
        assert len(e.get("inventory", [])) >= 1, f"{npc_id} missing inventory"


def test_seed_xuzhou_npcs_have_observable_details():
    world = World(":memory:")
    seed_xuzhou(world)
    for npc_id in ("xuzhou_magistrate", "xuzhou_innkeeper", "xuzhou_iron_merchant"):
        e = world.get_entity(npc_id)
        assert len(e["attributes"].get("observable_details", [])) >= 1, (
            f"{npc_id} missing observable_details"
        )


def test_seed_xuzhou_npc_tags():
    world = World(":memory:")
    seed_xuzhou(world)
    magistrate = world.get_entity("xuzhou_magistrate")
    assert "official" in magistrate["tags"]
    innkeeper = world.get_entity("xuzhou_innkeeper")
    assert "commoner" in innkeeper["tags"]
    merchant = world.get_entity("xuzhou_iron_merchant")
    assert "merchant" in merchant["tags"]


def test_seed_xuzhou_magistrate_has_dialogue_lines():
    world = World(":memory:")
    seed_xuzhou(world)
    magistrate = world.get_entity("xuzhou_magistrate")
    dialogue = magistrate["attributes"]["dialogue_lines"]
    assert len(dialogue["greetings"]) >= 2
    assert len(dialogue["topics"]) >= 2
    assert len(dialogue["farewells"]) >= 1
    assert len(dialogue["special"]) >= 1
    # Check topic structure
    for topic in dialogue["topics"]:
        assert "id" in topic
        assert "label" in topic
        assert "unlock_attitude" in topic
        assert "lines" in topic
        assert len(topic["lines"]) >= 1


def test_seed_xuzhou_innkeeper_has_dialogue_lines():
    world = World(":memory:")
    seed_xuzhou(world)
    innkeeper = world.get_entity("xuzhou_innkeeper")
    dialogue = innkeeper["attributes"]["dialogue_lines"]
    assert len(dialogue["greetings"]) >= 2
    assert len(dialogue["topics"]) >= 2
    assert len(dialogue["farewells"]) >= 1
    assert len(dialogue["special"]) >= 1
    # Check topic structure
    for topic in dialogue["topics"]:
        assert "id" in topic
        assert "label" in topic
        assert "unlock_attitude" in topic
        assert "lines" in topic
        assert len(topic["lines"]) >= 1


def test_seed_xuzhou_iron_merchant_has_dialogue_lines():
    world = World(":memory:")
    seed_xuzhou(world)
    merchant = world.get_entity("xuzhou_iron_merchant")
    dialogue = merchant["attributes"]["dialogue_lines"]
    assert len(dialogue["greetings"]) >= 2
    assert len(dialogue["topics"]) >= 2
    assert len(dialogue["farewells"]) >= 1
    assert len(dialogue["special"]) >= 1
    # Check topic structure
    for topic in dialogue["topics"]:
        assert "id" in topic
        assert "label" in topic
        assert "unlock_attitude" in topic
        assert "lines" in topic
        assert len(topic["lines"]) >= 1


# ----- Suzhou dialogue_lines (Phase 32) -----

def _assert_dialogue_structure(dialogue):
    """Helper: validate dialogue_lines structure."""
    assert len(dialogue["greetings"]) >= 2
    assert len(dialogue["topics"]) >= 2
    assert len(dialogue["farewells"]) >= 1
    assert len(dialogue["special"]) >= 1
    for topic in dialogue["topics"]:
        assert "id" in topic
        assert "label" in topic
        assert "unlock_attitude" in topic
        assert "lines" in topic
        assert len(topic["lines"]) >= 1


def test_seed_suzhou_silk_merchant_has_dialogue_lines():
    world = World(":memory:")
    seed_suzhou(world)
    npc = world.get_entity("silk_merchant_qian")
    _assert_dialogue_structure(npc["attributes"]["dialogue_lines"])


def test_seed_suzhou_garden_keeper_has_dialogue_lines():
    world = World(":memory:")
    seed_suzhou(world)
    npc = world.get_entity("garden_keeper_shen")
    _assert_dialogue_structure(npc["attributes"]["dialogue_lines"])


def test_seed_suzhou_boatman_has_dialogue_lines():
    world = World(":memory:")
    seed_suzhou(world)
    npc = world.get_entity("canal_boatman_feng")
    _assert_dialogue_structure(npc["attributes"]["dialogue_lines"])


# ----- Hangzhou dialogue_lines (Phase 32) -----

def test_seed_hangzhou_tea_merchant_has_dialogue_lines():
    world = World(":memory:")
    seed_hangzhou(world)
    npc = world.get_entity("tea_merchant_fang")
    _assert_dialogue_structure(npc["attributes"]["dialogue_lines"])


def test_seed_hangzhou_abbot_has_dialogue_lines():
    world = World(":memory:")
    seed_hangzhou(world)
    npc = world.get_entity("abbot_mingkong")
    _assert_dialogue_structure(npc["attributes"]["dialogue_lines"])


def test_seed_hangzhou_captain_has_dialogue_lines():
    world = World(":memory:")
    seed_hangzhou(world)
    npc = world.get_entity("canal_captain_sun")
    _assert_dialogue_structure(npc["attributes"]["dialogue_lines"])


# ----- Huai'an dialogue_lines (Phase 32) -----

def test_seed_huaian_governor_has_dialogue_lines():
    world = World(":memory:")
    seed_huaian(world)
    npc = world.get_entity("grain_governor_he")
    _assert_dialogue_structure(npc["attributes"]["dialogue_lines"])


def test_seed_huaian_broker_has_dialogue_lines():
    world = World(":memory:")
    seed_huaian(world)
    npc = world.get_entity("canal_broker_zhao")
    _assert_dialogue_structure(npc["attributes"]["dialogue_lines"])


def test_seed_huaian_daoist_has_dialogue_lines():
    world = World(":memory:")
    seed_huaian(world)
    npc = world.get_entity("daoist_qingxu")
    _assert_dialogue_structure(npc["attributes"]["dialogue_lines"])


# ----- Zhenjiang dialogue_lines (Phase 32) -----

def test_seed_zhenjiang_commander_has_dialogue_lines():
    world = World(":memory:")
    seed_zhenjiang(world)
    npc = world.get_entity("fortress_commander_liu")
    _assert_dialogue_structure(npc["attributes"]["dialogue_lines"])


def test_seed_zhenjiang_monk_has_dialogue_lines():
    world = World(":memory:")
    seed_zhenjiang(world)
    npc = world.get_entity("jinshan_monk")
    _assert_dialogue_structure(npc["attributes"]["dialogue_lines"])


def test_seed_zhenjiang_ferryman_has_dialogue_lines():
    world = World(":memory:")
    seed_zhenjiang(world)
    npc = world.get_entity("xijin_ferryman")
    _assert_dialogue_structure(npc["attributes"]["dialogue_lines"])
