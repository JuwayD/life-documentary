"""Yangzhou Market Street scenario (扬州街市)."""
from mingrpg.core.world import World


def seed_yangzhou_market(world: World) -> None:
    """Populate world with the market street area of Yangzhou."""

    # ---- Locations ----
    world.save_location({
        "id": "market_gate",
        "name": "街市入口",
        "type": "outdoor",
        "size": [15, 15],
        "exits": {"north": "street_main", "south": "market_street"},
        "tags": ["public", "crowded", "transition"],
        "description": (
            "一座石牌坊立于街口,上书'扬州市廛'。牌坊下行人络绎不绝,"
            "挑担的小贩、骑驴的客商、拄杖的老者,各色人等穿梭其间。"
        ),
    })
    world.save_location({
        "id": "market_street",
        "name": "街市中心",
        "type": "outdoor",
        "size": [30, 30],
        "exits": {"north": "market_gate", "west": "market_stall_food",
                   "east": "teahouse", "south": "market_stall_fabric"},
        "tags": ["public", "crowded", "commercial"],
        "description": (
            "街心最是热闹。青石板路两侧店铺鳞次栉比,幌子招展。"
            "绸缎铺、药铺、钱庄、杂货铺一字排开。叫卖声、讨价声、"
            "骡马嘶鸣声混成一片。偶尔有官差骑马而过,行人纷纷避让。"
        ),
    })
    world.save_location({
        "id": "market_stall_food",
        "name": "小吃摊",
        "type": "outdoor",
        "size": [5, 5],
        "exits": {"east": "market_street"},
        "tags": ["public", "commercial", "food"],
        "description": (
            "几张矮桌、几条长凳,支在街边。灶台上一口大锅咕嘟咕嘟冒着热气,"
            "旁边蒸笼里码着白胖的包子。老板手忙脚乱地招呼客人,"
            "空气中飘着葱油饼和卤肉的香气。"
        ),
    })
    world.save_location({
        "id": "market_stall_fabric",
        "name": "布匹摊",
        "type": "outdoor",
        "size": [8, 8],
        "exits": {"north": "market_street"},
        "tags": ["public", "commercial", "textile"],
        "description": (
            "摊位上各色布匹层层叠叠:粗布、棉布、素绢、花绫,应有尽有。"
            "一匹苏州产的云锦用红绸盖着,摆在最显眼处。布商手持木尺,"
            "正与一位妇人比划着尺寸。"
        ),
    })
    world.save_location({
        "id": "teahouse",
        "name": "悦来茶楼",
        "type": "indoor_commercial",
        "size": [10, 10],
        "exits": {"west": "market_street"},
        "tags": ["public", "commercial", "social"],
        "description": (
            "茶楼分两层,楼下大堂摆了七八张八仙桌,墙上挂着名家字画。"
            "说书先生正坐在高台上,醒木一拍,讲的是《水浒传》武松打虎一段。"
            "跑堂的提着铜壶穿梭其间,茶香氤氲。"
        ),
    })

    # ---- Entities ----
    world.save_entity({
        "id": "vendor_food",
        "name": "孙老四",
        "type": "npc",
        "location": "market_stall_food",
        "pos": [3, 3],
        "attributes": {
            "hp": 60, "max_hp": 60,
            "rank": "平民",
            "occupation": "小吃摊主",
            "personality": "热情好客,嗓门大,爱打听街坊闲事",
            "attack": 2, "defense": 9,
            "money_wen": 200,
            "price_list": {"baozi": 4, "congyoubing": 3, "lurou": 20},
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "来来来!热腾腾的包子刚出笼!", "min_attitude": -100, "max_attitude": 100},
                    {"text": "老主顾来了!今儿想吃点啥?", "min_attitude": 20, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "street_gossip", "label": "街坊闲事", "unlock_attitude": -10, "lines": [
                        {"text": "这条街上什么事我都知道。你问吧。", "min_attitude": -10, "max_attitude": 100},
                        {"text": "赵三那帮人又来收份子钱了,唉,小本生意难做啊。", "min_attitude": 0, "max_attitude": 100},
                        {"text": "码头那边昨夜来了批货,盖得严严实实的,不知道是什么。", "min_attitude": 15, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "慢走啊!改天再来!", "min_attitude": -100, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "哟,生面孔!来尝尝我的包子,扬州城里头一号!"},
                ],
            },
        },
        "status_effects": [],
        "inventory": [
            {"id": "baozi", "name": "肉包子", "qty": 20},
            {"id": "congyoubing", "name": "葱油饼", "qty": 15},
            {"id": "lurou", "name": "卤肉", "qty": 5},
        ],
        "tags": ["commoner", "merchant", "food_vendor"],
    })
    world.save_entity({
        "id": "vendor_fabric",
        "name": "周掌柜",
        "type": "npc",
        "location": "market_stall_fabric",
        "pos": [4, 4],
        "attributes": {
            "hp": 50, "max_hp": 50,
            "rank": "平民",
            "occupation": "布商",
            "personality": "精明算计,察言观色,对有钱人和气,对穷人冷淡",
            "attack": 1, "defense": 9,
            "money_wen": 500,
            "price_list": {"cotton_cloth": 50, "silk": 160, "brocade": 1200},
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "客官看看布?上好的苏绣、云锦,应有尽有。", "min_attitude": -100, "max_attitude": 100},
                    {"text": "贵客驾临!里面请,新到的货给您留着呢。", "min_attitude": 30, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "fabric_trade", "label": "布匹生意", "unlock_attitude": 0, "lines": [
                        {"text": "生意嘛,还过得去。就是最近码头那帮人抽成太狠。", "min_attitude": 0, "max_attitude": 100},
                        {"text": "那匹云锦?别问来历,反正是好货。", "min_attitude": 20, "max_attitude": 100},
                    ]},
                    {"id": "merchants", "label": "商帮消息", "unlock_attitude": 20, "lines": [
                        {"text": "（压低声音）吴员外的人常来我这拿货,都是大宗的。你懂的。", "min_attitude": 20, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "慢走!下次带朋友来啊!", "min_attitude": -100, "max_attitude": 100},
                ],
            },
        },
        "status_effects": [],
        "inventory": [
            {"id": "cotton_cloth", "name": "棉布", "qty": 10},
            {"id": "silk", "name": "素绢", "qty": 5},
            {"id": "brocade", "name": "云锦", "qty": 1},
            {"id": "wood_ruler", "name": "木尺", "qty": 1},
        ],
        "tags": ["commoner", "merchant", "fabric_vendor"],
    })
    world.save_entity({
        "id": "teahouse_owner",
        "name": "陈掌柜",
        "type": "npc",
        "location": "teahouse",
        "pos": [5, 3],
        "attributes": {
            "hp": 60, "max_hp": 60,
            "rank": "平民",
            "occupation": "茶馆老板",
            "personality": "见多识广,交游广阔,与三教九流都有来往,消息灵通",
            "is_advisor": True,
            "advisor_topics": ["街市传闻", "人情世故", "找证人"],
            "advisor_style": "热心仗义,以茶会友,消息灵通但偶有夸大",
            "skills_taught": ["persuasion"],
            "attack": 1, "defense": 9,
            "dialogue_lines": {
                "greetings": [
                    {"text": "客官里边请,上好的龙井刚沏上!", "min_attitude": -100, "max_attitude": 100},
                    {"text": "老朋友来了!今儿喝点什么?", "min_attitude": 20, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "rumors", "label": "打听消息", "unlock_attitude": -20, "lines": [
                        {"text": "最近街上不太平,赵三那帮人越发嚣张了。", "min_attitude": -20, "max_attitude": 100},
                        {"text": "听说码头那边来了批外地货,走的是夜路。", "min_attitude": 10, "max_attitude": 100},
                        {"text": "（压低声音）吴员外的人前几日来找过知府……", "min_attitude": 30, "max_attitude": 100},
                    ]},
                    {"id": "people", "label": "人物打听", "unlock_attitude": 0, "lines": [
                        {"text": "周掌柜?他跟码头那边走得很近,你要小心。", "min_attitude": 0, "max_attitude": 100},
                        {"text": "柳姑娘每日申时来唱曲,她知道不少官场秘闻。", "min_attitude": 20, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "慢走啊!改天再来喝茶。", "min_attitude": -100, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "生面孔啊!来来来,先坐下喝杯茶,扬州城里什么事我老陈不知道?" },
                    {"trigger": "high_attitude", "text": "（郑重地）你是信得过的人,我跟你说件要紧事……", "min_attitude": 50},
                ],
            },
            "money_wen": 300,
            "price_list": {"tea_leaves": 6, "teapot": 80},
            "service_catalog": {
                "tea_seat": {"name": "茶座打听消息", "price_wen": 8},
            },
            "memories": [],
        },
        "status_effects": [],
        "inventory": [
            {"id": "tea_leaves", "name": "茶叶", "qty": 30},
            {"id": "teapot", "name": "紫砂壶", "qty": 3},
        ],
        "tags": ["commoner", "merchant", "informant"],
    })
    world.save_entity({
        "id": "beggar_liu",
        "name": "乞丐老刘",
        "type": "npc",
        "location": "market_gate",
        "pos": [2, 1],
        "attributes": {
            "hp": 30, "max_hp": 30,
            "rank": "乞丐",
            "occupation": "乞丐",
            "personality": "看似落魄实则消息灵通,常在街市入口观察来往行人,知晓许多街头秘密",
            "attack": 1, "defense": 8,
            "dialogue_lines": {
                "greetings": [
                    {"text": "（伸出手）老爷行行好……", "min_attitude": -100, "max_attitude": 0},
                    {"text": "嘿,你来了。蹲下说,别让人看见。", "min_attitude": 10, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "street_news", "label": "街头消息", "unlock_attitude": -10, "lines": [
                        {"text": "昨儿半夜,码头那边来了几辆大车,盖得严严实实。", "min_attitude": -10, "max_attitude": 100},
                        {"text": "赵三手下那几个泼皮,每日在码头收份子钱。", "min_attitude": 0, "max_attitude": 100},
                        {"text": "有个外地来的书生前几日在茶楼打听盐税的事,后来就不见了。", "min_attitude": 20, "max_attitude": 100},
                    ]},
                    {"id": "people_rumors", "label": "人物底细", "unlock_attitude": 10, "lines": [
                        {"text": "吴员外?他表面做绸缎生意,暗地里什么都沾。", "min_attitude": 10, "max_attitude": 100},
                        {"text": "周寡妇的丈夫死得蹊跷,跟赵三脱不了干系。", "min_attitude": 30, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "走吧走吧,别在这蹲太久,引人注意。", "min_attitude": -100, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（斜眼打量）看你穿戴不像有钱人,不过……你要是给几个铜板,我可以告诉你些事。"},
                    {"trigger": "high_attitude", "text": "（认真地）你是好人。我跟你说个秘密——码头仓库下面有暗道。", "min_attitude": 40},
                ],
            },
            "money_wen": 5,
            "service_catalog": {
                "street_info": {"name": "打听街头消息", "price_wen": 10},
            },
            "memories": [],
        },
        "status_effects": [],
        "inventory": [
            {"id": "broken_bowl", "name": "破碗", "qty": 1},
        ],
        "tags": ["commoner", "beggar", "informant"],
    })
    world.save_entity({
        "id": "constable",
        "name": "李捕快",
        "type": "npc",
        "location": "market_street",
        "pos": [15, 15],
        "attributes": {
            "hp": 70, "max_hp": 70,
            "rank": "差役",
            "occupation": "巡街捕快",
            "personality": "忠于职守,不苟言笑,但也讲道理,不无故为难百姓",
            "attack": 5, "defense": 13,
            "weapon_damage": "1d6", "weapon_name": "腰刀",
            "money_wen": 100,
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "站住。你是什么人?有何事?", "min_attitude": -100, "max_attitude": 0},
                    {"text": "又是你?有什么事快说。", "min_attitude": 0, "max_attitude": 50},
                    {"text": "你来了。这边说话,别让旁人听见。", "min_attitude": 30, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "law_enforcement", "label": "街面治安", "unlock_attitude": 0, "lines": [
                        {"text": "赵三那帮人?我知道他们横行霸道,但没证据,拿他们没办法。", "min_attitude": 0, "max_attitude": 100},
                        {"text": "你若有确凿证据,我可以向上头禀报。但空口无凭,告不倒他们。", "min_attitude": 15, "max_attitude": 100},
                    ]},
                    {"id": "inside_info", "label": "内部消息", "unlock_attitude": 30, "lines": [
                        {"text": "（四下张望）上头有人压着这案子,我也不好多说。", "min_attitude": 30, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "走吧。别在街上惹事。", "min_attitude": -100, "max_attitude": 100},
                ],
            },
        },
        "status_effects": [],
        "inventory": [
            {"id": "saber", "name": "腰刀", "qty": 1},
            {"id": "whistle", "name": "哨子", "qty": 1},
        ],
        "tags": ["official", "guard", "law_enforcement"],
    })
