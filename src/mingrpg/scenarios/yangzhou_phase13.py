"""Phase 13: NPC Extension — 4 new NPCs to fill sparse locations and reach 34 total."""
from mingrpg.core.world import World


PHASE13_ENTITIES = [
    {
        "id": "flower_girl_mei",
        "name": "梅儿",
        "type": "npc",
        "location": "street_main",
        "pos": [12, 18],
        "attributes": {
            "hp": 30, "max_hp": 30,
            "rank": "平民",
            "occupation": "卖花女",
            "personality": "嘴甜眼尖,走街串巷卖花,消息灵通但分不清真假,对读书人有好感",
            "attack": 1, "defense": 7,
            "money_wen": 15,
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "公子买花吗?新鲜的菊花!", "min_attitude": -100, "max_attitude": 100},
                    {"text": "公子又来啦!今日特意给您留了好的。", "min_attitude": 20, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "street_news", "label": "街头消息", "unlock_attitude": -10, "lines": [
                        {"text": "街上什么事我不知道?你问吧。", "min_attitude": -10, "max_attitude": 100},
                        {"text": "衙役们在议论什么案子,我路过听见几句。", "min_attitude": 5, "max_attitude": 100},
                        {"text": "客栈那边来了几个生面孔,出手大方,但不让人靠近房间。", "min_attitude": 15, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "公子慢走!下回再来买花啊!", "min_attitude": -100, "max_attitude": 100},
                ],
            },
            "rumor_hooks": [
                "街上听见衙役议论案子",
                "给客栈送过花,看见生面孔",
            ],
            "schedule": {
                "卯时": {"location": "market_stall_food", "pos": [4, 2], "activity": "在街市批花"},
                "辰时": {"location": "street_main", "pos": [12, 18], "activity": "沿街叫卖"},
                "巳时": {"location": "inn_front", "pos": [5, 3], "activity": "在客栈门口卖花"},
                "午时": {"location": "teahouse", "pos": [1, 2], "activity": "在茶楼歇脚卖花"},
                "酉时": {"location": "street_main", "pos": [8, 12], "activity": "收摊回家"},
            },
        },
        "status_effects": [],
        "inventory": [
            {"id": "flower_basket", "name": "花篮", "qty": 1},
            {"id": "wild_chrysanthemum", "name": "野菊花", "qty": 5},
            {"id": "plum_blossom", "name": "梅花", "qty": 3},
        ],
        "tags": ["commoner", "merchant", "informant"],
    },
    {
        "id": "scholar_huang",
        "name": "黄老秀才",
        "type": "npc",
        "location": "academy_gate",
        "pos": [7, 6],
        "attributes": {
            "hp": 35, "max_hp": 35,
            "rank": "秀才",
            "occupation": "落第秀才",
            "personality": "屡试不中却放不下读书人的架子,靠代写书信为生,对时政愤愤不平",
            "attack": 1, "defense": 8,
            "money_wen": 25,
            "skills_taught": ["classical_chinese", "calligraphy"],
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "哦?你也是读书人?坐,坐。", "min_attitude": -100, "max_attitude": 100},
                    {"text": "你来了。今日想写什么?", "min_attitude": 10, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "writing", "label": "代写书信", "unlock_attitude": -20, "lines": [
                        {"text": "家书、状纸、拜帖,老夫都能写。润笔费好商量。", "min_attitude": -20, "max_attitude": 100},
                    ]},
                    {"id": "grievances", "label": "不平之事", "unlock_attitude": 10, "lines": [
                        {"text": "唉,老夫寒窗三十年,屡试不中。这世道,有才无命啊。", "min_attitude": 10, "max_attitude": 100},
                        {"text": "衙门?哼。老夫替人写过不少状纸,里面门道清楚得很。", "min_attitude": 20, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "慢走。有空来坐坐,老夫这里茶虽粗,但不收钱。", "min_attitude": -100, "max_attitude": 100},
                ],
            },
            "rumor_hooks": [
                "代写过奇怪的书信",
                "对衙门积怨已久",
                "认识书院里的学生",
            ],
            "schedule": {
                "卯时": {"location": "academy_gate", "pos": [7, 6], "activity": "在书院门口摆摊代写"},
                "巳时": {"location": "academy_gate", "pos": [7, 6], "activity": "替人写家书"},
                "午时": {"location": "teahouse", "pos": [4, 5], "activity": "去茶楼吃茶发牢骚"},
                "酉时": {"location": "academy_gate", "pos": [7, 6], "activity": "收摊回去温书"},
            },
            "observable_details": [
                "袖口沾着墨渍,手指被墨染黑",
                "摊上摆着几卷写废的纸,字迹工整",
            ],
        },
        "status_effects": [],
        "inventory": [
            {"id": "writing_brush", "name": "毛笔", "qty": 2},
            {"id": "ink_stone", "name": "砚台", "qty": 1},
            {"id": "xuan_paper", "name": "宣纸", "qty": 10},
        ],
        "tags": ["commoner", "scholar", "informant"],
    },
    {
        "id": "washerwoman_liu",
        "name": "刘婶",
        "type": "npc",
        "location": "ferry_pier",
        "pos": [3, 8],
        "attributes": {
            "hp": 40, "max_hp": 40,
            "rank": "平民",
            "occupation": "洗衣妇",
            "personality": "嗓门大,心肠热,在渡口洗衣多年,码头上的事多少知道一些",
            "attack": 1, "defense": 7,
            "money_wen": 10,
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "哟,这位公子,来渡口做什么?", "min_attitude": -100, "max_attitude": 100},
                    {"text": "又是你啊!来来来,坐下歇歇脚。", "min_attitude": 15, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "dock_gossip", "label": "渡口见闻", "unlock_attitude": -10, "lines": [
                        {"text": "我在渡口洗衣这么多年,什么事没见过。", "min_attitude": -10, "max_attitude": 100},
                        {"text": "有次天没亮就来,看见码头有人摸黑往船上搬箱子,贴着封条呢。", "min_attitude": 10, "max_attitude": 100},
                        {"text": "船夫们说河上有怪事,有些船夜里走,不挂灯笼。", "min_attitude": 20, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "慢走啊!有空来渡口找我聊天。", "min_attitude": -100, "max_attitude": 100},
                ],
            },
            "rumor_hooks": [
                "在渡口见过半夜卸货",
                "听船夫说过河上的怪事",
            ],
            "schedule": {
                "卯时": {"location": "ferry_pier", "pos": [3, 8], "activity": "在渡口洗衣"},
                "巳时": {"location": "ferry_pier", "pos": [3, 8], "activity": "晾晒衣物"},
                "午时": {"location": "market_stall_food", "pos": [2, 3], "activity": "去街市买菜"},
                "申时": {"location": "ferry_pier", "pos": [3, 8], "activity": "继续洗衣"},
            },
            "observable_details": [
                "手搓得通红,围裙上溅满水渍",
                "身边堆着几桶待洗的衣裳",
            ],
        },
        "status_effects": [],
        "inventory": [
            {"id": "wash_tub", "name": "木盆", "qty": 1},
            {"id": "washing_board", "name": "搓衣板", "qty": 1},
        ],
        "tags": ["commoner", "laborer", "informant"],
    },
    {
        "id": "gatekeeper_wu",
        "name": "吴门子",
        "type": "npc",
        "location": "court_yard",
        "pos": [10, 10],
        "attributes": {
            "hp": 55, "max_hp": 55,
            "rank": "差役",
            "occupation": "府衙门子",
            "personality": "看门多年,对进出衙门的人了如指掌,嘴上说不管闲事但什么都知道",
            "attack": 2, "defense": 10,
            "money_wen": 50,
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "站住。你找谁?报上名来。", "min_attitude": -100, "max_attitude": 0},
                    {"text": "哦,是你。进去吧,今日知府在。", "min_attitude": 10, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "visitor_log", "label": "访客记录", "unlock_attitude": 10, "lines": [
                        {"text": "我这簿子上记得清清楚楚,谁来过、什么时候来的。", "min_attitude": 10, "max_attitude": 100},
                        {"text": "有个常来的人,从不挂号。他有令牌,我不敢拦。", "min_attitude": 25, "max_attitude": 100},
                    ]},
                    {"id": "night_visitors", "label": "夜间来客", "unlock_attitude": 25, "lines": [
                        {"text": "（压低声音）夜里有人来找过知府,天没亮就走了。我不认识那人。", "min_attitude": 25, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "走吧。衙门的事,出去别乱说。", "min_attitude": -100, "max_attitude": 100},
                ],
            },
            "rumor_hooks": [
                "记录过谁进出衙门",
                "夜里有人来衙门找过知府",
            ],
            "schedule": {
                "卯时": {"location": "court_yard", "pos": [10, 10], "activity": "开衙门候人"},
                "辰时": {"location": "court_yard", "pos": [10, 10], "activity": "盘查来人"},
                "午时": {"location": "court_yard", "pos": [8, 8], "activity": "在门房吃饭"},
                "酉时": {"location": "court_yard", "pos": [10, 10], "activity": "关衙门落锁"},
            },
            "observable_details": [
                "腰间挂着一串钥匙,叮当作响",
                "手里拿着一本进出登记簿",
            ],
        },
        "status_effects": [],
        "inventory": [
            {"id": "court_keys", "name": "衙门钥匙", "qty": 1},
            {"id": "visitor_log", "name": "访客登记簿", "qty": 1},
        ],
        "tags": ["official", "guard"],
    },
]

# ---- New side threads ----

PHASE13_SIDE_THREADS = [
    {
        "id": "gatekeeper_visitors",
        "title": "门子账簿",
        "hook": "吴门子的访客簿上记着一个常来衙门却从不挂号的人,他只说'那位爷有令牌'。",
        "anchors": [
            {"location": "court_yard"},
            {"entity": "gatekeeper_wu"},
            {"entity": "shiye"},
        ],
        "stakes": "门子知道衙门里不为人知的往来,可能牵出暗中势力。",
    },
    {
        "id": "washerwoman_midnight_cargo",
        "title": "渡口夜货",
        "hook": "刘婶有次天没亮就来洗衣,看见码头有人摸黑往船上搬箱子,箱子上贴着封条。",
        "anchors": [
            {"location": "ferry_pier"},
            {"entity": "washerwoman_liu"},
            {"entity": "dock_boss_qian"},
        ],
        "stakes": "洗衣妇无意中目睹了走私,但她不知道那是什么,只觉得奇怪。",
    },
]


def seed_yangzhou_phase13(world: World) -> None:
    """Seed Phase 13 content: 4 new NPC entities + 2 side threads."""

    # ---- Save new NPCs ----
    for entity in PHASE13_ENTITIES:
        world.save_entity(entity)

    # ---- Merge evolution registry for new NPCs ----
    registry = world.get_flag("evolution_registry") or []
    existing_ids = {e["entity_id"] for e in registry}
    new_entries = [
        {"entity_id": "flower_girl_mei", "frequency": "every_5_turns",
         "last_evolved_turn": 0, "reason": "卖花女,街市消息灵通"},
        {"entity_id": "scholar_huang", "frequency": "every_5_turns",
         "last_evolved_turn": 0, "reason": "落第秀才,书院消息源"},
        {"entity_id": "washerwoman_liu", "frequency": "dormant",
         "last_evolved_turn": 0, "reason": "洗衣妇,渡口低频背景NPC"},
        {"entity_id": "gatekeeper_wu", "frequency": "every_3_turns",
         "last_evolved_turn": 0, "reason": "府衙门子,衙门往来记录者"},
    ]
    for entry in new_entries:
        if entry["entity_id"] not in existing_ids:
            registry.append(entry)
    world.set_flag("evolution_registry", registry)

    # ---- Attach new side threads to story seeds ----
    seeds = world.get_flag("story_seeds")
    if seeds:
        existing_thread_ids = {t["id"] for t in seeds.get("side_threads", [])}
        for thread in PHASE13_SIDE_THREADS:
            if thread["id"] not in existing_thread_ids:
                seeds["side_threads"].append(thread)
        world.set_flag("story_seeds", seeds)

    # ---- Attach rumor hooks from new side threads ----
    for thread in PHASE13_SIDE_THREADS:
        for anchor in thread["anchors"]:
            entity_id = anchor.get("entity")
            if entity_id:
                _append_unique_hook(world, entity_id, thread["hook"])
            location_id = anchor.get("location")
            if location_id:
                _append_location_thread(world, location_id, thread)

    world.set_flag("phase13_npc_expanded", True)


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
