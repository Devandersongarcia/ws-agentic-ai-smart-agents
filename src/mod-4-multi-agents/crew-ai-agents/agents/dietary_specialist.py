"""
Dietary Safety Specialist Agent for allergen and dietary management.
Ensures customer safety by analyzing allergen information and restrictions.
"""

from typing import Any, Dict, List

from crewai import Agent

from .base_agent import BaseRestaurantAgent


class DietarySpecialistAgent(BaseRestaurantAgent):
    """
    Specialist agent focused on food safety, allergens, and dietary restrictions.
    Ensures all recommendations are safe and suitable for customer health needs.
    """

    def create_agent(self, tools: List[Any]) -> Agent:
        """
        Create the Dietary Safety Specialist agent.
        
        Args:
            tools: List of tools available to the agent
            
        Returns:
            Configured Dietary Specialist Agent
        """
        self.validate_tools(tools)
        
        config = self.get_base_config()
        
        self.agent = Agent(
            role=self.settings.dietary_role,
            goal=self.settings.dietary_goal,
            backstory=self._get_backstory(),
            tools=tools,
            **config
        )
        
        return self.agent

    def _get_backstory(self) -> str:
        """
        Get the backstory for the Dietary Specialist agent.
        
        Returns:
            Agent backstory
        """
        return """
        You are a certified nutritionist and food safety expert with specialized training 
        in allergen management and dietary restrictions. With a background in both 
        clinical nutrition and restaurant food preparation, you understand the critical 
        importance of accurate allergen information.
        
        Your expertise includes:
        - Comprehensive knowledge of all major allergens and their hidden sources
        - Understanding of cross-contamination risks in kitchen environments
        - Familiarity with various dietary restrictions (vegan, vegetarian, kosher, halal, etc.)
        - Knowledge of food preparation methods that affect allergen presence
        - Awareness of international food labeling standards and regulations
        
        You take a safety-first approach, always erring on the side of caution when 
        there's any doubt about allergen presence. You understand that for many people, 
        dietary restrictions aren't just preferences but medical necessities that can 
        have serious health implications.
        
        Your assessments always:
        - Prioritize customer safety above all else
        - Provide clear, unambiguous safety information
        - Include warnings about potential cross-contamination
        - Suggest safe alternatives when risks are identified
        - Educate about hidden sources of allergens
        """

    def get_required_tools(self) -> List[str]:
        """
        Get list of required tools for the Dietary Specialist.
        
        Returns:
            List of required tool names
        """
        return [
            "allergen_checker",
            "supabase_retriever"
        ]

    def validate_dietary_safety(
        self,
        restaurant_name: str,
        menu_items: List[str],
        dietary_restrictions: Dict[str, Any]
    ) -> str:
        """
        Validate the safety of menu items for given dietary restrictions.
        
        Args:
            restaurant_name: Name of the restaurant
            menu_items: List of menu items to check
            dietary_restrictions: Dictionary of restrictions and allergens
            
        Returns:
            Safety assessment and recommendations
        """
        allergens = dietary_restrictions.get("allergens", [])
        dietary_type = dietary_restrictions.get("diet_type", "")
        medical_conditions = dietary_restrictions.get("medical", [])
        
        query = f"""
        Perform a comprehensive safety assessment for {restaurant_name}:
        
        Menu items to check: {', '.join(menu_items)}
        
        Dietary requirements:
        - Allergens to avoid: {', '.join(allergens) if allergens else 'None specified'}
        - Dietary type: {dietary_type if dietary_type else 'No specific diet'}
        - Medical conditions: {', '.join(medical_conditions) if medical_conditions else 'None'}
        
        Provide:
        1. Safety status for each menu item
        2. Identified risks and concerns
        3. Cross-contamination warnings
        4. Safe alternatives if items are unsuitable
        5. Questions to ask the restaurant staff
        6. Overall safety recommendation
        """
        
        if self.agent:
            response = self.agent.execute(query)
            return self.format_response(response)
        else:
            return "Agent not initialized."

    def create_safe_meal_plan(
        self,
        restaurant_name: str,
        dietary_restrictions: Dict[str, Any],
        meal_type: str = "dinner"
    ) -> str:
        """
        Create a complete safe meal plan for a customer with restrictions.
        
        Args:
            restaurant_name: Restaurant to create plan for
            dietary_restrictions: Customer's dietary restrictions
            meal_type: Type of meal (breakfast, lunch, dinner)
            
        Returns:
            Safe meal plan with specific recommendations
        """
        query = f"""
        Create a safe and enjoyable {meal_type} meal plan at {restaurant_name} for 
        a customer with these restrictions:
        
        Allergens: {dietary_restrictions.get('allergens', [])}
        Diet type: {dietary_restrictions.get('diet_type', 'No specific diet')}
        Preferences: {dietary_restrictions.get('preferences', [])}
        
        Include:
        - Appetizer recommendations (if safe options exist)
        - Main course options with modifications if needed
        - Dessert suggestions (if safe)
        - Beverage recommendations
        - Specific preparation instructions to give the kitchen
        - Warning flags for items to definitely avoid
        """
        
        if self.agent:
            response = self.agent.execute(query)
            return self.format_response(response)
        else:
            return "Agent not initialized."

    def analyze_allergen_risk(
        self,
        menu_description: str,
        allergens_to_check: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze allergen risk for a menu description.
        
        Args:
            menu_description: Description of the menu item
            allergens_to_check: List of allergens to check for
            
        Returns:
            Risk assessment dictionary
        """
        query = f"""
        Analyze this menu item for allergen risks:
        {menu_description}
        
        Check for these allergens: {', '.join(allergens_to_check)}
        
        Provide risk levels (High/Medium/Low/None) for each allergen and explain why.
        Include any hidden sources or cross-contamination risks.
        """
        
        if self.agent:
            response = self.agent.execute(query)
            
            risk_assessment = {
                "menu_item": menu_description[:50],
                "allergens_checked": allergens_to_check,
                "risk_level": "Unknown",
                "details": response,
                "safe": False
            }
            
            response_lower = response.lower()
            if "high risk" in response_lower or "not safe" in response_lower:
                risk_assessment["risk_level"] = "High"
                risk_assessment["safe"] = False
            elif "medium risk" in response_lower or "caution" in response_lower:
                risk_assessment["risk_level"] = "Medium"
                risk_assessment["safe"] = False
            elif "low risk" in response_lower or "likely safe" in response_lower:
                risk_assessment["risk_level"] = "Low"
                risk_assessment["safe"] = True
            elif "no risk" in response_lower or "safe" in response_lower:
                risk_assessment["risk_level"] = "None"
                risk_assessment["safe"] = True
            
            return risk_assessment
        else:
            return {"error": "Agent not initialized"}

    def emergency_alternative(
        self,
        original_choice: str,
        allergen_discovered: str
    ) -> str:
        """
        Quickly find safe alternatives when an allergen is discovered.
        
        Args:
            original_choice: Original menu item or restaurant
            allergen_discovered: Allergen that was found
            
        Returns:
            Immediate safe alternatives
        """
        query = f"""
        URGENT: Customer ordered {original_choice} but we discovered it contains {allergen_discovered}.
        
        Immediately suggest:
        1. Similar dishes that are definitely free from {allergen_discovered}
        2. How to modify the original dish to make it safe (if possible)
        3. Completely different but appealing alternatives
        4. What to tell the server to ensure safety
        
        Be clear and concise - this is a time-sensitive situation.
        """
        
        if self.agent:
            response = self.agent.execute(query)
            return self.format_response(response)
        else:
            return "Agent not initialized. Please seek immediate assistance from restaurant staff."