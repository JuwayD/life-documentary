"""Phase 11: World Content Deepening — antagonist NPCs, female NPCs, new side threads."""
from mingrpg.core.world import World


# ---- Antagonist & supporting NPCs ----

ANTAGONIST_ENTITIES = [
    {
        "id": "bully_zhao",
        "name": "赵三",
        "type": "npc",
        "location": "river_dock",
        "pos": [18, 10],
        "attributes": {
            "hp": 70, "max_hp": 70,
            "rank": "平民",
            "occupation": "漕帮打手",
            "personality": "横行市井,欺软怕硬,替豪商跑腿压价收货,手下有几个泼皮",
            "attack": 6, "defense": 12,
            "weapon_damage": "1d6", "weapon_name": "拳头",
            "dialogue_lines": {
                "greetings": [
                    {"text": "（斜眼）你谁啊?找老子什么事?", "min_attitude": -100, "max_attitude": -10},
                    {"text": "哟,是你啊。怎么,又来讨打?", "min_attitude": -10, "max_attitude": 20},
                ],
                "topics": [
                    {"id": "threat", "label": "警告", "unlock_attitude": -100, "lines": [
                        {"text": "少管闲事!不然让你在扬州混不下去!", "min_attitude": -100, "max_attitude": 0},
                        {"text": "（冷笑）你那破状纸有什么用?知府大人跟我家员外喝过茶。", "min_attitude": -50, "max_attitude": 20},
                    ]},
                    {"id": "boss", "label": "幕后指使", "unlock_attitude": 10, "lines": [
                        {"text": "（压低声音）我替谁办事?……哼,你最好别知道。", "min_attitude": 10, "max_attitude": 50},
                    ]},
                ],
                "farewells": [
                    {"text": "滚!别让老子再看见你!", "min_attitude": -100, "max_attitude": 0},
                    {"text": "走吧走吧,下次请我喝酒。", "min_attitude": 20, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（上下打量）就你?要告我?哈!回去照照镜子吧。"},
                ],
            },
            "money_wen": 150,
            "memories": [],
            "rumor_hooks": [
                "状纸上控告的恶霸",
                "替人压价收货",
                "夜里在货栈出没",
            ],
            "schedule": {
                "卯时": {"location": "market_stall_food", "pos": [3, 2], "activity": "在小吃摊白吃白喝"},
                "巳时": {"location": "river_dock", "pos": [18, 10], "activity": "在码头闲逛收保护费"},
                "午时": {"location": "teahouse", "pos": [3, 6], "activity": "在茶楼喝茶听消息"},
                "酉时": {"location": "warehouse", "pos": [10, 6], "activity": "去货栈接头"},
            },
        },
        "status_effects": [],
        "inventory": [
            {"id": "iron_ring", "name": "铁指环", "qty": 1},
        ],
        "tags": ["commoner", "bully", "antagonist"],
    },
    {
        "id": "merchant_wu",
        "name": "吴员外",
        "type": "npc",
        "location": "warehouse",
        "pos": [8, 4],
        "attributes": {
            "hp": 60, "max_hp": 60,
            "rank": "员外",
            "occupation": "绸缎商人",
            "personality": "表面和善实则狠辣,暗中操控码头货价,与府衙有利益往来",
            "attack": 1, "defense": 10,
            "dialogue_lines": {
                "greetings": [
                    {"text": "（微笑）这位公子面善,不知在哪发财?", "min_attitude": -100, "max_attitude": 100},
                    {"text": "哦,是你。来,坐,喝杯茶。", "min_attitude": 10, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "business", "label": "生意经", "unlock_attitude": -50, "lines": [
                        {"text": "做买卖嘛,和气生财。我吴某人最讲诚信。", "min_attitude": -50, "max_attitude": 100},
                        {"text": "扬州这地方,码头是命脉。谁掌握了码头,谁就掌握了钱脉。", "min_attitude": 10, "max_attitude": 100},
                    ]},
                    {"id": "dark_side", "label": "暗中勾当", "unlock_attitude": 40, "lines": [
                        {"text": "（意味深长）公子,有些生意……不方便摆在台面上。你应该懂。", "min_attitude": 40, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "慢走。有空来喝茶,生意上的事好商量。", "min_attitude": -100, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（热情地拱手）幸会幸会!在下吴某,做些绸缎小买卖。公子有什么需要,尽管开口。"},
                    {"trigger": "high_attitude", "text": "（压低声音,正色道）你是聪明人。我跟你交个底——码头那边的事,比你想的复杂得多。", "min_attitude": 60},
                ],
            },
            "money_wen": 5000,
            "price_list": {"silk_wholesale": 100, "brocade_wholesale": 900},
            "service_catalog": {
                "bulk_purchase": {"name": "大批量进货", "price_wen": 500},
            },
            "memories": [],
            "rumor_hooks": [
                "幕后的豪商",
                "暗中操控货价",
                "与府衙有账目往来",
            ],
            "schedule": {
                "巳时": {"location": "warehouse", "pos": [8, 4], "activity": "在货栈核对账目"},
                "午时": {"location": "teahouse", "pos": [7, 4], "activity": "在茶楼雅间会客"},
                "酉时": {"location": "inn_room", "pos": [4, 4], "activity": "回客栈歇息"},
            },
        },
        "status_effects": [],
        "inventory": [
            {"id": "account_book_wu", "name": "私账簿", "qty": 1},
            {"id": "jade_pendant", "name": "玉佩", "qty": 1},
        ],
        "tags": ["commoner", "merchant", "antagonist"],
    },
]

# ---- Female NPCs ----

FEMALE_ENTITIES = [
    {
        "id": "teahouse_singer",
        "name": "柳姑娘",
        "type": "npc",
        "location": "teahouse",
        "pos": [8, 6],
        "attributes": {
            "hp": 40, "max_hp": 40,
            "rank": "平民",
            "occupation": "茶楼歌伎",
            "personality": "温婉聪慧,善解人意,茶楼弹唱为生,听过不少官场秘闻",
            "attack": 1, "defense": 8,
            "dialogue_lines": {
                "greetings": [
                    {"text": "（浅笑）公子好雅兴,来听曲儿?", "min_attitude": -100, "max_attitude": 100},
                    {"text": "你来了。今日唱什么?你点。", "min_attitude": 20, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "gossip", "label": "茶楼闲话", "unlock_attitude": -10, "lines": [
                        {"text": "来茶楼的什么人都有,官场商场的事,我多少听了一些。", "min_attitude": -10, "max_attitude": 100},
                        {"text": "前几日有两个官差模样的人来喝茶,说的都是盐税的事。", "min_attitude": 10, "max_attitude": 100},
                    ]},
                    {"id": "secrets", "label": "秘闻", "unlock_attitude": 30, "lines": [
                        {"text": "（低声）有一次我弹琴时,屏风后面有人在谈生意。提到'夜渡'和'暗账'两个词。", "min_attitude": 30, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "公子慢走。改日再来听曲儿。", "min_attitude": -100, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（抬眸一看,微微欠身）公子是头一回来吧?请坐,小女子献丑弹一曲。"},
                ],
            },
            "money_wen": 60,
            "memories": [],
            "rumor_hooks": [
                "茶楼弹唱时听到的密谈",
                "有人出钱让她打听客人来历",
            ],
            "schedule": {
                "巳时": {"location": "teahouse", "pos": [8, 6], "activity": "在茶楼练曲"},
                "午时": {"location": "teahouse", "pos": [5, 5], "activity": "午间弹唱"},
                "酉时": {"location": "inn_hall", "pos": [6, 8], "activity": "回客栈休息"},
            },
        },
        "status_effects": [],
        "inventory": [
            {"id": "pipa", "name": "琵琶", "qty": 1},
        ],
        "tags": ["commoner", "entertainer", "informant"],
    },
    {
        "id": "herb_woman",
        "name": "宋婶",
        "type": "npc",
        "location": "clinic_front",
        "pos": [5, 6],
        "attributes": {
            "hp": 45, "max_hp": 45,
            "rank": "平民",
            "occupation": "药婆",
            "personality": "心直口快,懂草药偏方,常帮街坊接生看病,消息灵通",
            "attack": 1, "defense": 8,
            "dialogue_lines": {
                "greetings": [
                    {"text": "哟,这位小哥,哪里不舒服?", "min_attitude": -100, "max_attitude": 100},
                    {"text": "你又来了?坐,我给你把把脉。", "min_attitude": 15, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "medicine", "label": "药材内情", "unlock_attitude": -10, "lines": [
                        {"text": "最近药材涨价涨得厉害,何郎中都快进不起货了。", "min_attitude": -10, "max_attitude": 100},
                        {"text": "听说有人在码头低价收药材,再高价卖给药铺。", "min_attitude": 10, "max_attitude": 100},
                    ]},
                    {"id": "patients", "label": "病患消息", "unlock_attitude": 10, "lines": [
                        {"text": "前几日码头有个脚夫被人打伤了,送到回春堂。伤得不轻,但不肯报官。", "min_attitude": 10, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "走好啊!有什么不舒服再来。", "min_attitude": -100, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "哎呀,新面孔!来来来,让婶子看看你气色。"},
                ],
            },
            "money_wen": 35,
            "service_catalog": {
                "herb_consult": {"name": "偏方咨询", "price_wen": 5},
                "midwifery": {"name": "接生", "price_wen": 30},
            },
            "memories": [],
            "rumor_hooks": [
                "药材涨价的内情",
                "码头伤患的伤势",
            ],
        },
        "status_effects": [],
        "inventory": [
            {"id": "herb_pouch", "name": "草药袋", "qty": 1},
        ],
        "tags": ["commoner", "medicine", "informant"],
    },
    {
        "id": "temple_widow",
        "name": "周寡妇",
        "type": "npc",
        "location": "temple_gate",
        "pos": [8, 5],
        "attributes": {
            "hp": 35, "max_hp": 35,
            "rank": "平民",
            "occupation": "绣娘",
            "personality": "沉默寡言,每日来庙里上香,丈夫死因蹊跷,似有隐情",
            "attack": 1, "defense": 8,
            "dialogue_lines": {
                "greetings": [
                    {"text": "（低头不语,微微点头）", "min_attitude": -100, "max_attitude": 0},
                    {"text": "（轻声）你……又来了。", "min_attitude": 10, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "husband", "label": "亡夫之事", "unlock_attitude": 20, "lines": [
                        {"text": "（眼眶微红）我家那口子……走得太突然了。", "min_attitude": 20, "max_attitude": 100},
                        {"text": "（咬唇）他出事前一天,有人来找过他。我不认识那个人。", "min_attitude": 40, "max_attitude": 100},
                    ]},
                    {"id": "temple", "label": "庙中见闻", "unlock_attitude": 0, "lines": [
                        {"text": "我每日来上香,求城隍爷保佑。", "min_attitude": 0, "max_attitude": 100},
                        {"text": "庙里有时候来些奇怪的人,烧完香就走,也不求签。", "min_attitude": 15, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "（低头继续上香）", "min_attitude": -100, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（被吓了一跳,后退一步）你……你是谁?"},
                    {"trigger": "high_attitude", "text": "（泪光闪烁）你是好人。我告诉你……我丈夫死的那天晚上,码头有船。", "min_attitude": 50},
                ],
            },
            "money_wen": 40,
            "price_list": {"embroidery": 25},
            "memories": [],
            "rumor_hooks": [
                "丈夫死因不明",
                "常在庙里求签问卦",
                "有人见过她深夜在码头附近",
            ],
            "schedule": {
                "卯时": {"location": "temple_gate", "pos": [8, 5], "activity": "在庙前上香"},
                "巳时": {"location": "market_stall_fabric", "pos": [6, 5], "activity": "在布匹摊买绣线"},
                "酉时": {"location": "temple_hall", "pos": [4, 5], "activity": "在大殿求签"},
            },
        },
        "status_effects": [],
        "inventory": [
            {"id": "embroidery_needle", "name": "绣花针", "qty": 1},
            {"id": "incense_bundle", "name": "香烛", "qty": 3},
        ],
        "tags": ["commoner", "widow", "informant"],
    },
    {
        "id": "inn_maid",
        "name": "阿杏",
        "type": "npc",
        "location": "inn_hall",
        "pos": [12, 5],
        "attributes": {
            "hp": 35, "max_hp": 35,
            "rank": "平民",
            "occupation": "客栈丫鬟",
            "personality": "手脚勤快,嘴严但心善,对住客行踪了如指掌",
            "attack": 1, "defense": 8,
            "dialogue_lines": {
                "greetings": [
                    {"text": "客官有什么吩咐?", "min_attitude": -100, "max_attitude": 100},
                    {"text": "（小声）你来了。我有些事想告诉你。", "min_attitude": 20, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "guests", "label": "住客行踪", "unlock_attitude": 0, "lines": [
                        {"text": "住客来来往往,我收拾房间时多少看到些东西。", "min_attitude": 0, "max_attitude": 100},
                        {"text": "有个客人每次来都带个黑布包,从不让人碰。", "min_attitude": 15, "max_attitude": 100},
                    ]},
                    {"id": "wu_servants", "label": "吴员外随从", "unlock_attitude": 25, "lines": [
                        {"text": "（压低声音）吴员外的随从前几日来找掌柜,给了掌柜一包银子。我偷听到'夜渡'两个字。", "min_attitude": 25, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "客官慢走。", "min_attitude": -100, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（低头行礼）客官好。要住店的话,我去叫掌柜。"},
                ],
            },
            "money_wen": 15,
            "memories": [],
            "rumor_hooks": [
                "客栈失踪客人的线索",
                "吴员外的随从曾私下找过掌柜",
            ],
            "schedule": {
                "卯时": {"location": "inn_hall", "pos": [12, 5], "activity": "打扫大堂"},
                "午时": {"location": "inn_room", "pos": [4, 4], "activity": "收拾客房"},
                "酉时": {"location": "inn_hall", "pos": [8, 6], "activity": "准备晚饭"},
            },
        },
        "status_effects": [],
        "inventory": [
            {"id": "broom", "name": "扫帚", "qty": 1},
        ],
        "tags": ["commoner", "service", "maid"],
    },
]

# ---- New side threads ----

NEW_SIDE_THREADS = [
    {
        "id": "dock_gambling_den",
        "title": "码头赌局",
        "hook": "码头货栈后院有人聚赌,赵三常在那里出没,赌客中有衙役身影。",
        "anchors": [{"location": "warehouse"}, {"entity": "bully_zhao"}, {"entity": "dock_boss_qian"}],
        "stakes": "赌局可作为抓捕赵三的切入点,但参与赌博本身也触犯律法。",
    },
    {
        "id": "widow_husband_death",
        "title": "寡妇之冤",
        "hook": "周寡妇丈夫去年在码头溺亡,官府断为意外,但有人说当夜见过赵三在场。",
        "anchors": [{"location": "temple_gate"}, {"entity": "temple_widow"}, {"entity": "beggar_liu"}],
        "stakes": "查明死因可为主线增添铁证,但牵涉赵三会直接推高证人受压钟。",
    },
    {
        "id": "merchant_ledger",
        "title": "豪商暗账",
        "hook": "吴员外的私账簿记载着与府衙的银两往来,但账簿从不离身。",
        "anchors": [{"location": "warehouse"}, {"entity": "merchant_wu"}, {"entity": "shiye"}],
        "stakes": "取得账簿是扳倒豪商的关键,但吴员外身边有人保护。",
    },
    {
        "id": "singer_secret",
        "title": "歌伎知音",
        "hook": "柳姑娘弹唱时听到过吴员外与师爷的密谈,但她不敢声张。",
        "anchors": [{"location": "teahouse"}, {"entity": "teahouse_singer"}, {"entity": "merchant_wu"}],
        "stakes": "歌伎的证词可佐证府衙与豪商勾结,但保护她的安全是个问题。",
    },
]


def seed_yangzhou_phase11(world: World) -> None:
    """Seed Phase 11 content: antagonists, female NPCs, new threads."""

    # ---- Fix jail connectivity ----
    jail = world.get_location("jail")
    if jail:
        jail.setdefault("exits", {})["north"] = "court_yard"
        world.save_location(jail)

    court_yard = world.get_location("court_yard")
    if court_yard:
        court_yard.setdefault("exits", {})["south_jail"] = "jail"
        world.save_location(court_yard)

    # ---- Save antagonist & female NPCs ----
    for entity in ANTAGONIST_ENTITIES + FEMALE_ENTITIES:
        world.save_entity(entity)

    # ---- Merge evolution registry for new NPCs ----
    registry = world.get_flag("evolution_registry") or []
    existing_ids = {e["entity_id"] for e in registry}
    new_entries = [
        {"entity_id": "bully_zhao", "frequency": "every_2_turns",
         "last_evolved_turn": 0, "reason": "主线反派,需持续关注其动向"},
        {"entity_id": "merchant_wu", "frequency": "every_2_turns",
         "last_evolved_turn": 0, "reason": "幕后主使,关键NPC"},
        {"entity_id": "teahouse_singer", "frequency": "every_5_turns",
         "last_evolved_turn": 0, "reason": "茶楼歌伎,消息灵通"},
        {"entity_id": "herb_woman", "frequency": "every_5_turns",
         "last_evolved_turn": 0, "reason": "药婆,街坊消息"},
        {"entity_id": "temple_widow", "frequency": "every_5_turns",
         "last_evolved_turn": 0, "reason": "寡妇之冤支线相关"},
        {"entity_id": "inn_maid", "frequency": "every_5_turns",
         "last_evolved_turn": 0, "reason": "客栈丫鬟,知晓住客行踪"},
    ]
    for entry in new_entries:
        if entry["entity_id"] not in existing_ids:
            registry.append(entry)
    world.set_flag("evolution_registry", registry)

    # ---- Attach new side threads to story seeds ----
    seeds = world.get_flag("story_seeds")
    if seeds:
        existing_thread_ids = {t["id"] for t in seeds.get("side_threads", [])}
        for thread in NEW_SIDE_THREADS:
            if thread["id"] not in existing_thread_ids:
                seeds["side_threads"].append(thread)
        world.set_flag("story_seeds", seeds)

    # ---- Attach rumor hooks from new side threads ----
    for thread in NEW_SIDE_THREADS:
        for anchor in thread["anchors"]:
            entity_id = anchor.get("entity")
            if entity_id:
                _append_unique_hook(world, entity_id, thread["hook"])
            location_id = anchor.get("location")
            if location_id:
                _append_location_thread(world, location_id, thread)

    # ---- Attach main thread hooks for antagonist NPCs ----
    main_leads = [
        {"entity": "bully_zhao", "clue": "赵三就是状纸上控告的恶霸,码头打手"},
        {"entity": "merchant_wu", "clue": "吴员外是赵三背后的豪商,操控码头货价"},
    ]
    for lead in main_leads:
        _append_unique_hook(world, lead["entity"], lead["clue"])

    world.set_flag("phase11_world_deepened", True)


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
