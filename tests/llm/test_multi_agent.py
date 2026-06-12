"""Tests for multi-agent system — CombatAgent, SocialAgent, and delegate_to_agent integration."""
import json
from unittest.mock import MagicMock, patch

import pytest

from mingrpg.audit.logger import AuditLogger
from mingrpg.core.world import World
from mingrpg.llm.agents.base import AgentBase
from mingrpg.llm.agents.combat import CombatAgent
from mingrpg.llm.agents.law import LawAgent
from mingrpg.llm.agents.social import SocialAgent
from mingrpg.llm.tools_registry import build_tool_registry, _delegate_to_agent


# ============================================================================
# AgentBase — abstract class contract
# ============================================================================

class TestAgentBase:
    def test_agent_base_is_abstract(self):
        """AgentBase cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AgentBase(World(":memory:"))

    def test_combat_agent_has_agent_id(self):
        world = World(":memory:")
        agent = CombatAgent(world, api_key="test", base_url="http://test")
        assert agent.agent_id == "combat"

    def test_combat_agent_implements_all_abstract_methods(self):
        world = World(":memory:")
        agent = CombatAgent(world, api_key="test", base_url="http://test")
        assert agent.get_system_prompt()
        assert isinstance(agent.get_tools(), list)
        assert callable(agent.process)


# ============================================================================
# CombatAgent — tool registration
# ============================================================================

class TestCombatAgentTools:
    def test_combat_tools_include_essential_skills(self):
        world = World(":memory:")
        agent = CombatAgent(world, api_key="test", base_url="http://test")
        tools = agent.get_tools()
        tool_names = {t["name"] for t in tools}
        assert "skill_check" in tool_names
        assert "roll_dice" in tool_names
        assert "apply_damage" in tool_names
        assert "add_status" in tool_names
        assert "tick_statuses" in tool_names

    def test_combat_tool_schemas_are_valid(self):
        world = World(":memory:")
        agent = CombatAgent(world, api_key="test", base_url="http://test")
        for tool in agent.get_tools():
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
            assert tool["input_schema"]["type"] == "object"
            assert "properties" in tool["input_schema"]


# ============================================================================
# delegate_to_agent — tool registry integration
# ============================================================================

class TestDelegateToAgentTool:
    def test_delegate_to_agent_is_registered(self):
        world = World(":memory:")
        registry = build_tool_registry(world)
        assert "delegate_to_agent" in registry

    def test_delegate_to_agent_schema(self):
        world = World(":memory:")
        registry = build_tool_registry(world)
        schema = registry["delegate_to_agent"]["schema"]
        assert schema["name"] == "delegate_to_agent"
        assert "agent_id" in schema["input_schema"]["properties"]
        assert "context" in schema["input_schema"]["properties"]
        assert "agent_id" in schema["input_schema"]["required"]
        assert "context" in schema["input_schema"]["required"]

    def test_delegate_to_agent_unknown_agent_returns_error(self):
        world = World(":memory:")
        result = _delegate_to_agent(world, "nonexistent", {})
        assert "error" in result
        assert "unknown agent" in result["error"]

    def test_delegate_to_agent_combat_missing_entities_returns_error(self):
        world = World(":memory:")
        result = _delegate_to_agent(world, "combat", {
            "attacker_id": "ghost",
            "defender_id": "ghost2",
            "player_input": "attack",
        })
        # Should return error because entities don't exist
        assert "narration" in result or "error" in result


# ============================================================================
# CombatAgent — process with mocked LLM
# ============================================================================

@pytest.fixture
def combat_world():
    """World with combat-ready entities."""
    world = World(":memory:")
    world.save_entity({
        "id": "player", "name": "无名书生", "type": "player",
        "location": "hall", "pos": [3, 5],
        "attributes": {"hp": 100, "max_hp": 100, "str": 10, "dex": 12,
                       "weapon_name": "拳头", "weapon_damage": "1d4"},
        "status_effects": [], "inventory": [], "tags": [],
    })
    world.save_entity({
        "id": "bully", "name": "赵三", "type": "npc",
        "location": "hall", "pos": [3, 7],
        "attributes": {"hp": 50, "max_hp": 50, "attack": 3, "defense": 10,
                       "weapon_name": "短刀", "weapon_damage": "1d6"},
        "status_effects": [], "inventory": [], "tags": ["bully"],
    })
    return world


def _make_combat_response(text="赵三挥刀砍来，刀光一闪。", stop="end_turn"):
    resp = MagicMock()
    block = MagicMock()
    block.type = "text"
    block.text = text
    resp.content = [block]
    resp.stop_reason = stop
    return resp


def _make_tool_response(tool_name, tool_input, result, next_text="战斗结束。"):
    """Create a two-step response: tool_use then text."""
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = tool_name
    tool_block.id = "tool_001"
    tool_block.input = tool_input

    resp1 = MagicMock()
    resp1.content = [tool_block]
    resp1.stop_reason = "tool_use"

    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = next_text

    resp2 = MagicMock()
    resp2.content = [text_block]
    resp2.stop_reason = "end_turn"

    return resp1, resp2


class TestCombatAgentProcess:
    def test_process_returns_narration_and_writes(self, combat_world):
        agent = CombatAgent(combat_world, api_key="test", base_url="http://test")
        response = _make_combat_response()

        with patch.object(agent.client.messages, "create", return_value=response):
            result = agent.process({
                "attacker_id": "player",
                "defender_id": "bully",
                "player_input": "我冲上去给赵三一拳",
            })

        assert "narration" in result
        assert "writes" in result
        assert "combat_result" in result
        assert len(result["narration"]) > 0

    def test_process_executes_skill_check_tool(self, combat_world):
        agent = CombatAgent(combat_world, api_key="test", base_url="http://test")
        resp1, resp2 = _make_tool_response(
            "skill_check",
            {"attribute_value": 10, "dc": 10},
            {"roll": 12, "success": True},
        )

        with patch.object(agent.client.messages, "create",
                          side_effect=[resp1, resp2]):
            result = agent.process({
                "attacker_id": "player",
                "defender_id": "bully",
                "player_input": "我冲上去给赵三一拳",
            })

        assert len(result["writes"]) >= 1
        assert result["writes"][0]["tool"] == "skill_check"
        assert "error" not in result["writes"][0]["result"]

    def test_process_handles_llm_error_gracefully(self, combat_world):
        agent = CombatAgent(combat_world, api_key="test", base_url="http://test")

        with patch.object(agent.client.messages, "create",
                          side_effect=RuntimeError("API error")):
            result = agent.process({
                "attacker_id": "player",
                "defender_id": "bully",
                "player_input": "attack",
            })

        assert "error" in result["combat_result"]
        assert "narration" in result

    def test_process_with_missing_attacker(self, combat_world):
        agent = CombatAgent(combat_world, api_key="test", base_url="http://test")
        result = agent.process({
            "attacker_id": "ghost",
            "defender_id": "bully",
            "player_input": "attack",
        })
        assert "error" in result["combat_result"]

    def test_process_combat_result_tracks_hp(self, combat_world):
        agent = CombatAgent(combat_world, api_key="test", base_url="http://test")
        response = _make_combat_response()

        with patch.object(agent.client.messages, "create", return_value=response):
            result = agent.process({
                "attacker_id": "player",
                "defender_id": "bully",
                "player_input": "attack",
            })

        cr = result["combat_result"]
        assert "attacker_hp" in cr
        assert "defender_hp" in cr
        assert "attacker_incapacitated" in cr
        assert "defender_incapacitated" in cr


# ============================================================================
# Integration — GM Agent can call delegate_to_agent
# ============================================================================

class TestGMDelegationIntegration:
    def test_gm_agent_has_delegate_tool(self):
        world = World(":memory:")
        registry = build_tool_registry(world)
        assert "delegate_to_agent" in registry

    def test_delegate_to_agent_handler_callable(self):
        world = World(":memory:")
        registry = build_tool_registry(world)
        handler = registry["delegate_to_agent"]["handler"]
        assert callable(handler)

    def test_delegate_to_agent_combat_with_valid_entities(self, combat_world):
        """Full integration: delegate_to_agent with combat agent."""
        result = _delegate_to_agent(combat_world, "combat", {
            "attacker_id": "player",
            "defender_id": "bully",
            "player_input": "我冲上去给赵三一拳",
        })
        # Should have narration (even if LLM call fails, we get error narration)
        assert "narration" in result
        assert "writes" in result
        assert "combat_result" in result


# ============================================================================
# SocialAgent — agent identity and contract
# ============================================================================

class TestSocialAgentIdentity:
    def test_social_agent_has_agent_id(self):
        world = World(":memory:")
        agent = SocialAgent(world, api_key="test", base_url="http://test")
        assert agent.agent_id == "social"

    def test_social_agent_implements_all_abstract_methods(self):
        world = World(":memory:")
        agent = SocialAgent(world, api_key="test", base_url="http://test")
        assert agent.get_system_prompt()
        assert isinstance(agent.get_tools(), list)
        assert callable(agent.process)

    def test_social_agent_system_prompt_mentions_key_concepts(self):
        world = World(":memory:")
        agent = SocialAgent(world, api_key="test", base_url="http://test")
        prompt = agent.get_system_prompt()
        assert "说服" in prompt
        assert "欺骗" in prompt
        assert "威吓" in prompt
        assert "态度" in prompt


# ============================================================================
# SocialAgent — tool registration
# ============================================================================

class TestSocialAgentTools:
    def test_social_tools_include_essential_skills(self):
        world = World(":memory:")
        agent = SocialAgent(world, api_key="test", base_url="http://test")
        tools = agent.get_tools()
        tool_names = {t["name"] for t in tools}
        assert "skill_check" in tool_names
        assert "add_memory" in tool_names
        assert "set_attribute" in tool_names
        assert "add_status" in tool_names
        assert "transfer_money" in tool_names
        assert "log_event" in tool_names

    def test_social_tool_schemas_are_valid(self):
        world = World(":memory:")
        agent = SocialAgent(world, api_key="test", base_url="http://test")
        for tool in agent.get_tools():
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
            assert tool["input_schema"]["type"] == "object"
            assert "properties" in tool["input_schema"]


# ============================================================================
# delegate_to_agent — social agent integration
# ============================================================================

class TestDelegateToSocialAgent:
    def test_delegate_to_agent_social_registered(self):
        world = World(":memory:")
        registry = build_tool_registry(world)
        assert "delegate_to_agent" in registry
        desc = registry["delegate_to_agent"]["schema"]["description"]
        assert "social" in desc

    def test_delegate_to_agent_social_missing_participants_returns_error(self):
        world = World(":memory:")
        result = _delegate_to_agent(world, "social", {
            "target_id": "ghost",
            "interaction_type": "persuasion",
            "player_input": "说服他",
        })
        assert "narration" in result or "error" in result


# ============================================================================
# SocialAgent — process with mocked LLM
# ============================================================================

@pytest.fixture
def social_world():
    """World with social-ready entities."""
    world = World(":memory:")
    world.save_entity({
        "id": "player", "name": "无名书生", "type": "player",
        "location": "market", "pos": [5, 5],
        "attributes": {
            "hp": 100, "max_hp": 100, "cha": 14, "str": 10, "wis": 12,
            "identity": "书生", "money_wen": 500,
        },
        "status_effects": [], "inventory": [], "tags": [],
    })
    world.save_entity({
        "id": "merchant", "name": "陈掌柜", "type": "npc",
        "location": "market", "pos": [5, 6],
        "attributes": {
            "hp": 30, "max_hp": 30,
            "occupation": "绸缎商人",
            "personality": "精明但重信誉",
            "attitude": 10,
            "cha": 12,
            "money_wen": 2000,
        },
        "status_effects": [], "inventory": [], "tags": ["merchant"],
    })
    return world


def _make_social_response(text="陈掌柜沉吟片刻，微微点头。", stop="end_turn"):
    resp = MagicMock()
    block = MagicMock()
    block.type = "text"
    block.text = text
    resp.content = [block]
    resp.stop_reason = stop
    return resp


def _make_social_tool_response(tool_name, tool_input, result,
                                next_text="交易达成。"):
    """Create a two-step response: tool_use then text."""
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = tool_name
    tool_block.id = "tool_social_001"
    tool_block.input = tool_input

    resp1 = MagicMock()
    resp1.content = [tool_block]
    resp1.stop_reason = "tool_use"

    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = next_text

    resp2 = MagicMock()
    resp2.content = [text_block]
    resp2.stop_reason = "end_turn"

    return resp1, resp2


class TestSocialAgentProcess:
    def test_process_returns_narration_and_writes(self, social_world):
        agent = SocialAgent(social_world, api_key="test", base_url="http://test")
        response = _make_social_response()

        with patch.object(agent.client.messages, "create", return_value=response):
            result = agent.process({
                "player_id": "player",
                "target_id": "merchant",
                "interaction_type": "persuasion",
                "player_input": "我想说服陈掌柜降价",
            })

        assert "narration" in result
        assert "writes" in result
        assert "social_result" in result
        assert len(result["narration"]) > 0

    def test_process_social_result_has_interaction_type(self, social_world):
        agent = SocialAgent(social_world, api_key="test", base_url="http://test")
        response = _make_social_response()

        with patch.object(agent.client.messages, "create", return_value=response):
            result = agent.process({
                "player_id": "player",
                "target_id": "merchant",
                "interaction_type": "negotiation",
                "player_input": "这绸缎多少钱?",
            })

        sr = result["social_result"]
        assert sr["interaction_type"] == "negotiation"
        assert sr["target_id"] == "merchant"
        assert sr["player_id"] == "player"
        assert "target_attitude" in sr

    def test_process_executes_skill_check_tool(self, social_world):
        agent = SocialAgent(social_world, api_key="test", base_url="http://test")
        resp1, resp2 = _make_social_tool_response(
            "skill_check",
            {"attribute_value": 14, "dc": 15},
            {"roll": 16, "success": True, "margin": 15},
        )

        with patch.object(agent.client.messages, "create",
                          side_effect=[resp1, resp2]):
            result = agent.process({
                "player_id": "player",
                "target_id": "merchant",
                "interaction_type": "persuasion",
                "player_input": "我以理服人",
            })

        assert len(result["writes"]) >= 1
        assert result["writes"][0]["tool"] == "skill_check"
        assert "error" not in result["writes"][0]["result"]

    def test_process_executes_add_memory_tool(self, social_world):
        agent = SocialAgent(social_world, api_key="test", base_url="http://test")
        resp1, resp2 = _make_social_tool_response(
            "add_memory",
            {"entity_id": "merchant", "memory": "书生以理服人，令人信服"},
            {"ok": True},
        )

        with patch.object(agent.client.messages, "create",
                          side_effect=[resp1, resp2]):
            result = agent.process({
                "player_id": "player",
                "target_id": "merchant",
                "interaction_type": "persuasion",
                "player_input": "说服陈掌柜",
            })

        assert len(result["writes"]) >= 1
        assert result["writes"][0]["tool"] == "add_memory"

    def test_process_handles_llm_error_gracefully(self, social_world):
        agent = SocialAgent(social_world, api_key="test", base_url="http://test")

        with patch.object(agent.client.messages, "create",
                          side_effect=RuntimeError("API error")):
            result = agent.process({
                "player_id": "player",
                "target_id": "merchant",
                "interaction_type": "persuasion",
                "player_input": "说服",
            })

        assert "error" in result["social_result"]
        assert "narration" in result

    def test_process_with_missing_target(self, social_world):
        agent = SocialAgent(social_world, api_key="test", base_url="http://test")
        result = agent.process({
            "player_id": "player",
            "target_id": "ghost",
            "interaction_type": "persuasion",
            "player_input": "说服",
        })
        assert "error" in result["social_result"]

    def test_process_with_missing_player(self, social_world):
        agent = SocialAgent(social_world, api_key="test", base_url="http://test")
        result = agent.process({
            "player_id": "ghost",
            "target_id": "merchant",
            "interaction_type": "persuasion",
            "player_input": "说服",
        })
        assert "error" in result["social_result"]

    def test_process_deception_type(self, social_world):
        agent = SocialAgent(social_world, api_key="test", base_url="http://test")
        response = _make_social_response("陈掌柜似乎相信了你的话。")

        with patch.object(agent.client.messages, "create", return_value=response):
            result = agent.process({
                "player_id": "player",
                "target_id": "merchant",
                "interaction_type": "deception",
                "player_input": "我骗他说我是知府的亲戚",
                "social_context": {"lie": "我是知府的亲戚"},
            })

        assert result["social_result"]["interaction_type"] == "deception"
        assert "narration" in result

    def test_process_intimidation_type(self, social_world):
        agent = SocialAgent(social_world, api_key="test", base_url="http://test")
        response = _make_social_response("陈掌柜面露惧色。")

        with patch.object(agent.client.messages, "create", return_value=response):
            result = agent.process({
                "player_id": "player",
                "target_id": "merchant",
                "interaction_type": "intimidation",
                "player_input": "我拍桌子威胁他",
            })

        assert result["social_result"]["interaction_type"] == "intimidation"

    def test_process_negotiation_with_price_context(self, social_world):
        agent = SocialAgent(social_world, api_key="test", base_url="http://test")
        resp1, resp2 = _make_social_tool_response(
            "transfer_money",
            {"from_entity": "player", "to_entity": "merchant", "amount": 80},
            {"ok": True},
        )

        with patch.object(agent.client.messages, "create",
                          side_effect=[resp1, resp2]):
            result = agent.process({
                "player_id": "player",
                "target_id": "merchant",
                "interaction_type": "negotiation",
                "player_input": "这绸缎能不能便宜点?",
                "social_context": {
                    "topic": "绸缎价格",
                    "offer_price": 80,
                    "original_price": 100,
                },
            })

        assert result["social_result"]["interaction_type"] == "negotiation"
        assert len(result["writes"]) >= 1

    def test_process_insight_type(self, social_world):
        agent = SocialAgent(social_world, api_key="test", base_url="http://test")
        resp1, resp2 = _make_social_tool_response(
            "skill_check",
            {"attribute_value": 12, "dc": 15},
            {"roll": 14, "success": True, "margin": 11},
        )

        with patch.object(agent.client.messages, "create",
                          side_effect=[resp1, resp2]):
            result = agent.process({
                "player_id": "player",
                "target_id": "merchant",
                "interaction_type": "insight",
                "player_input": "我仔细观察他的表情",
            })

        assert result["social_result"]["interaction_type"] == "insight"
        assert len(result["writes"]) >= 1


# ============================================================================
# Integration — GM Agent can call delegate_to_agent with social
# ============================================================================

class TestGMDelegationSocialIntegration:
    def test_delegate_to_agent_social_with_valid_entities(self, social_world):
        """Full integration: delegate_to_agent with social agent."""
        result = _delegate_to_agent(social_world, "social", {
            "target_id": "merchant",
            "interaction_type": "persuasion",
            "player_input": "我想说服陈掌柜降价",
        })
        # Should have narration (even if LLM call fails, we get error narration)
        assert "narration" in result
        assert "writes" in result
        assert "social_result" in result


# ============================================================================
# LawAgent — agent identity and contract
# ============================================================================

class TestLawAgentIdentity:
    def test_law_agent_has_agent_id(self):
        world = World(":memory:")
        agent = LawAgent(world, api_key="test", base_url="http://test")
        assert agent.agent_id == "law"

    def test_law_agent_implements_all_abstract_methods(self):
        world = World(":memory:")
        agent = LawAgent(world, api_key="test", base_url="http://test")
        assert agent.get_system_prompt()
        assert isinstance(agent.get_tools(), list)
        assert callable(agent.process)

    def test_law_agent_system_prompt_mentions_key_concepts(self):
        world = World(":memory:")
        agent = LawAgent(world, api_key="test", base_url="http://test")
        prompt = agent.get_system_prompt()
        assert "大明律" in prompt
        assert "量刑" in prompt
        assert "法条" in prompt
        assert "query_laws" in prompt


# ============================================================================
# LawAgent — tool registration
# ============================================================================

class TestLawAgentTools:
    def test_law_tools_include_essential_skills(self):
        world = World(":memory:")
        agent = LawAgent(world, api_key="test", base_url="http://test")
        tools = agent.get_tools()
        tool_names = {t["name"] for t in tools}
        assert "query_laws" in tool_names
        assert "log_event" in tool_names
        assert "add_memory" in tool_names
        assert "set_attribute" in tool_names
        assert "add_status" in tool_names

    def test_law_tool_schemas_are_valid(self):
        world = World(":memory:")
        agent = LawAgent(world, api_key="test", base_url="http://test")
        for tool in agent.get_tools():
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
            assert tool["input_schema"]["type"] == "object"
            assert "properties" in tool["input_schema"]

    def test_law_tools_no_combat_tools(self):
        """LawAgent should NOT have combat-specific tools."""
        world = World(":memory:")
        agent = LawAgent(world, api_key="test", base_url="http://test")
        tool_names = {t["name"] for t in agent.get_tools()}
        assert "roll_dice" not in tool_names
        assert "apply_damage" not in tool_names
        assert "tick_statuses" not in tool_names


# ============================================================================
# delegate_to_agent — law agent integration
# ============================================================================

class TestDelegateToLawAgent:
    def test_delegate_to_agent_law_registered(self):
        world = World(":memory:")
        registry = build_tool_registry(world)
        assert "delegate_to_agent" in registry
        desc = registry["delegate_to_agent"]["schema"]["description"]
        assert "law" in desc

    def test_delegate_to_agent_law_context_description(self):
        world = World(":memory:")
        registry = build_tool_registry(world)
        ctx_desc = registry["delegate_to_agent"]["schema"]["input_schema"]["properties"]["context"]["description"]
        assert "law" in ctx_desc
        assert "case_type" in ctx_desc


# ============================================================================
# LawAgent — process with mocked LLM
# ============================================================================

@pytest.fixture
def law_world():
    """World with entities for legal scenarios."""
    world = World(":memory:")
    world.save_entity({
        "id": "player", "name": "无名书生", "type": "player",
        "location": "hall", "pos": [3, 5],
        "attributes": {
            "hp": 100, "max_hp": 100, "cha": 14, "str": 10, "wis": 12,
            "identity": "书生", "money_wen": 500,
        },
        "status_effects": [], "inventory": [], "tags": [],
    })
    world.save_entity({
        "id": "magistrate", "name": "王知府", "type": "npc",
        "location": "hall", "pos": [3, 7],
        "attributes": {
            "hp": 60, "max_hp": 60,
            "occupation": "知府",
            "personality": "清廉刚正",
            "attitude": 0,
        },
        "status_effects": [], "inventory": [], "tags": ["official"],
    })
    world.save_entity({
        "id": "bully", "name": "赵三", "type": "npc",
        "location": "hall", "pos": [3, 8],
        "attributes": {
            "hp": 50, "max_hp": 50,
            "occupation": "漕帮打手",
            "personality": "凶悍跋扈",
            "attitude": -20,
        },
        "status_effects": [], "inventory": [], "tags": ["bully"],
    })
    return world


def _make_law_response(text="经查明律，此行为触犯刑律。", stop="end_turn"):
    resp = MagicMock()
    block = MagicMock()
    block.type = "text"
    block.text = text
    resp.content = [block]
    resp.stop_reason = stop
    return resp


def _make_law_tool_response(tool_name, tool_input, result,
                             next_text="法律分析完毕。"):
    """Create a two-step response: tool_use then text."""
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = tool_name
    tool_block.id = "tool_law_001"
    tool_block.input = tool_input

    resp1 = MagicMock()
    resp1.content = [tool_block]
    resp1.stop_reason = "tool_use"

    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = next_text

    resp2 = MagicMock()
    resp2.content = [text_block]
    resp2.stop_reason = "end_turn"

    return resp1, resp2


class TestLawAgentProcess:
    def test_process_returns_narration_and_writes(self, law_world):
        agent = LawAgent(law_world, api_key="test", base_url="http://test")
        response = _make_law_response()

        with patch.object(agent.client.messages, "create", return_value=response):
            result = agent.process({
                "player_id": "player",
                "player_input": "我冲上去给知府一拳",
                "case_type": "criminal",
            })

        assert "narration" in result
        assert "writes" in result
        assert "law_result" in result
        assert len(result["narration"]) > 0

    def test_process_law_result_has_case_type(self, law_world):
        agent = LawAgent(law_world, api_key="test", base_url="http://test")
        response = _make_law_response()

        with patch.object(agent.client.messages, "create", return_value=response):
            result = agent.process({
                "player_id": "player",
                "player_input": "我告赵三殴打我",
                "case_type": "criminal",
            })

        lr = result["law_result"]
        assert lr["case_type"] == "criminal"
        assert lr["player_id"] == "player"

    def test_process_executes_query_laws_tool(self, law_world):
        agent = LawAgent(law_world, api_key="test", base_url="http://test")
        resp1, resp2 = _make_law_tool_response(
            "query_laws",
            {"query": "平民殴打朝廷命官", "top_k": 3},
            {"laws": [{"id": "大明律.刑律.斗殴.殴制使及本管长官",
                       "text": "凡杖殴本属知府...",
                       "consequence_hint": "杖一百,徒三年"}],
             "mode": "vector"},
        )

        with patch.object(agent.client.messages, "create",
                          side_effect=[resp1, resp2]):
            result = agent.process({
                "player_id": "player",
                "player_input": "我冲上去给知府一拳",
                "case_type": "criminal",
            })

        assert len(result["writes"]) >= 1
        assert result["writes"][0]["tool"] == "query_laws"
        assert "error" not in result["writes"][0]["result"]

    def test_process_extract_applicable_laws(self, law_world):
        agent = LawAgent(law_world, api_key="test", base_url="http://test")
        resp1, resp2 = _make_law_tool_response(
            "query_laws",
            {"query": "殴打官员"},
            {"laws": [{"id": "大明律.刑律.斗殴.殴制使及本管长官",
                       "text": "凡杖殴本属知府...",
                       "consequence_hint": "杖一百,徒三年"}],
             "mode": "vector"},
        )

        with patch.object(agent.client.messages, "create",
                          side_effect=[resp1, resp2]):
            result = agent.process({
                "player_id": "player",
                "player_input": "我打知府",
                "case_type": "criminal",
            })

        lr = result["law_result"]
        assert len(lr["applicable_laws"]) >= 1
        assert "id" in lr["applicable_laws"][0]
        assert "text" in lr["applicable_laws"][0]

    def test_process_handles_llm_error_gracefully(self, law_world):
        agent = LawAgent(law_world, api_key="test", base_url="http://test")

        with patch.object(agent.client.messages, "create",
                          side_effect=RuntimeError("API error")):
            result = agent.process({
                "player_id": "player",
                "player_input": "我打人了",
                "case_type": "criminal",
            })

        assert "error" in result["law_result"]
        assert "narration" in result

    def test_process_with_defendant_id(self, law_world):
        agent = LawAgent(law_world, api_key="test", base_url="http://test")
        response = _make_law_response("赵三涉嫌殴打他人。")

        with patch.object(agent.client.messages, "create", return_value=response):
            result = agent.process({
                "player_id": "player",
                "player_input": "我告赵三打我",
                "case_type": "criminal",
                "defendant_id": "bully",
                "charges": ["殴打"],
            })

        lr = result["law_result"]
        assert lr["defendant_id"] == "bully"
        assert "narration" in result

    def test_process_with_legal_context(self, law_world):
        agent = LawAgent(law_world, api_key="test", base_url="http://test")
        response = _make_law_response("案件涉及多方证人。")

        with patch.object(agent.client.messages, "create", return_value=response):
            result = agent.process({
                "player_id": "player",
                "player_input": "我要告状",
                "case_type": "procedural",
                "legal_context": {
                    "victim_id": "player",
                    "witness_ids": ["magistrate"],
                    "evidence": "伤痕",
                    "severity": "中等",
                },
            })

        assert "narration" in result
        assert "law_result" in result

    def test_process_civil_case_type(self, law_world):
        agent = LawAgent(law_world, api_key="test", base_url="http://test")
        response = _make_law_response("此乃田产纠纷。")

        with patch.object(agent.client.messages, "create", return_value=response):
            result = agent.process({
                "player_id": "player",
                "player_input": "我家的田被邻居占了",
                "case_type": "civil",
            })

        assert result["law_result"]["case_type"] == "civil"

    def test_process_administrative_case_type(self, law_world):
        agent = LawAgent(law_world, api_key="test", base_url="http://test")
        response = _make_law_response("官员渎职，当受弹劾。")

        with patch.object(agent.client.messages, "create", return_value=response):
            result = agent.process({
                "player_id": "player",
                "player_input": "知府收了贿赂不办案",
                "case_type": "administrative",
            })

        assert result["law_result"]["case_type"] == "administrative"

    def test_process_with_missing_player(self, law_world):
        agent = LawAgent(law_world, api_key="test", base_url="http://test")
        result = agent.process({
            "player_id": "ghost",
            "player_input": "告状",
            "case_type": "criminal",
        })
        # Should still return a result (player is optional context)
        assert "narration" in result
        assert "law_result" in result


# ============================================================================
# Integration — GM Agent can call delegate_to_agent with law
# ============================================================================

class TestGMDelegationLawIntegration:
    def test_delegate_to_agent_law_with_valid_world(self, law_world):
        """Full integration: delegate_to_agent with law agent."""
        result = _delegate_to_agent(law_world, "law", {
            "player_id": "player",
            "player_input": "我冲上去给知府一拳",
            "case_type": "criminal",
        })
        # Should have narration (even if LLM call fails, we get error narration)
        assert "narration" in result
        assert "writes" in result
        assert "law_result" in result

    def test_delegate_to_agent_law_in_agents_dict(self):
        """Law agent should be in the agents dict."""
        world = World(":memory:")
        result = _delegate_to_agent(world, "law", {
            "player_input": "test",
            "case_type": "criminal",
        })
        # Should NOT return "unknown agent" error
        assert "unknown agent" not in str(result.get("error", ""))
