# 🧪 Tiny Agent Workshop

Single-file AI agent implementations that each demonstrate one core agent concept. Every example runs in under 5 minutes with zero framework dependencies.

## Philosophy

> Learn agents by building them, not by installing frameworks.

Each file is a self-contained agent — no pip install, no npm install, just pure concept.

## Agents

| File | Concept | Language | Lines |
|------|---------|----------|-------|
| [`react_agent.py`](react_agent.py) | ReAct (Reason+Act) Loop | Python | ~80 |
| [`tool_caller.sh`](tool_caller.sh) | Tool Use & Function Calling | Bash | ~60 |
| [`memory_agent.js`](memory_agent.js) | Conversational Memory | Node.js | ~70 |
| [`router_agent.py`](router_agent.py) | Intent Routing / Mixture of Agents | Python | ~60 |
| [`guardrail_agent.py`](guardrail_agent.py) | Safety Guardrails & Output Validation | Python | ~50 |
| [`chain_agent.sh`](chain_agent.sh) | Agent Chaining / Pipeline | Bash | ~50 |

## Quick Start

All Python agents use only the OpenAI-compatible API (works with any provider):

```bash
export OPENAI_API_KEY="your-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # or your provider

python react_agent.py
```

Bash agents use `curl` to call the API directly. Node.js agents use built-in `fetch`.

## Agent Concepts Explained

### 1. ReAct Loop (`react_agent.py`)
The foundational agent pattern: **Reason → Act → Observe → Repeat**. The agent thinks about what to do, does it, observes the result, and decides next steps.

### 2. Tool Calling (`tool_caller.sh`)
How agents use external tools. Demonstrates structured function definitions and result parsing — the building block of all agent frameworks.

### 3. Conversational Memory (`memory_agent.js`)
Making agents remember context across turns. Shows sliding window, summarization, and importance-based memory management.

### 4. Intent Router (`router_agent.py`)
The "mixture of agents" pattern — a lightweight router classifies user intent and dispatches to specialized sub-agents. The basis for all multi-agent systems.

### 5. Safety Guardrails (`guardrail_agent.py`)
Input/output validation layers that prevent agents from doing harmful things. Demonstrates the guardrail pattern used in production systems.

### 6. Agent Chain (`chain_agent.sh`)
Piping agents together in a pipeline where each agent's output feeds the next. Shows how complex workflows emerge from simple composition.

## Why Single-File?

- **Maximum clarity** — everything in one place, no jumping between files
- **Copy-paste friendly** — grab what you need, modify, ship it
- **Educational** — every line matters, no framework magic hiding the concepts
- **Actually runnable** — no dependency hell, no version conflicts

## Requirements

- Python 3.8+ (for `.py` agents)
- Node.js 18+ (for `.js` agents)
- Bash + curl (for `.sh` agents)
- An OpenAI-compatible API endpoint

## License

MIT

---

*Part of the [Code Lab](https://github.com/robertsong2019) experiments series.*
