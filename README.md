# Arcade + Galileo Integration Recipe

**Example of integrating Arcade tools with Galileo observability using OpenTelemetry.**

This repository demonstrates how to build an agentic workflow that uses [Arcade](https://www.arcade.dev/) tools (Gmail, Google Docs) with complete observability via [Galileo](https://www.galileo.ai/) using standard OpenTelemetry instrumentation.

## What This Demonstrates

- **Agentic Workflow**: LLM-driven multi-step task execution using real-world tools
- **Arcade Integration**: Dynamic tool loading and execution via Arcade's API
- **Galileo Observability**: Complete trace visibility using OpenTelemetry Protocol (OTLP)
- **Patterns**: Code with type hints and error handling

### Example Workflow

The demo implements an email summarization workflow:
1. List today's emails using Gmail
2. Create a summary document in Google Docs
3. Send the summary via email

All operations are traced to Galileo for observability.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.10+** installed
- **Accounts and API Keys**:
  - [OpenAI API key](https://platform.openai.com/) for LLM operations
  - [Arcade account](https://www.arcade.dev/) with API key and user ID
  - [Galileo account](https://www.galileo.ai/) with API key and project name

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository (or copy the files)
cd arcade-galileo-demo

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp env.example .env

# Edit .env with your credentials
# Use your favorite text editor
nano .env
```

Required configuration in `.env`:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-...

# Arcade Configuration  
ARCADE_API_KEY=arcade_...
ARCADE_USER_ID=user_...

# Galileo Configuration
GALILEO_API_KEY=galileo_...
GALILEO_PROJECT_NAME=my-project
GALILEO_LOG_STREAM=default  # Optional, defaults to "default"
```

### 3. Run the Demo

```bash
python workflow.py
```

**Expected output:**

```
============================================================
Arcade + Galileo Integration Demo
============================================================

Loading Arcade tools (this takes ~30 seconds)...
Loaded 3 tools: Gmail_ListEmailsByHeader, GoogleDocs_CreateDocumentFromText, Gmail_SendEmail
Executing workflow...

[Round 1] Executing tool: Gmail_ListEmailsByHeader
[Round 2] Executing tool: GoogleDocs_CreateDocumentFromText
[Round 3] Executing tool: Gmail_SendEmail

============================================================
Workflow completed successfully!
============================================================

Result:
I've completed your email summary workflow. Check your inbox!

📊 View traces at: https://app.galileo.ai
   Project: my-project
```

### 4. View Traces in Galileo

1. Open [https://app.galileo.ai](https://app.galileo.ai)
2. Navigate to your project
3. View the complete trace hierarchy showing:
   - Workflow span
   - LLM calls with prompts and responses
   - Tool executions with inputs and outputs

## Project Structure

```
.
├── workflow.py           # Main demo workflow
├── instrumentation.py    # OpenTelemetry + Galileo setup
├── requirements.txt      # Python dependencies
├── env.example          # Environment template
├── .env                 # Your credentials (gitignored)
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

### Key Files

**`instrumentation.py`**  
Sets up OpenTelemetry with Galileo OTLP exporter. Import this module to configure tracing. Exports a `tracer` object for span creation.

**`workflow.py`**  
Demonstrates the complete integration:
- Loads Arcade tools in OpenAI format
- Creates LangChain agent with tools
- Executes multi-step workflow with full tracing

## Architecture

### How Tracing Works

```
┌─────────────────────────────────────────────────────────┐
│                    Your Application                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │  LangChain Agent                                 │  │
│  │  - LLM calls and responses                       │  │
│  │  - Token usage                                   │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Arcade Tools                                    │  │
│  │  - Tool execution spans                          │  │
│  │  - Input/output captured                         │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
                           │ OTLP over HTTP
                           ▼
┌─────────────────────────────────────────────────────────┐
│              OpenTelemetry Collector                     │
│              (Galileo OTLP Endpoint)                     │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  Galileo Platform                        │
│              (Trace Storage & Visualization)             │
└─────────────────────────────────────────────────────────┘
```

### What Gets Traced

- LLM prompts and completions
- Token counts and model parameters
- Chain executions
- Agent reasoning steps
- Arcade tool invocations
- Tool parameters (inputs)
- Tool results (outputs)
- Success/error status

## Using in Your Project

### Copy the Instrumentation

The `instrumentation.py` file is standalone and reusable:

```python
# In your project
from instrumentation import tracer

def my_function():
    with tracer.start_as_current_span("my-operation") as span:
        span.set_attribute("custom.attribute", "value")
        
        # Your code here
        result = do_something()
        
        span.set_attribute("output.value", str(result))
        return result
```

### Tracing Custom Operations

For any additional metadata or tools:

```python
with tracer.start_as_current_span(f"tool.{tool_name}") as span:
    # Set OpenInference attributes for Galileo UI
    span.set_attribute("openinference.span.kind", "tool")
    span.set_attribute("tool.name", tool_name)
    span.set_attribute("input.value", json.dumps(inputs))
    
    try:
        result = execute_tool(tool_name, inputs)
        span.set_attribute("output.value", json.dumps(result))
        span.set_attribute("tool.status", "success")
    except Exception as e:
        span.set_attribute("tool.status", "error")
        span.set_attribute("tool.error", str(e))
        raise
```

## Troubleshooting

### Issue: "authorization required" (403 error)

**Solution:** First-time users need to authorize Arcade to access tools like Gmail and Google Docs.

When you see this error, the workflow will automatically:
1. Display an authorization URL
2. Wait for you to complete authorization in your browser
3. Continue execution after you press Enter

Simply open the displayed URL, grant the requested permissions, and return to your terminal to continue.

### Issue: "Missing required environment variables"

**Solution:** Ensure all required variables are set in your `.env` file. Run:
```bash
cat .env  # Verify file exists and has correct values
```

### Issue: "No required tools found"

**Solution:** Your Arcade user may not have access to Gmail/Google Docs tools. Either:
- Authorize the tools when prompted (see authorization issue above)
- Modify `REQUIRED_ARCADE_TOOLS` in `workflow.py` to use tools you have access to

### Issue: "Traces not appearing in Galileo"

**Solution:** Verify:
1. Correct `GALILEO_API_KEY` and `GALILEO_PROJECT_NAME`
2. Project exists in Galileo dashboard
3. Network connectivity to `https://api.galileo.ai`

Check for errors in console output during workflow execution.

### Issue: Import errors or module not found

**Solution:** Ensure you're in the virtual environment:
```bash
source venv/bin/activate  # Should show (venv) in prompt
pip install -r requirements.txt
```

## Customization

### Use Different Tools

Modify the `REQUIRED_ARCADE_TOOLS` list in `workflow.py`:

```python
REQUIRED_ARCADE_TOOLS = [
    "Slack_SendMessage",
    "Github_CreateIssue",
    # Add any Arcade tools you need
]
```

Update the `task` in `execute_workflow()` to match your workflow.

### Change LLM Model

Modify constants in `workflow.py`:

```python
DEFAULT_LLM_MODEL = "gpt-4o-mini"  # or gpt-3.5-turbo, etc.
DEFAULT_LLM_TEMPERATURE = 0.3
```


## Why This Pattern?

**Standard OpenTelemetry**: No proprietary SDKs or wrappers. Uses standard OTLP, making it portable and maintainable.

**Separation of Concerns**: `instrumentation.py` handles all tracing setup. Application code stays clean.

**Complete Observability**: Traces LLM operations and tool executions with full input/output visibility.

## Learn More

- **Arcade Documentation**: [https://docs.arcade.dev](https://docs.arcade.dev)
- **Galileo OTLP Integration**: [https://v2docs.galileo.ai/how-to-guides/third-party-integrations/otel](https://v2docs.galileo.ai/how-to-guides/third-party-integrations/otel)
- **OpenTelemetry Python**: [https://opentelemetry.io/docs/languages/python/](https://opentelemetry.io/docs/languages/python/)
- **OpenInference Spec**: [https://github.com/Arize-ai/openinference](https://github.com/Arize-ai/openinference)

## Contributing

This is a reference implementation. Feel free to:
- Report issues or suggest improvements
- Fork and adapt for your use case
- Share your integrations

## License

MIT License - see LICENSE file for details.
