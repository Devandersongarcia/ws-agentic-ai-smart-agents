"""
Main entry point for the Restaurant Recommendation Multi-Agent System.
Provides CLI interface and API endpoints for agent interactions.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

sys.path.append(str(Path(__file__).parent))

from config import get_settings
from crews import RestaurantRecommendationCrew, CrewFactory, CrewType
from observability import LangfuseObserver, MetricsCollector, trace_agent_execution

console = Console()


class RestaurantRecommendationSystem:
    """
    Main system orchestrator for restaurant recommendations.
    Manages crew execution and user interactions.
    """

    def __init__(self):
        """Initialize the recommendation system."""
        self.settings = get_settings()
        self.crew = RestaurantRecommendationCrew()
        self.factory = CrewFactory()
        self.observer = LangfuseObserver()
        self.metrics = MetricsCollector()

    def interactive_mode(self) -> None:
        """Run interactive CLI mode for restaurant recommendations."""
        console.print(
            Panel(
                "[bold cyan]🍽️ Restaurant Recommendation System[/bold cyan]\n"
                "AI-powered dining recommendations with safety and value optimization",
                border_style="cyan"
            )
        )
        
        while True:
            console.print("\n[bold]Choose an option:[/bold]")
            console.print("1. Get restaurant recommendations")
            console.print("2. Check dietary safety")
            console.print("3. Find best deals")
            console.print("4. Quick recommendation")
            console.print("5. View system metrics")
            console.print("6. Exit")
            
            choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "4", "5", "6"])
            
            if choice == "1":
                self._handle_full_recommendation()
            elif choice == "2":
                self._handle_dietary_check()
            elif choice == "3":
                self._handle_deal_finder()
            elif choice == "4":
                self._handle_quick_recommendation()
            elif choice == "5":
                self._display_metrics()
            elif choice == "6":
                console.print("[yellow]Thank you for using Restaurant Recommendation System![/yellow]")
                break

    def _handle_full_recommendation(self) -> None:
        """Handle full restaurant recommendation flow."""
        console.print("\n[bold cyan]Restaurant Recommendation[/bold cyan]")
        
        preferences = {}
        
        preferences["cuisine_type"] = Prompt.ask(
            "Preferred cuisine type",
            default="any",
            choices=["italian", "chinese", "french", "indian", "japanese", "mexican", "thai", "american", "any"]
        )
        
        preferences["price_range"] = Prompt.ask(
            "Price range",
            default="$$",
            choices=["$", "$$", "$$$", "$$$$"]
        )
        
        preferences["location"] = Prompt.ask("Location/area", default="downtown")
        
        preferences["party_size"] = int(Prompt.ask("Party size", default="2"))
        
        preferences["occasion"] = Prompt.ask(
            "Occasion",
            default="casual",
            choices=["casual", "romantic", "business", "family", "celebration"]
        )
        
        has_restrictions = Confirm.ask("Do you have dietary restrictions?")
        if has_restrictions:
            allergens_input = Prompt.ask(
                "List allergens to avoid (comma-separated)",
                default=""
            )
            if allergens_input:
                preferences["allergens"] = [a.strip() for a in allergens_input.split(",")]
            
            preferences["dietary_type"] = Prompt.ask(
                "Dietary type",
                default="none",
                choices=["none", "vegetarian", "vegan", "gluten-free", "kosher", "halal"]
            )
            
            preferences["dietary_restrictions"] = True
        
        preferences["budget_conscious"] = Confirm.ask("Would you like to see available deals?", default=True)
        if preferences["budget_conscious"]:
            budget = Prompt.ask("Maximum budget per person", default="50")
            preferences["budget"] = float(budget)
        
        custom_request = Prompt.ask(
            "\nDescribe what you're looking for (or press Enter for auto)",
            default=""
        )
        
        if not custom_request:
            custom_request = self._generate_request_from_preferences(preferences)
        
        console.print("\n[yellow]🔍 Finding perfect restaurants for you...[/yellow]\n")
        
        with trace_agent_execution(
            self.observer,
            "RestaurantCrew",
            "Full recommendation"
        ) as trace:
            try:
                result = self.crew.recommend(custom_request, preferences)
                
                self._display_recommendations(result)
                
                self.metrics.record_system_request(
                    response_time=10.0,
                    success=True
                )
                
                satisfaction = Prompt.ask(
                    "\nHow satisfied are you with these recommendations? (1-5)",
                    choices=["1", "2", "3", "4", "5"]
                )
                
                self.observer.track_user_feedback(
                    trace_id=trace.id,
                    score=float(satisfaction) / 5.0,
                    comment="User rating from interactive mode"
                )
                
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
                self.metrics.record_system_request(response_time=0, success=False)

    def _handle_dietary_check(self) -> None:
        """Handle dietary safety check flow."""
        console.print("\n[bold cyan]Dietary Safety Check[/bold cyan]")
        
        restaurant = Prompt.ask("Restaurant name")
        menu_items = Prompt.ask("Menu items to check (comma-separated)")
        allergens = Prompt.ask("Allergens to avoid (comma-separated)")
        
        allergen_list = [a.strip() for a in allergens.split(",")]
        
        safety_crew = self.factory.create_crew(CrewType.SAFETY_FOCUSED)
        
        console.print("\n[yellow]🔍 Checking dietary safety...[/yellow]\n")
        
        result = self.crew.safe_dining_recommendation(
            allergens=allergen_list,
            cuisine_preference=None
        )
        
        console.print(Panel(result, title="Safety Assessment", border_style="green"))

    def _handle_deal_finder(self) -> None:
        """Handle deal finding flow."""
        console.print("\n[bold cyan]Deal Finder[/bold cyan]")
        
        budget = float(Prompt.ask("Budget per person", default="30"))
        party_size = int(Prompt.ask("Party size", default="2"))
        cuisine = Prompt.ask("Preferred cuisine (or 'any')", default="any")
        
        console.print("\n[yellow]🔍 Finding best deals...[/yellow]\n")
        
        result = self.crew.budget_dining_recommendation(
            max_budget=budget * party_size,
            party_size=party_size
        )
        
        console.print(Panel(result, title="Best Deals Found", border_style="green"))

    def _handle_quick_recommendation(self) -> None:
        """Handle quick recommendation flow."""
        console.print("\n[bold cyan]Quick Recommendation[/bold cyan]")
        
        cuisine = Prompt.ask(
            "Cuisine type",
            choices=["italian", "chinese", "french", "indian", "japanese", "mexican", "thai", "american"]
        )
        budget = Prompt.ask("Budget", default="$$", choices=["$", "$$", "$$$", "$$$$"])
        
        console.print("\n[yellow]🔍 Getting quick recommendation...[/yellow]\n")
        
        result = self.crew.quick_recommendation(
            cuisine_type=cuisine,
            budget=budget
        )
        
        console.print(Panel(result, title="Quick Recommendation", border_style="green"))

    def _display_recommendations(self, result: Dict[str, Any]) -> None:
        """
        Display recommendations in a formatted way.
        
        Args:
            result: Recommendation results
        """
        recommendations = result.get("recommendations", "No recommendations available")
        
        console.print(Panel(
            recommendations,
            title="🍽️ Your Personalized Recommendations",
            border_style="green"
        ))
        
        metadata = result.get("metadata", {})
        if metadata:
            console.print("\n[dim]Recommendation Details:[/dim]")
            console.print(f"  • Agents used: {', '.join(metadata.get('agents_used', []))}")
            console.print(f"  • Tasks completed: {metadata.get('tasks_completed', 0)}")

    def _display_metrics(self) -> None:
        """Display system metrics."""
        console.print("\n[bold cyan]System Metrics[/bold cyan]\n")
        
        langfuse_metrics = self.observer.get_metrics_summary()
        system_metrics = self.metrics.get_system_summary()
        
        table = Table(title="Performance Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Traces", str(langfuse_metrics["total_traces"]))
        table.add_row("Total Tokens", f"{langfuse_metrics['total_tokens']:,}")
        table.add_row("Total Cost", f"${langfuse_metrics['total_cost']:.4f}")
        table.add_row("System Uptime", system_metrics["uptime"])
        table.add_row("Total Requests", str(system_metrics["total_requests"]))
        table.add_row("Success Rate", f"{system_metrics['success_rate']:.1%}")
        table.add_row("Avg Response Time", f"{system_metrics['average_response_time']:.2f}s")
        
        console.print(table)
        
        if langfuse_metrics["agents"]:
            console.print("\n[bold]Agent Performance:[/bold]")
            for agent, metrics in langfuse_metrics["agents"].items():
                console.print(f"  • {agent}: {metrics['calls']} calls, "
                            f"avg {metrics['avg_time']:.1f}s, "
                            f"${metrics['avg_cost']:.4f}/call")
        
        if langfuse_metrics["tools"]:
            console.print("\n[bold]Tool Usage:[/bold]")
            for tool, metrics in langfuse_metrics["tools"].items():
                console.print(f"  • {tool}: {metrics['calls']} calls, "
                            f"avg {metrics['avg_time']:.1f}s")

    def _generate_request_from_preferences(self, preferences: Dict[str, Any]) -> str:
        """
        Generate natural language request from preferences.
        
        Args:
            preferences: User preferences dictionary
            
        Returns:
            Natural language request
        """
        parts = ["I'm looking for"]
        
        if preferences.get("occasion") != "casual":
            parts.append(f"a {preferences['occasion']}")
        
        if preferences.get("cuisine_type") and preferences["cuisine_type"] != "any":
            parts.append(f"{preferences['cuisine_type']}")
        
        parts.append("restaurant")
        
        if preferences.get("location"):
            parts.append(f"in {preferences['location']}")
        
        if preferences.get("party_size"):
            parts.append(f"for {preferences['party_size']} people")
        
        if preferences.get("price_range"):
            parts.append(f"in the {preferences['price_range']} price range")
        
        request = " ".join(parts) + "."
        
        if preferences.get("allergens"):
            request += f" Must avoid: {', '.join(preferences['allergens'])}."
        
        if preferences.get("dietary_type") and preferences["dietary_type"] != "none":
            request += f" Need {preferences['dietary_type']} options."
        
        return request

    def run_cli(self, args: argparse.Namespace) -> None:
        """
        Run CLI based on provided arguments.
        
        Args:
            args: Parsed command-line arguments
        """
        if args.mode == "interactive":
            self.interactive_mode()
        elif args.mode == "quick":
            result = self.crew.quick_recommendation(
                cuisine_type=args.cuisine,
                budget=args.budget
            )
            console.print(result)
        elif args.mode == "safe":
            allergens = args.allergens.split(",") if args.allergens else []
            result = self.crew.safe_dining_recommendation(
                allergens=allergens,
                cuisine_preference=args.cuisine
            )
            console.print(result)
        elif args.mode == "deals":
            result = self.crew.budget_dining_recommendation(
                max_budget=args.budget_amount,
                party_size=args.party_size
            )
            console.print(result)

    def shutdown(self) -> None:
        """Cleanup and shutdown system."""
        console.print("\n[yellow]Shutting down...[/yellow]")
        self.observer.shutdown()
        console.print("[green]System shutdown complete.[/green]")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Restaurant Recommendation Multi-Agent System"
    )
    
    parser.add_argument(
        "mode",
        choices=["interactive", "quick", "safe", "deals"],
        help="Execution mode",
        nargs="?",
        default="interactive"
    )
    
    parser.add_argument(
        "--cuisine",
        default="italian",
        help="Cuisine type for quick mode"
    )
    
    parser.add_argument(
        "--budget",
        default="$$",
        help="Budget range ($, $$, $$$, $$$$)"
    )
    
    parser.add_argument(
        "--allergens",
        default="",
        help="Comma-separated list of allergens"
    )
    
    parser.add_argument(
        "--budget-amount",
        type=float,
        default=50.0,
        help="Budget amount for deals mode"
    )
    
    parser.add_argument(
        "--party-size",
        type=int,
        default=2,
        help="Party size"
    )
    
    args = parser.parse_args()
    
    try:
        system = RestaurantRecommendationSystem()
        system.run_cli(args)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}[/red]")
        if args.mode == "interactive":
            console.print("[dim]Run with --help for usage information[/dim]")
    finally:
        if 'system' in locals():
            system.shutdown()


if __name__ == "__main__":
    main()