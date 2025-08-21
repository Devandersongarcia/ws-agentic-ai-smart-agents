"""
Restaurant Recommendation Multi-Agent System

This module demonstrates CrewAI's multi-agent collaboration capabilities
using built-in tools for autonomous restaurant recommendations.
"""

import os
import warnings
from typing import Dict, Any
from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool
from dotenv import load_dotenv

load_dotenv()

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*pydantic.*", category=Warning)
warnings.filterwarnings("ignore", message=".*Pydantic.*", category=Warning)
warnings.filterwarnings("ignore", message=".*path_separator.*", category=Warning)
warnings.filterwarnings("ignore", message=".*alembic.*", category=Warning)


@CrewBase
class RestaurantRecommendationCrew:
    """
    Multi-agent crew for restaurant recommendations.
    
    Implements a sequential process where three specialized agents
    collaborate to provide comprehensive dining recommendations.
    """

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        """Initialize the crew with necessary tools."""
        self.storage_path = "storage"
        self._setup_tools()

    def _setup_tools(self):
        """Configure FileReadTool for data access."""
        self.file_tool = FileReadTool()

    @agent
    def restaurant_concierge(self) -> Agent:
        """Restaurant recommendation specialist agent."""
        return Agent(
            config=self.agents_config['restaurant_concierge'],
            tools=[self.file_tool],
            verbose=True,
            max_iter=2
        )

    @agent
    def dietary_specialist(self) -> Agent:
        """Food safety and dietary expert agent."""
        return Agent(
            config=self.agents_config['dietary_specialist'],
            tools=[self.file_tool],
            verbose=True,
            max_iter=1
        )

    @agent
    def promotions_manager(self) -> Agent:
        """Deals and promotions specialist agent."""
        return Agent(
            config=self.agents_config['promotions_manager'],
            tools=[self.file_tool],
            verbose=True,
            max_iter=1
        )

    @task
    def restaurant_search(self) -> Task:
        """Task for searching and recommending restaurants."""
        return Task(
            config=self.tasks_config['restaurant_search'],
            agent=self.restaurant_concierge()
        )

    @task
    def dietary_safety_check(self) -> Task:
        """Task for analyzing dietary safety of recommendations."""
        return Task(
            config=self.tasks_config['dietary_safety_check'],
            agent=self.dietary_specialist(),
            context=[self.restaurant_search()]
        )

    @task
    def promotions_search(self) -> Task:
        """Task for finding deals and promotions."""
        return Task(
            config=self.tasks_config['promotions_search'],
            agent=self.promotions_manager(),
            context=[self.restaurant_search()]
        )

    @task
    def final_recommendation(self) -> Task:
        """Task for creating the ultimate recommendation guide."""
        return Task(
            config=self.tasks_config['final_recommendation'],
            agent=self.restaurant_concierge(),
            context=[
                self.restaurant_search(),
                self.dietary_safety_check(),
                self.promotions_search()
            ],
            output_file='report.md'
        )

    @crew
    def crew(self) -> Crew:
        """Create and configure the restaurant recommendation crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )

    def kickoff(self, inputs: Dict[str, Any]) -> str:
        """
        Execute the restaurant recommendation workflow.
        
        Args:
            inputs: Dictionary containing customer preferences
        
        Returns:
            Final recommendation report as string
        """
        result = self.crew().kickoff(inputs=inputs)

        if hasattr(result, 'raw'):
            return result.raw
        elif hasattr(result, '__str__'):
            return str(result)
        else:
            return "Recommendations generated successfully. Check report.md"
