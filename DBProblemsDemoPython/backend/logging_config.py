import os
import logging
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

def setup_otel_logging():
    """Configure OpenTelemetry logging with HTTP exporter"""
    # Create a resource that identifies your service
    resource = Resource(attributes={
        SERVICE_NAME: os.environ.get("OTEL_SERVICE_NAME", "db-problems-backend"),
        "service.version": "1.0.0",
        "deployment.environment": "demo"
    })

    # Create a logger provider
    logger_provider = LoggerProvider(resource=resource)
    
    # Set the global logger provider
    set_logger_provider(logger_provider)
    
    # Configure the HTTP OTLP exporter for logs
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_LOGS_ENDPOINT", 
                           os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", 
                                        "http://otel-collector:4318/v1/logs"))
    
    # Make sure the endpoint includes the /v1/logs path
    if not endpoint.endswith('/v1/logs'):
        if endpoint.endswith('/'):
            endpoint += 'v1/logs'
        else:
            endpoint += '/v1/logs'
    
    # Get headers if any are needed (like auth tokens)
    headers = {}
    token = os.environ.get("OTEL_EXPORTER_OTLP_HEADERS", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    # Create the HTTP exporter
    otlp_exporter = OTLPLogExporter(
        endpoint=endpoint,
        headers=headers
    )
    
    # Add the exporter to the logger provider with a batch processor
    # Adjust batch settings for more frequent sending
    batch_processor = BatchLogRecordProcessor(
        otlp_exporter,
        max_export_batch_size=512,
        schedule_delay_millis=5000  # 5 seconds
    )
    logger_provider.add_log_record_processor(batch_processor)
    
    # Return the logger provider
    return logger_provider

def setup_logger(name="app"):
    """Set up a logger with OpenTelemetry integration"""
    # Create or get the logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Remove any existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add a console handler for local viewing
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
    logger.addHandler(console_handler)
    
    # Get the logger provider
    logger_provider = get_logger_provider()
    
    # Add OpenTelemetry handler if provider is available
    if logger_provider:
        otlp_handler = LoggingHandler(logger_provider=logger_provider)
        logger.addHandler(otlp_handler)
    
    return logger

def get_logger_provider():
    """Get the global logger provider"""
    from opentelemetry._logs import get_logger_provider
    return get_logger_provider()

def force_flush_logs():
    """Force flush any pending logs"""
    try:
        logger_provider = get_logger_provider()
        if logger_provider:
            # Try using the public API if available
            if hasattr(logger_provider, "force_flush"):
                logger_provider.force_flush()
                return True
                
            # If not, try accessing the internal processors
            if hasattr(logger_provider, "_log_record_processors"):
                for processor in logger_provider._log_record_processors:
                    if hasattr(processor, "force_flush"):
                        processor.force_flush()
                return True
                
            # Final fallback for other logger provider implementations
            if hasattr(logger_provider, "processor") and hasattr(logger_provider.processor, "force_flush"):
                logger_provider.processor.force_flush()
                return True
                
        return False
    except Exception as e:
        import sys
        sys.stderr.write(f"Error flushing logs: {e}\n")
        return False

# Initialize OpenTelemetry logging
logger_provider = setup_otel_logging()