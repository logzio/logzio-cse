import os
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

# Dictionary to store global meters and instruments
_metrics = {}

def setup_otel_metrics():
    """Configure OpenTelemetry metrics"""
    # Create a resource that identifies your service
    resource = Resource(attributes={
        SERVICE_NAME: os.environ.get("OTEL_SERVICE_NAME", "db-problems-backend"),
        "service.version": "1.0.0",
        "deployment.environment": "demo"
    })

    # Configure the OTLP exporter for metrics
    otlp_exporter = OTLPMetricExporter(
        endpoint=os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
    )
    
    # Create a metric reader that will periodically export metrics
    reader = PeriodicExportingMetricReader(
        exporter=otlp_exporter,
        export_interval_millis=15000  # Export metrics every 15 seconds
    )
    
    # Create a meter provider
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[reader]
    )
    
    # Set the global meter provider
    metrics.set_meter_provider(meter_provider)
    
    # Create a meter for our service
    meter = metrics.get_meter("db-problems-backend")
    
    # Create common database-related metrics
    _metrics["db_connections_total"] = meter.create_counter(
        name="db_connections_total",
        description="Total number of database connections established",
        unit="1"
    )
    
    _metrics["db_connection_errors"] = meter.create_counter(
        name="db_connection_errors",
        description="Total number of database connection errors",
        unit="1"
    )
    
    _metrics["db_queries_total"] = meter.create_counter(
        name="db_queries_total",
        description="Total number of database queries executed",
        unit="1"
    )
    
    _metrics["db_query_duration"] = meter.create_histogram(
        name="db_query_duration",
        description="Duration of database queries",
        unit="ms"
    )
    
    _metrics["problem_simulations"] = meter.create_counter(
        name="problem_simulations",
        description="Count of database problem simulations by type",
        unit="1"
    )
    
    # Return the meter provider
    return meter_provider

def get_metric(name):
    """Get a specific metric instrument"""
    return _metrics.get(name)