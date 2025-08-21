"""
Base agent class for all restaurant recommendation agents.
Provides common configuration and capabilities.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from crewai import Agent
from langchain_openai import ChatOpenAI

from config import get_settings


class BaseRestaurantAgent(ABC):
    """
    Abstract base class for restaurant recommendation agents.
    Provides LLM configuration and common agent settings.
    """

    def __init__(self):
        """Initialize base agent with configuration."""
        self.settings = get_settings()
        self.llm = self._create_llm()
        self.agent = None

    def _create_llm(self) -> ChatOpenAI:
        """
        Create configured LLM instance.
        
        Returns:
            Configured ChatOpenAI instance
        """
        return ChatOpenAI(
            model=self.settings.openai_model_name,
            temperature=self.settings.openai_temperature,
            max_tokens=self.settings.openai_max_tokens,
            api_key=self.settings.openai_api_key
        )

    @abstractmethod
    def create_agent(self, tools: List[Any]) -> Agent:
        """
        Create the specific agent instance.
        
        Args:
            tools: List of tools available to the agent
            
        Returns:
            Configured Agent instance
        """
        pass

    def get_base_config(self) -> Dict[str, Any]:
        """
        Get base configuration for all agents.
        
        Returns:
            Dictionary with base agent configuration
        """
        return {
            "verbose": self.settings.app_debug,
            "max_iter": self.settings.crewai_max_iterations,
            "memory": self.settings.crewai_memory_type == "short_term",
            "llm": self.llm,
            "allow_delegation": True
        }

    def format_response(self, response: str) -> str:
        """
        Format agent response for consistent output.
        
        Args:
            response: Raw agent response
            
        Returns:
            Formatted response
        """
        lines = response.strip().split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)

    def validate_tools(self, tools: List[Any]) -> bool:
        """
        Validate that required tools are available.
        
        Args:
            tools: List of tools to validate
            
        Returns:
            True if all required tools are present
        """
        required_tool_names = self.get_required_tools()
        tool_names = [tool.name for tool in tools]
        
        for required in required_tool_names:
            if required not in tool_names:
                raise ValueError(f"Required tool '{required}' not found")
        
        return True

    @abstractmethod
    def get_required_tools(self) -> List[str]:
        """
        Get list of required tool names for this agent.
        
        Returns:
            List of required tool names
        """
        pass

    def get_agent_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the agent.
        
        Returns:
            Dictionary with agent metrics
        """
        if not self.agent:
            return {}
        
        return {
            "name": self.agent.role if self.agent else "Not initialized",
            "iterations": 0,
            "tokens_used": 0,
            "success_rate": 0.0
        }