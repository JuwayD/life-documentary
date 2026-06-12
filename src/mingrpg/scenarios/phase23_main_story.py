"""Phase 23: Main Story Progression — Cross-Region Investigation.

Ties together the scattered regional threads (Guazhou night crossing,
Nanjing exam scandal & salt tax, Suzhou silk conspiracy, Hangzhou tea
smuggling) into a unified investigation arc centered on merchant_wu.

Adds:
- A cross-region investigation thread with milestones
- A new pressure clock tracking imperial court awareness
- Expanded ending seeds for cross-region outcomes
- Quest log seeding for investigation tracking
"""
from mingrpg.core.world import World


# ---- Cross-region investigation thread ----

CROSS_REGION_THREAD = {
    "id": "jiangnan_network",
    "title": "江南暗网",
    "hook": (
        "扬州吴员外的生意远不止码头货栈——瓜洲的夜渡、南京的科场、"
        "苏州的丝税、杭州的茶运、淮安的漕运、徐州的铁器,处处有他的影子。若能将各地线索串联,"
        "或可揭开一张横跨江南的暗中交易网络。"
    ),
    "anchors": [
        # Yangzhou core
        {"entity": "merchant_wu"},
        {"entity": "dock_boss_qian"},
        {"location": "warehouse"},
        # Guazhou
        {"entity": "ferryman_chen"},
        {"entity": "guazhou_clerk"},
        {"location": "guazhou_ferry"},
        # Nanjing
        {"entity": "scholar_zhou"},
        {"entity": "qinhuai_madam"},
        {"entity": "gate_officer_sun"},
        {"location": "nanjing_confucius"},
        {"location": "nanjing_qinhuai"},
        # Suzhou
        {"entity": "silk_merchant_qian"},
        {"entity": "canal_boatman_feng"},
        {"location": "suzhou_silk_market"},
        # Hangzhou
        {"entity": "tea_merchant_fang"},
        {"entity": "canal_captain_sun"},
        {"location": "hangzhou_west_lake"},
        {"location": "hangzhou_canal_dock"},
        # Huai'an
        {"entity": "grain_governor_he"},
        {"entity": "canal_broker_zhao"},
        {"location": "huaian_grain_yamen"},
        {"location": "huaian_qingjiangpu"},
        # Xuzhou
        {"entity": "xuzhou_magistrate"},
        {"entity": "xuzhou_innkeeper"},
        {"entity": "xuzhou_iron_merchant"},
        {"location": "xuzhou_city_gate"},
        {"location": "xuzhou_yamen"},
        {"location": "xuzhou_inn"},
    ],
    "stakes": (
        "多线合一可迫使吴员外现身,但也会惊动他在府衙和商帮中的保护伞。"
        "轻举妄动可能让所有线索同时断裂。"
    ),
}


# ---- Investigation milestones (seeded into quest_log) ----

INVESTIGATION_MILESTONES = [
    {
        "id": "yz_petition_filed",
        "title": "状纸递出",
        "description": "在扬州府衙递出状纸,控告赵三欺压寒士。",
        "region": "yangzhou",
        "status": "active",
    },
    {
        "id": "gz_night_cargo",
        "title": "夜渡暗货",
        "description": "在瓜洲渡查到半夜过江的可疑货物。",
        "region": "guazhou",
        "status": "locked",
    },
    {
        "id": "nj_exam_clue",
        "title": "科场旧事",
        "description": "在南京贡院发现科场弊案与扬州商帮的关联。",
        "region": "nanjing",
        "status": "locked",
    },
    {
        "id": "nj_salt_trail",
        "title": "盐税暗线",
        "description": "在南京发现盐税走私与吴员外的货物有关。",
        "region": "nanjing",
        "status": "locked",
    },
    {
        "id": "sz_silk_evidence",
        "title": "丝税账簿",
        "description": "在苏州丝市找到吴员外商业网络的账目证据。",
        "region": "suzhou",
        "status": "locked",
    },
    {
        "id": "hz_tea_cargo",
        "title": "龙井暗运",
        "description": "在杭州码头发现茶叶走私的完整路线。",
        "region": "hangzhou",
        "status": "locked",
    },
    {
        "id": "confrontation",
        "title": "对质吴员外",
        "description": "掌握足够证据后,与吴员外当面对质。",
        "region": "yangzhou",
        "status": "locked",
    },
    {
        "id": "ha_grain_trail",
        "title": "漕运暗流",
        "description": "在淮安漕运总督府查到吴员外借漕运夹带私货的线索。",
        "region": "huaian",
        "status": "locked",
    },
    {
        "id": "xz_iron_route",
        "title": "铁器暗运",
        "description": "在徐州发现吴员外的铁器走私路线,铁器从扬州经徐州北运。",
        "region": "xuzhou",
        "status": "locked",
    },
]


# ---- New pressure clock ----

COURT_WIND_CLOCK = {
    "id": "court_wind",
    "name": "朝廷风声",
    "value": 0,
    "danger_at": 5,
}


# ---- Expanded ending seeds ----

CROSS_REGION_ENDINGS = [
    {
        "id": "network_dismantled",
        "title": "暗网瓦解",
        "trigger_hint": (
            "多地证据齐全、关键证人愿意出面、且朝廷风声尚未走漏时,"
            "可一举揭发吴员外的跨地域走私网络。"
        ),
        "outcome_hint": (
            "吴员外被拿问,漕帮势力大减,但玩家也将成为商帮的眼中钉。"
        ),
    },
    {
        "id": "partial_exposure",
        "title": "半壁揭开",
        "trigger_hint": (
            "掌握了部分地区的证据,但缺少关键一环;或朝廷风声已起,"
            "时间不足以查清全部线索。"
        ),
        "outcome_hint": (
            "部分罪行被追究,吴员外断尾求生,暗网受损但未瓦解。"
        ),
    },
    {
        "id": "network_retaliation",
        "title": "暗网反噬",
        "trigger_hint": (
            "调查过程中暴露行踪,吴员外先下手为强;"
            "或朝廷风声走漏,官府介入但方向被引导到玩家身上。"
        ),
        "outcome_hint": (
            "玩家反被诬陷,证据被销毁,需远走他乡或寻求更高层庇护。"
        ),
    },
]


def seed_phase23_main_story(world: World) -> None:
    """Seed Phase 23: cross-region investigation thread, quest log,
    pressure clock, and expanded endings."""

    # ---- Attach cross-region thread to story seeds ----
    seeds = world.get_flag("story_seeds")
    if seeds:
        existing_thread_ids = {t["id"] for t in seeds.get("side_threads", [])}
        if CROSS_REGION_THREAD["id"] not in existing_thread_ids:
            seeds["side_threads"].append(CROSS_REGION_THREAD)
        world.set_flag("story_seeds", seeds)

    # ---- Attach rumor hooks from cross-region thread ----
    for anchor in CROSS_REGION_THREAD["anchors"]:
        entity_id = anchor.get("entity")
        if entity_id:
            _append_unique_hook(world, entity_id, CROSS_REGION_THREAD["hook"])
        location_id = anchor.get("location")
        if location_id:
            _append_location_thread(world, location_id, CROSS_REGION_THREAD)

    # ---- Seed quest log with investigation milestones ----
    quest_log = world.get_flag("quest_log") or {"entries": []}
    existing_ids = {e["id"] for e in quest_log.get("entries", [])}
    for milestone in INVESTIGATION_MILESTONES:
        if milestone["id"] not in existing_ids:
            quest_log["entries"].append(milestone)
    world.set_flag("quest_log", quest_log)

    # ---- Add court wind pressure clock ----
    clocks = world.get_flag("pressure_clocks") or {}
    if "court_wind" not in clocks:
        clocks["court_wind"] = {
            "value": COURT_WIND_CLOCK["value"],
            "danger_at": COURT_WIND_CLOCK["danger_at"],
            "history": [0],
        }
        world.set_flag("pressure_clocks", clocks)

    # ---- Add expanded ending seeds ----
    existing_endings = world.get_flag("ending_seeds") or []
    existing_ending_ids = {e["id"] for e in existing_endings}
    for ending in CROSS_REGION_ENDINGS:
        if ending["id"] not in existing_ending_ids:
            existing_endings.append(ending)
    world.set_flag("ending_seeds", existing_endings)

    # ---- Update merchant_wu with investigation-relevant attributes ----
    wu = world.get_entity("merchant_wu")
    if wu:
        wu.setdefault("attributes", {})["is_investigation_target"] = True
        wu.setdefault("attributes", {})["network_regions"] = [
            "yangzhou", "guazhou", "nanjing", "suzhou", "hangzhou", "huaian", "xuzhou",
        ]
        world.save_entity(wu)

    world.set_flag("phase23_main_story", True)


def _append_unique_hook(world: World, entity_id: str, hook: str) -> None:
    entity = world.get_entity(entity_id)
    if entity is None:
        return
    hooks = entity.setdefault("attributes", {}).setdefault("rumor_hooks", [])
    if hook not in hooks:
        hooks.append(hook)
    world.save_entity(entity)


def _append_location_thread(world: World, location_id: str, thread: dict) -> None:
    location = world.get_location(location_id)
    if location is None:
        return
    threads = location.setdefault("story_threads", [])
    if not any(t.get("id") == thread["id"] for t in threads):
        threads.append({
            "id": thread["id"],
            "title": thread["title"],
            "hook": thread["hook"],
            "stakes": thread["stakes"],
        })
    world.save_location(location)
