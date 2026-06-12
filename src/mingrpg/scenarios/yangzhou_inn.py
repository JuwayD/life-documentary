"""Yangzhou Inn scenario (扬州客栈)."""
from mingrpg.core.world import World


def seed_yangzhou_inn(world: World) -> None:
    """Populate world with an inn near the market."""

    # ---- Locations ----
    world.save_location({
        "id": "inn_front",
        "name": "客栈门面",
        "type": "outdoor",
        "size": [10, 10],
        "exits": {"west": "market_street", "east": "inn_hall"},
        "tags": ["public", "commercial", "transition"],
        "description": (
            "一块黑漆金字的招牌高悬门楣:'悦来客栈'。门口一对石鼓,"
            "门内隐约可见账房柜台。檐下挂着两盏红灯笼,"
            "上书'宾至如归'四个字。"
        ),
    })
    world.save_location({
        "id": "inn_hall",
        "name": "客栈大堂",
        "type": "indoor_commercial",
        "size": [15, 15],
        "exits": {"west": "inn_front", "east": "inn_room"},
        "tags": ["public", "commercial", "social"],
        "description": (
            "大堂宽敞,正中是掌柜的柜台,上面放着算盘和账簿。"
            "几张方桌旁三三两两坐着住客,有的吃饭,有的闲聊。"
            "墙上贴着'莫谈国事'的纸条,炉火烧得正旺。"
            "楼梯通向二楼客房,店小二端着一壶热茶穿梭其间。"
        ),
    })
    world.save_location({
        "id": "inn_room",
        "name": "客房",
        "type": "indoor_private",
        "size": [8, 8],
        "exits": {"west": "inn_hall"},
        "tags": ["private", "commercial", "rest"],
        "description": (
            "一间不大的客房,收拾得还算干净。一张木床、一张桌、一把椅、"
            "一个洗脸架。窗外是后院,隐约可见马厩。桌上放着一盏油灯,"
            "角落里有个木盆。"
        ),
    })

    # ---- Entities ----
    world.save_entity({
        "id": "innkeeper",
        "name": "赵掌柜",
        "type": "npc",
        "location": "inn_hall",
        "pos": [7, 3],
        "attributes": {
            "hp": 60, "max_hp": 60,
            "rank": "平民",
            "occupation": "客栈掌柜",
            "personality": "八面玲珑,笑脸迎人,但账目分毫不差。见过南来北往的客,对江湖事略知一二",
            "attack": 1, "defense": 9,
            "dialogue_lines": {
                "greetings": [
                    {"text": "客官住店还是吃饭?里面请!", "min_attitude": -100, "max_attitude": 100},
                    {"text": "老主顾来了!楼上请,给您留了好房。", "min_attitude": 20, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "guests", "label": "住客消息", "unlock_attitude": 0, "lines": [
                        {"text": "最近南来北往的客商不少,生意还过得去。", "min_attitude": 0, "max_attitude": 100},
                        {"text": "前几日有几个生面孔住进来,出手阔绰,但不让人靠近他们的房间。", "min_attitude": 20, "max_attitude": 100},
                    ]},
                    {"id": "inn_secrets", "label": "客栈秘闻", "unlock_attitude": 30, "lines": [
                        {"text": "（低声）有个常客每月来一次,总在深夜出去,天亮才回来。他留的路引是假的。", "min_attitude": 30, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "慢走!下次再来啊!", "min_attitude": -100, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "哟,新客!打尖还是住店?咱这干净便宜,包您满意。"},
                ],
            },
            "money_wen": 800,
            "service_catalog": {
                "common_room": {"name": "通铺一晚", "price_wen": 10},
                "private_room": {"name": "客房一晚", "price_wen": 20},
                "meal": {"name": "热饭一份", "price_wen": 6},
            },
            "memories": [],
        },
        "status_effects": [],
        "inventory": [
            {"id": "account_book", "name": "账簿", "qty": 1},
            {"id": "abacus", "name": "算盘", "qty": 1},
            {"id": "room_keys", "name": "客房钥匙", "qty": 5},
        ],
        "tags": ["commoner", "merchant", "innkeeper"],
    })
    world.save_entity({
        "id": "inn_waiter",
        "name": "店小二",
        "type": "npc",
        "location": "inn_hall",
        "pos": [10, 7],
        "attributes": {
            "hp": 50, "max_hp": 50,
            "rank": "平民",
            "occupation": "店小二",
            "personality": "勤快机灵,眼观六路耳听八方,对掌柜忠诚,会看人下菜碟",
            "attack": 2, "defense": 9,
            "money_wen": 30,
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "客官里面请!打尖还是住店?", "min_attitude": -100, "max_attitude": 100},
                    {"text": "哟,老熟客来啦!楼上请!", "min_attitude": 20, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "guest_gossip", "label": "住客消息", "unlock_attitude": 0, "lines": [
                        {"text": "最近店里南来北往的客多,我也记不太清。", "min_attitude": 0, "max_attitude": 30},
                        {"text": "（压低声音）有个客人出手阔绰,但每晚都出去,天亮才回来。", "min_attitude": 20, "max_attitude": 100},
                    ]},
                    {"id": "local_tips", "label": "本地门道", "unlock_attitude": 10, "lines": [
                        {"text": "要吃饭去街市孙老四那儿,便宜实惠。要听消息去茶楼,陈掌柜什么都知道。", "min_attitude": 10, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "客官慢走!下次再来啊!", "min_attitude": -100, "max_attitude": 100},
                ],
            },
        },
        "status_effects": [],
        "inventory": [
            {"id": "teapot_waiter", "name": "茶壶", "qty": 1},
            {"id": "towel", "name": "抹布", "qty": 1},
        ],
        "tags": ["commoner", "service", "waiter"],
    })
    world.save_entity({
        "id": "traveling_merchant",
        "name": "马行商",
        "type": "npc",
        "location": "inn_hall",
        "pos": [5, 10],
        "attributes": {
            "hp": 55, "max_hp": 55,
            "rank": "平民",
            "occupation": "行商",
            "personality": "见多识广,走南闯北,肚子里有不少奇闻异事。喜欢喝酒聊天,但也谨慎多疑",
            "attack": 2, "defense": 9,
            "dialogue_lines": {
                "greetings": [
                    {"text": "哦?同是天涯沦落人,来喝一杯?", "min_attitude": -100, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "travel_stories", "label": "各地见闻", "unlock_attitude": -10, "lines": [
                        {"text": "我从南京来,那边贡院最近闹了场风波,说是有人夹带小抄。", "min_attitude": -10, "max_attitude": 100},
                        {"text": "苏州的丝价今年涨了三成,说是税关卡得紧。", "min_attitude": 0, "max_attitude": 100},
                        {"text": "杭州龙井茶今年收成不好,但奇怪的是市面上茶价反而跌了。", "min_attitude": 20, "max_attitude": 100},
                    ]},
                    {"id": "trade_routes", "label": "商路消息", "unlock_attitude": 10, "lines": [
                        {"text": "运河上不太平,有些船走夜路,不挂灯笼,也不靠码头。", "min_attitude": 10, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "后会有期!路上小心。", "min_attitude": -100, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "哟,这位兄弟面善。我走南闯北见过不少人,你眼神里有股正气。"},
                ],
            },
            "money_wen": 300,
            "memories": [],
        },
        "status_effects": [],
        "inventory": [
            {"id": "wine_gourd", "name": "酒葫芦", "qty": 1},
            {"id": "travel_letter", "name": "路引", "qty": 1},
            {"id": "samples", "name": "货样", "qty": 3},
        ],
        "tags": ["commoner", "merchant", "traveler"],
    })
