"""Phase 24: New Region — Zhenjiang (镇江).

A strategic military fortress at the confluence of the Yangtze River
and the Grand Canal. Historically a key garrison town guarding the
river crossing. Adds 3 locations, 3 NPCs, and 1 side thread linking
back to Yangzhou storylines.
"""
from mingrpg.core.world import World


# ---- Locations ----

ZHENJIANG_LOCATIONS = [
    {
        "id": "zhenjiang_xijin",
        "name": "西津渡口",
        "type": "outdoor",
        "size": [18, 14],
        "exits": {"north": "zhenjiang_fortress", "east": "zhenjiang_jinshan"},
        "tags": ["public", "dock", "travel"],
        "description": "西津渡是长江南岸最古老的渡口,石阶上苔痕斑驳。渡口旁有几间茶棚,供等船的旅客歇脚。江面上帆影点点,北岸隐约可见瓜洲。",
    },
    {
        "id": "zhenjiang_fortress",
        "name": "镇江卫所",
        "type": "indoor_military",
        "size": [20, 16],
        "exits": {"south": "zhenjiang_xijin"},
        "tags": ["military", "restricted", "official"],
        "description": "镇江卫所是江南防务重地,门前两尊石狮威严肃穆。所内校场宽阔,军旗猎猎。卫所指挥使掌管三千卫军,拱卫京师南大门。",
    },
    {
        "id": "zhenjiang_jinshan",
        "name": "金山寺",
        "type": "indoor_religious",
        "size": [16, 14],
        "exits": {"west": "zhenjiang_xijin"},
        "tags": ["sacred", "quiet", "scenic"],
        "description": "金山寺依山而建,殿宇层叠,远望如金山浮玉。寺内有法海洞、白龙洞等古迹。住持了凡禅师精通佛法,与江南各大寺庙皆有往来。",
    },
]

# ---- NPCs ----

ZHENJIANG_ENTITIES = [
    {
        "id": "fortress_commander_liu",
        "name": "刘指挥使",
        "type": "npc",
        "location": "zhenjiang_fortress",
        "pos": [10, 8],
        "attributes": {
            "hp": 80, "max_hp": 80,
            "rank": "指挥使",
            "occupation": "镇江卫指挥使",
            "personality": "镇江卫指挥使,武举出身,治军严明,对过往商船盘查甚严,但暗中也收些孝敬银子",
            "attack": 12, "defense": 18,
            "money_wen": 300,
            "price_list": {"military_pass": 50},
            "service_catalog": {
                "military_escort": {"name": "军士护送", "price_wen": 100},
                "check_cargo": {"name": "查验货物", "price_wen": 30},
            },
            "memories": [],
            "rumor_hooks": [
                "最近有批扬州来的货物被扣下了,说是夹带私盐",
                "朝廷要查江南盐税,卫所也接到了密令",
                "有个扬州豪商托人来说情,被他挡回去了",
            ],
            "schedule": {
                "卯时": {"location": "zhenjiang_fortress", "pos": [10, 8], "activity": "在校场点卯操练"},
                "巳时": {"location": "zhenjiang_fortress", "pos": [14, 10], "activity": "在卫所大堂处理军务"},
                "午时": {"location": "zhenjiang_xijin", "pos": [8, 6], "activity": "去渡口巡视防务"},
                "酉时": {"location": "zhenjiang_fortress", "pos": [10, 8], "activity": "回内堂歇息"},
            },
            "dialogue_lines": {
                "greetings": [
                    {"text": "（警惕）你是何人?有何事?", "min_attitude": -100, "max_attitude": -10},
                    {"text": "哦,是你。说吧,什么事。", "min_attitude": -10, "max_attitude": 30},
                    {"text": "（微笑）公子来了。来人,看茶。", "min_attitude": 30, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "military_duty", "label": "卫所防务", "unlock_attitude": -50, "lines": [
                        {"text": "镇江卫所拱卫京师南大门,本官掌管三千卫军。过往商船,本官都要盘查。", "min_attitude": -50, "max_attitude": 20},
                        {"text": "（压低声音）最近有批扬州来的货物被扣下了,说是夹带私盐。本官正在追查。", "min_attitude": 20, "max_attitude": 60},
                    ]},
                    {"id": "seized_cargo", "label": "扣货之事", "unlock_attitude": 40, "lines": [
                        {"text": "（正色）那批货是从扬州来的,半夜到的。里面夹带了私盐,本官依法扣押。", "min_attitude": 40, "max_attitude": 70},
                        {"text": "（左右看看）有个扬州豪商托人来说情,被本官挡回去了。但朝廷的密令……本官也有些为难。", "min_attitude": 70, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "去吧。卫所重地,不可久留。", "min_attitude": -100, "max_attitude": 0},
                    {"text": "慢走。若有什么消息,随时来报。", "min_attitude": 0, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（上下打量）新面孔。从哪来?……扬州?嗯,最近扬州来的人不少。"},
                    {"trigger": "high_attitude", "text": "（左右无人时低语）你若真想查扣货的事……去金山寺找了凡禅师,他知道的比本官多。", "min_attitude": 60},
                ],
            },
            "observable_details": [
                "腰间挂着一柄雁翎刀,刀鞘上刻着'忠勇'二字",
                "右手虎口有一道旧箭疤,据说是当年剿倭寇时留下的",
            ],
        },
        "status_effects": [],
        "inventory": [
            {"id": "military_seal", "name": "卫所印信", "qty": 1},
            {"id": "secret_decree", "name": "密令", "qty": 1},
        ],
        "tags": ["official", "military", "gatekeeper"],
    },
    {
        "id": "jinshan_monk",
        "name": "了凡禅师",
        "type": "npc",
        "location": "zhenjiang_jinshan",
        "pos": [8, 7],
        "attributes": {
            "hp": 40, "max_hp": 40,
            "rank": "僧侣",
            "occupation": "金山寺住持",
            "personality": "金山寺住持,精通佛法,与江南各大寺庙皆有往来,常为达官贵人讲经说法,消息极为灵通",
            "attack": 1, "defense": 12,
            "money_wen": 150,
            "memories": [],
            "rumor_hooks": [
                "扬州法海寺的方丈与他是同门师兄弟",
                "最近有官员来寺里烧香,说是求个心安",
                "听说有个扬州书生在查一桩大案",
            ],
            "schedule": {
                "寅时": {"location": "zhenjiang_jinshan", "pos": [6, 4], "activity": "在禅房打坐"},
                "卯时": {"location": "zhenjiang_jinshan", "pos": [10, 10], "activity": "在大殿早课"},
                "巳时": {"location": "zhenjiang_jinshan", "pos": [8, 7], "activity": "在藏经阁整理典籍"},
                "申时": {"location": "zhenjiang_xijin", "pos": [12, 8], "activity": "去渡口散步"},
            },
            "dialogue_lines": {
                "greetings": [
                    {"text": "（合十）施主有何事?", "min_attitude": -100, "max_attitude": -10},
                    {"text": "（微笑）施主又来了。请坐。", "min_attitude": -10, "max_attitude": 30},
                    {"text": "（起身相迎）施主来得正好,老衲刚泡了壶好茶。", "min_attitude": 30, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "temple_visitors", "label": "寺中来客", "unlock_attitude": -50, "lines": [
                        {"text": "金山寺香火旺盛,来烧香的善男信女不少。近来也有不少官员来烧香。", "min_attitude": -50, "max_attitude": 20},
                        {"text": "（叹气）最近有官员来寺里烧香,说是求个心安。老衲看在眼里,却不好说。", "min_attitude": 20, "max_attitude": 60},
                    ]},
                    {"id": "yangzhou_case", "label": "扬州之事", "unlock_attitude": 40, "lines": [
                        {"text": "扬州法海寺的方丈与老衲是同门师兄弟。他来信说,有个书生在查一桩大案。", "min_attitude": 40, "max_attitude": 70},
                        {"text": "（低声道）施主要查的事……老衲略知一二。卫所扣货的事,与扬州那边有关联。", "min_attitude": 70, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "施主慢走。佛门常开,有空再来。", "min_attitude": -100, "max_attitude": 0},
                    {"text": "施主走好。愿施主心想事成。", "min_attitude": 0, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（合十）施主面生。远道而来,可是有心事?"},
                    {"trigger": "high_attitude", "text": "（低声道）施主要查的事……去渡口找马渡子,他知晓夜间渡船的动向。", "min_attitude": 70},
                ],
            },
            "observable_details": [
                "眉心有一颗朱砂痣,据说是高僧相",
                "念珠是罕见的菩提子,颗颗圆润",
            ],
        },
        "status_effects": [],
        "inventory": [
            {"id": "prayer_beads", "name": "菩提念珠", "qty": 1},
            {"id": "temple_records", "name": "寺中访客录", "qty": 1},
        ],
        "tags": ["religious", "scholar", "informant"],
    },
    {
        "id": "xijin_ferryman",
        "name": "马渡子",
        "type": "npc",
        "location": "zhenjiang_xijin",
        "pos": [10, 6],
        "attributes": {
            "hp": 50, "max_hp": 50,
            "rank": "平民",
            "occupation": "渡夫",
            "personality": "在西津渡摆渡二十年的老渡夫,沉默寡言但观察力极强,对江面上的船只了如指掌",
            "attack": 3, "defense": 9,
            "money_wen": 40,
            "price_list": {"ferry_crossing": 8},
            "service_catalog": {
                "cross_to_guazhou": {"name": "渡江北上", "price_wen": 8},
                "night_crossing": {"name": "夜间渡江", "price_wen": 20},
            },
            "memories": [],
            "rumor_hooks": [
                "最近有船半夜从北岸过来,不走渡口",
                "卫所扣下的那批货,是从扬州来的",
                "有个扬州豪商的货常走夜路",
            ],
            "schedule": {
                "卯时": {"location": "zhenjiang_xijin", "pos": [10, 6], "activity": "解开缆绳准备渡客"},
                "辰时": {"location": "zhenjiang_xijin", "pos": [14, 8], "activity": "在渡口等客"},
                "午时": {"location": "zhenjiang_xijin", "pos": [6, 4], "activity": "在茶棚吃饭"},
                "酉时": {"location": "zhenjiang_xijin", "pos": [10, 6], "activity": "收船系缆"},
            },
            "dialogue_lines": {
                "greetings": [
                    {"text": "（沉默地看了你一眼）要渡江?", "min_attitude": -100, "max_attitude": -10},
                    {"text": "（点头）又是你。今天浪小,走吧。", "min_attitude": -10, "max_attitude": 30},
                    {"text": "（微笑）公子来了。今天风好,正适合渡江。", "min_attitude": 30, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "night_crossings", "label": "夜间渡江", "unlock_attitude": -50, "lines": [
                        {"text": "在西津渡摆渡二十年,江面上的船,我一眼就能认出。最近有船半夜从北岸过来,不走渡口。", "min_attitude": -50, "max_attitude": 20},
                        {"text": "（压低声音）那些船不点灯,靠岸也不走码头。给的钱不少,但我不接。", "min_attitude": 20, "max_attitude": 60},
                    ]},
                    {"id": "seized_goods", "label": "卫所扣货", "unlock_attitude": 30, "lines": [
                        {"text": "卫所扣下的那批货,是从扬州来的。半夜到的,我在渡口看得清楚。", "min_attitude": 30, "max_attitude": 70},
                        {"text": "（神秘地）有个扬州豪商的货常走夜路。谁?我不敢说。但刘指挥使知道。", "min_attitude": 70, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "慢走。要渡江随时来。", "min_attitude": -100, "max_attitude": 0},
                    {"text": "走好。有什么需要,渡口传个话就行。", "min_attitude": 0, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（上下打量）新面孔。从哪来?要渡江去哪?"},
                    {"trigger": "high_attitude", "text": "（神秘地）你要是真想查夜船的事……半夜来渡口等着,会有收获的。", "min_attitude": 70},
                ],
            },
            "observable_details": [
                "手掌满是老茧,指缝间常年发白",
                "腰间挂着一个铜哨,据说是夜间联络暗号",
            ],
        },
        "status_effects": [],
        "inventory": [
            {"id": "ferry_boat", "name": "渡船", "qty": 1},
            {"id": "copper_whistle", "name": "铜哨", "qty": 1},
        ],
        "tags": ["commoner", "ferryman", "informant"],
    },
]

# ---- Side thread ----

ZHENJIANG_SIDE_THREADS = [
    {
        "id": "zhenjiang_seized_cargo",
        "title": "卫所扣货",
        "hook": "刘指挥使说最近有批扬州来的货物被扣下了,说是夹带私盐。马渡子说卫所扣下的那批货是从扬州来的,半夜到的。了凡禅师说最近有官员来寺里烧香,说是求个心安。",
        "anchors": [
            {"location": "zhenjiang_fortress"},
            {"location": "zhenjiang_xijin"},
            {"entity": "fortress_commander_liu"},
            {"entity": "xijin_ferryman"},
            {"entity": "jinshan_monk"},
            {"entity": "merchant_wu"},
        ],
        "stakes": "卫所扣货案是扬州吴员外走私渠道的关键证据。追查此案可揭露'江南暗网'的军事掩护,但卫所势力强大,轻举妄动可能招致杀身之祸。",
    },
]


def seed_zhenjiang(world: World) -> None:
    """Seed Zhenjiang region: 3 locations, 3 NPCs, 1 side thread."""

    # ---- Wire up existing guazhou_ferry → zhenjiang_xijin exit ----
    guazhou_ferry = world.get_location("guazhou_ferry")
    if guazhou_ferry:
        guazhou_ferry.setdefault("exits", {})["south_zhenjiang"] = "zhenjiang_xijin"
        world.save_location(guazhou_ferry)

    # ---- Save new locations ----
    for loc in ZHENJIANG_LOCATIONS:
        world.save_location(loc)

    # ---- Save new NPCs ----
    for entity in ZHENJIANG_ENTITIES:
        world.save_entity(entity)

    # ---- Merge evolution registry ----
    registry = world.get_flag("evolution_registry") or []
    existing_ids = {e["entity_id"] for e in registry}
    new_entries = [
        {"entity_id": "fortress_commander_liu", "frequency": "every_4_turns",
         "last_evolved_turn": 0, "reason": "卫所指挥使,掌握军事防务与扣货信息"},
        {"entity_id": "jinshan_monk", "frequency": "every_6_turns",
         "last_evolved_turn": 0, "reason": "寺中住持,与官场有往来"},
        {"entity_id": "xijin_ferryman", "frequency": "every_3_turns",
         "last_evolved_turn": 0, "reason": "渡夫,知晓夜间渡船动向"},
    ]
    for entry in new_entries:
        if entry["entity_id"] not in existing_ids:
            registry.append(entry)
    world.set_flag("evolution_registry", registry)

    # ---- Attach side thread to story seeds ----
    seeds = world.get_flag("story_seeds")
    if seeds:
        existing_thread_ids = {t["id"] for t in seeds.get("side_threads", [])}
        for thread in ZHENJIANG_SIDE_THREADS:
            if thread["id"] not in existing_thread_ids:
                seeds["side_threads"].append(thread)
        world.set_flag("story_seeds", seeds)

    # ---- Attach rumor hooks from side thread ----
    for thread in ZHENJIANG_SIDE_THREADS:
        for anchor in thread["anchors"]:
            entity_id = anchor.get("entity")
            if entity_id:
                _append_unique_hook(world, entity_id, thread["hook"])
            location_id = anchor.get("location")
            if location_id:
                _append_location_thread(world, location_id, thread)

    world.set_flag("zhenjiang_seeded", True)


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
