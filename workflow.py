#!/usr/bin/env python3
"""
MCP + Galileo Demo

Reads the last email via Arcade MCP Gateway with automatic OpenTelemetry tracing.
LangChain auto-instrumentation sends traces (including tool calls)to Galileo - zero manual tracing code.

"""

import asyncio
import os
import sys

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from openinference.instrumentation.langchain import LangChainInstrumentor
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

load_dotenv()

# Configuration
GALILEO_API_KEY = os.getenv("GALILEO_API_KEY")
GALILEO_PROJECT_NAME = os.getenv("GALILEO_PROJECT_NAME")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
ARCADE_API_KEY = os.getenv("ARCADE_API_KEY")
ARCADE_USER_ID = os.getenv("ARCADE_USER_ID")

ALLOWED_TOOLS = ["Gmail_ListEmails", "Gmail_ListEmailsByHeader"]


def setup_telemetry() -> TracerProvider:
    """Configure OpenTelemetry to export traces to Galileo."""
    if not GALILEO_API_KEY or not GALILEO_PROJECT_NAME:
        sys.exit("Error: GALILEO_API_KEY and GALILEO_PROJECT_NAME required")

    provider = TracerProvider(
        resource=Resource.create({"service.name": "arcade-mcp-demo", "service.version": "1.0.0"})
    )

    provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint=os.getenv("GALILEO_OTLP_ENDPOINT", "https://api.galileo.ai/otel/traces"),
                headers={
                    "Galileo-API-Key": GALILEO_API_KEY,
                    "project": GALILEO_PROJECT_NAME,
                    "logstream": os.getenv("GALILEO_LOG_STREAM", "default"),
                },
            )
        )
    )

    trace.set_tracer_provider(provider)
    LangChainInstrumentor().instrument(tracer_provider=provider)
    return provider


async def read_last_email() -> str:
    """Connect to Arcade MCP Gateway and read the last email."""
    if not all([MCP_SERVER_URL, ARCADE_API_KEY, ARCADE_USER_ID, os.getenv("OPENAI_API_KEY")]):
        sys.exit("Error: OPENAI_API_KEY, MCP_SERVER_URL, ARCADE_API_KEY, ARCADE_USER_ID required")

    print(f"Connecting to: {MCP_SERVER_URL}\n")

    client = MultiServerMCPClient({
        "arcade": {
            "url": MCP_SERVER_URL,
            "transport": "streamable_http",
            "headers": {
                "Authorization": f"Bearer {ARCADE_API_KEY}",
                "Arcade-User-ID": ARCADE_USER_ID,
            },
        }
    })

    all_tools = await client.get_tools()
    tools = [t for t in all_tools if t.name in ALLOWED_TOOLS]
    print(f"Tools: {[t.name for t in tools]}\n")

    agent = create_react_agent(ChatOpenAI(model="gpt-4o"), tools)
    result = await agent.ainvoke({"messages": [{"role": "user", "content": "Read my last email"}]})

    return result["messages"][-1].content


async def main() -> None:
    """Entry point."""
    tracer_provider = setup_telemetry()

    try:
        response = await read_last_email()
        print(response)
    finally:
        tracer_provider.force_flush()
        print(f"\n📊 Traces: https://app.galileo.ai (project: {GALILEO_PROJECT_NAME})")


if __name__ == "__main__":
    asyncio.run(main())
