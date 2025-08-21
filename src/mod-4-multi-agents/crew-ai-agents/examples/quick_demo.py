"""
Quick demo script for workshop presentation.
Shows the multi-agent system in action with pre-tested queries.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from crews.restaurant_crew import RestaurantRecommendationCrew
from config.settings import Settings
from rich.console import Console
from rich.panel import Panel

console = Console()

def demo_simple_query():
    """Demonstrate a simple restaurant search."""
    console.print(Panel("🔍 Simple Query: Italian Restaurant", style="bold blue"))
    
    crew = RestaurantRecommendationCrew()
    crew.setup_agents()
    crew.setup_tools()
    
    request = {
        "cuisine": "Italian",
        "location": "downtown",
        "party_size": 2
    }
    
    result = crew.process_recommendation(request)
    console.print(result)

def demo_complex_query():
    """Demonstrate complex query with allergies and budget."""
    console.print(Panel("🎯 Complex Query: Safe Dining with Deals", style="bold green"))
    
    crew = RestaurantRecommendationCrew()
    crew.setup_agents()
    crew.setup_tools()
    
    request = {
        "cuisine": "Asian",
        "dietary_restrictions": ["vegetarian"],
        "allergens": ["peanuts", "shellfish"],
        "budget": "$$",
        "party_size": 4,
        "preferences": ["family-friendly", "good-reviews"]
    }
    
    result = crew.process_recommendation(request)
    console.print(result)

def demo_safety_first():
    """Demonstrate allergen-focused query."""
    console.print(Panel("🛡️ Safety First: Severe Allergy Check", style="bold red"))
    
    crew = RestaurantRecommendationCrew()
    crew.setup_agents()
    crew.setup_tools()
    
    request = {
        "allergens": ["gluten", "dairy", "eggs"],
        "dietary_restrictions": ["vegan"],
        "location": "any"
    }
    
    result = crew.process_recommendation(request)
    console.print(result)

if __name__ == "__main__":
    console.print(Panel.fit(
        "🤖 Restaurant Recommendation Multi-Agent System Demo",
        style="bold magenta"
    ))
    
    import sys
    if len(sys.argv) > 1:
        demo_type = sys.argv[1]
        if demo_type == "simple":
            demo_simple_query()
        elif demo_type == "complex":
            demo_complex_query()
        elif demo_type == "safety":
            demo_safety_first()
        else:
            console.print("Usage: python quick_demo.py [simple|complex|safety]")
    else:
        console.print("Running all demos...\n")
        demo_simple_query()
        console.print()
        demo_complex_query()
        console.print()
        demo_safety_first()