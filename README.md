# MakTek Multi-Agent Customer Support RAG System

A sophisticated multi-agent customer support system built with LangGraph, featuring Supervisor-Worker architecture, advanced memory management, and self-correction guardrails.

## Features

- 🧠 **Multi-Agent Architecture**: Supervisor coordinates specialized agents (Retriever, Generator, Escalator)
- 📚 **RAG Pipeline**: FAISS vector store for efficient similarity search
- 💾 **Dual Memory System**: Short-term (MemorySaver) and long-term (BaseStore) persistence
- 🛡️ **Advanced Guardrails**: Hallucination detection and relevance scoring
- 🔄 **Self-Correction Loops**: Automatic retry on hallucinations or low-quality retrievals
- ⚡ **Dynamic Model Selection**: Switch between OpenAI and Anthropic models
- 📝 **Auto-Summarization**: Condenses conversation history to save tokens

## Architecture

```
User Query → Supervisor → Retriever → Generator → Hallucination Check → Response
                ↓            ↓
            Escalator   (Low Relevance)
```

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd New\ Chatbot\ AntiGravity

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# Required: OPENAI_API_KEY or ANTHROPIC_API_KEY
```

### Run the System

```bash
# Run the main application
python main.py

# Run example scenarios
python examples/example_usage.py
```

## Project Structure

```
.
├── src/
│   ├── agents/          # Agent implementations
│   ├── guardrails/      # Self-correction logic
│   ├── memory/          # Memory management
│   ├── rag/             # Vector store & retrieval
│   ├── tools/           # Support ticket tools
│   ├── utils/           # Prompts & utilities
│   ├── state.py         # State definitions
│   ├── models.py        # Model configuration
│   └── graph.py         # LangGraph compilation
├── data/                # MakTek Q&A dataset
├── examples/            # Usage examples
├── tests/               # Test suite
└── main.py              # Entry point
```

## Key Components

### Agents
- **Supervisor**: Orchestrates the workflow and routes to appropriate agents
- **Retriever**: Searches the vector store for relevant information
- **Generator**: Synthesizes responses from retrieved documents
- **Escalator**: Creates support tickets for unresolved queries
- **Summarizer**: Condenses conversation history

### Guardrails
- **Hallucination Check**: Verifies generated answers against source documents
- **Relevance Scoring**: Auto-escalates low-quality retrievals

### Memory
- **Short-term**: Thread-specific conversation history with checkpointing
- **Long-term**: User preferences and patterns

## Configuration Options

See `.env.example` for all available configuration options including:
- Model selection (OpenAI/Anthropic)
- RAG parameters (relevance threshold, max docs)
- Memory settings (summarization trigger)
- Guardrail toggles

## License

MIT
