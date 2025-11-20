"""
OpenTelemetry + Galileo instrumentation setup.

Configures OTLP export to Galileo and provides utilities for tracing tool execution.
"""

import json
import os
import sys
from typing import Any, Callable, Dict

from dotenv import load_dotenv
from openinference.instrumentation.langchain import LangChainInstrumentor
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Tracer

load_dotenv()

GALILEO_API_KEY: str | None = os.getenv("GALILEO_API_KEY")
GALILEO_PROJECT_NAME: str | None = os.getenv("GALILEO_PROJECT_NAME")
GALILEO_LOG_STREAM: str = os.getenv("GALILEO_LOG_STREAM", "default")
GALILEO_OTLP_ENDPOINT: str = os.getenv(
    "GALILEO_OTLP_ENDPOINT",
    "https://api.galileo.ai/otel/traces"
)

if not GALILEO_API_KEY or not GALILEO_PROJECT_NAME:
    print("Error: GALILEO_API_KEY and GALILEO_PROJECT_NAME required", file=sys.stderr)
    sys.exit(1)

os.environ["OTEL_EXPORTER_OTLP_TRACES_HEADERS"] = (
    f"Galileo-API-Key={GALILEO_API_KEY},"
    f"project={GALILEO_PROJECT_NAME},"
    f"logstream={GALILEO_LOG_STREAM}"
)

resource = Resource.create({
    "service.name": "arcade-galileo-demo",
    "service.version": "1.0.0",
})

tracer_provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter(endpoint=GALILEO_OTLP_ENDPOINT)
span_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(span_processor)

trace.set_tracer_provider(tracer_provider)
LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

tracer: Tracer = trace.get_tracer(__name__)


def _serialize_for_span(data: Any) -> str:
    """Serialize data for span attributes, handling various types."""
    if isinstance(data, (dict, list, str, int, float, bool, type(None))):
        return json.dumps(data, indent=2, default=str)
    try:
        return json.dumps(data.__dict__, indent=2, default=str)
    except (TypeError, AttributeError):
        return str(data)


def execute_tool_with_tracing(
    tool_name: str,
    tool_executor: Callable[[], Any],
    inputs: Dict[str, Any]
) -> Any:
    """
    Execute a tool with OpenTelemetry tracing and OpenInference attributes.
    
    Creates a span with proper attributes for Galileo visualization.
    """
    with tracer.start_as_current_span(f"tool.{tool_name}") as span:
        span.set_attribute("openinference.span.kind", "tool")
        span.set_attribute("tool.name", tool_name)
        span.set_attribute("input.value", _serialize_for_span(inputs))
        span.set_attribute("tool.parameters", _serialize_for_span(inputs))

        try:
            result = tool_executor()
            span.set_attribute("output.value", _serialize_for_span(result))
            span.set_attribute("tool.status", "success")
            return result
        except Exception as e:
            span.set_attribute("tool.status", "error")
            span.set_attribute("tool.error", str(e))
            span.set_attribute("tool.error.type", type(e).__name__)
            raise
