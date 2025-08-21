"""
Restaurant Concierge Agent for customer-facing recommendations.
Specializes in understanding preferences and finding perfect matches.
"""

from typing import Any, List

from crewai import Agent

from .base_agent import BaseRestaurantAgent


class RestaurantConciergeAgent(BaseRestaurantAgent):
    """
    Customer-facing agent that understands preferences and recommends restaurants.
    Acts as the primary interface for users seeking dining recommendations.
    """

    def create_agent(self, tools: List[Any]) -> Agent:
        """
        Create the Restaurant Concierge agent.
        
        Args:
            tools: List of tools available to the agent
            
        Returns:
            Configured Restaurant Concierge Agent
        """
        self.validate_tools(tools)
        
        config = self.get_base_config()
        
        self.agent = Agent(
            role=self.settings.concierge_role,
            goal=self.settings.concierge_goal,
            backstory=self._get_backstory(),
            tools=tools,
            **config
        )
        
        return self.agent

    def _get_backstory(self) -> str:
        """
        Get the backstory for the Restaurant Concierge agent.
        
        Returns:
            Agent backstory
        """
        return """
        You are an experienced restaurant concierge with over 15 years of experience 
        in the hospitality industry. You have an extensive knowledge of various cuisines, 
        dining atmospheres, and what makes each restaurant unique. 
        
        Your expertise includes:
        - Understanding subtle preferences and dietary needs
        - Matching restaurants to occasions (romantic dinners, business lunches, family gatherings)
        - Knowledge of seasonal menus and chef specialties
        - Awareness of restaurant ambiance, service quality, and value
        
        You take pride in finding the perfect restaurant match for each customer, 
        considering not just their stated preferences but also reading between the lines 
        to understand what would truly delight them. You always provide personalized 
        recommendations with clear explanations of why each restaurant would be perfect 
        for their specific needs.
        
        Your recommendations are always:
        - Personalized to the customer's specific situation
        - Based on current, accurate information
        - Considerate of budget and practical constraints
        - Enthusiastic but honest about what to expect
        """

    def get_required_tools(self) -> List[str]:
        """
        Get list of required tools for the Restaurant Concierge.
        
        Returns:
            List of required tool names
        """
        return [
            "restaurant_search",
            "supabase_retriever"
        ]

    def recommend_restaurants(
        self,
        customer_request: str,
        preferences: Dict[str, Any]
    ) -> str:
        """
        Generate restaurant recommendations based on customer request.
        
        Args:
            customer_request: Natural language request from customer
            preferences: Structured preferences dictionary
            
        Returns:
            Personalized restaurant recommendations
        """
        query_parts = [customer_request]
        
        if preferences.get("cuisine_type"):
            query_parts.append(f"Cuisine preference: {preferences['cuisine_type']}")
        
        if preferences.get("price_range"):
            query_parts.append(f"Budget: {preferences['price_range']}")
        
        if preferences.get("occasion"):
            query_parts.append(f"Occasion: {preferences['occasion']}")
        
        if preferences.get("party_size"):
            query_parts.append(f"Party size: {preferences['party_size']} people")
        
        if preferences.get("location"):
            query_parts.append(f"Location: {preferences['location']}")
        
        enhanced_query = " | ".join(query_parts)
        
        if self.agent:
            response = self.agent.execute(enhanced_query)
            return self.format_response(response)
        else:
            return "Agent not initialized. Please create the agent first."

    def explain_recommendation(
        self,
        restaurant_name: str,
        customer_context: str
    ) -> str:
        """
        Provide detailed explanation for why a restaurant was recommended.
        
        Args:
            restaurant_name: Name of the recommended restaurant
            customer_context: Context about the customer's needs
            
        Returns:
            Detailed explanation of the recommendation
        """
        query = f"""
        Explain why {restaurant_name} is a perfect choice given this context:
        {customer_context}
        
        Include:
        - How it matches their preferences
        - What makes it special for their occasion
        - What they should try or expect
        - Any tips for the best experience
        """
        
        if self.agent:
            response = self.agent.execute(query)
            return self.format_response(response)
        else:
            return "Agent not initialized."

    def suggest_alternatives(
        self,
        original_choice: str,
        reason_for_alternative: str
    ) -> str:
        """
        Suggest alternative restaurants when the original choice doesn't work.
        
        Args:
            original_choice: Original restaurant selection
            reason_for_alternative: Why an alternative is needed
            
        Returns:
            Alternative restaurant suggestions
        """
        query = f"""
        The customer was interested in {original_choice} but needs alternatives 
        because: {reason_for_alternative}
        
        Suggest 3 similar alternatives that address their concern while maintaining 
        the appeal of the original choice. Explain how each alternative solves 
        the problem while preserving what they liked about the original.
        """
        
        if self.agent:
            response = self.agent.execute(query)
            return self.format_response(response)
        else:
            return "Agent not initialized."