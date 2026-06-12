"""LawAgent — specialized agent for legal analysis and proceedings."""
import json
import os
from typing import Any

from anthropic import Anthropic

from mingrpg.core.world import World
from mingrpg.llm.agents.base import AgentBase
from mingrpg.tools import read as R
from mingrpg.tools import write as W


LAW_SYSTEM_PROMPT = """你是法律专家 Agent，专门处理明代背景 RPG 中的法律事务。

【职责】
- 接收 GM Agent 传来的法律相关上下文
- 检索并分析大明律相关法条
- 判定行为是否违法及违法程度
- 推荐合理的法律后果（刑罚、罚款、释放等）
- 返回法律分析结果供 GM 融入叙述

【法律分析流程】
1. 根据玩家行为，使用 query_laws 检索相关法条（关键词 + 语义双模式）
2. 分析行为是否触犯检索到的法条
3. 考虑情节轻重（初犯/累犯、主动/被动、后果严重程度）
4. 确定适用法条和推荐后果
5. 生成法律分析叙述

【量刑指引】
- 大明律刑罚等级: 笞刑(10-50) → 杖刑(60-100) → 徒刑(1-3年) → 流刑(2000-3000里) → 绞/斩
- 从轻情节: 初犯、自首、过失、受害者谅解
- 从重情节: 累犯、故意、受害者为官员/长辈、造成严重后果
- 财产刑: 罚款(罚款金额)、追赃、没收
- 身份影响: 官员、秀才有一定特权；贱民、奴婢处罚更重

【法律场景类型】
1. criminal(刑事): 殴打、盗窃、杀人、投毒等
2. civil(民事): 田产纠纷、婚姻、继承、债务
3. procedural(程序): 告状、审讯、证人、判决
4. administrative(行政): 官员渎职、贪腐、违反官制

【输出要求】
- 返回结构化法律分析
- 列出所有适用法条（含法条ID和原文摘要）
- 推荐具体后果（刑罚类型、程度、理由）
- 法律叙述要体现明代司法特色（知府审案、师爷参谋、衙役执行）
- 如有多条适用法条，说明竞合关系（从重/从轻）

现在处理法律事务。"""


class LawAgent(AgentBase):
    """Specialized agent for legal analysis and proceedings in the
    Ming Dynasty setting."""

    agent_id = "law"

    def __init__(self, world: World, model: str = "mimo-v2.5-pro",
                 api_key: str | None = None, base_url: str | None = None):
        super().__init__(world)
        self.model = model
        self.client = Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"),
            base_url=base_url or os.environ.get("ANTHROPIC_BASE_URL"),
        )

    def get_system_prompt(self) -> str:
        return LAW_SYSTEM_PROMPT

    def get_tools(self) -> list[dict[str, Any]]:
        """Return law-specific tool schemas."""
        return [
            {
                "name": "query_laws",
                "description": "检索大明律法条，支持关键词和语义混合检索",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "关键词列表，如 ['殴打', '知府']",
                        },
                        "query": {
                            "type": "string",
                            "description": "自然语言查询，如 '平民殴打朝廷命官'",
                        },
                        "top_k": {
                            "type": "integer",
                            "default": 5,
                            "description": "返回结果数量",
                        },
                    },
                },
            },
            {
                "name": "log_event",
                "description": "记录法律相关事件（审讯、判决、释放等）",
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
            {
                "name": "add_memory",
                "description": "为实体添加法律相关记忆（被审讯、被判刑、被释放等）",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": "实体 ID",
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
                "description": "修改实体属性（如 reputation 声望、wanted_level 通缉等级）",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string"},
                        "attr": {
                            "type": "string",
                            "description": "属性名",
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
                "description": "添加法律相关状态（如 imprisoned 监禁、wanted 通缉、on_trial 受审）",
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
                            "default": -1,
                            "description": "持续回合数 (-1 为永久)",
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
        ]

    def _build_tool_registry(self) -> dict:
        """Build tool handler registry for law tools."""
        return {
            "query_laws": {"handler": lambda **kw: R.query_laws(**kw)},
            "log_event": {
                "handler": lambda **kw: W.log_event(self.world, **kw)
            },
            "add_memory": {
                "handler": lambda **kw: W.add_memory(self.world, **kw)
            },
            "set_attribute": {
                "handler": lambda **kw: W.set_attribute(self.world, **kw)
            },
            "add_status": {
                "handler": lambda **kw: W.add_status(self.world, **kw)
            },
        }

    def process(self, context: dict[str, Any]) -> dict[str, Any]:
        """Process a legal analysis delegation request.

        Args:
            context: Dict with keys:
                - player_id: str (default "player")
                - player_input: str (original player input)
                - case_type: str (criminal/civil/procedural/administrative)
                - defendant_id: str (optional, entity being accused)
                - charges: list[str] (optional, specific charges)
                - legal_context: dict (optional, additional context)

        Returns:
            Dict with:
                - narration: str (legal analysis description)
                - writes: list of write operations
                - law_result: dict (structured legal outcome)
        """
        registry = self._build_tool_registry()
        tools = self.get_tools()

        player_id = context.get("player_id", "player")
        case_type = context.get("case_type", "criminal")
        player_input = context.get("player_input", "")

        player = self.world.get_entity(player_id)

        # Build context message for the LLM
        context_msg = (
            f"【法律事务上下文】\n"
            f"当事人: {player['name'] if player else player_id}\n"
            f"案件类型: {case_type}\n"
            f"玩家输入: {player_input}\n"
        )

        if context.get("defendant_id"):
            defendant = self.world.get_entity(context["defendant_id"])
            context_msg += (
                f"被告: {defendant['name'] if defendant else context['defendant_id']}\n"
            )

        if context.get("charges"):
            context_msg += f"指控罪名: {', '.join(context['charges'])}\n"

        if context.get("legal_context"):
            ctx = context["legal_context"]
            if ctx.get("victim_id"):
                victim = self.world.get_entity(ctx["victim_id"])
                context_msg += f"受害者: {victim['name'] if victim else ctx['victim_id']}\n"
            if ctx.get("witness_ids"):
                names = []
                for wid in ctx["witness_ids"]:
                    w = self.world.get_entity(wid)
                    names.append(w["name"] if w else wid)
                context_msg += f"证人: {', '.join(names)}\n"
            if ctx.get("evidence"):
                context_msg += f"证据: {ctx['evidence']}\n"
            if ctx.get("severity"):
                context_msg += f"情节严重程度: {ctx['severity']}\n"

        messages = [{"role": "user", "content": context_msg}]

        writes = []
        narration_parts = []

        try:
            for _ in range(5):  # Max 5 iterations for legal analysis
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
                "narration": f"法律分析出错: {e}",
                "writes": writes,
                "law_result": {"error": str(e)},
            }

        narration = "\n\n".join(
            p.strip() for p in narration_parts if p and p.strip()
        )
        if not narration:
            narration = "知府沉吟不语，翻看着案卷。"

        # Extract applicable laws from writes
        applicable_laws = []
        for w in writes:
            if w["tool"] == "query_laws" and "laws" in w.get("result", {}):
                for law in w["result"]["laws"]:
                    applicable_laws.append({
                        "id": law.get("id", ""),
                        "text": law.get("text", ""),
                        "consequence_hint": law.get("consequence_hint", ""),
                    })

        return {
            "narration": narration,
            "writes": writes,
            "law_result": {
                "case_type": case_type,
                "applicable_laws": applicable_laws,
                "defendant_id": context.get("defendant_id", player_id),
                "player_id": player_id,
            },
        }
