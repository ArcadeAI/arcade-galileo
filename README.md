# Langchain + Arcade MCP -> Galileo Tracing Demo

**LangChain workflow leveraging tools using Arcade MCP Runtime with automatic tracing to Galileo.**

Arcade exposes tools (Gmail, Google Docs, etc.) via MCP protocol. LangChain auto-instrumentation captures all LLM calls and tool executions - zero manual tracing code.

## Stack

- **[LangChain](https://langchain.com/)** - Agent framework with MCP adapter
- **[Arcade](https://arcade.dev/)** - MCP Runtime exposing tools via MCP protocol
- **[Galileo](https://galileo.ai/)** - Observability platform (receives traces via OTLP)

## Quick Start

### 1. Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

Copy `env.example` to `.env` and fill in:

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Arcade MCP Gateway
MCP_SERVER_URL=https://api.arcade.dev/mcp/assist
ARCADE_API_KEY=arc_...
ARCADE_USER_ID=you@example.com

# Galileo
GALILEO_API_KEY=...
GALILEO_PROJECT_NAME=my-project
```

### 3. Run

```bash
python workflow.py
```

### 4. View Traces

Open [https://app.galileo.ai](https://app.galileo.ai) → Your project → See traces with:
- LLM calls (prompts, completions, tokens)
- MCP tool executions (inputs, outputs)

## How It Works

```
┌─────────────────────────────────────────┐
│           workflow.py                    │
│  ┌───────────────────────────────────┐  │
│  │  LangChain Agent + MCP Tools      │  │
│  │  (auto-instrumented)              │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
          │                    │
          │ MCP                │ OTLP
          ↕                    ↓
┌─────────────────┐   ┌─────────────────┐
│  Arcade MCP     │   │    Galileo      │
│  Runtime        │   │                 │
└─────────────────┘   └─────────────────┘
```

## Files

- `workflow.py` - Single file with telemetry setup + MCP workflow
- `requirements.txt` - Dependencies
- `.env` - Credentials (gitignored)

## Learn More

- [Arcade Documentation](https://docs.arcade.dev)
- [Galileo OTLP Integration](https://docs.galileo.ai)
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)

## License

MIT
