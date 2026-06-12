"""Multi-agent system — specialized agents for different game domains."""
from mingrpg.llm.agents.base import AgentBase
from mingrpg.llm.agents.combat import CombatAgent
from mingrpg.llm.agents.law import LawAgent
from mingrpg.llm.agents.social import SocialAgent

__all__ = ["AgentBase", "CombatAgent", "LawAgent", "SocialAgent"]
