"""
OpenTelemetry tracing configuration for CrewAI integration.
Provides distributed tracing across agent interactions.
"""

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from config import get_settings


class TracingConfig:
    """
    Configures OpenTelemetry tracing for observability.
    Integrates with Langfuse for comprehensive monitoring.
    """

    def __init__(self):
        """Initialize tracing configuration."""
        self.settings = get_settings()
        self.tracer = None
        self._setup_tracing()

    def _setup_tracing(self) -> None:
        """Set up OpenTelemetry tracing provider."""
        resource = Resource.create({
            "service.name": "restaurant-recommendation-agents",
            "service.version": self.settings.langfuse_release,
            "deployment.environment": self.settings.app_env
        })
        
        provider = TracerProvider(resource=resource)
        
        if hasattr(self.settings, 'otlp_endpoint'):
            otlp_exporter = OTLPSpanExporter(
                endpoint=self.settings.otlp_endpoint,
                headers={"api-key": self.settings.otlp_api_key} if hasattr(self.settings, 'otlp_api_key') else {}
            )
            
            provider.add_span_processor(
                BatchSpanProcessor(otlp_exporter)
            )
        
        trace.set_tracer_provider(provider)
        
        self.tracer = trace.get_tracer(__name__)

    def get_tracer(self) -> trace.Tracer:
        """
        Get the configured tracer instance.
        
        Returns:
            OpenTelemetry tracer
        """
        return self.tracer