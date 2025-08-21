"""
Factory for creating different types of crews based on use case.
Provides flexible crew configurations for various scenarios.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from crewai import Crew, Process

from agents import (
    RestaurantConciergeAgent,
    DietarySpecialistAgent,
    PromotionsManagerAgent
)
from tools import (
    RestaurantSearchTool,
    AllergenCheckerTool,
    CouponFinderTool,
    SupabaseRetrieverTool
)


class CrewType(str, Enum):
    """Types of crews that can be created."""
    
    FULL_SERVICE = "full_service"
    SAFETY_FOCUSED = "safety_focused"
    BUDGET_OPTIMIZED = "budget_optimized"
    QUICK_RECOMMENDATION = "quick_recommendation"
    CUSTOM = "custom"


class CrewFactory:
    """
    Factory for creating specialized crew configurations.
    Enables flexible crew composition based on specific needs.
    """

    def __init__(self):
        """Initialize the crew factory."""
        self.available_agents = {
            "concierge": RestaurantConciergeAgent,
            "dietary": DietarySpecialistAgent,
            "promotions": PromotionsManagerAgent
        }
        
        self.available_tools = {
            "restaurant_search": RestaurantSearchTool,
            "allergen_checker": AllergenCheckerTool,
            "coupon_finder": CouponFinderTool,
            "supabase_retriever": SupabaseRetrieverTool
        }

    def create_crew(
        self,
        crew_type: CrewType,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> Crew:
        """
        Create a crew based on the specified type.
        
        Args:
            crew_type: Type of crew to create
            custom_config: Optional custom configuration
            
        Returns:
            Configured Crew instance
        """
        if crew_type == CrewType.FULL_SERVICE:
            return self._create_full_service_crew()
        elif crew_type == CrewType.SAFETY_FOCUSED:
            return self._create_safety_focused_crew()
        elif crew_type == CrewType.BUDGET_OPTIMIZED:
            return self._create_budget_optimized_crew()
        elif crew_type == CrewType.QUICK_RECOMMENDATION:
            return self._create_quick_recommendation_crew()
        elif crew_type == CrewType.CUSTOM:
            if not custom_config:
                raise ValueError("Custom crew requires configuration")
            return self._create_custom_crew(custom_config)
        else:
            raise ValueError(f"Unknown crew type: {crew_type}")

    def _create_full_service_crew(self) -> Crew:
        """
        Create a full-service crew with all agents.
        
        Returns:
            Full-service Crew instance
        """
        tools = {
            name: cls() for name, cls in self.available_tools.items()
        }
        
        agents = []
        
        concierge = RestaurantConciergeAgent()
        agents.append(concierge.create_agent([
            tools["restaurant_search"],
            tools["supabase_retriever"]
        ]))
        
        dietary = DietarySpecialistAgent()
        agents.append(dietary.create_agent([
            tools["allergen_checker"],
            tools["supabase_retriever"]
        ]))
        
        promotions = PromotionsManagerAgent()
        agents.append(promotions.create_agent([
            tools["coupon_finder"],
            tools["restaurant_search"],
            tools["supabase_retriever"]
        ]))
        
        return Crew(
            agents=agents,
            process=Process.sequential,
            verbose=True
        )

    def _create_safety_focused_crew(self) -> Crew:
        """
        Create a crew focused on dietary safety.
        
        Returns:
            Safety-focused Crew instance
        """
        tools = {
            "allergen_checker": AllergenCheckerTool(),
            "restaurant_search": RestaurantSearchTool(),
            "supabase_retriever": SupabaseRetrieverTool()
        }
        
        agents = []
        
        dietary = DietarySpecialistAgent()
        agents.append(dietary.create_agent([
            tools["allergen_checker"],
            tools["supabase_retriever"]
        ]))
        
        concierge = RestaurantConciergeAgent()
        agents.append(concierge.create_agent([
            tools["restaurant_search"],
            tools["supabase_retriever"]
        ]))
        
        return Crew(
            agents=agents,
            process=Process.sequential,
            verbose=True
        )

    def _create_budget_optimized_crew(self) -> Crew:
        """
        Create a crew optimized for finding deals.
        
        Returns:
            Budget-optimized Crew instance
        """
        tools = {
            "coupon_finder": CouponFinderTool(),
            "restaurant_search": RestaurantSearchTool(),
            "supabase_retriever": SupabaseRetrieverTool()
        }
        
        agents = []
        
        promotions = PromotionsManagerAgent()
        agents.append(promotions.create_agent([
            tools["coupon_finder"],
            tools["restaurant_search"],
            tools["supabase_retriever"]
        ]))
        
        concierge = RestaurantConciergeAgent()
        agents.append(concierge.create_agent([
            tools["restaurant_search"],
            tools["supabase_retriever"]
        ]))
        
        return Crew(
            agents=agents,
            process=Process.sequential,
            verbose=True
        )

    def _create_quick_recommendation_crew(self) -> Crew:
        """
        Create a minimal crew for quick recommendations.
        
        Returns:
            Quick recommendation Crew instance
        """
        tools = {
            "restaurant_search": RestaurantSearchTool(),
            "supabase_retriever": SupabaseRetrieverTool()
        }
        
        concierge = RestaurantConciergeAgent()
        agent = concierge.create_agent([
            tools["restaurant_search"],
            tools["supabase_retriever"]
        ])
        
        return Crew(
            agents=[agent],
            process=Process.sequential,
            verbose=False
        )

    def _create_custom_crew(self, config: Dict[str, Any]) -> Crew:
        """
        Create a custom crew based on configuration.
        
        Args:
            config: Custom crew configuration
            
        Returns:
            Custom Crew instance
        """
        agent_names = config.get("agents", ["concierge"])
        tool_names = config.get("tools", ["restaurant_search"])
        process_type = config.get("process", "sequential")
        verbose = config.get("verbose", True)
        
        tools = {}
        for tool_name in tool_names:
            if tool_name in self.available_tools:
                tools[tool_name] = self.available_tools[tool_name]()
        
        agents = []
        for agent_name in agent_names:
            if agent_name in self.available_agents:
                agent_class = self.available_agents[agent_name]()
                
                agent_tools = []
                if agent_name == "concierge":
                    if "restaurant_search" in tools:
                        agent_tools.append(tools["restaurant_search"])
                    if "supabase_retriever" in tools:
                        agent_tools.append(tools["supabase_retriever"])
                elif agent_name == "dietary":
                    if "allergen_checker" in tools:
                        agent_tools.append(tools["allergen_checker"])
                    if "supabase_retriever" in tools:
                        agent_tools.append(tools["supabase_retriever"])
                elif agent_name == "promotions":
                    if "coupon_finder" in tools:
                        agent_tools.append(tools["coupon_finder"])
                    if "restaurant_search" in tools:
                        agent_tools.append(tools["restaurant_search"])
                    if "supabase_retriever" in tools:
                        agent_tools.append(tools["supabase_retriever"])
                
                if agent_tools:
                    agents.append(agent_class.create_agent(agent_tools))
        
        process = Process.sequential
        if process_type == "hierarchical":
            process = Process.hierarchical
        
        return Crew(
            agents=agents,
            process=process,
            verbose=verbose
        )

    def get_crew_info(self, crew_type: CrewType) -> Dict[str, Any]:
        """
        Get information about a crew type.
        
        Args:
            crew_type: Type of crew to get info for
            
        Returns:
            Dictionary with crew information
        """
        crew_info = {
            CrewType.FULL_SERVICE: {
                "description": "Complete crew with all agents for comprehensive recommendations",
                "agents": ["concierge", "dietary", "promotions"],
                "use_cases": [
                    "Complex dining decisions",
                    "Special occasions",
                    "Group dining with varied needs"
                ]
            },
            CrewType.SAFETY_FOCUSED: {
                "description": "Crew optimized for dietary restrictions and allergen safety",
                "agents": ["dietary", "concierge"],
                "use_cases": [
                    "Severe allergies",
                    "Medical dietary requirements",
                    "Religious dietary restrictions"
                ]
            },
            CrewType.BUDGET_OPTIMIZED: {
                "description": "Crew focused on finding the best deals and value",
                "agents": ["promotions", "concierge"],
                "use_cases": [
                    "Budget-conscious dining",
                    "Large group discounts",
                    "Special promotions hunting"
                ]
            },
            CrewType.QUICK_RECOMMENDATION: {
                "description": "Minimal crew for fast, simple recommendations",
                "agents": ["concierge"],
                "use_cases": [
                    "Quick lunch decisions",
                    "Simple preference matching",
                    "Fast responses needed"
                ]
            },
            CrewType.CUSTOM: {
                "description": "Flexible crew configuration based on specific needs",
                "agents": "Customizable",
                "use_cases": ["Specialized requirements", "Unique workflows"]
            }
        }
        
        return crew_info.get(crew_type, {})

    def list_available_components(self) -> Dict[str, List[str]]:
        """
        List all available agents and tools.
        
        Returns:
            Dictionary with available components
        """
        return {
            "agents": list(self.available_agents.keys()),
            "tools": list(self.available_tools.keys()),
            "crew_types": [ct.value for ct in CrewType]
        }