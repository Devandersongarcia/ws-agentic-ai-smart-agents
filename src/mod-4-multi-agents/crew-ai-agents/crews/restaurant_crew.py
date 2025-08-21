"""
Restaurant recommendation crew orchestrating multiple specialized agents.
Coordinates collaboration between concierge, dietary, and promotions agents.
"""

from typing import Any, Dict, List, Optional

from crewai import Crew, Task, Process
from crewai.agent import Agent

from config import get_settings
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


class RestaurantRecommendationCrew:
    """
    Orchestrates multiple agents to provide comprehensive restaurant recommendations.
    Manages task delegation and agent collaboration for optimal results.
    """

    def __init__(self):
        """Initialize the restaurant recommendation crew."""
        self.settings = get_settings()
        self.agents = {}
        self.tools = {}
        self.crew = None
        self._initialize_tools()
        self._initialize_agents()

    def _initialize_tools(self) -> None:
        """Initialize all tools for agents."""
        self.tools = {
            "restaurant_search": RestaurantSearchTool(),
            "allergen_checker": AllergenCheckerTool(),
            "coupon_finder": CouponFinderTool(),
            "supabase_retriever": SupabaseRetrieverTool()
        }

    def _initialize_agents(self) -> None:
        """Initialize all specialized agents."""
        concierge = RestaurantConciergeAgent()
        dietary = DietarySpecialistAgent()
        promotions = PromotionsManagerAgent()
        
        self.agents["concierge"] = concierge.create_agent([
            self.tools["restaurant_search"],
            self.tools["supabase_retriever"]
        ])
        
        self.agents["dietary"] = dietary.create_agent([
            self.tools["allergen_checker"],
            self.tools["supabase_retriever"]
        ])
        
        self.agents["promotions"] = promotions.create_agent([
            self.tools["coupon_finder"],
            self.tools["restaurant_search"],
            self.tools["supabase_retriever"]
        ])

    def create_recommendation_tasks(
        self,
        customer_request: str,
        preferences: Dict[str, Any]
    ) -> List[Task]:
        """
        Create tasks for restaurant recommendation workflow.
        
        Args:
            customer_request: Natural language request from customer
            preferences: Structured preferences and requirements
            
        Returns:
            List of tasks for the crew to execute
        """
        tasks = []
        
        search_task = Task(
            description=f"""
            Find restaurants matching this customer request: {customer_request}
            
            Consider these preferences:
            - Cuisine: {preferences.get('cuisine_type', 'Any')}
            - Budget: {preferences.get('price_range', 'Any')}
            - Location: {preferences.get('location', 'Any')}
            - Occasion: {preferences.get('occasion', 'Casual dining')}
            - Party size: {preferences.get('party_size', 2)}
            
            Provide 3-5 restaurant recommendations with detailed explanations 
            of why each matches the customer's needs.
            """,
            agent=self.agents["concierge"],
            expected_output="List of 3-5 restaurants with detailed match explanations"
        )
        tasks.append(search_task)
        
        if preferences.get('dietary_restrictions') or preferences.get('allergens'):
            safety_task = Task(
                description=f"""
                Validate the safety of recommended restaurants for these dietary requirements:
                - Allergens to avoid: {preferences.get('allergens', [])}
                - Dietary type: {preferences.get('dietary_type', 'None')}
                - Medical conditions: {preferences.get('medical_conditions', [])}
                
                For each recommended restaurant:
                1. Check menu items for allergen presence
                2. Assess cross-contamination risks
                3. Identify safe menu options
                4. Provide clear safety ratings
                5. Suggest alternatives if any restaurant is unsafe
                """,
                agent=self.agents["dietary"],
                expected_output="Safety assessment for each restaurant with safe menu options",
                context=[search_task]
            )
            tasks.append(safety_task)
        
        if preferences.get('budget_conscious', True):
            promotions_task = Task(
                description=f"""
                Find the best deals and promotions for the recommended restaurants.
                Budget: {preferences.get('budget', 'Not specified')}
                Party size: {preferences.get('party_size', 2)}
                
                For each restaurant:
                1. Search for active coupons and promotions
                2. Calculate potential savings
                3. Recommend optimal ordering strategies
                4. Highlight time-sensitive deals
                5. Provide coupon codes and claiming instructions
                """,
                agent=self.agents["promotions"],
                expected_output="Available deals with savings calculations and codes",
                context=[search_task]
            )
            tasks.append(promotions_task)
        
        synthesis_task = Task(
            description="""
            Create a final, comprehensive recommendation summary that includes:
            1. Top 3 restaurant recommendations ranked by overall fit
            2. Safety considerations and dietary accommodations
            3. Available deals and potential savings
            4. Specific menu recommendations for each restaurant
            5. Reservation tips and best times to visit
            6. Clear action steps for the customer
            
            Present this as a clear, actionable guide that the customer 
            can use to make their dining decision.
            """,
            agent=self.agents["concierge"],
            expected_output="Complete dining guide with ranked recommendations and action steps",
            context=tasks[:-1] if len(tasks) > 0 else []
        )
        tasks.append(synthesis_task)
        
        return tasks

    def recommend(
        self,
        customer_request: str,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive restaurant recommendations.
        
        Args:
            customer_request: Natural language request from customer
            preferences: Optional structured preferences
            
        Returns:
            Dictionary with recommendations and metadata
        """
        if preferences is None:
            preferences = {}
        
        tasks = self.create_recommendation_tasks(customer_request, preferences)
        
        process_type = Process.sequential
        if self.settings.crewai_process_type == "hierarchical":
            process_type = Process.hierarchical
        
        self.crew = Crew(
            agents=list(self.agents.values()),
            tasks=tasks,
            process=process_type,
            verbose=self.settings.app_debug
        )
        
        result = self.crew.kickoff()
        
        return {
            "recommendations": result,
            "metadata": {
                "agents_used": list(self.agents.keys()),
                "tasks_completed": len(tasks),
                "preferences": preferences
            }
        }

    def quick_recommendation(
        self,
        cuisine_type: str,
        budget: str = "$$"
    ) -> str:
        """
        Generate quick restaurant recommendation with minimal input.
        
        Args:
            cuisine_type: Type of cuisine desired
            budget: Price range
            
        Returns:
            Quick recommendation text
        """
        request = f"Find a good {cuisine_type} restaurant in the {budget} price range"
        preferences = {
            "cuisine_type": cuisine_type,
            "price_range": budget,
            "budget_conscious": budget in ["$", "$$"]
        }
        
        result = self.recommend(request, preferences)
        return result["recommendations"]

    def safe_dining_recommendation(
        self,
        allergens: List[str],
        cuisine_preference: Optional[str] = None
    ) -> str:
        """
        Generate recommendations focused on dietary safety.
        
        Args:
            allergens: List of allergens to avoid
            cuisine_preference: Optional cuisine type
            
        Returns:
            Safety-focused recommendations
        """
        request = f"Find restaurants that are safe for someone with {', '.join(allergens)} allergies"
        if cuisine_preference:
            request += f" and serve {cuisine_preference} cuisine"
        
        preferences = {
            "allergens": allergens,
            "dietary_restrictions": True,
            "cuisine_type": cuisine_preference
        }
        
        result = self.recommend(request, preferences)
        return result["recommendations"]

    def budget_dining_recommendation(
        self,
        max_budget: float,
        party_size: int = 2
    ) -> str:
        """
        Generate recommendations optimized for budget.
        
        Args:
            max_budget: Maximum budget for the meal
            party_size: Number of people
            
        Returns:
            Budget-optimized recommendations
        """
        request = f"Find great dining options for {party_size} people with a ${max_budget} budget"
        
        preferences = {
            "budget": max_budget,
            "party_size": party_size,
            "budget_conscious": True,
            "price_range": "$" if max_budget < 30 else "$$" if max_budget < 60 else "$$$"
        }
        
        result = self.recommend(request, preferences)
        return result["recommendations"]

    def get_crew_performance(self) -> Dict[str, Any]:
        """
        Get performance metrics for the crew execution.
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.crew:
            return {"status": "No crew execution yet"}
        
        return {
            "agents_count": len(self.agents),
            "tools_available": list(self.tools.keys()),
            "process_type": self.settings.crewai_process_type,
            "max_iterations": self.settings.crewai_max_iterations
        }