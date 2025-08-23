# 🍽️ CrewAI Restaurant Recommendation System

A demonstration of CrewAI's multi-agent collaboration using only built-in tools. This system showcases how specialized AI agents work together autonomously to provide comprehensive restaurant recommendations through sequential task execution.

## 🎯 Overview

This system demonstrates advanced multi-agent collaboration using CrewAI framework. Three specialized agents work together to analyze customer preferences, ensure dietary safety, find the best deals, and create personalized restaurant recommendations.

## 🤖 Agents

### 1. Restaurant Concierge
- **Role**: Restaurant Recommendation Specialist
- **Expertise**: 15+ years hospitality industry experience
- **Responsibilities**: Find perfect restaurants matching customer preferences
- **Tools**: Restaurant database search, file reading

### 2. Dietary Specialist  
- **Role**: Food Safety and Dietary Expert
- **Expertise**: Certified nutritionist with allergen management specialization
- **Responsibilities**: Ensure recommendations are safe for dietary restrictions
- **Tools**: Restaurant analysis, allergy guidelines, safety protocols

### 3. Promotions Manager
- **Role**: Deals and Promotions Specialist
- **Expertise**: Industry connections and promotional offers knowledge
- **Responsibilities**: Find best available deals and calculate savings
- **Tools**: Coupons database, promotional offers analysis

## 📋 Tasks Workflow

1. **Restaurant Search**: Find 3-5 restaurants matching customer criteria
2. **Dietary Safety Check**: Analyze recommendations for allergen safety
3. **Promotions Search**: Discover available deals and discounts  
4. **Final Recommendation**: Synthesize all information into actionable guide

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│              Customer Input             │
│     (preferences, allergies, budget)    │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│         Restaurant Concierge            │
│    🔍 Searches restaurant database      │
│    📝 Finds 3-5 matching venues        │
└─────────────┬───────────────────────────┘
              │
    ┌─────────▼─────────┐    ┌─────────────────┐
    │ Dietary Specialist │    │ Promotions Mgr  │
    │ ⚠️  Safety analysis │    │ 💰 Deals finder  │
    │ 🥗 Allergen check  │    │ 🎟️  Savings calc │
    └─────────┬─────────┘    └─────────┬───────┘
              │                        │
              └─────────┬──────────────┘
                        │
           ┌─────────────▼───────────────┐
           │     Final Recommendation    │
           │   📊 Ranked suggestions     │
           │   📋 Complete dining guide  │
           │   ✅ Actionable next steps  │
           └─────────────────────────────┘
```

## 🛠️ Technology Stack

- **CrewAI**: Multi-agent orchestration framework
- **OpenAI GPT-4o-mini**: Large language model for agents
- **YAML Configuration**: Declarative agent and task definitions
- **Built-in Tools**: File reading, JSON/CSV/DOCX search capabilities
- **Rich Console**: Beautiful terminal interface
- **Pydantic**: Data validation and settings management

## 📊 Data Sources

- **Restaurants Database**: `storage/json/restaurants.json` (8 restaurants with detailed info)
- **Promotional Offers**: `storage/csv/coupons_2025-07-31.csv` (65+ current deals)
- **Allergy Guidelines**: `storage/doc/allergy.docx` (Safety protocols)
- **Menu PDFs**: `storage/pdf/` (8 cuisine type menus)

## 🚀 Quick Start

### Prerequisites
- Python 3.10-3.12
- OpenAI API key

### Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. **Run the system**:
   ```bash
   python main.py
   ```

### Interactive Usage

The system will prompt you for:
- Cuisine preferences
- Budget range
- Location and party size
- Occasion type
- Allergies and dietary restrictions
- Preferred dining time

## 🧪 Testing

Test the crew directly:
```bash
python crew.py
```

This runs with sample customer data to verify all agents are working correctly.

## 📁 Project Structure

```
crew-ai-agents/
├── config/
│   ├── agents.yaml          # Agent definitions
│   └── tasks.yaml           # Task configurations
├── storage/                 # Data sources
│   ├── json/restaurants.json
│   ├── csv/coupons_2025-07-31.csv
│   ├── doc/allergy.docx
│   └── pdf/[menu files]
├── crew.py                  # Main crew implementation
├── main.py                  # Interactive entry point
├── requirements.txt         # Dependencies
├── .env                     # Environment configuration
└── README.md               # This file
```

## 🎓 Workshop Demo (15 minutes)

### Part 1: Architecture Overview (5 min)
1. Explain multi-agent collaboration concept
2. Show YAML configuration approach
3. Demonstrate agent specialization and delegation

### Part 2: Live Demonstration (7 min)
1. Run `python main.py`
2. Input sample customer requirements
3. Show agents working collaboratively
4. Highlight final recommendation output

### Part 3: Key Takeaways (3 min)
1. CrewAI's decorator pattern (@CrewBase, @agent, @task)
2. YAML-driven configuration for maintainability
3. Built-in tools vs custom RAG implementation
4. Memory and planning capabilities

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key
- `OPENAI_MODEL_NAME`: Model to use (default: gpt-4o-mini)
- `OPENAI_TEMPERATURE`: Creativity level (default: 0.7)
- `CREWAI_TELEMETRY_ENABLED`: Telemetry setting (default: false)

### Customization
- Modify `config/agents.yaml` to adjust agent behavior
- Update `config/tasks.yaml` to change task requirements
- Add new tools in `crew.py` for additional data sources
