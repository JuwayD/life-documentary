"""Phase 36: New Region — Ningbo (宁波).

The great maritime port of Zhejiang, known in earlier dynasties as Mingzhou
(明州). Home to the Tianyi Pavilion (天一阁), China's oldest private library,
and a key node in the coastal trade network despite the sea ban (海禁).
Adds 3 locations, 3 NPCs, and 1 side thread linking back to the Yangzhou
investigation network via Hangzhou.
"""
from mingrpg.core.world import World


# ---- Locations ----

NINGBO_LOCATIONS = [
    {
        "id": "ningbo_dock",
        "name": "宁波码头",
        "type": "outdoor",
        "size": [22, 16],
        "exits": {"north": "ningbo_shipsi", "east": "ningbo_tianyi"},
        "tags": ["public", "dock", "trade"],
        "description": "宁波码头濒临东海,港湾内泊满了渔船和商船。尽管朝廷海禁甚严,但码头上依然繁忙——近海渔船照常出入,暗中更有远洋商船趁夜装卸货物。码头旁有几家鱼行和货栈,空气中弥漫着鱼腥和桐油的气味。几个穿着短打的脚夫正在搬运货箱,箱子上的封条写着'瓷器'二字,但分量显然不止瓷器。",
    },
    {
        "id": "ningbo_shipsi",
        "name": "宁波市舶司",
        "type": "indoor_official",
        "size": [20, 16],
        "exits": {"south": "ningbo_dock"},
        "tags": ["official", "restricted", "trade_control"],
        "description": "宁波市舶司是朝廷设在浙东的海上贸易管理衙门,负责查验进出港口的船只、征收关税、稽查走私。大堂上悬着'奉旨海禁'的匾额,两侧堆着厚厚的船引和货单。陈把总在此坐镇,手下的水师兵丁日夜巡逻港口。但市舶司内部并非铁板一块——有人秉公执法,也有人暗中收银放行。",
    },
    {
        "id": "ningbo_tianyi",
        "name": "天一阁",
        "type": "indoor_cultural",
        "size": [18, 14],
        "exits": {"west": "ningbo_dock"},
        "tags": ["cultural", "library", "private"],
        "description": "天一阁是致仕兵部右侍郎范钦所建的藏书楼,坐落在月湖之畔。阁中藏书七万余卷,尤以地方志和科举录最为齐全。青砖灰瓦,古木参天,院中一池清水映着阁楼倒影。范老先生虽已年迈,但仍每日在此读书会客。阁中常有各地士子慕名前来查阅典籍,也有官场中人来此打探消息——范钦为官多年,对朝中局势了如指掌。",
    },
]

# ---- NPCs ----

NINGBO_ENTITIES = [
    {
        "id": "ningbo_fanqin",
        "name": "范钦",
        "type": "npc",
        "location": "ningbo_tianyi",
        "pos": [9, 7],
        "attributes": {
            "hp": 45, "max_hp": 45,
            "rank": "致仕官员",
            "occupation": "天一阁主人",
            "personality": "致仕兵部右侍郎,嘉靖年间进士,为官三十余年,历任多地。晚年归乡建天一阁藏书楼,闭门谢客,专心校勘古籍。性格沉稳内敛,不轻易表态,但对朝中局势和地方政事洞若观火。与江南官场中人多有书信往来,手中掌握大量地方志和档案。",
            "attack": 3, "defense": 10,
            "dialogue_lines": {
                "greetings": [
                    {"text": "（抬头从书卷中）阁下是……?天一阁不接待闲人。", "min_attitude": -100, "max_attitude": -10},
                    {"text": "哦,是你。坐吧,老夫正好歇歇眼睛。", "min_attitude": -10, "max_attitude": 30},
                    {"text": "（微笑）公子又来了?来人,上茶。今日有何见教?", "min_attitude": 30, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "books", "label": "藏书", "unlock_attitude": -50, "lines": [
                        {"text": "天一阁藏书七万余卷,地方志、科举录、邸报皆有收藏。你想查什么?", "min_attitude": -50, "max_attitude": 20},
                        {"text": "（从架上取下一册）这是万历八年的邸报,上面有些有意思的记载。你看看。", "min_attitude": 20, "max_attitude": 60},
                    ]},
                    {"id": "maritime", "label": "海禁", "unlock_attitude": 30, "lines": [
                        {"text": "海禁是祖制,但沿海百姓靠海吃海,禁是禁不住的。朝廷也是睁一只眼闭一只眼。", "min_attitude": 30, "max_attitude": 70},
                        {"text": "（压低声音）宁波这边的海贸,背后牵扯的人……比你想象的多。扬州那边的绸缎、杭州那边的茶叶,都从这里出海。", "min_attitude": 70, "max_attitude": 100},
                    ]},
                    {"id": "politics", "label": "朝中局势", "unlock_attitude": 60, "lines": [
                        {"text": "张居正推行一条鞭法,朝中反对的人不少。但万历皇帝信任他,暂时还稳得住。", "min_attitude": 60, "max_attitude": 85},
                        {"text": "（叹气）江南的商帮……朝廷不是不知道。只是现在要靠江南的税银,不好大动干戈。但风声越来越紧了。", "min_attitude": 85, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "去吧。天一阁的书,不是谁都能看的。", "min_attitude": -100, "max_attitude": 0},
                    {"text": "慢走。若想查什么典籍,随时来。", "min_attitude": 0, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（审视）年轻人,你从何处来?……扬州?嗯,老夫在扬州也有几位故交。你来天一阁,是查书还是查人?"},
                    {"trigger": "high_attitude", "text": "（从暗格中取出一封信）这封信是去年从扬州寄来的,写信的人……你认识。看看吧,对你有用。", "min_attitude": 80},
                ],
            },
            "money_wen": 500,
            "service_catalog": {
                "consult_archive": {"name": "查阅典籍", "price_wen": 20},
                "copy_document": {"name": "抄录文书", "price_wen": 30},
            },
            "memories": [],
            "rumor_hooks": [
                "范钦致仕前在兵部任职,对海防和海禁政策了如指掌",
                "天一阁中藏有历年邸报和地方志,可能包含江南商帮的旧档案",
                "范钦与扬州官场中人有书信往来,手中可能掌握关键线索",
            ],
            "schedule": {
                "卯时": {"location": "ningbo_tianyi", "pos": [9, 7], "activity": "在阁中晨读"},
                "巳时": {"location": "ningbo_tianyi", "pos": [14, 10], "activity": "在校勘室整理古籍"},
                "午时": {"location": "ningbo_tianyi", "pos": [9, 7], "activity": "午间小憩"},
                "申时": {"location": "ningbo_tianyi", "pos": [5, 4], "activity": "在院中散步会客"},
            },
            "observable_details": [
                "案上摊着一本地方志,页边写满了蝇头小楷的批注",
                "书架最高处有一个上了锁的暗格,里面似乎藏着什么",
            ],
        },
        "status_effects": [],
        "inventory": [
            {"id": "local_gazetteer", "name": "宁波府志", "qty": 1},
            {"id": "old_letter", "name": "旧信一封", "qty": 1},
        ],
        "tags": ["scholar", "retired_official", "informant"],
    },
    {
        "id": "ningbo_chief",
        "name": "陈把总",
        "type": "npc",
        "location": "ningbo_shipsi",
        "pos": [10, 8],
        "attributes": {
            "hp": 70, "max_hp": 70,
            "rank": "把总",
            "occupation": "市舶司把总",
            "personality": "宁波市舶司把总,武举出身,负责港口巡逻和走私稽查。表面上铁面无私,暗中却与海商有默契——每月收些'茶水银',对某些船只睁一只眼闭一只眼。但底线是不碰大宗违禁品,尤其是铁器和军用物资。",
            "attack": 7, "defense": 15,
            "dialogue_lines": {
                "greetings": [
                    {"text": "（警觉）站住!你是什么人?来市舶司有何公干?", "min_attitude": -100, "max_attitude": -10},
                    {"text": "哦,是你。有什么事?", "min_attitude": -10, "max_attitude": 30},
                    {"text": "（点头）你来了。坐,喝杯茶。有什么消息?", "min_attitude": 30, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "duty", "label": "海禁巡查", "unlock_attitude": -50, "lines": [
                        {"text": "朝廷海禁严明,本官奉旨巡查,绝不姑息走私之徒。", "min_attitude": -50, "max_attitude": 20},
                        {"text": "（压低声音）巡查是巡查,但宁波这地方……靠海吃海,总不能让百姓饿死。小打小闹的,本官也管不过来。", "min_attitude": 20, "max_attitude": 60},
                    ]},
                    {"id": "smuggling", "label": "走私暗线", "unlock_attitude": 50, "lines": [
                        {"text": "（左右看看）你是聪明人。宁波港的走私……不是一两个人的事。背后有杭州的茶商、苏州的丝商、甚至扬州的……你知道的。", "min_attitude": 50, "max_attitude": 80},
                        {"text": "（正色）本官每月收些茶水银,但大宗违禁品——铁器、军用物资——本官绝不放行。这是底线。", "min_attitude": 80, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "去吧。别在市舶司附近逗留。", "min_attitude": -100, "max_attitude": 0},
                    {"text": "慢走。有什么消息,随时来报。", "min_attitude": 0, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（上下打量）你不是本地人。来宁波做什么?……做生意?还是……查什么?"},
                    {"trigger": "high_attitude", "text": "（私下低语）你要是真想查走私的事……去码头看看,最近有条船叫'福顺号',半夜才进港。船上的货……不简单。", "min_attitude": 70},
                ],
            },
            "money_wen": 350,
            "service_catalog": {
                "port_pass": {"name": "港口通行令", "price_wen": 50},
                "ship_inquiry": {"name": "查询船只记录", "price_wen": 30},
            },
            "memories": [],
            "rumor_hooks": [
                "陈把总每月收海商的茶水银,对某些走私船睁一只眼闭一只眼",
                "最近有条叫'福顺号'的船,半夜进港,货物不明",
                "宁波市舶司内部有人秉公执法,有人暗中放行,派系斗争激烈",
            ],
            "schedule": {
                "卯时": {"location": "ningbo_shipsi", "pos": [10, 8], "activity": "在大堂处理公文"},
                "巳时": {"location": "ningbo_dock", "pos": [11, 8], "activity": "去码头巡查"},
                "午时": {"location": "ningbo_shipsi", "pos": [15, 12], "activity": "在内堂歇息"},
                "酉时": {"location": "ningbo_dock", "pos": [16, 10], "activity": "去码头查看晚归渔船"},
            },
            "observable_details": [
                "腰间挂着一把制式腰刀,刀鞘上有几道新划痕",
                "桌上放着一本船引登记簿,有几页被撕掉了",
            ],
        },
        "status_effects": [],
        "inventory": [
            {"id": "port_pass_official", "name": "市舶司通行令", "qty": 1},
            {"id": "ship_log", "name": "船只登记簿", "qty": 1},
        ],
        "tags": ["official", "military", "gatekeeper"],
    },
    {
        "id": "ningbo_sea_merchant",
        "name": "赵海商",
        "type": "npc",
        "location": "ningbo_dock",
        "pos": [14, 10],
        "attributes": {
            "hp": 50, "max_hp": 50,
            "rank": "商人",
            "occupation": "海商",
            "personality": "宁波最大的海商之一,经营近海贸易,暗中也做远洋走私。与杭州茶商、苏州丝商、甚至扬州吴员外都有生意往来。为人精明圆滑,善于在官府和商帮之间周旋。最近在筹备一批大买卖,需要打通各方关系。",
            "attack": 4, "defense": 11,
            "dialogue_lines": {
                "greetings": [
                    {"text": "（打量）你是……?要买海鲜还是谈生意?", "min_attitude": -100, "max_attitude": -10},
                    {"text": "哦,是你。来,坐,喝杯茶。", "min_attitude": -10, "max_attitude": 30},
                    {"text": "（热情）公子来了!快请坐,今日有好货。", "min_attitude": 30, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "trade", "label": "海上贸易", "unlock_attitude": -50, "lines": [
                        {"text": "我赵某人做的都是正经生意。近海打鱼、贩运海鲜,童叟无欺。", "min_attitude": -50, "max_attitude": 20},
                        {"text": "（压低声音）正经生意嘛……也有不那么正经的。海禁是海禁,但船总要出海的。", "min_attitude": 20, "max_attitude": 60},
                    ]},
                    {"id": "network", "label": "商路网络", "unlock_attitude": 40, "lines": [
                        {"text": "杭州的茶叶、苏州的丝绸、景德镇的瓷器……都从宁波出海。这条线跑了上百年了。", "min_attitude": 40, "max_attitude": 75},
                        {"text": "（四下看看）扬州那边……吴员外的货,也从这里出。不过最近风声紧,他的货改走陆路了。", "min_attitude": 75, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "慢走。要买海鲜随时来。", "min_attitude": -100, "max_attitude": 0},
                    {"text": "走好。有什么需要,随时来找我。", "min_attitude": 0, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（打量）新面孔。从哪来?……扬州?嗯,最近扬州来的人不少。是要出海,还是……查什么?"},
                    {"trigger": "high_attitude", "text": "（神秘地）你要是真想知道……半夜来码头,有条船叫'福顺号',船老大是我的人。他能告诉你很多事。", "min_attitude": 70},
                ],
            },
            "money_wen": 800,
            "price_list": {"dried_fish": 15, "sea_cucumber": 60, "pearl_strand": 200},
            "service_catalog": {
                "buy_seafood": {"name": "购买海货", "price_wen": 15},
                "arrange_passage": {"name": "安排船票", "price_wen": 80},
            },
            "memories": [],
            "rumor_hooks": [
                "赵海商与杭州茶商、苏州丝商都有生意往来,是江南商帮在宁波的代理人",
                "最近有条叫'福顺号'的船半夜进港,船上装的不是普通海货",
                "赵海商在筹备一批大买卖,需要打通市舶司的关系",
            ],
            "schedule": {
                "辰时": {"location": "ningbo_dock", "pos": [14, 10], "activity": "在码头查看货物"},
                "巳时": {"location": "ningbo_dock", "pos": [8, 6], "activity": "在鱼行谈生意"},
                "午时": {"location": "ningbo_shipsi", "pos": [12, 8], "activity": "去市舶司办船引"},
                "申时": {"location": "ningbo_dock", "pos": [14, 10], "activity": "在码头验货装船"},
            },
            "observable_details": [
                "右手食指上戴着一枚玉扳指,据说是从南洋带回来的",
                "腰间挂着一串铜钥匙和一个小罗盘",
            ],
        },
        "status_effects": [],
        "inventory": [
            {"id": "trade_ledger_nb", "name": "海贸账册", "qty": 1},
            {"id": "compass", "name": "航海罗盘", "qty": 1},
        ],
        "tags": ["merchant", "smuggler", "informant"],
    },
]

# ---- Side thread ----

NINGBO_SIDE_THREADS = [
    {
        "id": "ningbo_sea_route",
        "title": "海上暗线",
        "hook": "赵海商说杭州茶叶、苏州丝绸都从宁波出海,扬州吴员外的货也曾从这里走。陈把总说最近有条叫'福顺号'的船半夜进港。范钦说江南商帮的网络比想象的更大,宁波是出海的最后一站。",
        "anchors": [
            {"location": "ningbo_dock"},
            {"location": "ningbo_shipsi"},
            {"location": "ningbo_tianyi"},
            {"entity": "ningbo_fanqin"},
            {"entity": "ningbo_chief"},
            {"entity": "ningbo_sea_merchant"},
            {"entity": "merchant_wu"},
        ],
        "stakes": "宁波是江南暗网的出海口,货物从这里装船出海,远销南洋和日本。追查海上暗线可揭露整个走私网络的终端,但海商势力盘根错节,市舶司内部也不干净,轻举妄动可能引来杀身之祸。",
    },
]


def seed_ningbo(world: World) -> None:
    """Seed Ningbo region: 3 locations, 3 NPCs, 1 side thread."""

    # ---- Wire up existing hangzhou_canal_dock → ningbo_dock exit ----
    hangzhou_dock = world.get_location("hangzhou_canal_dock")
    if hangzhou_dock:
        hangzhou_dock.setdefault("exits", {})["southeast_ningbo"] = "ningbo_dock"
        world.save_location(hangzhou_dock)

    # ---- Save new locations ----
    for loc in NINGBO_LOCATIONS:
        world.save_location(loc)

    # ---- Save new NPCs ----
    for entity in NINGBO_ENTITIES:
        world.save_entity(entity)

    # ---- Merge evolution registry ----
    registry = world.get_flag("evolution_registry") or []
    existing_ids = {e["entity_id"] for e in registry}
    new_entries = [
        {"entity_id": "ningbo_fanqin", "frequency": "every_5_turns",
         "last_evolved_turn": 0, "reason": "天一阁主人,致仕官员,掌握朝中消息和地方档案"},
        {"entity_id": "ningbo_chief", "frequency": "every_3_turns",
         "last_evolved_turn": 0, "reason": "市舶司把总,掌控港口巡查和走私稽查"},
        {"entity_id": "ningbo_sea_merchant", "frequency": "every_2_turns",
         "last_evolved_turn": 0, "reason": "海商,江南商帮在宁波的代理人,掌握出海暗线"},
    ]
    for entry in new_entries:
        if entry["entity_id"] not in existing_ids:
            registry.append(entry)
    world.set_flag("evolution_registry", registry)

    # ---- Attach side thread to story seeds ----
    seeds = world.get_flag("story_seeds")
    if seeds:
        existing_thread_ids = {t["id"] for t in seeds.get("side_threads", [])}
        for thread in NINGBO_SIDE_THREADS:
            if thread["id"] not in existing_thread_ids:
                seeds["side_threads"].append(thread)
        world.set_flag("story_seeds", seeds)

    # ---- Attach rumor hooks from side thread ----
    for thread in NINGBO_SIDE_THREADS:
        for anchor in thread["anchors"]:
            entity_id = anchor.get("entity")
            if entity_id:
                _append_unique_hook(world, entity_id, thread["hook"])
            location_id = anchor.get("location")
            if location_id:
                _append_location_thread(world, location_id, thread)

    world.set_flag("ningbo_seeded", True)


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
