"""Tool registry — maps tool name to (handler, JSON schema for LLM)."""
from mingrpg.tools import birth as B
from mingrpg.tools import read as R
from mingrpg.tools import write as W
from mingrpg.tools import util as U
from mingrpg.llm.agents.combat import CombatAgent
from mingrpg.llm.agents.law import LawAgent
from mingrpg.llm.agents.social import SocialAgent


def build_tool_registry(world):
    """Build dict {name: {handler, schema}} bound to a specific world."""

    return {
        # ---------- READ ----------
        "get_entity": {
            "handler": lambda **kw: R.get_entity(world, **kw),
            "schema": {
                "name": "get_entity",
                "description": "读取一个实体的完整状态(包括位置、属性、状态、物品)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string",
                                       "description": "实体ID,如 'player' / 'zhifu'"},
                    },
                    "required": ["entity_id"],
                },
            },
        },
        "get_location": {
            "handler": lambda **kw: R.get_location(world, **kw),
            "schema": {
                "name": "get_location",
                "description": "读取场景信息(名称、类型、出口、特征标签)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "location_id": {"type": "string"},
                    },
                    "required": ["location_id"],
                },
            },
        },
        "list_entities_nearby": {
            "handler": lambda **kw: R.list_entities_nearby(world, **kw),
            "schema": {
                "name": "list_entities_nearby",
                "description": "列出某实体附近 radius 格内的其他实体(同一场景)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "actor_id": {"type": "string"},
                        "radius": {"type": "integer", "default": 5},
                    },
                    "required": ["actor_id"],
                },
            },
        },
        "query_laws": {
            "handler": lambda **kw: R.query_laws(**kw),
            "schema": {
                "name": "query_laws",
                "description": (
                    "检索相关的明代法律/礼制/民俗条文。"
                    "玩家行为涉及暴力、违法、礼制、夜间出行等情形时必须调用。"
                    "返回的法条 id 必须在叙述中引用。"
                    "支持两种检索方式: keywords(关键词列表) 和 query(自然语言描述),可同时使用。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "关键词列表,如 ['打','官员']",
                        },
                        "query": {
                            "type": "string",
                            "description": (
                                "自然语言描述,如 '平民殴打知府' 或 '夜间外出遇到宵禁'。"
                                "使用语义检索匹配最相关法条。"
                            ),
                        },
                        "top_k": {"type": "integer", "default": 5},
                    },
                },
            },
        },
        "get_world_time": {
            "handler": lambda **kw: R.get_world_time(world, **kw),
            "schema": {
                "name": "get_world_time",
                "description": "获取游戏内时间(年号、季节、时辰)",
                "input_schema": {"type": "object", "properties": {}},
            },
        },
        "get_recent_events": {
            "handler": lambda **kw: R.get_recent_events(world, **kw),
            "schema": {
                "name": "get_recent_events",
                "description": "查看最近的世界事件日志",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "default": 10},
                    },
                },
            },
        },
        "list_locations": {
            "handler": lambda **kw: R.list_locations(world, **kw),
            "schema": {
                "name": "list_locations",
                "description": "列出世界中的所有场景(场景ID、名称、类型、出口、标签)",
                "input_schema": {"type": "object", "properties": {}},
            },
        },
        "list_birth_templates": {
            "handler": lambda **kw: B.list_birth_templates(**kw),
            "schema": {
                "name": "list_birth_templates",
                "description": "列出可用的出生模板摘要,用于新游戏或测试配置选择。",
                "input_schema": {"type": "object", "properties": {}},
            },
        },
        "get_birth_template": {
            "handler": lambda **kw: B.get_birth_template(**kw),
            "schema": {
                "name": "get_birth_template",
                "description": "读取指定出生模板的完整属性、技能、物品、背景与初始位置。",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "template_id": {"type": "string", "description": "出生模板ID"},
                    },
                    "required": ["template_id"],
                },
            },
        },
        "apply_birth_template": {
            "handler": lambda **kw: B.apply_birth_template(world, **kw),
            "schema": {
                "name": "apply_birth_template",
                "description": "将出生模板应用到玩家实体。用于新游戏/测试重置后的出生配置写入。",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "template_id": {"type": "string", "description": "出生模板ID"},
                        "entity_id": {"type": "string", "default": "player"},
                    },
                    "required": ["template_id"],
                },
            },
        },

        # ---------- UTIL ----------
        "roll_dice": {
            "handler": lambda **kw: U.roll_dice(**kw),
            "schema": {
                "name": "roll_dice",
                "description": (
                    "掷骰子,用于不确定性判定。"
                    "格式 NdM+K,如 '1d20+5'。"
                    "用法示例:技能检定(1d20)、伤害(1d6+2)、运气(2d10)。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "notation": {"type": "string"},
                    },
                    "required": ["notation"],
                },
            },
        },
        "calculate_distance": {
            "handler": lambda **kw: U.calculate_distance(**kw),
            "schema": {
                "name": "calculate_distance",
                "description": "计算两点之间的距离(欧氏/切比雪夫/曼哈顿)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "from_pos": {"type": "array",
                                     "items": {"type": "number"}},
                        "to_pos": {"type": "array",
                                   "items": {"type": "number"}},
                    },
                    "required": ["from_pos", "to_pos"],
                },
            },
        },

        # ---------- WRITE ----------
        "set_attribute": {
            "handler": lambda **kw: W.set_attribute(world, **kw),
            "schema": {
                "name": "set_attribute",
                "description": "修改实体的某个属性(如 hp、mood、rank)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string"},
                        "attr": {"type": "string"},
                        "value": {},
                    },
                    "required": ["entity_id", "attr", "value"],
                },
            },
        },
        "move_entity": {
            "handler": lambda **kw: W.move_entity(world, **kw),
            "schema": {
                "name": "move_entity",
                "description": "移动实体到新坐标和/或新场景",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string"},
                        "to_pos": {"type": "array",
                                   "items": {"type": "number"}},
                        "to_location": {"type": "string"},
                    },
                    "required": ["entity_id"],
                },
            },
        },
        "add_status": {
            "handler": lambda **kw: W.add_status(world, **kw),
            "schema": {
                "name": "add_status",
                "description": (
                    "给实体添加状态效果(如 '通缉'、'中毒'、'被擒'、'流血')。"
                    "duration: 持续回合,-1 为永久。reason: 添加原因。"
                    "damage_per_tick: 每回合造成伤害(默认0),用于中毒/流血等。"
                    "effect_type: 效果类别(bleeding/poison/stun/wanted等)。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string"},
                        "status": {"type": "string"},
                        "duration": {"type": "integer", "default": 1},
                        "reason": {"type": "string", "default": ""},
                        "damage_per_tick": {"type": "integer", "default": 0},
                        "effect_type": {"type": "string",
                                         "description": "效果类别: bleeding/poison/stun/wanted 等"},
                    },
                    "required": ["entity_id", "status"],
                },
            },
        },
        "remove_status": {
            "handler": lambda **kw: W.remove_status(world, **kw),
            "schema": {
                "name": "remove_status",
                "description": "移除实体的某个状态效果",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string"},
                        "status": {"type": "string"},
                    },
                    "required": ["entity_id", "status"],
                },
            },
        },
        "add_item": {
            "handler": lambda **kw: W.add_item(world, **kw),
            "schema": {
                "name": "add_item",
                "description": "向实体物品栏中添加物品",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string"},
                        "item": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "name": {"type": "string"},
                                "qty": {"type": "integer", "default": 1},
                            },
                            "required": ["id", "name"],
                        },
                    },
                    "required": ["entity_id", "item"],
                },
            },
        },
        "remove_item": {
            "handler": lambda **kw: W.remove_item(world, **kw),
            "schema": {
                "name": "remove_item",
                "description": "从实体物品栏中移除指定 id 的物品",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string"},
                        "item_id": {"type": "string"},
                    },
                    "required": ["entity_id", "item_id"],
                },
            },
        },
        "log_event": {
            "handler": lambda **kw: W.log_event(world, **kw),
            "schema": {
                "name": "log_event",
                "description": "向世界事件日志追加一条事件记录(用于历史溯源)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "event": {
                            "type": "object",
                            "description": "事件对象,应包含 actor/type/summary 等字段",
                        },
                    },
                    "required": ["event"],
                },
            },
        },
        "set_flag": {
            "handler": lambda **kw: W.set_flag(world, **kw),
            "schema": {
                "name": "set_flag",
                "description": "设置剧情标记(key-value)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string"},
                        "value": {},
                    },
                    "required": ["key", "value"],
                },
            },
        },
        "add_memory": {
            "handler": lambda **kw: W.add_memory(world, **kw),
            "schema": {
                "name": "add_memory",
                "description": (
                    "给 NPC 添加记忆(NPC 会记住玩家做过的事)。"
                    "importance 0-10,值越高 NPC 越容易回忆起。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string"},
                        "text": {"type": "string"},
                        "importance": {"type": "integer", "default": 5},
                    },
                    "required": ["entity_id", "text"],
                },
            },
        },
        "advance_time": {
            "handler": lambda **kw: W.advance_time(world, **kw),
            "schema": {
                "name": "advance_time",
                "description": "推进游戏内时间。units='shichen'(时辰,2小时)或'day'(天)。时辰从亥时→子时会自动增加day_index。",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "units": {"type": "string", "default": "shichen"},
                        "amount": {"type": "integer", "default": 1},
                    },
                },
            },
        },
        "transfer_money": {
            "handler": lambda **kw: W.transfer_money(world, **kw),
            "schema": {
                "name": "transfer_money",
                "description": "在两个实体之间转移金钱(文)。用于给赏钱、赔偿、贿赂等纯金钱转移。",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "from_entity": {"type": "string",
                                         "description": "出钱方实体ID"},
                        "to_entity": {"type": "string",
                                       "description": "收钱方实体ID"},
                        "amount": {"type": "integer",
                                    "description": "转移金额(文),必须>0"},
                        "reason": {"type": "string", "default": "",
                                    "description": "交易原因(如'给赏钱','赔偿')"},
                    },
                    "required": ["from_entity", "to_entity", "amount"],
                },
            },
        },
        "purchase_item": {
            "handler": lambda **kw: W.purchase_item(world, **kw),
            "schema": {
                "name": "purchase_item",
                "description": (
                    "购买卖方库存中的物品: 自动扣钱、给钱、转移物品数量。"
                    "优先使用卖方 attributes.price_list[item_id],也可临时提供 unit_price_wen。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "buyer": {"type": "string", "description": "买方实体ID"},
                        "seller": {"type": "string", "description": "卖方实体ID"},
                        "item_id": {"type": "string", "description": "物品ID"},
                        "qty": {"type": "integer", "default": 1},
                        "unit_price_wen": {"type": "integer",
                                           "description": "临时单价(文),可省略以使用价目表"},
                        "reason": {"type": "string", "default": ""},
                    },
                    "required": ["buyer", "seller", "item_id"],
                },
            },
        },
        "hire_service": {
            "handler": lambda **kw: W.hire_service(world, **kw),
            "schema": {
                "name": "hire_service",
                "description": (
                    "雇佣 NPC 或购买服务: 自动转钱,并在服务提供者 attributes.current_contract 记录契约。"
                    "优先使用 provider attributes.service_catalog[service_id].price_wen,也可临时提供 price_wen。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "payer": {"type": "string", "description": "付款方实体ID"},
                        "provider": {"type": "string", "description": "服务提供者实体ID"},
                        "service_id": {"type": "string", "description": "服务ID"},
                        "price_wen": {"type": "integer",
                                      "description": "临时价格(文),可省略以使用服务目录"},
                        "duration": {"type": "integer", "default": 1},
                        "reason": {"type": "string", "default": ""},
                    },
                    "required": ["payer", "provider", "service_id"],
                },
            },
        },
        "record_clue": {
            "handler": lambda **kw: W.record_clue(world, **kw),
            "schema": {
                "name": "record_clue",
                "description": (
                    "记录玩家发现的主线/支线线索。只写入 story_progress 和事件日志,"
                    "不判断任务是否完成或线索是否正确。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "thread_id": {"type": "string", "description": "剧情线ID"},
                        "clue": {"type": "string", "description": "发现的具体事实/证词/证物"},
                        "source_entity": {"type": "string", "default": "",
                                          "description": "线索来源NPC实体ID"},
                        "location_id": {"type": "string", "default": "",
                                        "description": "发现线索的地点ID"},
                        "evidence_item": {"type": "string", "default": "",
                                          "description": "相关证物或物品名"},
                    },
                    "required": ["thread_id", "clue"],
                },
            },
        },
        "advance_pressure_clock": {
            "handler": lambda **kw: W.advance_pressure_clock(world, **kw),
            "schema": {
                "name": "advance_pressure_clock",
                "description": (
                    "推进叙事压力钟,如证人受压/府衙耐心/舆论发酵。"
                    "代码只记录数值并报告是否达到危险线,具体升级后果由GM判断。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "clock_id": {"type": "string", "description": "压力钟ID"},
                        "amount": {"type": "integer", "default": 1},
                        "reason": {"type": "string", "default": ""},
                        "danger_at": {"type": "integer", "default": 3},
                    },
                    "required": ["clock_id"],
                },
            },
        },

        # ---------- COMBAT ----------
        "skill_check": {
            "handler": lambda **kw: U.skill_check(**kw),
            "schema": {
                "name": "skill_check",
                "description": (
                    "技能/攻击检定: 掷1d20 + attribute_value + modifier, 与DC比较。"
                    "自然20=大成功(无视DC), 自然1=大失败(无视modifier)。"
                    "advantage=True 时掷两次取高。"
                    "返回 success/margin/critical 供叙事使用。"
                    "用法: 攻击时 attribute_value=攻击方str/dex, dc=防御方defense; "
                    "非战斗检定时 attribute_value=对应属性值, dc=难度等级。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "attribute_value": {
                            "type": "integer",
                            "description": "属性加值(如 str/dex 值)",
                        },
                        "dc": {
                            "type": "integer",
                            "description": "难度等级(DC), 攻击时为对方defense",
                        },
                        "modifier": {
                            "type": "integer", "default": 0,
                            "description": "额外调整值(如武器加成、环境因素)",
                        },
                        "advantage": {
                            "type": "boolean", "default": False,
                            "description": "是否优势(掷两次取高)",
                        },
                    },
                    "required": ["attribute_value", "dc"],
                },
            },
        },
        "apply_damage": {
            "handler": lambda **kw: W.apply_damage(world, **kw),
            "schema": {
                "name": "apply_damage",
                "description": (
                    "对实体造成伤害,扣减HP。"
                    "HP降至0时 incapacitated=True,但不会自动添加'死亡'/'昏迷'状态——"
                    "你需要根据情境调用 add_status 和 log_event。"
                    "damage_type 用于区分物理/火焰/毒等。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string"},
                        "amount": {
                            "type": "integer",
                            "description": "伤害量(必须≥0)",
                        },
                        "damage_type": {
                            "type": "string", "default": "physical",
                            "description": "伤害类型: physical/fire/poison 等",
                        },
                        "source": {
                            "type": "string", "default": "",
                            "description": "伤害来源(攻击方ID或描述)",
                        },
                    },
                    "required": ["entity_id", "amount"],
                },
            },
        },
        "tick_statuses": {
            "handler": lambda **kw: W.tick_statuses(world, **kw),
            "schema": {
                "name": "tick_statuses",
                "description": (
                    "推进一回合/一个时辰: 对所有状态效果 duration-1, "
                    "到期自动移除, damage_per_tick>0 的造成对应伤害。"
                    "entity_id 留空则对全部实体生效。"
                    "战斗回合结束时必须调用,也可在 narrative time 推进时调用。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": "指定实体ID,留空则全部实体",
                        },
                    },
                },
            },
        },
        # ---------- Phase 6 Step 2: Advisor ----------
        "ask_advisor": {
            "handler": lambda **kw: W.ask_advisor(world, **kw),
            "schema": {
                "name": "ask_advisor",
                "description": (
                    "记录一次玩家向顾问NPC请教,返回顾问资料供GM生成建议。"
                    "此工具不生成建议内容——建议由GM以顾问口吻说出。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "advisor_id": {
                            "type": "string",
                            "description": "顾问NPC的ID",
                        },
                        "question": {
                            "type": "string",
                            "description": "玩家向顾问请教的问题",
                        },
                        "player_id": {
                            "type": "string", "default": "player",
                            "description": "玩家实体ID",
                        },
                        "topic": {
                            "type": "string", "default": "",
                            "description": "请教的主题分类,可选",
                        },
                    },
                    "required": ["advisor_id", "question"],
                },
            },
        },
        "list_advisors": {
            "handler": lambda **kw: R.list_advisors(world, **kw),
            "schema": {
                "name": "list_advisors",
                "description": (
                    "列出世界中所有顾问NPC,可选按地点过滤。"
                    "用于发现可咨询的对象。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "location_id": {
                            "type": "string",
                            "description": "按地点过滤,留空则返回全部顾问",
                        },
                    },
                },
            },
        },
        # ---------- Phase 6 Step 4: Party ----------
        "list_party": {
            "handler": lambda **kw: R.list_party(world, **kw),
            "schema": {
                "name": "list_party",
                "description": "列出玩家当前队伍成员和当前行动角色。代码只返回队伍数据,不判断谁该行动。",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "leader_id": {"type": "string", "default": "player"},
                    },
                },
            },
        },
        "join_party": {
            "handler": lambda **kw: W.join_party(world, **kw),
            "schema": {
                "name": "join_party",
                "description": "记录某实体加入玩家队伍。只记录关系、记忆和事件,是否愿意加入由GM判断。",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string", "description": "加入队伍的实体ID"},
                        "leader_id": {"type": "string", "default": "player"},
                        "role": {"type": "string", "default": "同伴"},
                        "joined_reason": {"type": "string", "default": ""},
                    },
                    "required": ["entity_id"],
                },
            },
        },
        "leave_party": {
            "handler": lambda **kw: W.leave_party(world, **kw),
            "schema": {
                "name": "leave_party",
                "description": "记录某实体离开玩家队伍。只记录关系、记忆和事件,离队原因由GM叙述。",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string", "description": "离开队伍的实体ID"},
                        "leader_id": {"type": "string", "default": "player"},
                        "reason": {"type": "string", "default": ""},
                    },
                    "required": ["entity_id"],
                },
            },
        },
        "set_active_actor": {
            "handler": lambda **kw: W.set_active_actor(world, **kw),
            "schema": {
                "name": "set_active_actor",
                "description": "设置当前行动角色为某个队伍成员。用于同行者代为交涉/观察/行动。",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string", "description": "队伍成员实体ID"},
                        "leader_id": {"type": "string", "default": "player"},
                        "reason": {"type": "string", "default": ""},
                    },
                    "required": ["entity_id"],
                },
            },
        },
        # ---------- Phase 6 Step 3: Observation ----------
        "list_observables": {
            "handler": lambda **kw: R.list_observables(world, **kw),
            "schema": {
                "name": "list_observables",
                "description": (
                    "列出玩家当前位置已可见或已发现的可观察细节。"
                    "细节来自地点 observable_details 和同地点实体 attributes.observable_details。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "actor_id": {"type": "string", "default": "player"},
                        "include_discovered": {"type": "boolean", "default": True},
                    },
                },
            },
        },
        "discover_observation": {
            "handler": lambda **kw: W.discover_observation(world, **kw),
            "schema": {
                "name": "discover_observation",
                "description": (
                    "记录玩家发现了一个可观察细节。只持久化发现事实和事件,"
                    "不判断线索意义或后续后果。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "detail_id": {"type": "string", "description": "细节ID"},
                        "target_id": {"type": "string", "description": "地点或实体ID,可选"},
                        "actor_id": {"type": "string", "default": "player"},
                        "source": {"type": "string", "default": "observe"},
                    },
                    "required": ["detail_id"],
                },
            },
        },
        # ---------- Phase 6: Skills / 修炼 ----------
        "list_skills": {
            "handler": lambda **kw: R.list_skills(world, **kw),
            "schema": {
                "name": "list_skills",
                "description": "列出某个实体的技能列表(含等级、经验)。默认查玩家。",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string", "default": "player"},
                    },
                },
            },
        },
        "advance_skill": {
            "handler": lambda **kw: W.advance_skill(world, **kw),
            "schema": {
                "name": "advance_skill",
                "description": (
                    "增加/减少某个实体的技能经验和等级。代码只执行加减操作,"
                    "是否获得经验、何时突破由GM根据叙事判断。"
                    "技能存于 entity attributes.skills[skill_id]。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string", "description": "实体ID"},
                        "skill_id": {"type": "string", "description": "技能ID(如 'litigation','martial_arts')"},
                        "xp_delta": {"type": "integer", "default": 0, "description": "经验变化量"},
                        "level_delta": {"type": "integer", "default": 0, "description": "等级变化量"},
                        "name": {"type": "string", "default": "", "description": "技能中文名(可选,仅首次或更名时填)"},
                        "reason": {"type": "string", "default": "", "description": "原因说明(用于审计)"},
                        "note": {"type": "string", "default": "", "description": "备注信息(可选)"},
                    },
                    "required": ["entity_id", "skill_id"],
                },
            },
        },
        "list_quest_log": {
            "handler": lambda **kw: R.list_quest_log(world, **kw),
            "schema": {
                "name": "list_quest_log",
                "description": (
                    "列出调查日志中的里程碑条目。"
                    "可按 status 过滤(active/completed/locked)。"
                    "用于了解跨地域调查的整体进度。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "按状态过滤: active/completed/locked,留空返回全部",
                        },
                    },
                },
            },
        },
        "update_quest_log": {
            "handler": lambda **kw: W.update_quest_log(world, **kw),
            "schema": {
                "name": "update_quest_log",
                "description": (
                    "添加或更新调查日志条目。"
                    "用于记录跨地域调查的里程碑进展。"
                    "status 可为: active(进行中)/completed(已完成)/locked(未解锁)。"
                    "代码只持久化条目,由GM决定何时解锁和完成。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entry_id": {"type": "string", "description": "条目稳定ID"},
                        "title": {"type": "string", "description": "里程碑标题"},
                        "description": {"type": "string", "default": "", "description": "详细描述"},
                        "region": {"type": "string", "default": "",
                                   "description": "关联地域: yangzhou/guazhou/nanjing/suzhou/hangzhou"},
                        "status": {"type": "string", "default": "active",
                                   "description": "状态: active/completed/locked"},
                    },
                    "required": ["entry_id", "title"],
                },
            },
        },
        "list_endings": {
            "handler": lambda **kw: R.list_endings(world, **kw),
            "schema": {
                "name": "list_endings",
                "description": "列出可用结局种子和已记录的结局进度。代码只返回数据,不判断是否达成。",
                "input_schema": {"type": "object", "properties": {}},
            },
        },
        "record_ending": {
            "handler": lambda **kw: W.record_ending(world, **kw),
            "schema": {
                "name": "record_ending",
                "description": (
                    "记录一个已达成或候选结局。代码只持久化GM给出的结局标题、摘要和结果,"
                    "不自动判断结局条件。final=true 表示主线正式收束。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "ending_id": {"type": "string", "description": "稳定结局ID"},
                        "title": {"type": "string", "description": "结局标题"},
                        "summary": {"type": "string", "description": "结局摘要"},
                        "outcome": {"type": "string", "default": "", "description": "余波/后果"},
                        "actor_id": {"type": "string", "default": "player"},
                        "thread_id": {"type": "string", "default": "main_thread"},
                        "final": {"type": "boolean", "default": False},
                    },
                    "required": ["ending_id", "title", "summary"],
                },
            },
        },
        "update_ending_progress": {
            "handler": lambda **kw: W.update_ending_progress(world, **kw),
            "schema": {
                "name": "update_ending_progress",
                "description": (
                    "注册或更新一个结局方向的进度步骤。代码只存储步骤状态,GM决定有哪些步骤、"
                    "何时完成。用于向玩家展示距离各结局方向还有多远。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "ending_id": {"type": "string", "description": "结局方向ID(应与 ending_seeds 中的 id 对应)"},
                        "step_id": {"type": "string", "description": "步骤ID(稳定标识)"},
                        "step_label": {"type": "string", "description": "步骤描述(展示给玩家看)"},
                        "completed": {"type": "boolean", "default": True, "description": "是否已完成"},
                    },
                    "required": ["ending_id", "step_id", "step_label"],
                },
            },
        },
        "train_skill": {
            "handler": lambda **kw: W.train_skill(world, **kw),
            "schema": {
                "name": "train_skill",
                "description": (
                    "记录一次修炼/练习并授予经验。代码只执行经验加算和事件记录,"
                    "是否获得经验、获得多少由GM根据叙事判断。"
                    "适用于玩家自主练习、读书、打坐等场景。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string", "description": "实体ID"},
                        "skill_id": {"type": "string", "description": "技能ID(如 'litigation','calligraphy')"},
                        "xp_granted": {"type": "integer", "default": 1, "description": "授予的经验值"},
                        "name": {"type": "string", "default": "", "description": "技能中文名(可选)"},
                        "reason": {"type": "string", "default": "", "description": "原因说明(用于审计)"},
                    },
                    "required": ["entity_id", "skill_id"],
                },
            },
        },
        "learn_from_npc": {
            "handler": lambda **kw: W.learn_from_npc(world, **kw),
            "schema": {
                "name": "learn_from_npc",
                "description": (
                    "记录向NPC学习并授予经验。代码验证教师是NPC,记录教师记忆和事件,"
                    "学习结果由GM根据叙事判断。"
                    "适用于向先生请教、拜师学艺、跟随练习等场景。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "learner_id": {"type": "string", "description": "学习者实体ID"},
                        "teacher_id": {"type": "string", "description": "教师NPC实体ID"},
                        "skill_id": {"type": "string", "description": "技能ID"},
                        "xp_granted": {"type": "integer", "default": 3, "description": "授予的经验值"},
                        "name": {"type": "string", "default": "", "description": "技能中文名(可选)"},
                        "reason": {"type": "string", "default": "", "description": "原因说明(用于审计)"},
                    },
                    "required": ["learner_id", "teacher_id", "skill_id"],
                },
            },
        },
        # ---------- Phase 31: Weather ----------
        "get_weather": {
            "handler": lambda **kw: R.get_weather(world, **kw),
            "schema": {
                "name": "get_weather",
                "description": (
                    "获取当前天气状况(天气类型、强度、描述)。"
                    "天气影响NPC行为、户外活动和叙述氛围。"
                    "未设置时根据季节返回默认天气。"
                ),
                "input_schema": {"type": "object", "properties": {}},
            },
        },
        "set_weather": {
            "handler": lambda **kw: W.set_weather(world, **kw),
            "schema": {
                "name": "set_weather",
                "description": (
                    "更新当前天气状况。"
                    "condition: clear(晴)/cloudy(阴)/rain(雨)/storm(暴风雨)/fog(雾)/snow(雪)。"
                    "intensity: light(轻微)/moderate(中等)/heavy(强烈)。"
                    "text: 天气描述文本,用于GM叙述。"
                    "天气变化应自然融入叙述,如'一阵秋风吹过,天色渐暗'。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "condition": {
                            "type": "string",
                            "description": "天气类型: clear/cloudy/rain/storm/fog/snow",
                        },
                        "intensity": {
                            "type": "string",
                            "default": "light",
                            "description": "强度: light/moderate/heavy",
                        },
                        "text": {
                            "type": "string",
                            "description": "天气描述文本,用于叙述",
                        },
                        "reason": {
                            "type": "string",
                            "default": "",
                            "description": "天气变化原因(用于审计)",
                        },
                    },
                },
            },
        },

        # ---------- Phase 10: World Evolution ----------
        "list_evolutions": {
            "handler": lambda **kw: R.list_evolutions(world, **kw),
            "schema": {
                "name": "list_evolutions",
                "description": (
                    "列出当前演化注册表中所有实体及其频率、上次演化时间。"
                    "用于了解哪些实体在持续演化、是否需要调整频率。"
                ),
                "input_schema": {"type": "object", "properties": {}},
            },
        },
        "register_evolution": {
            "handler": lambda **kw: W.register_evolution(world, **kw),
            "schema": {
                "name": "register_evolution",
                "description": (
                    "将实体注册到演化列表,使其在玩家不直接交互时也能持续变化。"
                    "frequency 决定演化频率: every_turn(每回合)/every_2_turns(隔一回合)/"
                    "every_5_turns(低频)/dormant(暂停)。"
                    "reason 记录注册原因供后续调整参考。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string", "description": "要注册演化的实体ID"},
                        "frequency": {
                            "type": "string",
                            "default": "every_2_turns",
                            "description": "演化频率: every_turn/every_2_turns/every_5_turns/dormant",
                        },
                        "reason": {"type": "string", "default": "", "description": "注册原因"},
                    },
                    "required": ["entity_id"],
                },
            },
        },
        "update_evolution": {
            "handler": lambda **kw: W.update_evolution(world, **kw),
            "schema": {
                "name": "update_evolution",
                "description": (
                    "更新已注册实体的演化频率或原因。"
                    "用于根据空间距离、叙事关联、时间衰减等因素动态调整。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string", "description": "实体ID"},
                        "frequency": {
                            "type": "string",
                            "description": "新频率: every_turn/every_2_turns/every_5_turns/dormant",
                        },
                        "reason": {"type": "string", "description": "更新原因"},
                    },
                    "required": ["entity_id"],
                },
            },
        },
        "remove_evolution": {
            "handler": lambda **kw: W.remove_evolution(world, **kw),
            "schema": {
                "name": "remove_evolution",
                "description": "将实体从演化列表中移除,停止其自动演化。",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string", "description": "要移除的实体ID"},
                    },
                    "required": ["entity_id"],
                },
            },
        },

        # ---------- Phase 28: NPC Dialogue ----------
        "get_npc_dialogue": {
            "handler": lambda **kw: R.get_npc_dialogue(world, **kw),
            "schema": {
                "name": "get_npc_dialogue",
                "description": (
                    "获取NPC可用的对话选项(问候/话题/告别/特殊台词)。"
                    "根据NPC对玩家的态度值过滤可用台词。"
                    "用于在玩家与NPC交谈前了解NPC可以说什么。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "npc_id": {
                            "type": "string",
                            "description": "NPC实体ID",
                        },
                        "player_id": {
                            "type": "string",
                            "default": "player",
                            "description": "玩家实体ID",
                        },
                    },
                    "required": ["npc_id"],
                },
            },
        },
        "record_dialogue": {
            "handler": lambda **kw: W.record_dialogue(world, **kw),
            "schema": {
                "name": "record_dialogue",
                "description": (
                    "记录一次玩家与NPC的对话交互。"
                    "添加NPC记忆、记录事件、可选调整态度值。"
                    "GM决定对话内容,代码只持久化状态变化。"
                    "revealed_rumor: NPC透露的传闻线索(如有)。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "npc_id": {
                            "type": "string",
                            "description": "NPC实体ID",
                        },
                        "player_id": {
                            "type": "string",
                            "default": "player",
                            "description": "玩家实体ID",
                        },
                        "topic": {
                            "type": "string",
                            "default": "",
                            "description": "对话主题(如'打听消息','问路')",
                        },
                        "player_line": {
                            "type": "string",
                            "default": "",
                            "description": "玩家说的话(摘要)",
                        },
                        "npc_response": {
                            "type": "string",
                            "default": "",
                            "description": "NPC的回应(摘要)",
                        },
                        "attitude_delta": {
                            "type": "integer",
                            "default": 0,
                            "description": "态度变化量(正=友善,负=敌意)",
                        },
                        "revealed_rumor": {
                            "type": "string",
                            "default": "",
                            "description": "NPC透露的传闻线索(如有)",
                        },
                    },
                    "required": ["npc_id"],
                },
            },
        },
        # ---------- Phase 16: Multi-Agent Delegation ----------
        "delegate_to_agent": {
            "handler": lambda **kw: _delegate_to_agent(world, **kw),
            "schema": {
                "name": "delegate_to_agent",
                "description": (
                    "将特定任务委托给专业 Agent 处理。"
                    "当前支持的 agent_id: combat(战斗专家), social(社交专家), law(法律专家)。"
                    "用于复杂战斗场景，让战斗专家处理攻击检定、伤害计算等细节；"
                    "用于社交场景，让社交专家处理说服、欺骗、威吓、议价等互动；"
                    "用于法律场景，让法律专家处理法条检索、量刑分析、司法程序。"
                    "返回专业 Agent 的处理结果，包括叙述和执行的写操作。"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "description": "专业 Agent ID，如 'combat', 'social', 'law'",
                        },
                        "context": {
                            "type": "object",
                            "description": (
                                "委托上下文，包含 Agent 所需信息。"
                                "combat agent 需要: attacker_id, defender_id, player_input。"
                                "social agent 需要: target_id, interaction_type, player_input。"
                                "interaction_type: persuasion/deception/intimidation/negotiation/insight"
                                "law agent 需要: player_input, case_type(criminal/civil/procedural/administrative)。"
                                "可选: defendant_id, charges, legal_context(含 victim_id/witness_ids/evidence/severity)"
                            ),
                        },
                    },
                    "required": ["agent_id", "context"],
                },
            },
        },
    }


def get_anthropic_tools(registry: dict) -> list:
    """Return tools in Anthropic API format."""
    return [t["schema"] for t in registry.values()]


def _delegate_to_agent(world, agent_id: str, context: dict) -> dict:
    """Handler for delegate_to_agent tool.

    Routes delegation requests to the appropriate specialized agent.
    """
    agents = {
        "combat": CombatAgent,
        "social": SocialAgent,
        "law": LawAgent,
    }

    agent_cls = agents.get(agent_id)
    if agent_cls is None:
        return {"error": f"unknown agent '{agent_id}', available: {list(agents.keys())}"}

    try:
        agent = agent_cls(world)
        return agent.process(context)
    except Exception as e:
        return {"error": f"agent '{agent_id}' failed: {type(e).__name__}: {e}"}
