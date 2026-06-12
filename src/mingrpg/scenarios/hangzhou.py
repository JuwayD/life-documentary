"""Phase 22: New Region — Hangzhou (杭州).

Paradise on Earth — a city of West Lake, Longjing tea, and Buddhist temples.
Connected to Suzhou via the Grand Canal. Adds 3 locations, 3 NPCs,
and 1 side thread linking back to Suzhou and Yangzhou storylines.
"""
from mingrpg.core.world import World


# ---- Locations ----

HANGZHOU_LOCATIONS = [
    {
        "id": "hangzhou_west_lake",
        "name": "西湖",
        "type": "outdoor",
        "size": [24, 18],
        "exits": {"west": "hangzhou_canal_dock", "south": "hangzhou_lingyin_temple"},
        "tags": ["public", "scenic", "tea"],
        "description": "西湖十景尽收眼底,苏堤春晓、断桥残雪。湖畔茶楼林立,游人如织,丝竹之声不绝于耳。",
    },
    {
        "id": "hangzhou_lingyin_temple",
        "name": "灵隐寺",
        "type": "indoor_religious",
        "size": [20, 16],
        "exits": {"north": "hangzhou_west_lake"},
        "tags": ["quiet", "religious", "academic"],
        "description": "千年古刹,飞来峰下梵音阵阵。寺中藏经阁珍本无数,香客往来不绝,多有达官贵人前来祈福。",
    },
    {
        "id": "hangzhou_canal_dock",
        "name": "拱宸桥码头",
        "type": "outdoor",
        "size": [16, 12],
        "exits": {"east": "hangzhou_west_lake", "north_suzhou": "suzhou_canal_bridge"},
        "tags": ["public", "dock", "travel"],
        "description": "拱宸桥横跨运河,桥下南来北往的货船云集。码头上脚夫忙碌,茶箱货垛堆积如山,是杭州水路的咽喉。",
    },
]

# ---- NPCs ----

HANGZHOU_ENTITIES = [
    {
        "id": "tea_merchant_fang",
        "name": "方掌柜",
        "type": "npc",
        "location": "hangzhou_west_lake",
        "pos": [14, 9],
        "attributes": {
            "hp": 50, "max_hp": 50,
            "rank": "商人",
            "occupation": "茶商",
            "personality": "杭州最大的茶行'清风阁'掌柜,精通龙井品鉴,与江南各地茶帮关系深厚,消息极为灵通",
            "attack": 2, "defense": 10,
            "money_wen": 900,
            "price_list": {"longjing_tea": 60, "tea_cake": 15, "rumor": 12},
            "service_catalog": {
                "trade_info": {"name": "茶路消息", "price_wen": 12},
                "introduce_tea_house": {"name": "引见茶友", "price_wen": 40},
            },
            "memories": [],
            "rumor_hooks": [
                "苏州的钱掌柜说最近丝路上不太平,有官府的人在查",
                "扬州有个姓吴的豪商,暗中在杭州收茶叶走暗舱北上",
                "灵隐寺的明空方丈与朝中大人有旧,常为官员指点迷津",
            ],
            "schedule": {
                "卯时": {"location": "hangzhou_west_lake", "pos": [14, 9], "activity": "在清风阁开门品茶"},
                "巳时": {"location": "hangzhou_west_lake", "pos": [18, 12], "activity": "在湖畔茶田巡视"},
                "午时": {"location": "hangzhou_lingyin_temple", "pos": [10, 8], "activity": "去灵隐寺进香品茗"},
                "酉时": {"location": "hangzhou_west_lake", "pos": [14, 9], "activity": "回清风阁清点茶货"},
            },
            "dialogue_lines": {
                "greetings": [
                    {"text": "（抬眼）客官要品茶?", "min_attitude": -100, "max_attitude": -10},
                    {"text": "哟,是你。来,刚到一批明前龙井。", "min_attitude": -10, "max_attitude": 30},
                    {"text": "（热情）公子来了!快请坐,今日有好茶。", "min_attitude": 30, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "tea_trade", "label": "茶路生意", "unlock_attitude": -50, "lines": [
                        {"text": "杭州龙井甲天下,我清风阁的茶,从苏州到南京,哪家茶楼不认?", "min_attitude": -50, "max_attitude": 20},
                        {"text": "（压低声音）茶路上也不太平。最近运河上查得紧,有茶商的货被扣了。", "min_attitude": 20, "max_attitude": 60},
                    ]},
                    {"id": "wu_connection", "label": "扬州暗线", "unlock_attitude": 40, "lines": [
                        {"text": "扬州那个姓吴的?他在杭州有暗线,常走茶货北上。", "min_attitude": 40, "max_attitude": 70},
                        {"text": "（四下看看）他的货走暗舱,孙船老大接的活。灵隐寺的方丈也知道些事。", "min_attitude": 70, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "慢走。要买茶随时来。", "min_attitude": -100, "max_attitude": 0},
                    {"text": "走好。有什么需要,随时来找我。", "min_attitude": 0, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（打量）新面孔。从哪来?……扬州?嗯,最近扬州来的茶客不少。"},
                    {"trigger": "high_attitude", "text": "（神秘地）你要是真想查暗运的事……去灵隐寺找明空方丈,他与朝中大人有旧。", "min_attitude": 60},
                ],
            },
            "observable_details": [
                "手指间常年浸染茶色,指甲缝里嵌着细碎的茶叶末",
                "腰间挂着一只紫砂小壶,壶身已被茶渍染成深褐色",
            ],
        },
        "status_effects": [],
        "inventory": [
            {"id": "longjing_samples", "name": "明前龙井样品", "qty": 3},
            {"id": "tea_trade_ledger", "name": "茶路账簿", "qty": 1},
        ],
        "tags": ["merchant", "informant", "broker"],
    },
    {
        "id": "abbot_mingkong",
        "name": "明空方丈",
        "type": "npc",
        "location": "hangzhou_lingyin_temple",
        "pos": [10, 8],
        "attributes": {
            "hp": 40, "max_hp": 40,
            "rank": "僧人",
            "occupation": "方丈",
            "personality": "灵隐寺方丈,博学多才,精通佛法与诗文。与杭州官场中人颇有往来,常为士子指点迷津,但从不直接介入俗务",
            "attack": 1, "defense": 8,
            "money_wen": 100,
            "memories": [],
            "rumor_hooks": [
                "南京科场弊案的消息已传到杭州,寺中常有赴考举子来问前程",
                "运河上近来有官兵查私盐,也有茶商的货被扣了",
                "苏州拙政园的园主与寺中长老是故交,常有书信往来",
            ],
            "schedule": {
                "卯时": {"location": "hangzhou_lingyin_temple", "pos": [6, 4], "activity": "在大殿主持早课"},
                "巳时": {"location": "hangzhou_lingyin_temple", "pos": [10, 8], "activity": "在禅房接见香客"},
                "午时": {"location": "hangzhou_lingyin_temple", "pos": [14, 10], "activity": "在藏经阁整理典籍"},
                "申时": {"location": "hangzhou_west_lake", "pos": [8, 6], "activity": "去湖畔散步吟诗"},
            },
            "dialogue_lines": {
                "greetings": [
                    {"text": "（合十）施主有何事?", "min_attitude": -100, "max_attitude": -10},
                    {"text": "（微笑）施主又来了。请坐。", "min_attitude": -10, "max_attitude": 30},
                    {"text": "（起身相迎）施主来得正好,老衲刚泡了壶好茶。", "min_attitude": 30, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "temple_visitors", "label": "寺中来客", "unlock_attitude": -50, "lines": [
                        {"text": "灵隐寺香火旺盛,来烧香的善男信女不少。近来也有不少赴考举子来问前程。", "min_attitude": -50, "max_attitude": 20},
                        {"text": "（叹气）南京科场弊案的消息已传到杭州,寺中常有举子来问前程,老衲也不知如何开解。", "min_attitude": 20, "max_attitude": 60},
                    ]},
                    {"id": "official_connections", "label": "官场往来", "unlock_attitude": 40, "lines": [
                        {"text": "老衲与杭州官场中人有些往来,但从不介入俗务。出家人以清净为本。", "min_attitude": 40, "max_attitude": 70},
                        {"text": "（低声道）施主若要查什么事……老衲可以为施主引见几位故交。但老衲不便出面。", "min_attitude": 70, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "施主慢走。佛门常开,有空再来。", "min_attitude": -100, "max_attitude": 0},
                    {"text": "施主走好。愿施主心想事成。", "min_attitude": 0, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（合十）施主面生。远道而来,可是有心事?"},
                    {"trigger": "high_attitude", "text": "（低声道）施主要查的事……老衲略知一二。朝中有些旧交,或可相助。", "min_attitude": 70},
                ],
            },
            "observable_details": [
                "身披金线袈裟,手持一串沉香木念珠,珠面光滑如镜",
                "目光深邃平和,说话时声音低沉而有力,令人不自觉地安静下来",
            ],
        },
        "status_effects": [],
        "inventory": [
            {"id": "prayer_beads", "name": "沉香木念珠", "qty": 1},
            {"id": "buddhist_scripture", "name": "手抄金刚经", "qty": 1},
        ],
        "tags": ["religious", "informant", "advisor"],
    },
    {
        "id": "canal_captain_sun",
        "name": "孙船老大",
        "type": "npc",
        "location": "hangzhou_canal_dock",
        "pos": [8, 6],
        "attributes": {
            "hp": 60, "max_hp": 60,
            "rank": "平民",
            "occupation": "运河船老大",
            "personality": "在运河上跑了三十年的老船头,手下有三条大船,脾气暴躁但讲义气,黑白两道都有面子",
            "attack": 4, "defense": 11,
            "money_wen": 80,
            "price_list": {"canal_trip": 10, "cargo_trip": 30},
            "service_catalog": {
                "ride_to_suzhou": {"name": "搭船去苏州", "price_wen": 10},
                "cargo_transport": {"name": "运货去苏州", "price_wen": 30},
                "smuggle_ride": {"name": "暗舱搭船", "price_wen": 60},
            },
            "memories": [],
            "rumor_hooks": [
                "扬州那个姓吴的豪商,在杭州也有暗线,常走茶货北上",
                "最近运河上查得紧,官兵上了好几条船搜私盐",
                "苏州枫桥下的冯船家是我老相识,他的消息比我灵通",
            ],
            "schedule": {
                "卯时": {"location": "hangzhou_canal_dock", "pos": [8, 6], "activity": "在码头检查船只"},
                "辰时": {"location": "hangzhou_canal_dock", "pos": [12, 8], "activity": "指挥装卸货物"},
                "午时": {"location": "hangzhou_west_lake", "pos": [6, 4], "activity": "去湖边酒楼吃饭"},
                "酉时": {"location": "hangzhou_canal_dock", "pos": [8, 6], "activity": "收船歇息算账"},
            },
            "dialogue_lines": {
                "greetings": [
                    {"text": "（粗声）要搭船还是运货?", "min_attitude": -100, "max_attitude": -10},
                    {"text": "哟,是你。来,坐,喝碗茶。", "min_attitude": -10, "max_attitude": 30},
                    {"text": "（热情）公子来了!快请坐,今天风好,正适合走船。", "min_attitude": 30, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "canal_traffic", "label": "运河近况", "unlock_attitude": -50, "lines": [
                        {"text": "运河上跑船三十年,什么风浪没见过。最近查得紧,官兵上了好几条船搜私盐。", "min_attitude": -50, "max_attitude": 20},
                        {"text": "（压低声音）有些船不走官道,半夜靠岸。给的钱不少,但风险也大。", "min_attitude": 20, "max_attitude": 60},
                    ]},
                    {"id": "tea_smuggling", "label": "暗舱生意", "unlock_attitude": 40, "lines": [
                        {"text": "扬州那个姓吴的?他在杭州有暗线。茶货走暗舱,我接的活。", "min_attitude": 40, "max_attitude": 70},
                        {"text": "（四下看看）苏州枫桥下的冯船家是我老相识。他的消息比我灵通。你去问问他。", "min_attitude": 70, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "慢走。要搭船随时来。", "min_attitude": -100, "max_attitude": 0},
                    {"text": "走好。有什么需要,水上传个话就行。", "min_attitude": 0, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（打量）新面孔。从哪来?要搭船去哪?"},
                    {"trigger": "high_attitude", "text": "（神秘地）你要是真想查暗舱的事……跟我跑一趟苏州,我带你见冯船家。", "min_attitude": 70},
                ],
            },
            "observable_details": [
                "左耳缺了一角,据说是年轻时与人械斗留下的",
                "腰间别着一把短刀,刀鞘上刻着一条青龙",
            ],
        },
        "status_effects": [],
        "inventory": [
            {"id": "cargo_boat", "name": "运河货船", "qty": 1},
            {"id": "manifest_book", "name": "货运清单", "qty": 1},
        ],
        "tags": ["commoner", "ferryman", "informant"],
    },
]

# ---- Side thread ----

HANGZHOU_SIDE_THREADS = [
    {
        "id": "hangzhou_tea_smuggling",
        "title": "龙井暗运",
        "hook": "方掌柜说扬州有个姓吴的豪商暗中在杭州收茶叶走暗舱北上。孙船老大说运河上查得紧,官兵上了好几条船。苏州枫桥下的冯船家也有消息。明前龙井价值不菲,若与丝税走私案并查,或可揭开吴员外在江南的完整商业网络。",
        "anchors": [
            {"location": "hangzhou_west_lake"},
            {"location": "hangzhou_canal_dock"},
            {"entity": "tea_merchant_fang"},
            {"entity": "canal_captain_sun"},
            {"entity": "merchant_wu"},
        ],
        "stakes": "龙井暗运可揭露吴员外在杭州的茶叶走私线路,与苏州丝税、扬州盐税三线合一。但杭州茶帮势力盘根错节,轻举妄动可能断了线索。",
    },
]


def seed_hangzhou(world: World) -> None:
    """Seed Hangzhou region: 3 locations, 3 NPCs, 1 side thread."""

    # ---- Wire up existing suzhou_canal_bridge → hangzhou_canal_dock exit ----
    suzhou_canal_bridge = world.get_location("suzhou_canal_bridge")
    if suzhou_canal_bridge:
        suzhou_canal_bridge.setdefault("exits", {})["south_hangzhou"] = "hangzhou_canal_dock"
        world.save_location(suzhou_canal_bridge)

    # ---- Save new locations ----
    for loc in HANGZHOU_LOCATIONS:
        world.save_location(loc)

    # ---- Save new NPCs ----
    for entity in HANGZHOU_ENTITIES:
        world.save_entity(entity)

    # ---- Merge evolution registry ----
    registry = world.get_flag("evolution_registry") or []
    existing_ids = {e["entity_id"] for e in registry}
    new_entries = [
        {"entity_id": "tea_merchant_fang", "frequency": "every_3_turns",
         "last_evolved_turn": 0, "reason": "茶商,掌握茶路消息与商帮动态"},
        {"entity_id": "abbot_mingkong", "frequency": "every_5_turns",
         "last_evolved_turn": 0, "reason": "方丈,知晓官场与士林消息"},
        {"entity_id": "canal_captain_sun", "frequency": "every_4_turns",
         "last_evolved_turn": 0, "reason": "运河船老大,掌握水路动向"},
    ]
    for entry in new_entries:
        if entry["entity_id"] not in existing_ids:
            registry.append(entry)
    world.set_flag("evolution_registry", registry)

    # ---- Attach side thread to story seeds ----
    seeds = world.get_flag("story_seeds")
    if seeds:
        existing_thread_ids = {t["id"] for t in seeds.get("side_threads", [])}
        for thread in HANGZHOU_SIDE_THREADS:
            if thread["id"] not in existing_thread_ids:
                seeds["side_threads"].append(thread)
        world.set_flag("story_seeds", seeds)

    # ---- Attach rumor hooks from side thread ----
    for thread in HANGZHOU_SIDE_THREADS:
        for anchor in thread["anchors"]:
            entity_id = anchor.get("entity")
            if entity_id:
                _append_unique_hook(world, entity_id, thread["hook"])
            location_id = anchor.get("location")
            if location_id:
                _append_location_thread(world, location_id, thread)

    world.set_flag("hangzhou_seeded", True)


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
