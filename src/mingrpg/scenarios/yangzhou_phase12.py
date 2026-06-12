"""Phase 12: NPC Expansion — 4 new NPCs to reach 30+ vision target."""
from mingrpg.core.world import World


PHASE12_ENTITIES = [
    {
        "id": "storyteller_sun",
        "name": "孙说书",
        "type": "npc",
        "location": "teahouse",
        "pos": [2, 3],
        "attributes": {
            "hp": 40, "max_hp": 40,
            "rank": "平民",
            "occupation": "茶楼说书人",
            "personality": "口若悬河,记忆力极好,把街头巷尾的传闻编成段子,在茶楼很受欢迎",
            "attack": 1, "defense": 8,
            "money_wen": 40,
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "客官请坐,今儿说的是武松打虎!", "min_attitude": -100, "max_attitude": 100},
                    {"text": "老听客来了!今日给您留了前排座。", "min_attitude": 20, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "stories", "label": "坊间传闻", "unlock_attitude": -10, "lines": [
                        {"text": "最近这官司啊,比话本还精彩。赵三那事,里面水深着呢。", "min_attitude": -10, "max_attitude": 100},
                        {"text": "衙门的人来听过书,被我编进段子了,他们脸都绿了。", "min_attitude": 15, "max_attitude": 100},
                    ]},
                    {"id": "story_sources", "label": "消息来源", "unlock_attitude": 20, "lines": [
                        {"text": "茶楼里什么人没有?我耳朵灵着呢。你要打听什么,先请我喝壶好茶。", "min_attitude": 20, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "慢走!下回再来听书啊!", "min_attitude": -100, "max_attitude": 100},
                ],
            },
            "rumor_hooks": [
                "把近来官司编进段子",
                "衙门的人来茶楼听过书",
            ],
            "schedule": {
                "巳时": {"location": "teahouse", "pos": [2, 3], "activity": "在茶楼整理话本"},
                "午时": {"location": "teahouse", "pos": [6, 4], "activity": "午间说书"},
                "酉时": {"location": "market_stall_food", "pos": [3, 2], "activity": "收摊后喝酒"},
            },
        },
        "status_effects": [],
        "inventory": [
            {"id": "story_book", "name": "话本册", "qty": 1},
            {"id": "wooden_clapper", "name": "醒木", "qty": 1},
        ],
        "tags": ["commoner", "entertainer", "informant"],
    },
    {
        "id": "fortune_yao",
        "name": "姚半仙",
        "type": "npc",
        "location": "temple_gate",
        "pos": [4, 6],
        "attributes": {
            "hp": 35, "max_hp": 35,
            "rank": "平民",
            "occupation": "算命先生",
            "personality": "故弄玄虚但观察力极强,靠相面算命为生,看人极准",
            "attack": 1, "defense": 8,
            "money_wen": 30,
            "service_catalog": {
                "face_reading": {"name": "相面", "price_wen": 10},
                "palm_reading": {"name": "看手相", "price_wen": 8},
                "divination": {"name": "起卦", "price_wen": 15},
            },
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "这位施主,贫道观你面相,似有心事。", "min_attitude": -100, "max_attitude": 100},
                    {"text": "又来了?你的命格我已了然于胸。", "min_attitude": 20, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "fortune", "label": "算命问卦", "unlock_attitude": -20, "lines": [
                        {"text": "你印堂发黑,近日恐有口舌之争。不过……有贵人相助。", "min_attitude": -20, "max_attitude": 100},
                        {"text": "（端详手掌）你这手相,命中有波折,但终能化险为夷。", "min_attitude": 10, "max_attitude": 100},
                    ]},
                    {"id": "observations", "label": "街头见闻", "unlock_attitude": 10, "lines": [
                        {"text": "贫道虽在此摆摊,但往来之人皆入我眼。有些事,看到了也不便说。", "min_attitude": 10, "max_attitude": 100},
                        {"text": "那码头的寡妇,手上有黄泥印子。你猜是哪来的?", "min_attitude": 25, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "去吧。天机不可多泄。", "min_attitude": -100, "max_attitude": 100},
                ],
            },
            "rumor_hooks": [
                "给码头脚夫算过命",
                "看面相看出蹊跷",
            ],
            "schedule": {
                "卯时": {"location": "temple_gate", "pos": [4, 6], "activity": "在庙前摆摊"},
                "巳时": {"location": "temple_gate", "pos": [4, 6], "activity": "给人算命看相"},
                "酉时": {"location": "market_stall_food", "pos": [2, 2], "activity": "收摊去喝酒"},
            },
        },
        "status_effects": [],
        "inventory": [
            {"id": "divination_sticks", "name": "卦签", "qty": 1},
            {"id": "bagua_cloth", "name": "八卦布", "qty": 1},
        ],
        "tags": ["commoner", "diviner", "informant"],
    },
    {
        "id": "porter_chen",
        "name": "陈脚夫",
        "type": "npc",
        "location": "street_main",
        "pos": [10, 15],
        "attributes": {
            "hp": 60, "max_hp": 60,
            "rank": "平民",
            "occupation": "街头挑夫",
            "personality": "老实本分,手脚勤快,在街头替人挑货为生,消息不太灵通但嘴不严",
            "attack": 2, "defense": 9,
            "money_wen": 20,
            "service_catalog": {
                "carry_goods": {"name": "挑货搬运", "price_wen": 8},
            },
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "这位爷,要搬货吗?便宜!", "min_attitude": -100, "max_attitude": 100},
                    {"text": "又是你啊。有什么活尽管吩咐。", "min_attitude": 10, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "dock_news", "label": "码头消息", "unlock_attitude": 0, "lines": [
                        {"text": "我就是个挑货的,什么都不知道。", "min_attitude": -50, "max_attitude": 10},
                        {"text": "（压低声音）昨儿帮人搬了几箱货,死沉死沉的,也不知道是什么。", "min_attitude": 15, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "好嘞,有活再找我。", "min_attitude": -100, "max_attitude": 100},
                ],
            },
            "rumor_hooks": [
                "替人搬过货",
                "街上见过可疑的人",
            ],
            "schedule": {
                "卯时": {"location": "street_main", "pos": [10, 15], "activity": "在街头等活"},
                "午时": {"location": "market_gate", "pos": [5, 4], "activity": "在街市揽生意"},
                "酉时": {"location": "street_main", "pos": [15, 20], "activity": "收工歇脚"},
            },
        },
        "status_effects": [],
        "inventory": [
            {"id": "carrying_pole", "name": "扁担", "qty": 1},
            {"id": "rope_chen", "name": "麻绳", "qty": 2},
        ],
        "tags": ["commoner", "laborer"],
    },
    {
        "id": "jailer_zhang",
        "name": "张牢头",
        "type": "npc",
        "location": "jail",
        "pos": [2, 2],
        "attributes": {
            "hp": 65, "max_hp": 65,
            "rank": "差役",
            "occupation": "大牢牢头",
            "personality": "见惯犯人,心肠硬但讲规矩,对读书人略有敬意,喝点酒话就多",
            "attack": 3, "defense": 11,
            "weapon_damage": "1d4", "weapon_name": "铁尺",
            "money_wen": 80,
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "你来大牢做什么?这里不是你该来的地方。", "min_attitude": -100, "max_attitude": 0},
                    {"text": "哦,是你。坐吧,喝口酒。", "min_attitude": 20, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "prisoners", "label": "牢里之事", "unlock_attitude": 10, "lines": [
                        {"text": "牢里关过什么人?多了去了。你想问哪个?", "min_attitude": 10, "max_attitude": 100},
                        {"text": "（喝了口酒）前阵子关了个外地来的,没两天就被提走了。上头的命令。", "min_attitude": 25, "max_attitude": 100},
                    ]},
                    {"id": "jail_secrets", "label": "牢房秘闻", "unlock_attitude": 30, "lines": [
                        {"text": "（醉眼朦胧）夜里提审?有。不是我审的,是衙门里来的人。我不认识。", "min_attitude": 30, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "走吧。这儿阴气重,别久待。", "min_attitude": -100, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（上下打量）你是谁?大牢重地,闲人免进。有话快说。"},
                ],
            },
            "rumor_hooks": [
                "牢里关过什么人",
                "衙役夜里提审过犯人",
            ],
            "schedule": {
                "卯时": {"location": "jail", "pos": [2, 2], "activity": "点名查犯人"},
                "午时": {"location": "jail", "pos": [3, 1], "activity": "给犯人送饭"},
                "酉时": {"location": "court_yard", "pos": [10, 10], "activity": "去院子透气喝酒"},
            },
        },
        "status_effects": [],
        "inventory": [
            {"id": "iron_ruler", "name": "铁尺", "qty": 1},
            {"id": "jail_keys", "name": "牢门钥匙", "qty": 1},
        ],
        "tags": ["official", "guard", "jail"],
    },
]

# ---- New side threads ----

PHASE12_SIDE_THREADS = [
    {
        "id": "storyteller_lawsuit",
        "title": "说书人官司",
        "hook": "孙说书把近来的官司编进段子,引得衙役来茶楼查问,但说书人消息来源不止一处。",
        "anchors": [
            {"location": "teahouse"},
            {"entity": "storyteller_sun"},
            {"entity": "teahouse_owner"},
        ],
        "stakes": "说书人知道很多坊间传闻,但公开说书会引来衙门注意。",
    },
    {
        "id": "fortune_teller_secrets",
        "title": "半仙知命",
        "hook": "姚半仙给周寡妇算过命,看出她手上有码头特有的黄泥印记,却没说破。",
        "anchors": [
            {"location": "temple_gate"},
            {"entity": "fortune_yao"},
            {"entity": "temple_widow"},
        ],
        "stakes": "算命先生的观察力极强,可能成为查明寡妇之冤的关键证人。",
    },
]


def seed_yangzhou_phase12(world: World) -> None:
    """Seed Phase 12 content: 4 new NPC entities + 2 side threads."""

    # ---- Save new NPCs ----
    for entity in PHASE12_ENTITIES:
        world.save_entity(entity)

    # ---- Merge evolution registry for new NPCs ----
    registry = world.get_flag("evolution_registry") or []
    existing_ids = {e["entity_id"] for e in registry}
    new_entries = [
        {"entity_id": "storyteller_sun", "frequency": "every_5_turns",
         "last_evolved_turn": 0, "reason": "说书人,茶楼消息中枢"},
        {"entity_id": "fortune_yao", "frequency": "every_5_turns",
         "last_evolved_turn": 0, "reason": "算命先生,庙前消息灵通"},
        {"entity_id": "porter_chen", "frequency": "dormant",
         "last_evolved_turn": 0, "reason": "街头挑夫,低频背景NPC"},
        {"entity_id": "jailer_zhang", "frequency": "every_5_turns",
         "last_evolved_turn": 0, "reason": "牢头,大牢信息源"},
    ]
    for entry in new_entries:
        if entry["entity_id"] not in existing_ids:
            registry.append(entry)
    world.set_flag("evolution_registry", registry)

    # ---- Attach new side threads to story seeds ----
    seeds = world.get_flag("story_seeds")
    if seeds:
        existing_thread_ids = {t["id"] for t in seeds.get("side_threads", [])}
        for thread in PHASE12_SIDE_THREADS:
            if thread["id"] not in existing_thread_ids:
                seeds["side_threads"].append(thread)
        world.set_flag("story_seeds", seeds)

    # ---- Attach rumor hooks from new side threads ----
    for thread in PHASE12_SIDE_THREADS:
        for anchor in thread["anchors"]:
            entity_id = anchor.get("entity")
            if entity_id:
                _append_unique_hook(world, entity_id, thread["hook"])
            location_id = anchor.get("location")
            if location_id:
                _append_location_thread(world, location_id, thread)

    world.set_flag("phase12_npc_expanded", True)


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
