"""Abstract base class for specialized agents."""
from abc import ABC, abstractmethod
from typing import Any

from mingrpg.core.world import World


class AgentBase(ABC):
    """Base class for all specialized agents.

    Each agent:
    - Has a unique agent_id (e.g. "combat", "social", "law")
    - Receives context from the GM Agent
    - Returns a structured result dict
    - Shares the same World instance as the GM
    """

    agent_id: str = ""

    def __init__(self, world: World):
        self.world = world

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this specialized agent."""
        ...

    @abstractmethod
    def get_tools(self) -> list[dict[str, Any]]:
        """Return the tool schemas this agent can use."""
        ...

    @abstractmethod
    def process(self, context: dict[str, Any]) -> dict[str, Any]:
        """Process a delegation request and return a structured result.

        Args:
            context: Dict containing relevant state from the GM Agent.
                     Typically includes: player_input, entities, location,
                     recent_events, and any domain-specific data.

        Returns:
            Dict with at minimum:
              - "narration": str (the agent's narrative contribution)
              - "writes": list of write operations performed (tool_name, args, result)
        """
        ...
