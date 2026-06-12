"""Phase 17: New Region — Guazhou Ferry (瓜洲渡).

A small town across the Yangtze from Yangzhou, historically a major
crossing point. Adds 3 locations, 3 NPCs, and a side thread linking
back to the main Yangzhou storyline.
"""
from mingrpg.core.world import World


# ---- Locations ----

GUAZHOU_LOCATIONS = [
    {
        "id": "guazhou_ferry",
        "name": "瓜洲渡口",
        "type": "outdoor",
        "size": [16, 12],
        "exits": {"north": "ferry_pier", "south": "guazhou_town"},
        "tags": ["public", "dock", "travel"],
        "description": "南岸渡口比北岸冷清些,几棵老柳歪斜地立在岸边。一条石阶通向镇子,阶上长满青苔。",
    },
    {
        "id": "guazhou_town",
        "name": "瓜洲镇街",
        "type": "outdoor",
        "size": [18, 14],
        "exits": {"north": "guazhou_ferry", "east": "guazhou_inn"},
        "tags": ["public", "commercial", "quiet"],
        "description": "一条青石板街沿江铺开,两旁是低矮的瓦房。镇子不大,行人稀少,偶有挑担的农夫经过。",
    },
    {
        "id": "guazhou_inn",
        "name": "瓜洲客栈",
        "type": "indoor_commercial",
        "size": [12, 10],
        "exits": {"west": "guazhou_town"},
        "tags": ["commercial", "lodging", "social"],
        "description": "客栈门面不大,堂内摆着几张方桌。墙上挂着褪色的酒旗,柜台上放着一本住客簿。",
    },
]

# ---- NPCs ----

GUAZHOU_ENTITIES = [
    {
        "id": "ferryman_chen",
        "name": "陈老渡",
        "type": "npc",
        "location": "guazhou_ferry",
        "pos": [8, 4],
        "attributes": {
            "hp": 50, "max_hp": 50,
            "rank": "平民",
            "occupation": "渡夫",
            "personality": "在瓜洲摆渡三十年,沉默寡言但观察力极强,对运河上的船只如数家珍",
            "attack": 2, "defense": 9,
            "money_wen": 30,
            "price_list": {"ferry_crossing": 5},
            "service_catalog": {
                "cross_river": {"name": "渡河", "price_wen": 5},
                "night_crossing": {"name": "夜间渡河", "price_wen": 15},
            },
            "memories": [],
            "rumor_hooks": [
                "最近有奇怪的船半夜过江",
                "北岸码头货栈的人来问过船期",
                "吴员外的货从不走瓜洲渡口",
            ],
            "schedule": {
                "卯时": {"location": "guazhou_ferry", "pos": [8, 4], "activity": "解开缆绳准备渡客"},
                "辰时": {"location": "guazhou_ferry", "pos": [10, 6], "activity": "在渡口等客"},
                "午时": {"location": "guazhou_inn", "pos": [3, 5], "activity": "去客栈吃饭"},
                "酉时": {"location": "guazhou_ferry", "pos": [8, 4], "activity": "收船系缆"},
            },
            "observable_details": [
                "手掌满是老茧,指缝间常年发白",
                "腰间挂着一个铜哨,据说是夜间联络暗号",
            ],
            "dialogue_lines": {
                "greetings": [
                    {"text": "（点点头）要过江?", "min_attitude": -100, "max_attitude": 100},
                    {"text": "哦,是你。船备好了,随时能走。", "min_attitude": 10, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "ferry", "label": "渡船", "unlock_attitude": -100, "lines": [
                        {"text": "过江五文,夜间十五文。风雨天不出船。", "min_attitude": -100, "max_attitude": 100},
                    ]},
                    {"id": "night_traffic", "label": "夜间行船", "unlock_attitude": 20, "lines": [
                        {"text": "（压低声音）最近半夜总有船从北岸过来,不走渡口,直接往下游芦苇荡去。", "min_attitude": 20, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "慢走。", "min_attitude": -100, "max_attitude": 100},
                    {"text": "路上小心,江面风大。", "min_attitude": 10, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（上下打量）你不是本地人。要过江?五文钱。"},
                ],
            },
        },
        "status_effects": [],
        "inventory": [
            {"id": "ferry_boat", "name": "乌篷渡船", "qty": 1},
            {"id": "copper_whistle", "name": "铜哨", "qty": 1},
        ],
        "tags": ["commoner", "ferryman", "informant"],
    },
    {
        "id": "guazhou_clerk",
        "name": "郑书办",
        "type": "npc",
        "location": "guazhou_town",
        "pos": [10, 8],
        "attributes": {
            "hp": 40, "max_hp": 40,
            "rank": "书办",
            "occupation": "瓜洲镇书办",
            "personality": "管着瓜洲的渡口税簿和往来登记,为人谨慎但贪小便宜,对扬州府的人既敬畏又好奇",
            "attack": 1, "defense": 8,
            "money_wen": 80,
            "memories": [],
            "rumor_hooks": [
                "渡口税簿上有些条目对不上",
                "有人拿扬州府的名头来免过路税",
                "最近查过几条没有路引的船",
            ],
            "schedule": {
                "卯时": {"location": "guazhou_town", "pos": [10, 8], "activity": "在镇公所开门办公"},
                "巳时": {"location": "guazhou_ferry", "pos": [6, 8], "activity": "去渡口查税簿"},
                "午时": {"location": "guazhou_inn", "pos": [6, 4], "activity": "在客栈吃午饭"},
                "申时": {"location": "guazhou_town", "pos": [10, 8], "activity": "回公所整理文书"},
            },
            "observable_details": [
                "袖口磨得发亮,指尖沾着朱砂",
                "随身带着一串渡口税牌",
            ],
            "dialogue_lines": {
                "greetings": [
                    {"text": "（抬头看了一眼）什么事?", "min_attitude": -100, "max_attitude": 0},
                    {"text": "哦,是你。坐,喝口茶。", "min_attitude": 10, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "tax_records", "label": "渡口税簿", "unlock_attitude": -50, "lines": [
                        {"text": "渡口税簿?那是官府文书,不能随便给人看。", "min_attitude": -50, "max_attitude": 0},
                        {"text": "（犹豫）……好吧,你看看。不过有几个条目对不上,我也纳闷。", "min_attitude": 20, "max_attitude": 100},
                    ]},
                    {"id": "permits", "label": "路引盘查", "unlock_attitude": 0, "lines": [
                        {"text": "最近查过几条没有路引的船,上面有令。", "min_attitude": 0, "max_attitude": 100},
                        {"text": "（压低声音）有人拿扬州府的名头来免过路税,我不敢不从。", "min_attitude": 30, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "慢走。", "min_attitude": -100, "max_attitude": 100},
                    {"text": "有事再来。", "min_attitude": 10, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（打量一番）你是哪来的?有路引吗?……哦,扬州来的。有什么事?"},
                ],
            },
        },
        "status_effects": [],
        "inventory": [
            {"id": "tax_book", "name": "渡口税簿", "qty": 1},
            {"id": "travel_permit_stack", "name": "路引存根", "qty": 5},
        ],
        "tags": ["official", "clerk", "informant"],
    },
    {
        "id": "traveler_li",
        "name": "李行客",
        "type": "npc",
        "location": "guazhou_inn",
        "pos": [8, 6],
        "attributes": {
            "hp": 45, "max_hp": 45,
            "rank": "平民",
            "occupation": "行商",
            "personality": "走南闯北的行商,消息灵通,嘴皮子利索,但说话真假参半",
            "attack": 3, "defense": 10,
            "money_wen": 200,
            "price_list": {"travel_rumor": 10},
            "memories": [],
            "rumor_hooks": [
                "从南京来的路上听说朝廷要查盐税",
                "在扬州见过一个被通缉的人",
                "瓜洲客栈住过一个出手阔绰的神秘客人",
            ],
            "schedule": {
                "卯时": {"location": "guazhou_inn", "pos": [8, 6], "activity": "在客栈睡懒觉"},
                "巳时": {"location": "guazhou_town", "pos": [5, 6], "activity": "在镇上闲逛打听行情"},
                "午时": {"location": "guazhou_inn", "pos": [4, 4], "activity": "在客栈吃饭"},
                "酉时": {"location": "guazhou_ferry", "pos": [12, 6], "activity": "去渡口看来往船只"},
            },
            "observable_details": [
                "背着一个鼓鼓囊囊的包袱,里面叮当作响",
                "靴子上沾着不同地方的泥土",
            ],
            "dialogue_lines": {
                "greetings": [
                    {"text": "（热情地）哟,这位朋友,也是赶路的?", "min_attitude": -100, "max_attitude": 100},
                    {"text": "哈哈,又见面了!来来来,坐下聊。", "min_attitude": 10, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "travel_news", "label": "路上见闻", "unlock_attitude": -50, "lines": [
                        {"text": "从南京来的路上听说朝廷要查盐税,风声很紧。", "min_attitude": -50, "max_attitude": 100},
                        {"text": "（神秘兮兮）我在扬州见过一个被通缉的人,不过嘛……记不太清了。", "min_attitude": 0, "max_attitude": 100},
                    ]},
                    {"id": "inn_guest", "label": "客栈奇客", "unlock_attitude": 10, "lines": [
                        {"text": "这客栈前阵子住过一个出手阔绰的客人,半夜走的,账都没结。", "min_attitude": 10, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "后会有期!路上小心。", "min_attitude": -100, "max_attitude": 100},
                    {"text": "改天请你喝酒!", "min_attitude": 20, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（拱手）在下李行客,走南闯北做些小买卖。兄台贵姓?"},
                ],
            },
        },
        "status_effects": [],
        "inventory": [
            {"id": "travel_pack", "name": "行囊", "qty": 1},
            {"id": "fake_permit", "name": "可疑路引", "qty": 1},
        ],
        "tags": ["commoner", "merchant", "informant"],
    },
]

# ---- Side thread ----

GUAZHOU_SIDE_THREADS = [
    {
        "id": "guazhou_night_crossing",
        "title": "夜渡暗货",
        "hook": "陈老渡说最近常有船半夜从北岸过来,不走渡口,直接在下游芦苇荡靠岸。有人在那边接货。",
        "anchors": [
            {"location": "guazhou_ferry"},
            {"entity": "ferryman_chen"},
            {"entity": "merchant_wu"},
        ],
        "stakes": "这条线索可追查吴员外的走私渠道,但夜间行动本身也容易触犯宵禁。",
    },
]


def seed_guazhou(world: World) -> None:
    """Seed Guazhou Ferry region: 3 locations, 3 NPCs, 1 side thread."""

    # ---- Wire up existing ferry_pier → guazhou_ferry exit ----
    ferry_pier = world.get_location("ferry_pier")
    if ferry_pier:
        ferry_pier.setdefault("exits", {})["south_guazhou"] = "guazhou_ferry"
        world.save_location(ferry_pier)

    # ---- Save new locations ----
    for loc in GUAZHOU_LOCATIONS:
        world.save_location(loc)

    # ---- Save new NPCs ----
    for entity in GUAZHOU_ENTITIES:
        world.save_entity(entity)

    # ---- Merge evolution registry ----
    registry = world.get_flag("evolution_registry") or []
    existing_ids = {e["entity_id"] for e in registry}
    new_entries = [
        {"entity_id": "ferryman_chen", "frequency": "every_3_turns",
         "last_evolved_turn": 0, "reason": "渡夫,知晓夜间渡船动向"},
        {"entity_id": "guazhou_clerk", "frequency": "every_5_turns",
         "last_evolved_turn": 0, "reason": "镇书办,掌握税簿记录"},
        {"entity_id": "traveler_li", "frequency": "every_4_turns",
         "last_evolved_turn": 0, "reason": "行商,流动消息源"},
    ]
    for entry in new_entries:
        if entry["entity_id"] not in existing_ids:
            registry.append(entry)
    world.set_flag("evolution_registry", registry)

    # ---- Attach side thread to story seeds ----
    seeds = world.get_flag("story_seeds")
    if seeds:
        existing_thread_ids = {t["id"] for t in seeds.get("side_threads", [])}
        for thread in GUAZHOU_SIDE_THREADS:
            if thread["id"] not in existing_thread_ids:
                seeds["side_threads"].append(thread)
        world.set_flag("story_seeds", seeds)

    # ---- Attach rumor hooks from side thread ----
    for thread in GUAZHOU_SIDE_THREADS:
        for anchor in thread["anchors"]:
            entity_id = anchor.get("entity")
            if entity_id:
                _append_unique_hook(world, entity_id, thread["hook"])
            location_id = anchor.get("location")
            if location_id:
                _append_location_thread(world, location_id, thread)

    world.set_flag("guazhou_seeded", True)


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
