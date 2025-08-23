# 🤖 Agentic AI Workshop: From RAG to Multi-Agent Systems

A comprehensive workshop repository demonstrating the evolution from basic AI concepts to sophisticated multi-agent systems. This hands-on learning path covers RAG (Retrieval-Augmented Generation), LLMs, and intelligent agents using modern frameworks and best practices.

## 🎯 Workshop Overview

This repository is structured as a progressive learning journey through four modules, each building upon the previous to create a complete understanding of modern AI agent architectures.

### Learning Path
```
Module 1: Foundations (GIP - Get In Position)
    ↓
Module 2: RAG Systems (Vector Databases & Retrieval)
    ↓
Module 3: Single Agents (Autonomous Decision Making)
    ↓
Module 4: Multi-Agent Systems (Orchestration & Collaboration)
```

## 📚 Modules

### Module 1: GIP - Get In Position
**Location:** `src/mod-1-gip/`

Foundation concepts and environment setup for AI development.
- Understanding LLMs and their capabilities
- Setting up development environments
- Basic prompt engineering
- Introduction to AI frameworks

### Module 2: RAG - Retrieval-Augmented Generation
**Location:** `src/mod-2-rag/`

Building intelligent systems that combine retrieval with generation.

#### 🔧 Components:
- **rag-llama-index/** - Production RAG pipeline with LlamaIndex
  - Multi-collection vector database architecture (Astra DB)
  - Document preprocessing (PDF, JSON, CSV, DOCX)
  - Semantic chunking and embedding generation
  - Metadata extraction and quality assurance
  - Observability with Langfuse integration

- **langflow-pipelines/** - Visual RAG workflows
  - PDF processing with Docling
  - Multi-modal file handling
  - ChromaDB vector storage
  - Online query systems

### Module 3: Single Agent Systems
**Location:** `src/mod-3-agent/`

Creating autonomous agents with decision-making capabilities.

#### 🔧 Components:
- **dify-n8n-pipelines/** - Enterprise agent workflows
  - Spark specialist assistant ("Ask Lumi")
  - Knowledge base integration
  - Workflow automation

- **langflow-pipelines/** - Visual agent builders
  - Agent with ChromaDB knowledge base
  - Tool integration patterns
  - Decision tree implementations

### Module 4: Multi-Agent Orchestration
**Location:** `src/mod-4-multi-agents/`

Advanced multi-agent collaboration and orchestration patterns.

#### 🔧 Components:
- **crew-ai-agents/** - Restaurant Recommendation System
  - 3 specialized agents working in harmony:
    - 🍴 Restaurant Concierge (finds matching venues)
    - 🥗 Dietary Specialist (ensures food safety)
    - 💰 Promotions Manager (discovers best deals)
  - Sequential task execution
  - YAML-based configuration
  - Built-in CrewAI tools
  - LangFuse v3 observability integration
  - Production-ready with full tracing

- **langflow-pipelines/** - Visual multi-agent workflows
  - Agent communication patterns
  - Parallel and sequential processing
  - Result aggregation strategies

## 🛠️ Technology Stack

### Core Frameworks
- **LlamaIndex** - Advanced RAG and data ingestion
- **CrewAI** - Multi-agent orchestration
- **Langflow** - Visual workflow builder
- **Dify** - Enterprise AI application platform
- **n8n** - Workflow automation

### Infrastructure
- **Vector Databases**: Astra DB, ChromaDB, Supabase
- **LLMs**: OpenAI GPT-4o-mini, Claude, local models
- **Observability**: Langfuse v3, OpenTelemetry
- **Data Processing**: Docling, pandas, embeddings

### Languages & Tools
- **Python 3.9+** - Primary development language
- **YAML** - Configuration management
- **JSON** - Pipeline definitions
- **Rich** - Terminal UI components

## 🚀 Quick Start

### Prerequisites
```bash
python --version

python -m venv venv
source venv/bin/activate
```

### Installation
```bash
git clone https://github.com/yourusername/ws-agentic-ai-smart-agents.git
cd ws-agentic-ai-smart-agents

cd src/mod-4-multi-agents/crew-ai-agents
pip install -r requirements.txt

cp .env.example .env
```

### Running Examples

#### RAG Pipeline (Module 2)
```bash
cd src/mod-2-rag/rag-llama-index
python ingestion.py
```

#### Multi-Agent System (Module 4)
```bash
cd src/mod-4-multi-agents/crew-ai-agents
python main.py
```

## 🚀 Workshop Structure

### Day 1: Foundations & RAG
- **Morning**: Module 1 - AI fundamentals, LLMs, prompt engineering
- **Afternoon**: Module 2 - Building RAG systems, vector databases

### Day 2: Agents & Orchestration
- **Morning**: Module 3 - Single agent development, tools, decision-making
- **Afternoon**: Module 4 - Multi-agent systems, CrewAI, production deployment

## 🎓 Learning Objectives

By completing this workshop, you will:
1. ✅ Understand the fundamentals of LLMs and prompt engineering
2. ✅ Build production-ready RAG systems with vector databases
3. ✅ Create autonomous agents with decision-making capabilities
4. ✅ Orchestrate multi-agent systems for complex tasks
5. ✅ Implement observability and monitoring for AI systems
6. ✅ Deploy AI applications with enterprise-grade patterns

## 🛠️ Key Features Demonstrated

- **Production Patterns**: Error handling, retry logic, graceful degradation
- **Observability**: Full tracing with Langfuse v3, performance metrics
- **Scalability**: Multi-collection architectures, parallel processing
- **Security**: API key management, data validation, safe prompting
- **User Experience**: Rich terminal interfaces, progress tracking
- **Testing**: Quality assurance, validation pipelines

## 🤝 Use Cases

### Restaurant Recommendation System (Module 4)
Complete multi-agent system that:
- Searches restaurant databases
- Validates dietary restrictions
- Finds promotional offers
- Generates personalized recommendations

### Document Processing Pipeline (Module 2)
RAG system that:
- Ingests multiple file formats
- Creates semantic embeddings
- Stores in vector databases
- Enables intelligent retrieval

## 📚 Resources

### Documentation
- [CrewAI Docs](https://docs.crewai.com)
- [LlamaIndex Docs](https://docs.llamaindex.ai)
- [Langflow Docs](https://docs.langflow.org)
- [Langfuse Docs](https://langfuse.com/docs)

### Datasets
- Restaurant data (8 venues with full details)
- Promotional offers (65+ active coupons)
- Allergy guidelines and dietary information
- Multi-cuisine menu collections

## 🔧 Configuration

Each module includes:
- `.env.example` - Environment variable templates
- `requirements.txt` - Python dependencies
- Configuration files (YAML/JSON)
- README with specific instructions

## 🚨 Important Notes

- **API Keys Required**: OpenAI, Astra DB, Langfuse (depending on module)
- **Python Version**: 3.9+ required for latest features
- **Storage**: ~500MB for sample data and models
- **Internet**: Required for API calls and package installation

---

*For questions or support, please open an issue in the repository.*