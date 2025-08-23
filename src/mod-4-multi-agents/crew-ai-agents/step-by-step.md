# 🎓 CrewAI Multi-Agent System: Step-by-Step Workshop Guide

## 📚 Workshop Overview

In this hands-on workshop, you'll build a production-ready multi-agent system that demonstrates real-world AI orchestration patterns. We'll create three specialized agents that collaborate to provide restaurant recommendations.

**Duration:** 2 hours  
**Level:** Intermediate  
**Prerequisites:** Basic Python, Understanding of LLMs

---

## 🎯 Learning Objectives

By the end of this workshop, you will:
1. ✅ Understand multi-agent collaboration patterns
2. ✅ Configure agents using YAML
3. ✅ Implement sequential task execution
4. ✅ Add observability with LangFuse
5. ✅ Build production-ready AI systems

---

## 📋 Table of Contents

1. [Environment Setup](#step-1-environment-setup)
2. [Understanding the Architecture](#step-2-understanding-the-architecture)
3. [Configuring Agents](#step-3-configuring-agents)
4. [Defining Tasks](#step-4-defining-tasks)
5. [Building the Crew](#step-5-building-the-crew)
6. [Creating the Interface](#step-6-creating-the-interface)
7. [Adding Observability](#step-7-adding-observability)
8. [Testing & Running](#step-8-testing--running)
9. [Production Deployment](#step-9-production-deployment)
10. [Exercises & Challenges](#step-10-exercises--challenges)

---

## Step 1: Environment Setup
**Time: 10 minutes**

### 1.1 Create Project Structure

```bash
mkdir crew-ai-agents
cd crew-ai-agents

mkdir -p config storage/{json,csv,doc,pdf}
```

### 1.2 Install Dependencies

```bash
python -m venv venv
source venv/bin/activate

cat > requirements.txt << EOF
crewai==0.165.1
crewai-tools==0.62.3
python-dotenv>=1.0.0
pydantic>=2.5.0
pyyaml>=6.0.0
rich>=13.0.0
openai>=1.0.0
langfuse==3.3.0
openlit>=1.0.0
EOF

pip install -r requirements.txt
```

### 1.3 Configure Environment Variables

```bash
cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL_NAME=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
CREWAI_TELEMETRY_ENABLED=false
EOF
```

**🎯 Checkpoint:** You should now have a project with all dependencies installed.

---

## Step 2: Understanding the Architecture
**Time: 15 minutes**

### 2.1 The Multi-Agent Pattern

```
┌─────────────────────────────────────────┐
│           Customer Request              │
│    "I want Italian food under $50"     │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│      Agent 1: Restaurant Concierge      │
│   Searches database for matches         │
└─────────────┬───────────────────────────┘
              │
              ▼
    ┌──────────────────┬──────────────────┐
    ▼                  ▼                  
┌──────────┐    ┌──────────────┐
│ Agent 2  │    │   Agent 3    │
│ Dietary  │    │  Promotions  │
│Specialist│    │   Manager    │
└────┬─────┘    └──────┬───────┘
     │                 │
     └────────┬────────┘
              ▼
┌─────────────────────────────────────────┐
│         Final Recommendation            │
│     Synthesized from all agents         │
└─────────────────────────────────────────┘
```

### 2.2 Key Concepts

**Agent:** An autonomous entity with a specific role and expertise  
**Task:** A specific objective an agent must complete  
**Crew:** A team of agents working together  
**Tool:** Capabilities agents can use (file reading, search, etc.)

### 2.3 Why Multi-Agent?

- **Specialization:** Each agent focuses on one domain
- **Scalability:** Easy to add new agents
- **Maintainability:** Changes to one agent don't affect others
- **Reliability:** Agents can validate each other's work

**💡 Discussion:** What other multi-agent scenarios can you think of?

---

## Step 3: Configuring Agents
**Time: 20 minutes**

### 3.1 Create Agent Configuration

Create `config/agents.yaml`:

```yaml
# Restaurant Concierge Agent
restaurant_concierge:
  role: Restaurant Recommendation Specialist
  goal: Find the perfect restaurants that match customer preferences
  backstory: |
    You are an experienced restaurant concierge with over 15 years 
    in the hospitality industry. You have extensive knowledge of 
    various cuisines, dining atmospheres, and price ranges. Your 
    expertise helps customers discover amazing dining experiences 
    that perfectly match their preferences and budget.
  verbose: true
  allow_delegation: true
  max_iter: 2

# Dietary Specialist Agent  
dietary_specialist:
  role: Food Safety and Dietary Expert
  goal: Ensure all restaurant recommendations are safe for customer dietary needs
  backstory: |
    You are a certified nutritionist and food safety expert with 
    specialized knowledge in allergies, dietary restrictions, and 
    medical dietary requirements. You analyze restaurant offerings 
    to ensure they meet specific dietary needs and flag any 
    potential allergen concerns.
  verbose: true
  allow_delegation: false
  max_iter: 1

# Promotions Manager Agent
promotions_manager:
  role: Deals and Promotions Specialist
  goal: Find the best available deals and calculate potential savings
  backstory: |
    You are a deals hunter with extensive connections in the 
    restaurant industry. You know all current promotions, happy 
    hour specials, and exclusive discounts. Your mission is to 
    maximize value for customers while maintaining quality 
    dining experiences.
  verbose: true
  allow_delegation: false
  max_iter: 1
```

### 3.2 Understanding Agent Properties

| Property | Purpose | Best Practice |
|----------|---------|---------------|
| `role` | Agent's job title | Be specific and descriptive |
| `goal` | What the agent aims to achieve | Clear, measurable objective |
| `backstory` | Agent's expertise and personality | Adds context for better responses |
| `verbose` | Show agent's thinking process | Use `true` for debugging |
| `allow_delegation` | Can delegate tasks to other agents | Only for coordinator agents |
| `max_iter` | Maximum attempts at a task | Balance between quality and speed |

**🎯 Exercise:** Modify one agent's backstory and observe how it affects responses.

---

## Step 4: Defining Tasks
**Time: 20 minutes**

### 4.1 Create Task Configuration

Create `config/tasks.yaml`:

```yaml
# Task 1: Search for restaurants
restaurant_search:
  description: |
    Search for restaurants that match the customer's preferences.
    
    Customer preferences:
    - Cuisine type: {cuisine_type}
    - Budget: {budget}
    - Location: {location}
    - Party size: {party_size}
    - Occasion: {occasion}
    
    Your task:
    1. Use FileReadTool to read storage/json/restaurants.json
    2. Analyze the JSON content to find restaurants matching the cuisine type
    3. Filter by budget requirements
    4. Consider location preferences
    5. Return 3-5 suitable restaurants with details
    
    IMPORTANT: You MUST search the restaurants.json file to find ACTUAL restaurants.
    Do NOT make up restaurant names. Only use restaurants that exist in the file.
  expected_output: |
    A list of 3-5 restaurants with:
    - Restaurant name
    - Cuisine type
    - Price range
    - Location
    - Why it matches the customer's preferences

# Task 2: Check dietary requirements
dietary_safety_check:
  description: |
    Analyze the recommended restaurants for dietary safety.
    
    Customer dietary information:
    - Allergens: {allergens}
    - Dietary restrictions: {dietary_restrictions}
    - Medical conditions: {medical_conditions}
    
    Your task:
    1. Review each recommended restaurant
    2. Use FileReadTool to check storage/doc/allergy.docx for guidelines
    3. Identify potential allergen risks
    4. Suggest safe menu options
    5. Provide clear warnings if needed
  expected_output: |
    For each restaurant:
    - Dietary safety assessment
    - Specific allergen warnings
    - Recommended safe dishes
    - Items to avoid

# Task 3: Find promotions
promotions_search:
  description: |
    Search for available deals and promotions.
    
    Your task:
    1. Use FileReadTool to read storage/csv/coupons_2025-07-31.csv
    2. Find applicable promotions for recommended restaurants
    3. Calculate potential savings
    4. Prioritize best value deals
    5. Check validity dates and restrictions
  expected_output: |
    Available promotions:
    - Restaurant name
    - Promotion details
    - Discount percentage or amount
    - Validity period
    - Any restrictions
    - Calculated savings for the party

# Task 4: Create final recommendation
final_recommendation:
  description: |
    Create the ultimate dining recommendation guide.
    
    Synthesize all information from previous tasks:
    1. Restaurant recommendations
    2. Dietary safety analysis
    3. Available promotions
    
    Create a comprehensive guide that includes:
    - Top 3 restaurant recommendations ranked by fit
    - Clear dietary information for each
    - Available deals and savings
    - Specific dish recommendations
    - Reservation suggestions for {dining_time}
    - Total estimated cost for {party_size} people
  expected_output: |
    # Restaurant Recommendations for {occasion}
    
    ## Top Recommendation
    [Detailed restaurant info with reasoning]
    
    ## Alternative Options
    [2-3 other suitable restaurants]
    
    ## Dietary Considerations
    [Safety information and recommendations]
    
    ## Available Deals
    [Promotions and savings]
    
    ## Action Steps
    1. Make reservation
    2. Mention dietary needs
    3. Ask about promotions
```

### 4.2 Task Dependencies

```python
dietary_task.context = [restaurant_search_task]
promotions_task.context = [restaurant_search_task]
final_task.context = [restaurant_search_task, dietary_task, promotions_task]
```

**💡 Key Concept:** Context allows tasks to access results from previous tasks.

---

## Step 5: Building the Crew
**Time: 25 minutes**

### 5.1 Create the Main Crew Implementation

Create `crew.py`:

```python
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


# Test the crew directly
if __name__ == "__main__":
    crew = RestaurantRecommendationCrew()
    
    # Sample customer data
    inputs = {
        "cuisine_type": "Italian",
        "budget": "$30-50",
        "location": "Downtown",
        "party_size": "4",
        "occasion": "Business Lunch",
        "allergens": "nuts",
        "dietary_restrictions": "vegetarian options needed",
        "medical_conditions": "none",
        "dining_time": "12:30 PM"
    }
    
    print("🚀 Starting Restaurant Recommendation Crew...")
    result = crew.kickoff(inputs)
    print("\n📋 Final Recommendations:")
    print(result)
```

### 5.2 Understanding the Decorators

| Decorator | Purpose | Usage |
|-----------|---------|-------|
| `@CrewBase` | Marks class as a CrewAI crew | Required for all crews |
| `@agent` | Defines an agent method | Returns configured Agent |
| `@task` | Defines a task method | Returns configured Task |
| `@crew` | Defines the crew composition | Returns configured Crew |

### 5.3 Key Implementation Details

```python
process=Process.sequential
process=Process.hierarchical

context=[self.restaurant_search()]

# Output File
output_file='report.md'
```

**🎯 Exercise:** Change from sequential to hierarchical processing and observe the difference.

---

## Step 6: Creating the Interface
**Time: 15 minutes**

### 6.1 Build Interactive CLI

Create `main.py`:

```python
"""
Restaurant Recommendation System

Interactive interface for the CrewAI multi-agent restaurant recommendation system.
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

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
    inputs["location"] = Prompt.ask("📍 Preferred area?", default="Downtown")
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
            result = crew.kickoff(customer_inputs)
            elapsed = time.time() - start_time
            
            progress.update(task2, description=f"[green]✓ Completed in {elapsed:.1f}s")
        
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
            console.print("✅ Report saved as 'report.md'")
        
    except KeyboardInterrupt:
        console.print("\n[bold red]❌ Operation cancelled[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        console.print("[dim]Please check your configuration and try again[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### 6.2 Rich Console Features

- **Panels:** Visual containers for information
- **Progress Bars:** Show task execution status
- **Prompts:** Interactive user input
- **Colors:** Enhance readability and UX

**💡 Tip:** Rich console makes CLI apps feel professional and user-friendly.

---

## Step 7: Adding Observability
**Time: 15 minutes**

### 7.1 Create Observability Module

Create `observability.py`:

```python
"""
LangFuse Observability Module for CrewAI

Provides OpenTelemetry-based tracing and monitoring for the multi-agent system.
"""

import os
from typing import Optional, Dict, Any
from contextlib import contextmanager
from langfuse import get_client
from dotenv import load_dotenv

load_dotenv()


class LangFuseObservability:
    """
    Manages LangFuse integration for CrewAI observability.
    
    Provides tracing, monitoring, and analytics for agent interactions.
    """
    
    def __init__(self):
        """Initialize LangFuse client if credentials are available."""
        self.enabled = self._check_credentials()
        
        if self.enabled:
            self.client = get_client()
        else:
            self.client = None
    
    def _check_credentials(self) -> bool:
        """Check if LangFuse credentials are configured."""
        return all([
            os.getenv("LANGFUSE_PUBLIC_KEY"),
            os.getenv("LANGFUSE_SECRET_KEY"),
            os.getenv("LANGFUSE_HOST")
        ])
    
    @contextmanager
    def trace(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Create a tracing context for CrewAI operations.
        
        Args:
            name: Name of the trace
            metadata: Optional metadata to attach to the trace
        """
        if not self.enabled:
            yield None
            return
        
        trace = self.client.start_as_current_span(name=name)
        
        if metadata:
            trace.update_current_observation(metadata=metadata)
        
        try:
            yield trace
        finally:
            self.flush()
    
    def score(self, name: str, value: float, comment: Optional[str] = None):
        """Add a score to the current trace."""
        if self.enabled and self.client:
            self.client.score(name=name, value=value, comment=comment)
    
    def flush(self):
        """Flush pending traces to LangFuse."""
        if self.enabled and self.client:
            self.client.flush()
    
    @property
    def is_enabled(self) -> bool:
        """Check if observability is enabled."""
        return self.enabled


observability = LangFuseObservability()
```

### 7.2 Integrate Observability

Update `crew.py` kickoff method:

```python
def kickoff(self, inputs: Dict[str, Any]) -> str:
    """Execute with observability."""
    from observability import observability
    
    with observability.trace("restaurant-recommendation", inputs):
        result = self.crew().kickoff(inputs=inputs)
        
        observability.score(
            name="recommendation_quality",
            value=0.95,
            comment="High quality recommendations generated"
        )
    
    return result
```

### 7.3 Benefits of Observability

- **Trace Every LLM Call:** See token usage and costs
- **Debug Agent Decisions:** Step-by-step reasoning
- **Performance Metrics:** Identify bottlenecks
- **Cost Optimization:** Track and reduce token usage

**🎯 Demo:** Show LangFuse dashboard with live traces.

---

## Step 8: Testing & Running
**Time: 10 minutes**

### 8.1 Add Sample Data

Create `storage/json/restaurants.json`:

```json
[
  {
    "name": "La Bella Italia",
    "cuisine": "Italian",
    "price_range": "$30-50",
    "location": "Downtown",
    "rating": 4.7,
    "specialties": ["pasta", "pizza", "risotto"],
    "dietary_options": ["vegetarian", "gluten-free"],
    "atmosphere": "romantic, cozy"
  },
  {
    "name": "Tokyo Sushi House",
    "cuisine": "Japanese",
    "price_range": "$40-70",
    "location": "Midtown",
    "rating": 4.8,
    "specialties": ["sushi", "sashimi", "ramen"],
    "dietary_options": ["vegetarian", "pescatarian"],
    "atmosphere": "modern, minimalist"
  }
]
```

### 8.2 Test Individual Components

```bash
python crew.py

python main.py

python -m pytest tests/ -v
```

### 8.3 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "No API key" | Check .env file has OPENAI_API_KEY |
| "File not found" | Ensure storage/ directory has data files |
| "Import error" | Run `pip install -r requirements.txt` |
| "Slow response" | Reduce max_iter in agents.yaml |

---

## Step 9: Production Deployment
**Time: 10 minutes**

### 9.1 Production Checklist

```python
PRODUCTION_CONFIG = {
    "error_handling": "comprehensive",
    "retry_logic": "exponential_backoff",
    "logging": "structured",
    "monitoring": "langfuse",
    "caching": "redis",
    "rate_limiting": "enabled",
    "security": "api_key_rotation"
}
```

### 9.2 Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

### 9.3 API Wrapper

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from crew import RestaurantRecommendationCrew

app = FastAPI()

class RecommendationRequest(BaseModel):
    cuisine_type: str
    budget: str
    location: str
    party_size: str

@app.post("/recommend")
async def get_recommendations(request: RecommendationRequest):
    try:
        crew = RestaurantRecommendationCrew()
        result = crew.kickoff(request.dict())
        return {"recommendations": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Step 10: Exercises & Challenges
**Time: 20 minutes**

### 🎯 Exercise 1: Add a New Agent
**Difficulty:** ⭐⭐

Add a "Review Analyst" agent that:
- Reads customer reviews
- Provides sentiment analysis
- Adds review scores to recommendations

```yaml
# Add to agents.yaml
review_analyst:
  role: Customer Review Specialist
  goal: Analyze customer feedback and sentiment
  backstory: You are an expert in analyzing customer reviews...
```

### 🎯 Exercise 2: Implement Caching
**Difficulty:** ⭐⭐⭐

Add caching to avoid repeated API calls:

```python
import functools
import hashlib

@functools.lru_cache(maxsize=100)
def cached_recommendation(inputs_hash):
    crew = RestaurantRecommendationCrew()
    return crew.kickoff(inputs)
```

### 🎯 Exercise 3: Add Weather Integration
**Difficulty:** ⭐⭐⭐⭐

Create a weather-aware recommendation system:
- Check weather for dining date
- Suggest indoor/outdoor seating
- Adjust recommendations based on weather

### 🎯 Exercise 4: Multi-Language Support
**Difficulty:** ⭐⭐⭐⭐⭐

Extend the system to support multiple languages:
- Detect user language
- Translate recommendations
- Maintain cultural context

---

## 🎓 Key Takeaways

### What You've Learned

1. **Multi-Agent Architecture**
   - Agents specialize in specific domains
   - Tasks define what agents should accomplish
   - Crews orchestrate agent collaboration

2. **Configuration Management**
   - YAML separates logic from configuration
   - Declarative approach improves maintainability
   - Easy to modify without changing code

3. **Production Patterns**
   - Error handling and retry logic
   - Observability and monitoring
   - Performance optimization

4. **CrewAI Best Practices**
   - Use built-in tools when possible
   - Keep agents focused on single responsibilities
   - Leverage context for task dependencies

### Next Steps

1. **Extend the System**
   - Add more agents for specialized tasks
   - Integrate external APIs
   - Build a web interface

2. **Optimize Performance**
   - Implement caching strategies
   - Parallel task execution
   - Token usage optimization

3. **Deploy to Production**
   - Set up CI/CD pipeline
   - Add comprehensive testing
   - Implement monitoring dashboards

---

## 📚 Additional Resources

### Documentation
- [CrewAI Official Docs](https://docs.crewai.com)
- [LangFuse Integration Guide](https://langfuse.com/docs)
- [OpenAI API Reference](https://platform.openai.com/docs)

### Community
- CrewAI Discord Server
- GitHub Discussions
- Stack Overflow #crewai tag

### Advanced Topics
- Hierarchical crew structures
- Custom tool development
- Agent memory systems
- Async task execution

---

## 🤔 Reflection Questions

1. How would you scale this system to handle 1000s of requests?
2. What other industries could benefit from multi-agent systems?
3. How would you implement agent learning from past interactions?
4. What security considerations are important for production?

---

## 🎉 Congratulations!

You've successfully built a production-ready multi-agent system! This foundation can be adapted for countless real-world applications:

- **Customer Service:** Multi-agent support systems
- **Research:** Literature review and synthesis
- **Finance:** Investment analysis and recommendations
- **Healthcare:** Patient care coordination
- **Education:** Personalized learning paths

Remember: The power of multi-agent systems lies in specialization and collaboration. Each agent should do one thing exceptionally well, and together they achieve what no single agent could.

---

*Happy Building! 🚀*
