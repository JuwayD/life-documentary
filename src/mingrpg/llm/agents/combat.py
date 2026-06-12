"""CombatAgent — specialized agent for handling combat encounters."""
import json
import os
from typing import Any

from anthropic import Anthropic

from mingrpg.core.world import World
from mingrpg.llm.agents.base import AgentBase
from mingrpg.tools import util as U
from mingrpg.tools import write as W


COMBAT_SYSTEM_PROMPT = """你是战斗专家 Agent，专门处理明代背景 RPG 中的战斗与冲突场景。

【职责】
- 接收 GM Agent 传来的战斗上下文
- 执行攻击检定、伤害计算、状态管理
- 返回战斗结果供 GM 融入叙述

【战斗流程】
1. 读取攻击方和防御方属性
2. 调用 skill_check 进行攻击检定 (1d20 + str/dex vs defense)
3. 若命中，调用 roll_dice 计算伤害
4. 调用 apply_damage 扣减 HP
5. 必要时调用 add_status 添加持续效果（中毒、流血等）
6. 回合结束时调用 tick_statuses 推进状态衰减

【检定规则】
- 攻击: skill_check(attribute_value=攻击方str或dex, dc=防御方defense)
- 伤害: roll_dice(武器damage dice)，如 "1d6"、"1d8"
- 自然20: 大成功，伤害可加倍
- 自然1: 大失败，可描述反效果
- 优势(advantage): 伏击、高处、人多打人少
- 劣势: 被围、受伤、醉酒 → modifier=-2~-5

【输出要求】
- 返回 JSON 格式的结果
- 包含 narration（战斗描写）和 writes（执行的写操作列表）
- 战斗描写要有画面感：动作、表情、伤害效果
- 描述要符合明代语境

现在处理战斗回合。"""


class CombatAgent(AgentBase):
    """Specialized agent for combat encounters."""

    agent_id = "combat"

    def __init__(self, world: World, model: str = "mimo-v2.5-pro",
                 api_key: str | None = None, base_url: str | None = None):
        super().__init__(world)
        self.model = model
        self.client = Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"),
            base_url=base_url or os.environ.get("ANTHROPIC_BASE_URL"),
        )

    def get_system_prompt(self) -> str:
        return COMBAT_SYSTEM_PROMPT

    def get_tools(self) -> list[dict[str, Any]]:
        """Return combat-specific tool schemas."""
        return [
            {
                "name": "skill_check",
                "description": "攻击检定: 掷1d20 + attribute_value + modifier, 与DC比较",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "attribute_value": {"type": "integer", "description": "属性加值"},
                        "dc": {"type": "integer", "description": "难度等级"},
                        "modifier": {"type": "integer", "default": 0, "description": "额外调整值"},
                        "advantage": {"type": "boolean", "default": False, "description": "是否优势"},
                    },
                    "required": ["attribute_value", "dc"],
                },
            },
            {
                "name": "roll_dice",
                "description": "掷骰子计算伤害",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "notation": {"type": "string", "description": "骰子格式如 1d6+2"},
                    },
                    "required": ["notation"],
                },
            },
            {
                "name": "apply_damage",
                "description": "对实体造成伤害",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string"},
                        "amount": {"type": "integer", "description": "伤害量"},
                        "damage_type": {"type": "string", "default": "physical"},
                        "source": {"type": "string", "default": ""},
                    },
                    "required": ["entity_id", "amount"],
                },
            },
            {
                "name": "add_status",
                "description": "添加状态效果(中毒、流血、眩晕等)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string"},
                        "status": {"type": "string"},
                        "duration": {"type": "integer", "default": 1},
                        "reason": {"type": "string", "default": ""},
                        "damage_per_tick": {"type": "integer", "default": 0},
                        "effect_type": {"type": "string"},
                    },
                    "required": ["entity_id", "status"],
                },
            },
            {
                "name": "tick_statuses",
                "description": "推进状态效果衰减和持续伤害",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string", "description": "指定实体，留空则全部"},
                    },
                },
            },
        ]

    def _build_tool_registry(self) -> dict:
        """Build tool handler registry for combat tools."""
        return {
            "skill_check": {"handler": lambda **kw: U.skill_check(**kw)},
            "roll_dice": {"handler": lambda **kw: U.roll_dice(**kw)},
            "apply_damage": {"handler": lambda **kw: W.apply_damage(self.world, **kw)},
            "add_status": {"handler": lambda **kw: W.add_status(self.world, **kw)},
            "tick_statuses": {"handler": lambda **kw: W.tick_statuses(self.world, **kw)},
        }

    def process(self, context: dict[str, Any]) -> dict[str, Any]:
        """Process a combat delegation request.

        Args:
            context: Dict with keys:
                - attacker_id: str (attacker entity ID)
                - defender_id: str (defender entity ID)
                - player_input: str (original player input)
                - combat_state: dict (optional, additional combat context)

        Returns:
            Dict with:
                - narration: str (combat description)
                - writes: list of write operations
                - combat_result: dict (structured combat outcome)
        """
        registry = self._build_tool_registry()
        tools = self.get_tools()

        # Build context message
        attacker = self.world.get_entity(context.get("attacker_id", "player"))
        defender = self.world.get_entity(context.get("defender_id", ""))

        if not attacker or not defender:
            return {
                "narration": "战斗参与者信息不完整。",
                "writes": [],
                "combat_result": {"error": "missing combatant"},
            }

        context_msg = (
            f"【战斗上下文】\n"
            f"攻击方: {attacker['name']} (ID={attacker['id']}, "
            f"HP={attacker['attributes'].get('hp', '?')}, "
            f"STR={attacker['attributes'].get('str', 10)}, "
            f"DEX={attacker['attributes'].get('dex', 10)})\n"
            f"防御方: {defender['name']} (ID={defender['id']}, "
            f"HP={defender['attributes'].get('hp', '?')}, "
            f"defense={defender['attributes'].get('defense', 10)})\n"
            f"玩家输入: {context.get('player_input', '')}\n"
            f"武器: {attacker['attributes'].get('weapon_name', '徒手')} "
            f"({attacker['attributes'].get('weapon_damage', '1d4')})\n"
        )

        if context.get("combat_state"):
            context_msg += f"附加状态: {json.dumps(context['combat_state'], ensure_ascii=False)}\n"

        messages = [{"role": "user", "content": context_msg}]

        writes = []
        narration_parts = []

        try:
            for _ in range(5):  # Max 5 iterations for combat
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
                "narration": f"战斗处理出错: {e}",
                "writes": writes,
                "combat_result": {"error": str(e)},
            }

        narration = "\n\n".join(p.strip() for p in narration_parts if p and p.strip())
        if not narration:
            narration = "战斗激烈进行中..."

        # Build structured combat result
        attacker_final = self.world.get_entity(context.get("attacker_id", "player"))
        defender_final = self.world.get_entity(context.get("defender_id", ""))

        return {
            "narration": narration,
            "writes": writes,
            "combat_result": {
                "attacker_hp": attacker_final["attributes"].get("hp", 0) if attacker_final else 0,
                "defender_hp": defender_final["attributes"].get("hp", 0) if defender_final else 0,
                "attacker_incapacitated": any(
                    s.get("name") in ("昏迷", "濒死")
                    for s in (attacker_final or {}).get("status_effects", [])
                ),
                "defender_incapacitated": any(
                    s.get("name") in ("昏迷", "濒死")
                    for s in (defender_final or {}).get("status_effects", [])
                ),
            },
        }
