"""
Restaurant Recommendation System

Interactive interface for the CrewAI multi-agent restaurant recommendation system.
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*Pydantic.*")
warnings.filterwarnings("ignore", message=".*pydantic.*")
warnings.filterwarnings("ignore", message=".*model_fields.*")

from crew import RestaurantRecommendationCrew  
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
import sys
import time

def get_customer_input():
    """
    Collect customer dining preferences interactively.
    
    Returns:
        dict: Customer preferences including cuisine, budget, location, etc.
    """
    console = Console()
    
    console.print(Panel.fit(
        "🍽️ Welcome to the AI Restaurant Recommendation System\n"
        "Powered by CrewAI Multi-Agent Collaboration",
        style="bold blue"
    ))
    
    console.print("\n[bold]Please provide your dining preferences:[/bold]\n")
    
    inputs = {}
    
    inputs["cuisine_type"] = Prompt.ask("🍜 What type of cuisine?", default="Italian")
    inputs["budget"] = Prompt.ask("💰 Budget per person?", default="$30-60")
    inputs["location"] = Prompt.ask("📍 Preferred area?", default="Savassi")
    inputs["party_size"] = Prompt.ask("👥 Party size?", default="2")
    inputs["occasion"] = Prompt.ask("🎉 Occasion?", default="Dinner")
    
    console.print("\n[bold]Dietary Requirements:[/bold]\n")
    
    inputs["allergens"] = Prompt.ask("⚠️  Allergies?", default="none")
    inputs["dietary_restrictions"] = Prompt.ask("🥗 Dietary restrictions?", default="none")
    inputs["medical_conditions"] = Prompt.ask("🏥 Medical conditions?", default="none")
    inputs["dining_time"] = Prompt.ask("🕐 Dining time?", default="7:00 PM")
    
    return inputs


def display_agent_intro(console):
    """
    Display introduction of the AI agents.
    
    Args:
        console: Rich console instance for formatted output.
    """
    console.print("\n[bold yellow]🤖 Your AI Agent Team:[/bold yellow]")
    
    agents = [
        ("🍴", "Restaurant Concierge", "Finding perfect restaurants matching your preferences"),
        ("🥗", "Dietary Specialist", "Ensuring food safety and dietary compatibility"),
        ("💰", "Promotions Manager", "Searching for the best deals and discounts")
    ]
    
    for emoji, name, task in agents:
        console.print(f"  {emoji} [cyan]{name}[/cyan]: {task}")
    
    console.print("\n[dim]Agents will collaborate to provide comprehensive recommendations...[/dim]\n")


def main():
    """
    Main execution function.
    
    Orchestrates the multi-agent recommendation process with
    interactive input, progress tracking, and result display.
    """
    console = Console()
    
    try:
        customer_inputs = get_customer_input()
        display_agent_intro(console)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task1 = progress.add_task("[cyan]Initializing AI agents...", total=None)
            crew = RestaurantRecommendationCrew()
            time.sleep(1)
            progress.update(task1, description="[green]✓ Agents initialized")
            
            task2 = progress.add_task("[cyan]Agents collaborating on recommendations...", total=None)
            
            console.print("\n[bold]Agent Activity Log:[/bold]")
            console.print("-" * 50)
            
            start_time = time.time()
            try:
                result = crew.kickoff(customer_inputs)
                elapsed = time.time() - start_time
                progress.update(task2, description=f"[green]✓ Completed in {elapsed:.1f}s")
            except Exception as e:
                progress.update(task2, description="[red]✗ Error during execution")
                raise e
        
        console.print("\n")
        console.print(Panel(
            result,
            title="🎯 Your Personalized Restaurant Recommendations",
            border_style="green",
            expand=False
        ))
        
        console.print("\n[bold]📊 Process Statistics:[/bold]")
        console.print(f"  • Total execution time: {elapsed:.2f} seconds")
        console.print(f"  • Agents used: 3 (Concierge, Dietary, Promotions)")
        console.print(f"  • Tools executed: Multiple searches and validations")
        save_report = Prompt.ask("\n💾 Save this report?", choices=["y", "n"], default="y")
        
        if save_report == "y":
            with open("report.md", "w") as f:
                f.write(f"# Restaurant Recommendations\n\n")
                f.write(f"Generated for: {customer_inputs['occasion']}\n")
                f.write(f"Party size: {customer_inputs['party_size']}\n\n")
                f.write(result)
            console.print("✅ Report saved as 'recommendation_report.md'")
        
    except KeyboardInterrupt:
        console.print("\n[bold red]❌ Operation cancelled[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        console.print("[dim]Please check your configuration and try again[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()
