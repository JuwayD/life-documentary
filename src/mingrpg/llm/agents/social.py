"""SocialAgent — specialized agent for social interactions."""
import json
import os
from typing import Any

from anthropic import Anthropic

from mingrpg.core.world import World
from mingrpg.llm.agents.base import AgentBase
from mingrpg.tools import util as U
from mingrpg.tools import write as W


SOCIAL_SYSTEM_PROMPT = """你是社交专家 Agent，专门处理明代背景 RPG 中的社交与人际互动场景。

【职责】
- 接收 GM Agent 传来的社交上下文
- 执行社交检定（说服、欺骗、威吓、议价等）
- 管理 NPC 态度变化与记忆
- 返回社交结果供 GM 融入叙述

【社交检定类型】
1. 说服 (persuasion): 以理服人，用 CHA 检定
   - DC 10: 对方本就倾向同意
   - DC 15: 对方中立，需要好理由
   - DC 20: 对方本不同意，需要强理由
   - DC 25: 对方强烈反对，极难说服
2. 欺骗 (deception): 隐瞒真相或编造谎言，用 CHA 检定
   - DC 10: 小谎言，对方不警觉
   - DC 15: 一般谎言
   - DC 20: 重大谎言或对方警觉
   - DC 25: 荒谬谎言或对方极度警觉
3. 威吓 (intimidation): 以势压人，用 STR 或 CHA 检定
   - DC 10: 对方胆小或处于弱势
   - DC 15: 一般威吓
   - DC 20: 对方有底气或性格刚强
   - DC 25: 对方有强大靠山
4. 察言观色 (insight): 判断对方是否在说谎或隐瞒，用 WIS 检定
   - DC 10: 对方明显紧张
   - DC 15: 一般掩饰
   - DC 20: 对方善于隐藏
   - DC 25: 对方面无表情

【议价规则】
- 基础价格由场景物价决定
- CHA 检定成功可降价 10-30%（视 margin 而定）
- 大成功（自然20）可降价 50%
- 大失败（自然1）对方加价或拒绝交易
- 商人性格影响底价：贪财商人难砍价，爽快商人好说话

【NPC 态度系统】
- 态度值范围: -100（仇恨）到 +100（崇拜）
- 初始态度由 NPC 性格和玩家身份决定
- 社交检定结果会改变态度值：
  - 大成功: +15~+20
  - 成功: +5~+10
  - 失败: -5~-10
  - 大失败: -15~-20
- 态度影响 NPC 行为：友好时提供帮助，敌对时拒绝或攻击

【输出要求】
- 返回 JSON 格式的结果
- 包含 narration（社交描写）和 writes（执行的写操作列表）
- 社交描写要有画面感：表情、语气、肢体语言
- 描述要符合明代社会礼仪和阶层关系
- 注意明代身份差异：对官员要恭敬，对平民可平等，对仆从可居高临下

现在处理社交互动。"""


class SocialAgent(AgentBase):
    """Specialized agent for social interactions (persuasion, deception,
    intimidation, negotiation, insight)."""

    agent_id = "social"

    def __init__(self, world: World, model: str = "mimo-v2.5-pro",
                 api_key: str | None = None, base_url: str | None = None):
        super().__init__(world)
        self.model = model
        self.client = Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"),
            base_url=base_url or os.environ.get("ANTHROPIC_BASE_URL"),
        )

    def get_system_prompt(self) -> str:
        return SOCIAL_SYSTEM_PROMPT

    def get_tools(self) -> list[dict[str, Any]]:
        """Return social-specific tool schemas."""
        return [
            {
                "name": "skill_check",
                "description": "社交检定: 掷1d20 + 属性值 + 修正, 与DC比较",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "attribute_value": {
                            "type": "integer",
                            "description": "属性加值 (CHA/WIS/STR)",
                        },
                        "dc": {
                            "type": "integer",
                            "description": "难度等级",
                        },
                        "modifier": {
                            "type": "integer",
                            "default": 0,
                            "description": "额外调整值 (好感度/身份加成等)",
                        },
                        "advantage": {
                            "type": "boolean",
                            "default": False,
                            "description": "是否优势 (如对方本就倾向同意)",
                        },
                    },
                    "required": ["attribute_value", "dc"],
                },
            },
            {
                "name": "add_memory",
                "description": "为 NPC 添加社交记忆 (印象深刻、被欺骗、被威吓等)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": "NPC 实体 ID",
                        },
                        "memory": {
                            "type": "string",
                            "description": "记忆内容",
                        },
                        "importance": {
                            "type": "string",
                            "default": "normal",
                            "description": "重要程度: low/normal/high",
                        },
                    },
                    "required": ["entity_id", "memory"],
                },
            },
            {
                "name": "set_attribute",
                "description": "修改 NPC 属性 (如 attitude 态度值)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string"},
                        "attr": {
                            "type": "string",
                            "description": "属性名 (如 attitude, trust 等)",
                        },
                        "value": {
                            "description": "新属性值",
                        },
                    },
                    "required": ["entity_id", "attr", "value"],
                },
            },
            {
                "name": "add_status",
                "description": "添加社交状态效果 (如 charmed/impressed/intimidated/suspicious)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string"},
                        "status": {
                            "type": "string",
                            "description": "状态名",
                        },
                        "duration": {
                            "type": "integer",
                            "default": 3,
                            "description": "持续回合数",
                        },
                        "reason": {
                            "type": "string",
                            "default": "",
                            "description": "原因",
                        },
                    },
                    "required": ["entity_id", "status"],
                },
            },
            {
                "name": "transfer_money",
                "description": "议价结果: 转移金钱 (如降价后支付)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "from_entity": {"type": "string"},
                        "to_entity": {"type": "string"},
                        "amount": {
                            "type": "integer",
                            "description": "金额 (文)",
                        },
                    },
                    "required": ["from_entity", "to_entity", "amount"],
                },
            },
            {
                "name": "log_event",
                "description": "记录重要社交事件",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "event": {
                            "type": "object",
                            "description": (
                                "事件对象，包含 type/summary/detail 等字段"
                            ),
                        },
                    },
                    "required": ["event"],
                },
            },
        ]

    def _build_tool_registry(self) -> dict:
        """Build tool handler registry for social tools."""
        return {
            "skill_check": {"handler": lambda **kw: U.skill_check(**kw)},
            "add_memory": {
                "handler": lambda **kw: W.add_memory(self.world, **kw)
            },
            "set_attribute": {
                "handler": lambda **kw: W.set_attribute(self.world, **kw)
            },
            "add_status": {
                "handler": lambda **kw: W.add_status(self.world, **kw)
            },
            "transfer_money": {
                "handler": lambda **kw: W.transfer_money(self.world, **kw)
            },
            "log_event": {
                "handler": lambda **kw: W.log_event(self.world, **kw)
            },
        }

    def process(self, context: dict[str, Any]) -> dict[str, Any]:
        """Process a social interaction delegation request.

        Args:
            context: Dict with keys:
                - player_id: str (default "player")
                - target_id: str (NPC entity ID)
                - interaction_type: str (persuasion/deception/intimidation/
                  negotiation/insight)
                - player_input: str (original player input)
                - social_context: dict (optional, additional context like
                  topic, offer_price, etc.)

        Returns:
            Dict with:
                - narration: str (social interaction description)
                - writes: list of write operations
                - social_result: dict (structured outcome)
        """
        registry = self._build_tool_registry()
        tools = self.get_tools()

        player_id = context.get("player_id", "player")
        target_id = context.get("target_id", "")
        interaction_type = context.get("interaction_type", "persuasion")

        player = self.world.get_entity(player_id)
        target = self.world.get_entity(target_id)

        if not player or not target:
            return {
                "narration": "社交参与者信息不完整。",
                "writes": [],
                "social_result": {"error": "missing participant"},
            }

        player_attrs = player.get("attributes", {})
        target_attrs = target.get("attributes", {})

        # Build context message for the LLM
        context_msg = (
            f"【社交上下文】\n"
            f"发起方: {player['name']} (ID={player['id']})\n"
            f"  - CHA={player_attrs.get('cha', 10)}, "
            f"STR={player_attrs.get('str', 10)}, "
            f"WIS={player_attrs.get('wis', 10)}\n"
            f"  - 身份: {player_attrs.get('identity', '书生')}\n"
            f"目标: {target['name']} (ID={target['id']})\n"
            f"  - 职业: {target_attrs.get('occupation', '?')}\n"
            f"  - 性格: {target_attrs.get('personality', '?')}\n"
            f"  - 当前态度: {target_attrs.get('attitude', 0)}\n"
            f"互动类型: {interaction_type}\n"
            f"玩家输入: {context.get('player_input', '')}\n"
        )

        if context.get("social_context"):
            ctx = context["social_context"]
            if ctx.get("topic"):
                context_msg += f"话题: {ctx['topic']}\n"
            if ctx.get("offer_price") is not None:
                context_msg += f"出价: {ctx['offer_price']}文\n"
            if ctx.get("original_price") is not None:
                context_msg += f"原价: {ctx['original_price']}文\n"
            if ctx.get("lie"):
                context_msg += f"谎言内容: {ctx['lie']}\n"

        # Add NPC memories for context
        memories = target_attrs.get("memories", [])
        if memories:
            recent = memories[-3:]
            context_msg += (
                f"NPC 近期记忆: "
                + "; ".join(str(m) for m in recent)
                + "\n"
            )

        messages = [{"role": "user", "content": context_msg}]

        writes = []
        narration_parts = []

        try:
            for _ in range(5):  # Max 5 iterations for social interaction
                response = self.client.messages.create(
                    model=self.model,
                    system=self.get_system_prompt(),
                    tools=tools,
                    max_tokens=2048,
                    messages=messages,
                )

                for block in response.content:
                    if block.type == "text" and block.text:
                        narration_parts.append(block.text)

                if response.stop_reason != "tool_use":
                    break

                messages.append({"role": "assistant", "content": response.content})
                tool_results = []

                for block in response.content:
                    if block.type != "tool_use":
                        continue

                    name = block.name
                    args = block.input or {}
                    handler = registry.get(name, {}).get("handler")

                    if handler is None:
                        out = {"error": f"unknown tool '{name}'"}
                    else:
                        try:
                            out = handler(**args)
                        except Exception as e:
                            out = {"error": f"{type(e).__name__}: {e}"}

                    writes.append({"tool": name, "args": args, "result": out})
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(out, ensure_ascii=False),
                    })

                messages.append({"role": "user", "content": tool_results})

        except Exception as e:
            return {
                "narration": f"社交处理出错: {e}",
                "writes": writes,
                "social_result": {"error": str(e)},
            }

        narration = "\n\n".join(
            p.strip() for p in narration_parts if p and p.strip()
        )
        if not narration:
            narration = f"{target['name']}沉默不语。"

        # Build structured social result
        target_final = self.world.get_entity(target_id)
        player_final = self.world.get_entity(player_id)

        return {
            "narration": narration,
            "writes": writes,
            "social_result": {
                "interaction_type": interaction_type,
                "target_attitude": (
                    target_final["attributes"].get("attitude", 0)
                    if target_final else 0
                ),
                "target_id": target_id,
                "player_id": player_id,
            },
        }
