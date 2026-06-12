"""Phase 29: New Region — Xuzhou (徐州).

The "Thoroughfare of Five Provinces" (五省通衢), a strategic military and
commercial crossroads where the Grand Canal meets major north-south land
routes. Known for its iron and coal industries, and as a key garrison
town guarding the northern approach to Jiangnan. Adds 3 locations,
3 NPCs, and 1 side thread linking back to Yangzhou investigation lines.
"""
from mingrpg.core.world import World


# ---- Locations ----

XUZHOU_LOCATIONS = [
    {
        "id": "xuzhou_city_gate",
        "name": "徐州城门",
        "type": "outdoor",
        "size": [20, 16],
        "exits": {"north": "xuzhou_yamen", "east": "xuzhou_inn"},
        "tags": ["public", "gate", "travel"],
        "description": "徐州城门巍峨壮观,城楼上旌旗招展。城门外是通往南北的官道,车马络绎不绝。城门旁有守卒盘查过往行人,城根下有几个卖茶水和干粮的小摊。这里是五省通衢的咽喉,南来北往的商旅都要经过此处。",
    },
    {
        "id": "xuzhou_yamen",
        "name": "徐州府衙",
        "type": "indoor_official",
        "size": [22, 18],
        "exits": {"south": "xuzhou_city_gate"},
        "tags": ["official", "restricted", "legal"],
        "description": "徐州府衙是淮北地区最高官署,大堂上悬着'明镜高匾。两侧列着刑具和鸣冤鼓。知府钱大人在此审理案件、处理政务。衙门外有差役值守,堂上文书堆积如山。近来徐州地面不太平,知府大人颇为头疼。",
    },
    {
        "id": "xuzhou_inn",
        "name": "徐州驿站",
        "type": "indoor_commercial",
        "size": [16, 14],
        "exits": {"west": "xuzhou_city_gate"},
        "tags": ["commercial", "lodging", "information"],
        "description": "徐州驿站是官道上最大的客栈,两层木楼,楼下大堂人声鼎沸。南来北往的客商、脚夫、行旅都在此歇脚。掌柜周老五精明能干,对各路消息了如指掌。大堂里常有人谈论各地商情和官场动向。",
    },
]

# ---- NPCs ----

XUZHOU_ENTITIES = [
    {
        "id": "xuzhou_magistrate",
        "name": "钱知府",
        "type": "npc",
        "location": "xuzhou_yamen",
        "pos": [11, 9],
        "attributes": {
            "hp": 60, "max_hp": 60,
            "rank": "知府",
            "occupation": "徐州知府",
            "personality": "徐州知府,进士出身,为官谨慎但魄力不足。徐州地处要冲,各方势力交错,他左右逢源但难以决断。近来收到朝廷密令严查漕运走私,又有地方豪商暗中施压,两头为难。",
            "attack": 6, "defense": 14,
            "dialogue_lines": {
                "greetings": [
                    {"text": "（抬头）何人击鼓?有何冤情?", "min_attitude": -100, "max_attitude": -10},
                    {"text": "哦,是你。坐吧,本官今日心情尚可。", "min_attitude": -10, "max_attitude": 30},
                    {"text": "（微笑）公子来了?来人,看茶。", "min_attitude": 30, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "duty", "label": "朝廷密令", "unlock_attitude": -50, "lines": [
                        {"text": "朝廷确有密令严查漕运走私。本官奉旨行事,绝不姑息。", "min_attitude": -50, "max_attitude": 20},
                        {"text": "（叹气）密令是下了,可徐州这地方……水太深,本官也是左右为难。", "min_attitude": 20, "max_attitude": 60},
                    ]},
                    {"id": "corruption", "label": "官商勾结", "unlock_attitude": 40, "lines": [
                        {"text": "（压低声音）你是聪明人。有些事本官知道,但……证据呢?没有证据,本官也无能为力。", "min_attitude": 40, "max_attitude": 80},
                        {"text": "（正色）若你有真凭实据,本官自当秉公办理。但若是捕风捉影……休怪本官不客气。", "min_attitude": 80, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "去吧。本官还有公务要处理。", "min_attitude": -100, "max_attitude": 0},
                    {"text": "慢走。若有什么消息,随时来报。", "min_attitude": 0, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（审视）你从扬州来?……嗯,本官知道了。有何事,说吧。"},
                    {"trigger": "high_attitude", "text": "（左右无人时低语）你若真想查漕运的事……去问问驿站的周老五,他知道的比本官多。", "min_attitude": 60},
                ],
            },
            "money_wen": 400,
            "service_catalog": {
                "file_complaint": {"name": "递状纸", "price_wen": 30},
                "check_records": {"name": "查阅卷宗", "price_wen": 50},
            },
            "memories": [],
            "rumor_hooks": [
                "朝廷密令严查漕运走私,钱知府压力很大",
                "有扬州来的豪商托人向知府行贿,被他暂时搁置",
                "徐州地面近来不太平,铁器行的生意有些蹊跷",
            ],
            "schedule": {
                "卯时": {"location": "xuzhou_yamen", "pos": [11, 9], "activity": "在大堂处理公务"},
                "巳时": {"location": "xuzhou_yamen", "pos": [15, 12], "activity": "在内堂接见属官"},
                "午时": {"location": "xuzhou_city_gate", "pos": [10, 8], "activity": "去城门巡视防务"},
                "酉时": {"location": "xuzhou_yamen", "pos": [11, 9], "activity": "回内堂歇息"},
            },
            "observable_details": [
                "案上堆着几份用红笔批了'严查'的文书",
                "腰间挂着一枚朝廷颁发的官印,据说是万历皇帝亲赐",
            ],
        },
        "status_effects": [],
        "inventory": [
            {"id": "official_seal", "name": "徐州府印", "qty": 1},
            {"id": "secret_decree", "name": "朝廷密令", "qty": 1},
        ],
        "tags": ["official", "governor", "investigation_ally"],
    },
    {
        "id": "xuzhou_innkeeper",
        "name": "周老五",
        "type": "npc",
        "location": "xuzhou_inn",
        "pos": [8, 7],
        "attributes": {
            "hp": 40, "max_hp": 40,
            "rank": "平民",
            "occupation": "驿站掌柜",
            "personality": "徐州驿站掌柜,在官道上开了二十年客栈,八面玲珑,消息灵通。对南来北往的客商了如指掌,谁的货走哪条路、谁和谁有生意往来,他心里都有一本账。但嘴很紧,不会轻易透露。",
            "attack": 2, "defense": 9,
            "dialogue_lines": {
                "greetings": [
                    {"text": "客官打尖还是住店?", "min_attitude": -100, "max_attitude": -10},
                    {"text": "哟,是你啊。来,坐,给你留了壶好茶。", "min_attitude": -10, "max_attitude": 30},
                    {"text": "（热情）公子来了!快请坐,想听什么消息?", "min_attitude": 30, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "travelers", "label": "南来北往", "unlock_attitude": -50, "lines": [
                        {"text": "徐州这地方,南来北往的人多了去了。谁的货走哪条路,我多少知道一些。", "min_attitude": -50, "max_attitude": 20},
                        {"text": "（压低声音）最近有批扬州来的货,不走官道,半夜从西门进……你懂的。", "min_attitude": 20, "max_attitude": 60},
                    ]},
                    {"id": "iron_trade", "label": "铁器生意", "unlock_attitude": 30, "lines": [
                        {"text": "孙铁商?他最近生意好得很。货源嘛……我不方便说。", "min_attitude": 30, "max_attitude": 70},
                        {"text": "（四下看看）扬州吴员外的管事,每个月都来。每次住三天,走的时候货比来的时候多。", "min_attitude": 70, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "慢走。有空再来。", "min_attitude": -100, "max_attitude": 0},
                    {"text": "走好。有什么想知道的,随时来找我。", "min_attitude": 0, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（打量）新面孔啊。从哪来?……扬州?嗯,最近扬州来的人不少。"},
                    {"trigger": "high_attitude", "text": "（神秘地）你要是真想查铁器的事……半夜去西门看看,会有收获的。", "min_attitude": 70},
                ],
            },
            "money_wen": 250,
            "price_list": {"common_room": 8, "private_room": 15, "meal": 5},
            "service_catalog": {
                "room_night": {"name": "住店一晚", "price_wen": 8},
                "private_room": {"name": "上房一晚", "price_wen": 15},
                "meal": {"name": "一顿饭", "price_wen": 5},
                "news": {"name": "打听消息", "price_wen": 10},
            },
            "memories": [],
            "rumor_hooks": [
                "最近有批扬州来的铁器不走官道,半夜从西门进城",
                "有个扬州豪商的管事常来徐州,每次都在驿站住三天",
                "铁器行的孙老板最近生意突然好了起来,货源却说不清楚",
            ],
            "schedule": {
                "卯时": {"location": "xuzhou_inn", "pos": [8, 7], "activity": "开门迎客"},
                "巳时": {"location": "xuzhou_inn", "pos": [12, 10], "activity": "在大堂招呼客人"},
                "午时": {"location": "xuzhou_city_gate", "pos": [14, 8], "activity": "去城门接客人"},
                "酉时": {"location": "xuzhou_inn", "pos": [8, 7], "activity": "在柜台算账"},
            },
            "observable_details": [
                "左手小指缺了一截,据说是年轻时做黑生意被人砍的",
                "柜台下藏着一本小册子,记着各路客商的行踪习惯",
            ],
        },
        "status_effects": [],
        "inventory": [
            {"id": "guest_book", "name": "住客登记簿", "qty": 1},
            {"id": "abacus", "name": "算盘", "qty": 1},
        ],
        "tags": ["commoner", "merchant", "informant"],
    },
    {
        "id": "xuzhou_iron_merchant",
        "name": "孙铁商",
        "type": "npc",
        "location": "xuzhou_city_gate",
        "pos": [14, 10],
        "attributes": {
            "hp": 55, "max_hp": 55,
            "rank": "商人",
            "occupation": "铁器商人",
            "personality": "徐州最大的铁器商人,经营铁锅、农具、兵器。表面是正经生意人,暗中也做些走私铁器的勾当。与扬州吴员外有生意往来,替他转运铁器北上,避开官府盘查。",
            "attack": 4, "defense": 12,
            "dialogue_lines": {
                "greetings": [
                    {"text": "（警惕）你是……?要买铁器?", "min_attitude": -100, "max_attitude": -10},
                    {"text": "哦,是你。来,看看新到的货。", "min_attitude": -10, "max_attitude": 30},
                    {"text": "（热情）公子来了!快请坐,喝杯茶。", "min_attitude": 30, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "legitimate", "label": "正经生意", "unlock_attitude": -50, "lines": [
                        {"text": "我孙某人做的都是正经生意。铁锅、农具、菜刀,童叟无欺。", "min_attitude": -50, "max_attitude": 20},
                        {"text": "徐州这地方,铁器生意好做。南来北往的客商都要用。", "min_attitude": 0, "max_attitude": 50},
                    ]},
                    {"id": "smuggling", "label": "暗中勾当", "unlock_attitude": 50, "lines": [
                        {"text": "（压低声音）你既然知道……扬州那边的货,确实是我接的。但这是生意,不犯法吧?", "min_attitude": 50, "max_attitude": 80},
                        {"text": "（正色）吴员外的管事每个月来一次。货走西门,半夜进。这是规矩。", "min_attitude": 80, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "慢走。要买铁器随时来。", "min_attitude": -100, "max_attitude": 0},
                    {"text": "走好。有什么需要,随时来找我。", "min_attitude": 0, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（打量）新面孔。要买什么?铁锅还是农具?"},
                    {"trigger": "high_attitude", "text": "（神秘地）你要是真想知道……去问问知府大人,他手里有朝廷的密令。", "min_attitude": 70},
                ],
            },
            "money_wen": 600,
            "price_list": {"iron_pot": 30, "iron_tool": 20, "iron_weapon": 80},
            "service_catalog": {
                "buy_iron": {"name": "购买铁器", "price_wen": 30},
                "custom_order": {"name": "定制铁器", "price_wen": 100},
            },
            "memories": [],
            "rumor_hooks": [
                "最近有批扬州来的生铁不走官道,半夜从西门进城",
                "扬州吴员外的管事常来徐州,每次都在孙铁商的仓库住三天",
                "铁器行的生意突然好了起来,货源却说不清楚",
            ],
            "schedule": {
                "辰时": {"location": "xuzhou_city_gate", "pos": [14, 10], "activity": "在城门附近看货"},
                "巳时": {"location": "xuzhou_city_gate", "pos": [8, 6], "activity": "在茶摊与客商谈生意"},
                "午时": {"location": "xuzhou_inn", "pos": [12, 10], "activity": "在驿站与外地客商吃饭"},
                "申时": {"location": "xuzhou_city_gate", "pos": [14, 10], "activity": "在城门验货点数"},
            },
            "observable_details": [
                "右手虎口有一道旧伤疤,据说是年轻时打铁留下的",
                "腰间挂着一串钥匙,据说是仓库的钥匙",
            ],
        },
        "status_effects": [],
        "inventory": [
            {"id": "iron_samples", "name": "铁器样品", "qty": 3},
            {"id": "trade_ledger", "name": "铁器账册", "qty": 1},
        ],
        "tags": ["merchant", "broker", "informant"],
    },
]

# ---- Side thread ----

XUZHOU_SIDE_THREADS = [
    {
        "id": "xuzhou_iron_route",
        "title": "铁器暗运",
        "hook": "周老五说最近有批扬州来的铁器不走官道,半夜从西门进城。孙铁商说扬州吴员外的管事常来徐州,每次都在他的仓库住三天。钱知府说朝廷密令严查漕运走私,徐州地面近来不太平。",
        "anchors": [
            {"location": "xuzhou_city_gate"},
            {"location": "xuzhou_inn"},
            {"entity": "xuzhou_magistrate"},
            {"entity": "xuzhou_innkeeper"},
            {"entity": "xuzhou_iron_merchant"},
            {"entity": "merchant_wu"},
        ],
        "stakes": "徐州是铁器北运的关键中转站,吴员外的铁器走私路线从此经过。追查铁器暗运可揭露暗网的北方运输线,但徐州势力复杂,知府态度暧昧,轻举妄动可能打草惊蛇。",
    },
]


def seed_xuzhou(world: World) -> None:
    """Seed Xuzhou region: 3 locations, 3 NPCs, 1 side thread."""

    # ---- Wire up existing huaian_qingjiangpu → xuzhou_city_gate exit ----
    huaian_qingjiangpu = world.get_location("huaian_qingjiangpu")
    if huaian_qingjiangpu:
        huaian_qingjiangpu.setdefault("exits", {})["west_xuzhou"] = "xuzhou_city_gate"
        world.save_location(huaian_qingjiangpu)

    # ---- Save new locations ----
    for loc in XUZHOU_LOCATIONS:
        world.save_location(loc)

    # ---- Save new NPCs ----
    for entity in XUZHOU_ENTITIES:
        world.save_entity(entity)

    # ---- Merge evolution registry ----
    registry = world.get_flag("evolution_registry") or []
    existing_ids = {e["entity_id"] for e in registry}
    new_entries = [
        {"entity_id": "xuzhou_magistrate", "frequency": "every_4_turns",
         "last_evolved_turn": 0, "reason": "徐州知府,掌握朝廷密令与地方势力平衡"},
        {"entity_id": "xuzhou_innkeeper", "frequency": "every_3_turns",
         "last_evolved_turn": 0, "reason": "驿站掌柜,知晓各路客商行踪"},
        {"entity_id": "xuzhou_iron_merchant", "frequency": "every_2_turns",
         "last_evolved_turn": 0, "reason": "铁器商人,与吴员外有生意往来,掌握北方运输线"},
    ]
    for entry in new_entries:
        if entry["entity_id"] not in existing_ids:
            registry.append(entry)
    world.set_flag("evolution_registry", registry)

    # ---- Attach side thread to story seeds ----
    seeds = world.get_flag("story_seeds")
    if seeds:
        existing_thread_ids = {t["id"] for t in seeds.get("side_threads", [])}
        for thread in XUZHOU_SIDE_THREADS:
            if thread["id"] not in existing_thread_ids:
                seeds["side_threads"].append(thread)
        world.set_flag("story_seeds", seeds)

    # ---- Attach rumor hooks from side thread ----
    for thread in XUZHOU_SIDE_THREADS:
        for anchor in thread["anchors"]:
            entity_id = anchor.get("entity")
            if entity_id:
                _append_unique_hook(world, entity_id, thread["hook"])
            location_id = anchor.get("location")
            if location_id:
                _append_location_thread(world, location_id, thread)

    world.set_flag("xuzhou_seeded", True)


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
