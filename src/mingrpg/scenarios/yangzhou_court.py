"""Default starting scenario: Yangzhou Court Hall (扬州府衙大堂)."""
from mingrpg.core.world import World


def seed_yangzhou_court(world: World) -> None:
    """Populate world with the opening scene at 扬州府衙大堂."""

    # ---- Locations ----
    world.save_location({
        "id": "court_hall",
        "name": "扬州府衙大堂",
        "type": "indoor_official",
        "size": [10, 10],
        "exits": {"south": "court_yard"},
        "tags": ["public", "official", "high_security"],
        "description": (
            "正堂三楹,正中悬'明镜高悬'匾额,案上文房四宝齐备。"
            "两旁衙役各执水火棍,百姓鸦雀无声。"
        ),
        "observable_details": [
            {"id": "court_hall_case_table", "text": "公案右角压着一沓未批状纸,最上面露出'漕'字。", "discovery_value": 8, "tags": ["clue", "petition"]},
            {"id": "court_hall_side_screen", "text": "侧屏后隐约有脚步声,似有人在暗处旁听公堂。", "discovery_value": 14, "tags": ["hidden", "official"]},
        ],
    })
    world.save_location({
        "id": "court_yard",
        "name": "府衙院子",
        "type": "outdoor",
        "size": [20, 20],
        "exits": {"north": "court_hall", "south": "street_main"},
        "tags": ["public", "official"],
        "description": "青砖铺地,石狮一对,旗杆高悬府衙旗号。",
    })
    world.save_location({
        "id": "street_main",
        "name": "扬州府前大街",
        "type": "outdoor",
        "size": [30, 30],
        "exits": {"north": "court_yard", "south": "market_gate"},
        "tags": ["public", "crowded"],
        "description": "市井繁华,商贩叫卖,行人如织。",
    })
    world.save_location({
        "id": "jail",
        "name": "扬州县衙大牢",
        "type": "indoor_jail",
        "size": [5, 5],
        "exits": {},
        "tags": ["confined", "official", "filthy"],
        "description": "阴暗潮湿,稻草满地,锁链叮当作响。",
    })

    # ---- Entities ----
    world.save_entity({
        "id": "player",
        "name": "无名书生",
        "type": "player",
        "location": "court_hall",
        "pos": [3, 5],
        "attributes": {
            "hp": 100, "max_hp": 100,
            "rank": "平民",
            "occupation": "落第书生",
            "str": 10, "dex": 12, "int": 16, "cha": 13,
            "observation": 10,
            "money_wen": 50,  # 五十文钱
            "background": "你寒窗十年,赴乡试落榜,流寓扬州。今日因为状告地痞欺凌,前来府衙陈情。",
            "skills": {
                "litigation": {"name": "讼学", "xp": 0, "level": 0, "note": "熟悉状纸格式与府衙程序"},
            },
        },
        "status_effects": [],
        "inventory": [
            {"id": "scroll_petition", "name": "状纸一张", "qty": 1},
            {"id": "brush", "name": "毛笔", "qty": 1},
        ],
        "tags": ["protagonist", "commoner", "literate"],
    })

    world.save_entity({
        "id": "zhifu_wang",
        "name": "王知府",
        "type": "npc",
        "location": "court_hall",
        "pos": [3, 7],
        "attributes": {
            "hp": 80, "max_hp": 80,
            "rank": "四品",
            "occupation": "扬州知府",
            "personality": "外严内贪,惯于敷衍小民,对豪强让步",
            "attack": 1, "defense": 10,
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "堂下何人?有何事禀报?", "min_attitude": -100, "max_attitude": 100},
                    {"text": "（头也不抬）你又来了。", "min_attitude": -50, "max_attitude": -10},
                    {"text": "（微微颔首）你来了,坐吧。", "min_attitude": 20, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "petition", "label": "状纸之事", "unlock_attitude": -100, "lines": [
                        {"text": "本府自会秉公办理,你先回去候着。", "min_attitude": -100, "max_attitude": 0},
                        {"text": "此案已有眉目,你且宽心。", "min_attitude": 10, "max_attitude": 100},
                    ]},
                    {"id": "corruption", "label": "府衙弊端", "unlock_attitude": 30, "lines": [
                        {"text": "（压低声音）有些事不可乱说。本府……也有难处。", "min_attitude": 30, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "退下吧。", "min_attitude": -100, "max_attitude": 100},
                    {"text": "去吧,有消息本府差人告知你。", "min_attitude": 20, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（审视状纸）哦?你要告赵三?……此事本府知道了,你先下去。"},
                ],
            },
        },
        "status_effects": [],
        "inventory": [{"id": "fan", "name": "折扇", "qty": 1}],
        "tags": ["official", "high_rank"],
    })

    world.save_entity({
        "id": "guard_a",
        "name": "衙役甲",
        "type": "npc",
        "location": "court_hall",
        "pos": [1, 7],
        "attributes": {
            "hp": 60, "max_hp": 60, "rank": "差役",
            "occupation": "府衙差役",
            "attack": 4, "defense": 12,
            "weapon_damage": "1d6", "weapon_name": "水火棍",
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "站住!你是什么人?", "min_attitude": -100, "max_attitude": 0},
                    {"text": "哦,是你啊。进去吧。", "min_attitude": 10, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "court_business", "label": "衙门之事", "unlock_attitude": 0, "lines": [
                        {"text": "知府大人今日心情不好,你说话小心些。", "min_attitude": 0, "max_attitude": 100},
                        {"text": "状纸的事我们管不了,你找师爷去。", "min_attitude": -50, "max_attitude": 50},
                    ]},
                ],
                "farewells": [
                    {"text": "走吧走吧,别在衙门口逗留。", "min_attitude": -100, "max_attitude": 100},
                ],
            },
        },
        "status_effects": [],
        "inventory": [{"id": "stick", "name": "水火棍", "qty": 1}],
        "tags": ["official", "guard"],
    })

    world.save_entity({
        "id": "guard_b",
        "name": "衙役乙",
        "type": "npc",
        "location": "court_hall",
        "pos": [5, 7],
        "attributes": {
            "hp": 60, "max_hp": 60, "rank": "差役",
            "occupation": "府衙差役",
            "attack": 4, "defense": 12,
            "weapon_damage": "1d6", "weapon_name": "水火棍",
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "有何公干?报上名来。", "min_attitude": -100, "max_attitude": 0},
                    {"text": "又来了?今日知府大人在,你运气不错。", "min_attitude": 10, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "court_rumor", "label": "衙门传闻", "unlock_attitude": 10, "lines": [
                        {"text": "（左右看看）昨夜有人来衙门找过师爷,天没亮就走了。", "min_attitude": 10, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "行了,进去吧。", "min_attitude": -100, "max_attitude": 100},
                ],
            },
        },
        "status_effects": [],
        "inventory": [{"id": "stick", "name": "水火棍", "qty": 1}],
        "tags": ["official", "guard"],
    })

    world.save_entity({
        "id": "shiye",
        "name": "刘师爷",
        "type": "npc",
        "location": "court_hall",
        "pos": [4, 6],
        "attributes": {
            "hp": 50, "max_hp": 50, "rank": "幕僚",
            "occupation": "知府幕宾",
            "personality": "机敏圆滑,善于揣摩上意",
            "is_advisor": True,
            "advisor_topics": ["府衙程序", "状纸策略", "官场风险"],
            "advisor_style": "圆滑谨慎,提醒风险,不直接替玩家决定",
            "attack": 1, "defense": 9,
            "dialogue_lines": {
                "greetings": [
                    {"text": "这位公子,有何见教?", "min_attitude": -100, "max_attitude": 100},
                    {"text": "（左右看看,压低声音）你来了?小心行事。", "min_attitude": 10, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "court_process", "label": "府衙程序", "unlock_attitude": -50, "lines": [
                        {"text": "按规矩,状纸递上需等三日方有回音。", "min_attitude": -50, "max_attitude": 100},
                        {"text": "若想快些,须得打点差役,这是规矩。", "min_attitude": 10, "max_attitude": 100},
                    ]},
                    {"id": "insider_info", "label": "内部消息", "unlock_attitude": 30, "lines": [
                        {"text": "（四下张望）知府大人最近心烦,上面来人查过盐税……", "min_attitude": 30, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "慢走,路上小心。", "min_attitude": -100, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "（上下打量）你就是那个递状纸的书生?……嗯,我知道了。"},
                ],
            },
            "observable_details": [
                {"id": "shiye_ink_stain", "text": "刘师爷袖口沾着新鲜朱砂批痕,像刚改过什么文书。", "discovery_value": 10, "tags": ["clue", "document"]},
                {"id": "shiye_hidden_note", "text": "他腰间书袋露出半截纸角,墨迹写着'暂缓收案'四字。", "discovery_value": 16, "tags": ["hidden", "petition"]},
            ],
            "memories": [],
        },
        "status_effects": [],
        "inventory": [],
        "tags": ["official", "scholarly"],
    })

    # ---- Initial flags & time ----
    world.set_world_time({
        "year": "万历十年", "season": "秋", "time_of_day": "巳时",
        "date": "辛卯", "day_index": 0,
    })
    world.set_flag("scene_opened", True)

    # ---- Initial evolution registry (key NPCs) ----
    world.set_flag("evolution_registry", [
        {"entity_id": "zhifu_wang", "frequency": "every_2_turns",
         "last_evolved_turn": 0, "reason": "知府是主线核心NPC,需持续关注府衙态度变化"},
        {"entity_id": "shiye", "frequency": "every_2_turns",
         "last_evolved_turn": 0, "reason": "师爷是关键顾问,可能暗中操作"},
        {"entity_id": "guard_a", "frequency": "every_5_turns",
         "last_evolved_turn": 0, "reason": "衙役在场维持秩序"},
        {"entity_id": "guard_b", "frequency": "every_5_turns",
         "last_evolved_turn": 0, "reason": "衙役在场维持秩序"},
    ])

    world.append_event({
        "actor": "system",
        "type": "scene_start",
        "summary": "玩家站在扬州府衙大堂上,准备向王知府陈情",
    })
