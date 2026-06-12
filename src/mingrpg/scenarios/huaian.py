"""Phase 27: New Region — Huai'an (淮安).

The grain transport capital of the Ming dynasty, where the Grand Canal
meets the Huai River. Home to the Grain Transport Governor (漕运总督)
and a major hub controlling northern grain shipments. Adds 3 locations,
3 NPCs, and 1 side thread linking back to Yangzhou investigation lines.
"""
from mingrpg.core.world import World


# ---- Locations ----

HUAIAN_LOCATIONS = [
    {
        "id": "huaian_qingjiangpu",
        "name": "清江浦",
        "type": "outdoor",
        "size": [20, 16],
        "exits": {"north": "huaian_grain_yamen", "east": "huaian_xuanmiao"},
        "tags": ["public", "canal", "commercial"],
        "description": "清江浦是大运河上最繁忙的码头之一,南来北往的漕船在此停靠卸货。码头上脚夫忙碌,货栈林立,茶棚酒肆鳞次栉比。河面上帆樯如林,偶有官船鸣锣开道。",
    },
    {
        "id": "huaian_grain_yamen",
        "name": "漕运总督府",
        "type": "indoor_military",
        "size": [22, 18],
        "exits": {"south": "huaian_qingjiangpu"},
        "tags": ["official", "restricted", "military"],
        "description": "漕运总督府是朝廷设在淮安的最高衙门,掌管天下漕运。府门前石狮雄踞,旗杆高耸。大堂上悬着'天庾正供'匾额,两侧列着漕运文书与运河舆图。总督何大人在此调度各省漕粮北运京师。",
    },
    {
        "id": "huaian_xuanmiao",
        "name": "玄妙观",
        "type": "indoor_religious",
        "size": [14, 12],
        "exits": {"west": "huaian_qingjiangpu"},
        "tags": ["sacred", "quiet", "scenic"],
        "description": "玄妙观是淮安城中最古老的道观,殿宇幽深,古柏参天。观中供奉三清,香火不绝。道长清虚子精通易理,常为往来漕船官员占卜吉凶,对运河上的大小事务了如指掌。",
    },
]

# ---- NPCs ----

HUAIAN_ENTITIES = [
    {
        "id": "grain_governor_he",
        "name": "何总督",
        "type": "npc",
        "location": "huaian_grain_yamen",
        "pos": [11, 9],
        "attributes": {
            "hp": 70, "max_hp": 70,
            "rank": "总督",
            "occupation": "漕运总督",
            "personality": "漕运总督,进士出身,为官清正但深谙官场之道。掌管天下漕运,对漕粮调度与运河治安负有全责。近来对江南商帮借漕运夹带私货之事已有耳闻,但牵涉甚广,不敢轻动。",
            "attack": 8, "defense": 16,
            "money_wen": 500,
            "service_catalog": {
                "cargo_inquiry": {"name": "查询漕运记录", "price_wen": 50},
                "official_letter": {"name": "开具通行文书", "price_wen": 200},
            },
            "memories": [],
            "rumor_hooks": [
                "近来有漕船夹带私盐被查出,何总督正在追查来源",
                "扬州吴员外曾托人向总督府行贿,被何总督严词拒绝",
                "朝廷对江南漕运腐败已有风声,何总督压力很大",
            ],
            "schedule": {
                "卯时": {"location": "huaian_grain_yamen", "pos": [11, 9], "activity": "在大堂处理漕运文书"},
                "巳时": {"location": "huaian_qingjiangpu", "pos": [10, 8], "activity": "去码头巡视漕船到港"},
                "午时": {"location": "huaian_grain_yamen", "pos": [15, 12], "activity": "在内堂接见属官"},
                "酉时": {"location": "huaian_xuanmiao", "pos": [7, 6], "activity": "去玄妙观散步散心"},
            },
            "dialogue_lines": {
                "greetings": [
                    {"text": "（抬头）何人求见?有何事?", "min_attitude": -100, "max_attitude": -10},
                    {"text": "哦,是你。坐吧,本官今日得闲。", "min_attitude": -10, "max_attitude": 30},
                    {"text": "（微笑）公子来了?来人,看茶。", "min_attitude": 30, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "grain_transport", "label": "漕运调度", "unlock_attitude": -50, "lines": [
                        {"text": "天下漕粮北运京师,本官掌管调度。各省漕船何时到港、何时放行,都在本官案头。", "min_attitude": -50, "max_attitude": 20},
                        {"text": "（叹气）近来有漕船夹带私盐被查出,本官正在追查来源。牵涉甚广,不敢轻动。", "min_attitude": 20, "max_attitude": 60},
                    ]},
                    {"id": "corruption", "label": "商帮暗流", "unlock_attitude": 40, "lines": [
                        {"text": "（压低声音）扬州吴员外曾托人向本官行贿,被本官严词拒绝。但他的势力……不容小觑。", "min_attitude": 40, "max_attitude": 80},
                        {"text": "（正色）朝廷对江南漕运腐败已有风声。你若真有证据,本官自当秉公办理。", "min_attitude": 80, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "去吧。本官还有公务要处理。", "min_attitude": -100, "max_attitude": 0},
                    {"text": "慢走。若有什么消息,随时来报。", "min_attitude": 0, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（审视）你从扬州来?……嗯,本官知道了。有何事,说吧。"},
                    {"trigger": "high_attitude", "text": "（左右无人时低语）你若真想查漕运的事……去清江浦找赵牙人,他知道的比本官多。", "min_attitude": 60},
                ],
            },
            "observable_details": [
                "案上堆着厚厚的漕运文书,有几份用红笔批了'严查'",
                "腰间挂着一枚御赐玉佩,据说是万历皇帝亲赐",
            ],
        },
        "status_effects": [],
        "inventory": [
            {"id": "grain_seal", "name": "漕运总督印", "qty": 1},
            {"id": "secret_memorial", "name": "密折草稿", "qty": 1},
        ],
        "tags": ["official", "governor", "investigation_ally"],
    },
    {
        "id": "canal_broker_zhao",
        "name": "赵牙人",
        "type": "npc",
        "location": "huaian_qingjiangpu",
        "pos": [14, 10],
        "attributes": {
            "hp": 45, "max_hp": 45,
            "rank": "平民",
            "occupation": "运河牙人",
            "personality": "清江浦最大的牙人,替南来北往的船主撮合生意,从中抽成。八面玲珑,消息灵通,但唯利是图,谁出价高就替谁办事。暗中也替扬州方面牵线搭桥。",
            "attack": 3, "defense": 9,
            "money_wen": 200,
            "price_list": {"market_info": 15, "ship_arrangement": 40},
            "service_catalog": {
                "find_cargo_ship": {"name": "找货船", "price_wen": 40},
                "market_intel": {"name": "打听商情", "price_wen": 15},
            },
            "memories": [],
            "rumor_hooks": [
                "最近有几条扬州来的船不走官码头,半夜在芦苇荡卸货",
                "有个扬州豪商的管事常来找他安排暗舱运输",
                "漕运总督府的文书最近查得紧,他有些慌了",
            ],
            "schedule": {
                "辰时": {"location": "huaian_qingjiangpu", "pos": [14, 10], "activity": "在码头等船靠岸揽生意"},
                "巳时": {"location": "huaian_qingjiangpu", "pos": [8, 6], "activity": "在茶棚与船主谈生意"},
                "午时": {"location": "huaian_qingjiangpu", "pos": [16, 12], "activity": "在货栈验货点数"},
                "申时": {"location": "huaian_xuanmiao", "pos": [10, 8], "activity": "去道观找道长算卦"},
            },
            "dialogue_lines": {
                "greetings": [
                    {"text": "（上下打量）你要找船还是打听消息?", "min_attitude": -100, "max_attitude": -10},
                    {"text": "哟,是你。来,坐,喝碗茶。", "min_attitude": -10, "max_attitude": 30},
                    {"text": "（热情）公子来了!快请坐,今天有好几条船到港。", "min_attitude": 30, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "canal_traffic", "label": "码头动向", "unlock_attitude": -50, "lines": [
                        {"text": "清江浦是大运河上最繁忙的码头,南来北往的漕船都在此停靠。谁的货走哪条路,我多少知道一些。", "min_attitude": -50, "max_attitude": 20},
                        {"text": "（压低声音）最近有几条扬州来的船不走官码头,半夜在芦苇荡卸货。", "min_attitude": 20, "max_attitude": 60},
                    ]},
                    {"id": "smuggling", "label": "暗中勾当", "unlock_attitude": 40, "lines": [
                        {"text": "有个扬州豪商的管事常来找我安排暗舱运输。给的钱不少,但风险也大。", "min_attitude": 40, "max_attitude": 70},
                        {"text": "（四下看看）漕运总督府的文书最近查得紧,我有些慌了。你若要查,小心为上。", "min_attitude": 70, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "慢走。要找船随时来。", "min_attitude": -100, "max_attitude": 0},
                    {"text": "走好。有什么需要,随时来找我。", "min_attitude": 0, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（打量）新面孔。从哪来?要找什么船?"},
                    {"trigger": "high_attitude", "text": "（神秘地）你要是真想查暗舱的事……半夜去芦苇荡看看,会有收获的。", "min_attitude": 70},
                ],
            },
            "observable_details": [
                "左手无名指缺了一截,据说是年轻时做黑生意被人砍的",
                "袖中藏着一本小册子,记着各路船主的行船习惯",
            ],
        },
        "status_effects": [],
        "inventory": [
            {"id": "broker_ledger", "name": "牙人账册", "qty": 1},
            {"id": "cargo_manifest", "name": "过货清单", "qty": 3},
        ],
        "tags": ["commoner", "merchant", "informant"],
    },
    {
        "id": "daoist_qingxu",
        "name": "清虚子",
        "type": "npc",
        "location": "huaian_xuanmiao",
        "pos": [7, 6],
        "attributes": {
            "hp": 35, "max_hp": 35,
            "rank": "道长",
            "occupation": "玄妙观住持",
            "personality": "玄妙观住持,精通易理与风水,常为漕运官员占卜吉凶。表面上是出家人,实则对运河上下的政商关系了如指掌。与何总督有私交,偶尔为其指点迷津。",
            "attack": 2, "defense": 10,
            "money_wen": 100,
            "memories": [],
            "rumor_hooks": [
                "何总督最近常来观里,说是求个心安",
                "运河上有些船挂着漕运旗号,实则运的是私货",
                "扬州方向来的消息说,有个书生在查一桩大案",
            ],
            "schedule": {
                "寅时": {"location": "huaian_xuanmiao", "pos": [5, 4], "activity": "在丹房打坐修炼"},
                "卯时": {"location": "huaian_xuanmiao", "pos": [10, 10], "activity": "在三清殿早课"},
                "巳时": {"location": "huaian_xuanmiao", "pos": [7, 6], "activity": "在偏殿为香客解签"},
                "酉时": {"location": "huaian_qingjiangpu", "pos": [6, 4], "activity": "去码头散步观河"},
            },
            "dialogue_lines": {
                "greetings": [
                    {"text": "（捻须）施主求签还是问卦?", "min_attitude": -100, "max_attitude": -10},
                    {"text": "（微笑）施主又来了。请坐,老道刚泡了壶好茶。", "min_attitude": -10, "max_attitude": 30},
                    {"text": "（起身相迎）施主来得正好。今日卦象不错,施主有福。", "min_attitude": 30, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "canal_affairs", "label": "运河之事", "unlock_attitude": -50, "lines": [
                        {"text": "老道在这玄妙观住了三十年,运河上下的事,多少知道一些。", "min_attitude": -50, "max_attitude": 20},
                        {"text": "（叹气）运河上有些船挂着漕运旗号,实则运的是私货。老道看在眼里,却不好说。", "min_attitude": 20, "max_attitude": 60},
                    ]},
                    {"id": "governor_friendship", "label": "何总督", "unlock_attitude": 40, "lines": [
                        {"text": "何总督最近常来观里,说是求个心安。老道与他有私交,偶尔为其指点迷津。", "min_attitude": 40, "max_attitude": 70},
                        {"text": "（低声道）总督大人压力很大。朝廷对江南漕运腐败已有风声。你若要查,他可以是盟友。", "min_attitude": 70, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "施主慢走。道观常开,有空再来。", "min_attitude": -100, "max_attitude": 0},
                    {"text": "施主走好。愿施主逢凶化吉。", "min_attitude": 0, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（上下打量）施主面生。远道而来,可是有心事?"},
                    {"trigger": "high_attitude", "text": "（低声道）施主要查的事……老道略知一二。扬州方向来的消息说,有个书生在查一桩大案。", "min_attitude": 70},
                ],
            },
            "observable_details": [
                "手持一柄拂尘,据说是龙虎山张天师所赠",
                "殿中挂着一幅运河舆图,上面标注着各处漕运关卡",
            ],
        },
        "status_effects": [],
        "inventory": [
            {"id": "divination_sticks", "name": "签筒", "qty": 1},
            {"id": "canal_map", "name": "运河舆图", "qty": 1},
        ],
        "tags": ["religious", "scholar", "informant"],
    },
]

# ---- Side thread ----

HUAIAN_SIDE_THREADS = [
    {
        "id": "huaian_grain_corruption",
        "title": "漕运暗流",
        "hook": "何总督说近来有漕船夹带私盐被查出,正在追查来源。赵牙人说有扬州来的船不走官码头,半夜在芦苇荡卸货。清虚子说运河上有些船挂着漕运旗号,实则运的是私货。",
        "anchors": [
            {"location": "huaian_grain_yamen"},
            {"location": "huaian_qingjiangpu"},
            {"entity": "grain_governor_he"},
            {"entity": "canal_broker_zhao"},
            {"entity": "daoist_qingxu"},
            {"entity": "merchant_wu"},
        ],
        "stakes": "淮安是漕运枢纽,吴员外的私货北运必经此地。追查漕运暗流可揭露私盐走私的完整路线,但漕运总督府势力庞大,牵一发而动全身。",
    },
]


def seed_huaian(world: World) -> None:
    """Seed Huai'an region: 3 locations, 3 NPCs, 1 side thread."""

    # ---- Wire up existing river_dock → huaian_qingjiangpu exit ----
    river_dock = world.get_location("river_dock")
    if river_dock:
        river_dock.setdefault("exits", {})["north_huaian"] = "huaian_qingjiangpu"
        world.save_location(river_dock)

    # ---- Save new locations ----
    for loc in HUAIAN_LOCATIONS:
        world.save_location(loc)

    # ---- Save new NPCs ----
    for entity in HUAIAN_ENTITIES:
        world.save_entity(entity)

    # ---- Merge evolution registry ----
    registry = world.get_flag("evolution_registry") or []
    existing_ids = {e["entity_id"] for e in registry}
    new_entries = [
        {"entity_id": "grain_governor_he", "frequency": "every_4_turns",
         "last_evolved_turn": 0, "reason": "漕运总督,掌管天下漕运与运河治安"},
        {"entity_id": "canal_broker_zhao", "frequency": "every_3_turns",
         "last_evolved_turn": 0, "reason": "运河牙人,知晓私货运调动向"},
        {"entity_id": "daoist_qingxu", "frequency": "every_6_turns",
         "last_evolved_turn": 0, "reason": "道观住持,与官场有往来,消息灵通"},
    ]
    for entry in new_entries:
        if entry["entity_id"] not in existing_ids:
            registry.append(entry)
    world.set_flag("evolution_registry", registry)

    # ---- Attach side thread to story seeds ----
    seeds = world.get_flag("story_seeds")
    if seeds:
        existing_thread_ids = {t["id"] for t in seeds.get("side_threads", [])}
        for thread in HUAIAN_SIDE_THREADS:
            if thread["id"] not in existing_thread_ids:
                seeds["side_threads"].append(thread)
        world.set_flag("story_seeds", seeds)

    # ---- Attach rumor hooks from side thread ----
    for thread in HUAIAN_SIDE_THREADS:
        for anchor in thread["anchors"]:
            entity_id = anchor.get("entity")
            if entity_id:
                _append_unique_hook(world, entity_id, thread["hook"])
            location_id = anchor.get("location")
            if location_id:
                _append_location_thread(world, location_id, thread)

    world.set_flag("huaian_seeded", True)


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
