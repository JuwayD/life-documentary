"""Phase 21: New Region — Suzhou (苏州).

The Venice of the East — a city of canals, silk, and literati culture.
Connected to Yangzhou via the Grand Canal. Adds 3 locations, 3 NPCs,
and 1 side thread linking back to Yangzhou storylines.
"""
from mingrpg.core.world import World


# ---- Locations ----

SUZHOU_LOCATIONS = [
    {
        "id": "suzhou_silk_market",
        "name": "阊门丝市",
        "type": "outdoor",
        "size": [20, 14],
        "exits": {"east": "suzhou_garden", "south": "suzhou_canal_bridge"},
        "tags": ["public", "commercial", "silk"],
        "description": "阊门内外是苏州最繁华的丝市,绸缎庄、绣坊、染行鳞次栉比。南来北往的客商在此议价,空气中弥漫着蚕丝的清香。",
    },
    {
        "id": "suzhou_garden",
        "name": "拙政园",
        "type": "outdoor",
        "size": [24, 18],
        "exits": {"west": "suzhou_silk_market"},
        "tags": ["quiet", "academic", "noble"],
        "description": "园中假山池沼、亭台楼阁错落有致,回廊曲折通幽。园主致仕归隐,常邀文人雅集。池中锦鲤悠游,竹影婆娑。",
    },
    {
        "id": "suzhou_canal_bridge",
        "name": "枫桥",
        "type": "outdoor",
        "size": [16, 12],
        "exits": {"north": "suzhou_silk_market", "north_canal": "river_dock"},
        "tags": ["public", "dock", "travel"],
        "description": "枫桥横跨运河,桥下舟船往来不绝。桥畔有寒山寺钟声隐隐传来,是南北水路的咽喉要道。",
    },
]

# ---- NPCs ----

SUZHOU_ENTITIES = [
    {
        "id": "silk_merchant_qian",
        "name": "钱掌柜",
        "type": "npc",
        "location": "suzhou_silk_market",
        "pos": [12, 7],
        "attributes": {
            "hp": 50, "max_hp": 50,
            "rank": "商人",
            "occupation": "丝绸商人",
            "personality": "苏州最大的绸缎庄'锦绣坊'掌柜,精明老练,与江南各地商帮都有往来,消息极为灵通",
            "attack": 2, "defense": 10,
            "money_wen": 800,
            "price_list": {"silk_bolt": 120, "silk_thread": 30, "rumor": 15},
            "service_catalog": {
                "trade_info": {"name": "商路消息", "price_wen": 15},
                "introduce_trader": {"name": "引见商帮", "price_wen": 50},
            },
            "memories": [],
            "rumor_hooks": [
                "扬州的绸缎生意最近被一个姓吴的垄断了",
                "南京科场的事牵扯到不少商帮",
                "朝廷要查江南丝税,好几家大商号都在暗中转移货物",
            ],
            "schedule": {
                "卯时": {"location": "suzhou_silk_market", "pos": [12, 7], "activity": "在锦绣坊开门查账"},
                "巳时": {"location": "suzhou_silk_market", "pos": [16, 10], "activity": "在丝市巡视货品"},
                "午时": {"location": "suzhou_garden", "pos": [10, 8], "activity": "去拙政园赴文人雅集"},
                "酉时": {"location": "suzhou_silk_market", "pos": [12, 7], "activity": "回锦绣坊清点货物"},
            },
            "dialogue_lines": {
                "greetings": [
                    {"text": "（抬头看了一眼）客官要买丝绸?", "min_attitude": -100, "max_attitude": -10},
                    {"text": "哟,是你。来,看看新到的苏绣。", "min_attitude": -10, "max_attitude": 30},
                    {"text": "（热情相迎）公子来了!快请坐,上茶。", "min_attitude": 30, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "silk_trade", "label": "丝绸生意", "unlock_attitude": -50, "lines": [
                        {"text": "苏州丝绸甲天下,我锦绣坊的货,从杭州到扬州,哪家商号不认?", "min_attitude": -50, "max_attitude": 20},
                        {"text": "（压低声音）最近丝路不太平,有官府的人在查。好几家都在暗中转移货物。", "min_attitude": 20, "max_attitude": 60},
                    ]},
                    {"id": "yangzhou_connection", "label": "扬州商帮", "unlock_attitude": 30, "lines": [
                        {"text": "扬州那个姓吴的?他垄断了绸缎生意,苏州这边也被他挤得厉害。", "min_attitude": 30, "max_attitude": 70},
                        {"text": "（四下看看）吴员外在苏州有人。谁?……我不好说。但他的货常走暗舱,冯船家知道。", "min_attitude": 70, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "慢走。要买丝绸随时来。", "min_attitude": -100, "max_attitude": 0},
                    {"text": "走好。有什么需要,随时来找我。", "min_attitude": 0, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（打量）新面孔。从哪来?……扬州?嗯,最近扬州来的人不少。"},
                    {"trigger": "high_attitude", "text": "（神秘地）你要是真想查丝税的事……去枫桥找冯船家,他知道暗舱的规矩。", "min_attitude": 60},
                ],
            },
            "observable_details": [
                "手指修长白皙,指甲修剪得极为整齐",
                "腰间挂着一把精致的折扇,扇骨是象牙所制",
            ],
        },
        "status_effects": [],
        "inventory": [
            {"id": "silk_samples", "name": "上等丝绸样品", "qty": 3},
            {"id": "trade_ledger", "name": "商路账簿", "qty": 1},
        ],
        "tags": ["merchant", "informant", "broker"],
    },
    {
        "id": "garden_keeper_shen",
        "name": "沈园丁",
        "type": "npc",
        "location": "suzhou_garden",
        "pos": [6, 10],
        "attributes": {
            "hp": 45, "max_hp": 45,
            "rank": "平民",
            "occupation": "园丁",
            "personality": "拙政园老园丁,服侍过三代园主,为人忠厚寡言,但对园中来客了如指掌",
            "attack": 2, "defense": 8,
            "money_wen": 40,
            "memories": [],
            "rumor_hooks": [
                "园主最近常接待从南京来的贵客",
                "有个扬州来的书生曾在园中借住",
                "园中假山下藏着一间密室,只有园主有钥匙",
            ],
            "schedule": {
                "卯时": {"location": "suzhou_garden", "pos": [4, 6], "activity": "在园中修剪花木"},
                "巳时": {"location": "suzhou_garden", "pos": [12, 12], "activity": "打理池塘锦鲤"},
                "午时": {"location": "suzhou_garden", "pos": [6, 10], "activity": "在园中小亭歇息吃饭"},
                "申时": {"location": "suzhou_silk_market", "pos": [8, 6], "activity": "去丝市买花种"},
            },
            "dialogue_lines": {
                "greetings": [
                    {"text": "（停下手中的活）你是……来逛园子的?", "min_attitude": -100, "max_attitude": -10},
                    {"text": "哦,是你。园子里今天清静,随便逛。", "min_attitude": -10, "max_attitude": 30},
                    {"text": "（微笑）公子来了。今日花开得好,我带你看看。", "min_attitude": 30, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "garden_visitors", "label": "园中来客", "unlock_attitude": -50, "lines": [
                        {"text": "园主致仕归隐,平时不怎么见客。不过最近常有南京来的贵客。", "min_attitude": -50, "max_attitude": 20},
                        {"text": "（压低声音）前阵子有个扬州来的书生,在园中借住了几天。后来不知去向。", "min_attitude": 20, "max_attitude": 60},
                    ]},
                    {"id": "secret_room", "label": "假山密室", "unlock_attitude": 50, "lines": [
                        {"text": "（犹豫）园中假山下……确实有间密室。只有园主有钥匙。", "min_attitude": 50, "max_attitude": 80},
                        {"text": "（四下看看）我这串钥匙里没有那一把。园主从不让人靠近那地方。", "min_attitude": 80, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "慢走。园子里的路不好走,当心脚下。", "min_attitude": -100, "max_attitude": 0},
                    {"text": "走好。想来看花,随时来。", "min_attitude": 0, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（上下打量）新面孔。这园子不常有外人来。你是来找人的?"},
                    {"trigger": "high_attitude", "text": "（神秘地）你要是真想知道密室的事……等园主出门的时候,我带你去看看。", "min_attitude": 70},
                ],
            },
            "observable_details": [
                "双手布满老茧和泥土,指甲缝里嵌着青苔",
                "腰间别着一串铜钥匙,走起来叮当作响",
            ],
        },
        "status_effects": [],
        "inventory": [
            {"id": "garden_keys", "name": "园门钥匙", "qty": 1},
            {"id": "flower_seeds", "name": "花种", "qty": 5},
        ],
        "tags": ["commoner", "informant", "servant"],
    },
    {
        "id": "canal_boatman_feng",
        "name": "冯船家",
        "type": "npc",
        "location": "suzhou_canal_bridge",
        "pos": [8, 6],
        "attributes": {
            "hp": 55, "max_hp": 55,
            "rank": "平民",
            "occupation": "运河船夫",
            "personality": "在运河上跑了二十年的老船夫,熟悉每一条水路,嘴碎但心善",
            "attack": 3, "defense": 9,
            "money_wen": 60,
            "price_list": {"canal_trip": 8, "night_trip": 20},
            "service_catalog": {
                "ride_to_yangzhou": {"name": "搭船去扬州", "price_wen": 8},
                "night_ride": {"name": "夜间行船", "price_wen": 20},
                "smuggle_ride": {"name": "暗舱搭船", "price_wen": 50},
            },
            "memories": [],
            "rumor_hooks": [
                "最近有船半夜从扬州方向过来,不走正道",
                "运河上查私盐的官兵越来越多了",
                "有个扬州豪商的货常走暗舱,给的钱不少",
            ],
            "schedule": {
                "卯时": {"location": "suzhou_canal_bridge", "pos": [8, 6], "activity": "在桥下系缆等客"},
                "辰时": {"location": "suzhou_canal_bridge", "pos": [12, 8], "activity": "载客往返"},
                "午时": {"location": "suzhou_silk_market", "pos": [6, 4], "activity": "去丝市旁的面摊吃饭"},
                "酉时": {"location": "suzhou_canal_bridge", "pos": [8, 6], "activity": "收船歇息"},
            },
            "dialogue_lines": {
                "greetings": [
                    {"text": "（吐出一口烟）要搭船?", "min_attitude": -100, "max_attitude": -10},
                    {"text": "哟,是你。来,坐,抽袋烟。", "min_attitude": -10, "max_attitude": 30},
                    {"text": "（热情）公子来了!快上船,今天水路顺当。", "min_attitude": 30, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "night_boats", "label": "夜半船声", "unlock_attitude": -50, "lines": [
                        {"text": "最近有船半夜从扬州方向过来,不走正道。我在这条河上二十年,什么船声没听过。", "min_attitude": -50, "max_attitude": 20},
                        {"text": "（压低声音）那些船走暗舱,不点灯,靠岸也不走码头。给的钱不少,但我不接。", "min_attitude": 20, "max_attitude": 60},
                    ]},
                    {"id": "canal_patrol", "label": "运河官兵", "unlock_attitude": 20, "lines": [
                        {"text": "运河上查私盐的官兵越来越多了。前几天还上了一条船搜。", "min_attitude": 20, "max_attitude": 60},
                        {"text": "（神秘地）有个扬州豪商的货常走暗舱。谁?我不敢说。但苏州这边有人接应。", "min_attitude": 60, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "慢走。要搭船随时来。", "min_attitude": -100, "max_attitude": 0},
                    {"text": "走好。有什么需要,水上传个话就行。", "min_attitude": 0, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（打量）新面孔。从哪来?要搭船去哪?"},
                    {"trigger": "high_attitude", "text": "（神秘地）你要是真想查暗舱的事……半夜来枫桥下等着,会看到不该看到的船。", "min_attitude": 70},
                ],
            },
            "observable_details": [
                "小腿上有一道长长的疤痕,据说是被船篙上的铁钩划的",
                "随身带着一根烟杆,烟丝里掺了薄荷",
            ],
        },
        "status_effects": [],
        "inventory": [
            {"id": "canal_boat", "name": "运河乌篷船", "qty": 1},
            {"id": "waterproof_cloth", "name": "油布", "qty": 2},
        ],
        "tags": ["commoner", "ferryman", "informant"],
    },
]

# ---- Side thread ----

SUZHOU_SIDE_THREADS = [
    {
        "id": "suzhou_silk_conspiracy",
        "title": "丝税暗流",
        "hook": "钱掌柜说朝廷要查江南丝税,好几家大商号在暗中转移货物。冯船家说最近常有船半夜从扬州方向过来走暗舱。扬州那个姓吴的豪商,在苏州也有人脉。",
        "anchors": [
            {"location": "suzhou_silk_market"},
            {"location": "suzhou_canal_bridge"},
            {"entity": "silk_merchant_qian"},
            {"entity": "canal_boatman_feng"},
            {"entity": "merchant_wu"},
        ],
        "stakes": "丝税调查可揭露扬州吴员外在苏州的商业网络,与盐税走私互为印证。但苏州商帮势力庞大,轻举妄动可能招致报复。",
    },
]


def seed_suzhou(world: World) -> None:
    """Seed Suzhou region: 3 locations, 3 NPCs, 1 side thread."""

    # ---- Wire up existing river_dock → suzhou_canal_bridge exit ----
    river_dock = world.get_location("river_dock")
    if river_dock:
        river_dock.setdefault("exits", {})["south_suzhou"] = "suzhou_canal_bridge"
        world.save_location(river_dock)

    # ---- Save new locations ----
    for loc in SUZHOU_LOCATIONS:
        world.save_location(loc)

    # ---- Save new NPCs ----
    for entity in SUZHOU_ENTITIES:
        world.save_entity(entity)

    # ---- Merge evolution registry ----
    registry = world.get_flag("evolution_registry") or []
    existing_ids = {e["entity_id"] for e in registry}
    new_entries = [
        {"entity_id": "silk_merchant_qian", "frequency": "every_3_turns",
         "last_evolved_turn": 0, "reason": "丝绸商人,掌握商路消息与商帮动态"},
        {"entity_id": "garden_keeper_shen", "frequency": "every_5_turns",
         "last_evolved_turn": 0, "reason": "园丁,知晓园中来客"},
        {"entity_id": "canal_boatman_feng", "frequency": "every_4_turns",
         "last_evolved_turn": 0, "reason": "运河船夫,掌握水路动向"},
    ]
    for entry in new_entries:
        if entry["entity_id"] not in existing_ids:
            registry.append(entry)
    world.set_flag("evolution_registry", registry)

    # ---- Attach side thread to story seeds ----
    seeds = world.get_flag("story_seeds")
    if seeds:
        existing_thread_ids = {t["id"] for t in seeds.get("side_threads", [])}
        for thread in SUZHOU_SIDE_THREADS:
            if thread["id"] not in existing_thread_ids:
                seeds["side_threads"].append(thread)
        world.set_flag("story_seeds", seeds)

    # ---- Attach rumor hooks from side thread ----
    for thread in SUZHOU_SIDE_THREADS:
        for anchor in thread["anchors"]:
            entity_id = anchor.get("entity")
            if entity_id:
                _append_unique_hook(world, entity_id, thread["hook"])
            location_id = anchor.get("location")
            if location_id:
                _append_location_thread(world, location_id, thread)

    world.set_flag("suzhou_seeded", True)


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
