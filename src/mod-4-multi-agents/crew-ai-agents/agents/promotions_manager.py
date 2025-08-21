"""
Promotions Manager Agent for finding and optimizing deals.
Specializes in matching customers with the best available promotions.
"""

from typing import Any, Dict, List, Optional

from crewai import Agent

from .base_agent import BaseRestaurantAgent


class PromotionsManagerAgent(BaseRestaurantAgent):
    """
    Agent specialized in finding deals, optimizing discounts, and maximizing value.
    Helps customers save money while enjoying great dining experiences.
    """

    def create_agent(self, tools: List[Any]) -> Agent:
        """
        Create the Promotions Manager agent.
        
        Args:
            tools: List of tools available to the agent
            
        Returns:
            Configured Promotions Manager Agent
        """
        self.validate_tools(tools)
        
        config = self.get_base_config()
        
        self.agent = Agent(
            role=self.settings.promotions_role,
            goal=self.settings.promotions_goal,
            backstory=self._get_backstory(),
            tools=tools,
            **config
        )
        
        return self.agent

    def _get_backstory(self) -> str:
        """
        Get the backstory for the Promotions Manager agent.
        
        Returns:
            Agent backstory
        """
        return """
        You are a savvy promotions specialist with extensive experience in restaurant 
        marketing and customer value optimization. You have insider knowledge of how 
        restaurant promotions work and know exactly how to maximize savings without 
        compromising on quality.
        
        Your expertise includes:
        - Understanding seasonal promotion patterns and timing
        - Knowledge of combination deals and stacking opportunities
        - Awareness of loyalty programs and member benefits
        - Skills in calculating real value beyond percentage discounts
        - Experience with different types of promotions (happy hours, prix fixe, etc.)
        
        You believe that everyone deserves a great dining experience regardless of budget. 
        You take pride in finding creative ways to help customers enjoy premium restaurants 
        at affordable prices. You understand that value isn't just about the lowest price, 
        but about getting the best experience for the money spent.
        
        Your recommendations always:
        - Maximize value while meeting customer preferences
        - Consider the total cost including tips and taxes
        - Highlight time-sensitive deals that shouldn't be missed
        - Explain the real savings in practical terms
        - Suggest strategic timing for maximum discounts
        """

    def get_required_tools(self) -> List[str]:
        """
        Get list of required tools for the Promotions Manager.
        
        Returns:
            List of required tool names
        """
        return [
            "coupon_finder",
            "restaurant_search",
            "supabase_retriever"
        ]

    def find_best_deals(
        self,
        preferences: Dict[str, Any],
        budget: float,
        party_size: int = 2,
        date: Optional[str] = None
    ) -> str:
        """
        Find the best deals matching customer preferences and budget.
        
        Args:
            preferences: Customer dining preferences
            budget: Total budget for the meal
            party_size: Number of people dining
            date: Specific date for dining (for time-sensitive deals)
            
        Returns:
            Optimized deal recommendations
        """
        query = f"""
        Find the best dining deals for a party of {party_size} with a budget of ${budget}.
        
        Preferences:
        - Cuisine: {preferences.get('cuisine_type', 'Any')}
        - Location: {preferences.get('location', 'Any')}
        - Occasion: {preferences.get('occasion', 'Casual dining')}
        - Dietary needs: {preferences.get('dietary', 'None')}
        {f"- Date: {date}" if date else ""}
        
        Find and analyze:
        1. Active promotions and coupons
        2. Happy hour or early bird specials
        3. Group dining deals for {party_size} people
        4. Loyalty program benefits
        5. Day-specific promotions
        
        Calculate actual savings and recommend the top 3 options with:
        - Total cost estimate (including tax/tip)
        - Savings amount and percentage
        - What's included in the deal
        - Any restrictions or conditions
        - How to claim the promotion
        """
        
        if self.agent:
            response = self.agent.execute(query)
            return self.format_response(response)
        else:
            return "Agent not initialized."

    def optimize_order_for_savings(
        self,
        restaurant_name: str,
        desired_items: List[str],
        available_coupons: List[str]
    ) -> str:
        """
        Optimize order to maximize savings with available promotions.
        
        Args:
            restaurant_name: Restaurant name
            desired_items: Items customer wants to order
            available_coupons: List of available coupon codes
            
        Returns:
            Optimized ordering strategy
        """
        query = f"""
        Create an optimized ordering strategy for {restaurant_name}.
        
        Customer wants: {', '.join(desired_items)}
        Available coupons: {', '.join(available_coupons)}
        
        Provide:
        1. Best combination of items and coupons
        2. Ordering sequence to maximize discounts
        3. Items to add/remove for better deals
        4. Timing recommendations (if applicable)
        5. Total savings calculation
        6. Alternative combinations if first choice unavailable
        
        Consider minimum order requirements, exclusions, and combination rules.
        """
        
        if self.agent:
            response = self.agent.execute(query)
            return self.format_response(response)
        else:
            return "Agent not initialized."

    def create_dining_calendar(
        self,
        budget_per_week: float,
        num_weeks: int = 4
    ) -> str:
        """
        Create a dining calendar optimized for deals and promotions.
        
        Args:
            budget_per_week: Weekly dining budget
            num_weeks: Number of weeks to plan
            
        Returns:
            Optimized dining calendar with deals
        """
        query = f"""
        Create a {num_weeks}-week dining calendar with a weekly budget of ${budget_per_week}.
        
        For each week, suggest:
        1. Best day/time for dining out based on promotions
        2. Restaurant with the best deal that week
        3. Specific promotion to use
        4. Estimated cost and savings
        5. Variety in cuisine types across weeks
        
        Optimize for:
        - Maximum value within budget
        - Variety of experiences
        - Time-sensitive promotions
        - Seasonal specials
        
        Present as a clear calendar with actionable recommendations.
        """
        
        if self.agent:
            response = self.agent.execute(query)
            return self.format_response(response)
        else:
            return "Agent not initialized."

    def compare_value_propositions(
        self,
        restaurants: List[str],
        budget: float,
        criteria: Dict[str, Any]
    ) -> str:
        """
        Compare value propositions across multiple restaurants.
        
        Args:
            restaurants: List of restaurants to compare
            budget: Budget for comparison
            criteria: Comparison criteria (quality, quantity, ambiance, etc.)
            
        Returns:
            Detailed value comparison
        """
        query = f"""
        Compare value propositions for these restaurants: {', '.join(restaurants)}
        Budget: ${budget}
        
        Evaluation criteria:
        {', '.join([f"{k}: {v}" for k, v in criteria.items()])}
        
        For each restaurant provide:
        1. Available deals and base prices
        2. Value score (1-10) based on criteria
        3. What you get for the budget
        4. Hidden costs or fees
        5. Best time to visit for value
        6. Overall recommendation
        
        Rank them by overall value and explain the ranking.
        """
        
        if self.agent:
            response = self.agent.execute(query)
            return self.format_response(response)
        else:
            return "Agent not initialized."

    def alert_expiring_deals(
        self,
        user_preferences: Dict[str, Any],
        days_ahead: int = 3
    ) -> str:
        """
        Alert about expiring deals matching user preferences.
        
        Args:
            user_preferences: User's dining preferences
            days_ahead: Number of days to look ahead
            
        Returns:
            Urgent deals alert
        """
        query = f"""
        DEAL ALERT: Find promotions expiring in the next {days_ahead} days that match:
        
        Preferences:
        - Cuisine: {user_preferences.get('cuisine_type', 'Any')}
        - Budget range: {user_preferences.get('price_range', 'Any')}
        - Location: {user_preferences.get('location', 'Any')}
        
        List urgently expiring deals with:
        1. Expiration date and time
        2. Discount amount/percentage
        3. Restaurant name and cuisine
        4. How to claim
        5. Why it's worth considering now
        
        Prioritize by value and urgency.
        """
        
        if self.agent:
            response = self.agent.execute(query)
            return self.format_response(response)
        else:
            return "Agent not initialized."