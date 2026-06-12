"""Phase 20: New Region — Nanjing (南京).

The southern capital of the Ming Dynasty, a grand city with the imperial
examination hall, bustling markets, and ancient temples. Adds 4 locations,
4 NPCs, and 2 side threads linking back to Yangzhou storylines.
"""
from mingrpg.core.world import World


# ---- Locations ----

NANJING_LOCATIONS = [
    {
        "id": "nanjing_confucius",
        "name": "夫子庙贡院",
        "type": "outdoor",
        "size": [20, 16],
        "exits": {"south": "nanjing_qinhuai", "east": "nanjing_jiming"},
        "tags": ["public", "academic", "sacred"],
        "description": "江南贡院巍峨壮观,号舍连绵数千间。每逢科考之年,天下举子云集于此。院前广场立着孔子像,香火不断。",
    },
    {
        "id": "nanjing_qinhuai",
        "name": "秦淮河畔",
        "type": "outdoor",
        "size": [24, 12],
        "exits": {"north": "nanjing_confucius", "west": "nanjing_jubaomen"},
        "tags": ["public", "entertainment", "commercial"],
        "description": "桨声灯影里的秦淮河,两岸画舫林立,丝竹之声不绝。河畔酒楼茶肆鳞次栉比,是金陵最繁华之处。",
    },
    {
        "id": "nanjing_jubaomen",
        "name": "聚宝门大街",
        "type": "outdoor",
        "size": [22, 14],
        "exits": {"east": "nanjing_qinhuai", "north_gate": "guazhou_ferry"},
        "tags": ["public", "commercial", "gate"],
        "description": "聚宝门是南京南城最宏伟的城门,门内大街商铺林立,南北货物在此交汇。城门守卫盘查过往行人,查验路引。",
    },
    {
        "id": "nanjing_jiming",
        "name": "鸡鸣寺",
        "type": "indoor_religious",
        "size": [16, 14],
        "exits": {"west": "nanjing_confucius"},
        "tags": ["sacred", "quiet", "academic"],
        "description": "鸡鸣寺依山而建,俯瞰玄武湖。寺内藏经阁珍本无数,常有举子来此借阅。住持慧远禅师博学多才,与官场中人颇有往来。",
    },
]

# ---- NPCs ----

NANJING_ENTITIES = [
    {
        "id": "scholar_zhou",
        "name": "周举子",
        "type": "npc",
        "location": "nanjing_confucius",
        "pos": [10, 8],
        "attributes": {
            "hp": 35, "max_hp": 35,
            "rank": "举人",
            "occupation": "赴考举子",
            "personality": "浙江来的举子,才华横溢但性格孤傲,对科场弊案深恶痛绝",
            "attack": 1, "defense": 7,
            "money_wen": 120,
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "这位仁兄,也是来赴考的?", "min_attitude": -100, "max_attitude": 100},
                    {"text": "你来了。今日温书可有心得?", "min_attitude": 15, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "exam_scandal", "label": "科场之事", "unlock_attitude": 0, "lines": [
                        {"text": "今科主考官与某富商有旧,贡院里有人夹带小抄。你信不信?", "min_attitude": 0, "max_attitude": 100},
                        {"text": "扬州来的考生说当地有人卖考题。我虽无实据,但空穴来风未必无因。", "min_attitude": 15, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "保重。科场如战场,小心为上。", "min_attitude": -100, "max_attitude": 100},
                ],
            },
            "rumor_hooks": [
                "听说今科主考官与某富商有旧",
                "贡院号舍有人夹带小抄",
                "扬州来的考生说当地有人卖考题",
            ],
            "schedule": {
                "卯时": {"location": "nanjing_confucius", "pos": [10, 8], "activity": "在贡院前晨读"},
                "巳时": {"location": "nanjing_jiming", "pos": [8, 6], "activity": "去寺里借阅典籍"},
                "午时": {"location": "nanjing_qinhuai", "pos": [12, 6], "activity": "在河畔酒楼吃饭"},
                "酉时": {"location": "nanjing_confucius", "pos": [10, 8], "activity": "回住处温书"},
            },
            "observable_details": [
                "手指因长年握笔而微微弯曲,指节处有墨痕",
                "袖中藏着几页写满批注的经义",
            ],
        },
        "status_effects": [],
        "inventory": [
            {"id": "exam_notes", "name": "经义笔记", "qty": 3},
            {"id": "travel_permit", "name": "浙江路引", "qty": 1},
        ],
        "tags": ["scholar", "informant", "examinee"],
    },
    {
        "id": "qinhuai_madam",
        "name": "秦淮鸨母",
        "type": "npc",
        "location": "nanjing_qinhuai",
        "pos": [16, 6],
        "attributes": {
            "hp": 55, "max_hp": 55,
            "rank": "平民",
            "occupation": "画舫管事",
            "personality": "秦淮河上最大的画舫'月华舫'管事,八面玲珑,消息灵通,暗中为达官显贵牵线搭桥",
            "attack": 2, "defense": 10,
            "money_wen": 500,
            "price_list": {"rumor": 20, "introduction": 50},
            "service_catalog": {
                "listen_rumor": {"name": "打听消息", "price_wen": 20},
                "meet_guest": {"name": "引见贵客", "price_wen": 50},
            },
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "公子面生,第一次来月华舫?", "min_attitude": -100, "max_attitude": 100},
                    {"text": "哟,老主顾来了!里面请,今日有新曲子。", "min_attitude": 20, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "qinhuai_rumors", "label": "秦淮消息", "unlock_attitude": 0, "lines": [
                        {"text": "秦淮河上什么消息没有?就看你出不出得起价。", "min_attitude": 0, "max_attitude": 100},
                        {"text": "扬州盐商常来月华舫宴客。有个出手阔绰的,专程从扬州来。", "min_attitude": 15, "max_attitude": 100},
                        {"text": "听说朝廷要查江南盐税。你要是跟这事沾边,趁早脱身。", "min_attitude": 25, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "慢走。下次来,我给你留最好的雅间。", "min_attitude": -100, "max_attitude": 100},
                ],
            },
            "rumor_hooks": [
                "扬州盐商常来月华舫宴客",
                "有个出手阔绰的客人专程从扬州来",
                "听说朝廷要查江南盐税",
            ],
            "schedule": {
                "巳时": {"location": "nanjing_qinhuai", "pos": [16, 6], "activity": "在画舫梳妆安排事务"},
                "午时": {"location": "nanjing_qinhuai", "pos": [14, 8], "activity": "在河畔茶楼会客"},
                "酉时": {"location": "nanjing_qinhuai", "pos": [18, 6], "activity": "画舫开张迎客"},
                "子时": {"location": "nanjing_qinhuai", "pos": [16, 6], "activity": "打烊清点账目"},
            },
            "observable_details": [
                "腕上戴着成色极好的翡翠镯子",
                "对每个客人都能叫出名字和喜好",
            ],
        },
        "status_effects": [],
        "inventory": [
            {"id": "guest_book", "name": "宾客簿", "qty": 1},
            {"id": "jade_bracelet", "name": "翡翠镯子", "qty": 1},
        ],
        "tags": ["entertainer", "informant", "broker"],
    },
    {
        "id": "gate_officer_sun",
        "name": "孙守备",
        "type": "npc",
        "location": "nanjing_jubaomen",
        "pos": [11, 7],
        "attributes": {
            "hp": 70, "max_hp": 70,
            "rank": "守备",
            "occupation": "聚宝门守备",
            "personality": "聚宝门守备官,恪尽职守但贪财,对过往商旅雁过拔毛",
            "attack": 8, "defense": 14,
            "money_wen": 150,
            "price_list": {"pass_tax": 10},
            "service_catalog": {
                "quick_pass": {"name": "快速通关", "price_wen": 30},
                "check_records": {"name": "查过关记录", "price_wen": 15},
            },
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "站住!路引拿出来看看。", "min_attitude": -100, "max_attitude": 0},
                    {"text": "哦,是你。进去吧。", "min_attitude": 10, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "gate_business", "label": "城门之事", "unlock_attitude": 0, "lines": [
                        {"text": "最近有批货没交税就过去了。上头要查过境商税。", "min_attitude": 10, "max_attitude": 100},
                        {"text": "扬州来的人总带着奇怪的货物。你说巧不巧?", "min_attitude": 20, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "走吧。路上小心。", "min_attitude": -100, "max_attitude": 100},
                ],
            },
            "rumor_hooks": [
                "最近有批货没交税就过去了",
                "扬州来的人总带着奇怪的货物",
                "上头要查过境商税",
            ],
            "schedule": {
                "卯时": {"location": "nanjing_jubaomen", "pos": [11, 7], "activity": "开城门点卯"},
                "辰时": {"location": "nanjing_jubaomen", "pos": [14, 9], "activity": "巡查城门内外"},
                "午时": {"location": "nanjing_jubaomen", "pos": [8, 5], "activity": "在城楼吃饭休息"},
                "酉时": {"location": "nanjing_jubaomen", "pos": [11, 7], "activity": "关城门落锁"},
            },
            "observable_details": [
                "腰间挂着一串城门钥匙,走起来叮当作响",
                "右手虎口有一道旧刀疤",
            ],
        },
        "status_effects": [],
        "inventory": [
            {"id": "gate_keys", "name": "城门钥匙", "qty": 1},
            {"id": "pass_records", "name": "过境记录册", "qty": 1},
        ],
        "tags": ["official", "military", "gatekeeper"],
    },
    {
        "id": "monk_huiyuan",
        "name": "慧远禅师",
        "type": "npc",
        "location": "nanjing_jiming",
        "pos": [8, 7],
        "attributes": {
            "hp": 40, "max_hp": 40,
            "rank": "僧侣",
            "occupation": "鸡鸣寺住持",
            "personality": "鸡鸣寺住持,博学多才,与南京官场中人颇有往来,常为士子指点迷津",
            "attack": 1, "defense": 12,
            "money_wen": 100,
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "施主,阿弥陀佛。来寺中可是有所求?", "min_attitude": -100, "max_attitude": 100},
                    {"text": "你又来了。禅房请坐,老衲沏茶。", "min_attitude": 20, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "temple_matters", "label": "寺中之事", "unlock_attitude": 10, "lines": [
                        {"text": "藏经阁有本禁书,记载着前朝旧案。你若有缘,可来借阅。", "min_attitude": 10, "max_attitude": 100},
                        {"text": "常有官员来寺里密谈。老衲是出家人,但……有些事听到了也不会忘。", "min_attitude": 25, "max_attitude": 100},
                    ]},
                    {"id": "buddhist_wisdom", "label": "佛法指点", "unlock_attitude": -10, "lines": [
                        {"text": "施主面有忧色。世间之事,因果循环,善恶终有报。", "min_attitude": -10, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "阿弥陀佛。施主慢走。", "min_attitude": -100, "max_attitude": 100},
                ],
            },
            "rumor_hooks": [
                "寺里藏经阁有本禁书",
                "常有官员来寺里密谈",
                "扬州法海寺的方杖与他是同门",
            ],
            "schedule": {
                "寅时": {"location": "nanjing_jiming", "pos": [6, 4], "activity": "在禅房打坐"},
                "卯时": {"location": "nanjing_jiming", "pos": [10, 8], "activity": "在大殿早课"},
                "巳时": {"location": "nanjing_jiming", "pos": [8, 7], "activity": "在藏经阁整理典籍"},
                "申时": {"location": "nanjing_confucius", "pos": [14, 10], "activity": "去贡院附近散步"},
            },
            "observable_details": [
                "眉心有一颗朱砂痣,据说是高僧相",
                "念珠是罕见的紫檀木,颗颗圆润",
            ],
        },
        "status_effects": [],
        "inventory": [
            {"id": "prayer_beads", "name": "紫檀念珠", "qty": 1},
            {"id": "forbidden_book", "name": "藏经阁禁书", "qty": 1},
        ],
        "tags": ["religious", "scholar", "informant"],
    },
]

# ---- Side threads ----

NANJING_SIDE_THREADS = [
    {
        "id": "nanjing_exam_scandal",
        "title": "科场风云",
        "hook": "周举子说今科主考官与扬州某富商有旧,贡院里有人夹带小抄,扬州甚至有人卖考题。",
        "anchors": [
            {"location": "nanjing_confucius"},
            {"entity": "scholar_zhou"},
            {"entity": "merchant_wu"},
        ],
        "stakes": "追查科场弊案可揭露扬州与南京的利益链条,但牵涉甚广,需谨慎行事。",
    },
    {
        "id": "nanjing_salt_investigation",
        "title": "江南盐税",
        "hook": "秦淮鸨母说朝廷要查江南盐税,扬州盐商常来月华舫宴客,聚宝门守备说最近有批货没交税就过去了。",
        "anchors": [
            {"location": "nanjing_qinhuai"},
            {"location": "nanjing_jubaomen"},
            {"entity": "qinhuai_madam"},
            {"entity": "gate_officer_sun"},
            {"entity": "merchant_wu"},
        ],
        "stakes": "盐税调查牵涉扬州吴员外的走私渠道,可顺藤摸瓜找到更多证据。",
    },
]


def seed_nanjing(world: World) -> None:
    """Seed Nanjing region: 4 locations, 4 NPCs, 2 side threads."""

    # ---- Wire up existing guazhou_ferry → nanjing_jubaomen exit ----
    guazhou_ferry = world.get_location("guazhou_ferry")
    if guazhou_ferry:
        guazhou_ferry.setdefault("exits", {})["north_nanjing"] = "nanjing_jubaomen"
        world.save_location(guazhou_ferry)

    # ---- Save new locations ----
    for loc in NANJING_LOCATIONS:
        world.save_location(loc)

    # ---- Save new NPCs ----
    for entity in NANJING_ENTITIES:
        world.save_entity(entity)

    # ---- Merge evolution registry ----
    registry = world.get_flag("evolution_registry") or []
    existing_ids = {e["entity_id"] for e in registry}
    new_entries = [
        {"entity_id": "scholar_zhou", "frequency": "every_4_turns",
         "last_evolved_turn": 0, "reason": "赴考举子,关注科场动态"},
        {"entity_id": "qinhuai_madam", "frequency": "every_3_turns",
         "last_evolved_turn": 0, "reason": "画舫管事,消息灵通"},
        {"entity_id": "gate_officer_sun", "frequency": "every_5_turns",
         "last_evolved_turn": 0, "reason": "城门守备,掌握过境信息"},
        {"entity_id": "monk_huiyuan", "frequency": "every_6_turns",
         "last_evolved_turn": 0, "reason": "寺中住持,与官场有往来"},
    ]
    for entry in new_entries:
        if entry["entity_id"] not in existing_ids:
            registry.append(entry)
    world.set_flag("evolution_registry", registry)

    # ---- Attach side threads to story seeds ----
    seeds = world.get_flag("story_seeds")
    if seeds:
        existing_thread_ids = {t["id"] for t in seeds.get("side_threads", [])}
        for thread in NANJING_SIDE_THREADS:
            if thread["id"] not in existing_thread_ids:
                seeds["side_threads"].append(thread)
        world.set_flag("story_seeds", seeds)

    # ---- Attach rumor hooks from side threads ----
    for thread in NANJING_SIDE_THREADS:
        for anchor in thread["anchors"]:
            entity_id = anchor.get("entity")
            if entity_id:
                _append_unique_hook(world, entity_id, thread["hook"])
            location_id = anchor.get("location")
            if location_id:
                _append_location_thread(world, location_id, thread)

    world.set_flag("nanjing_seeded", True)


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
