import logging
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from datetime import datetime, timezone
import json

class CustomJSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "log": f"{record.levelname}: {record.getMessage()}",
            "stream": "stdout" if record.levelno < logging.ERROR else "stderr",
            "time": datetime.fromtimestamp(record.created, timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        }
        return json.dumps(log_entry)

app = FastAPI()

log_path = "/kapow/data/Logs/fastapi_app.log"
file_handler = logging.FileHandler(log_path)
file_handler.setFormatter(CustomJSONFormatter())
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(CustomJSONFormatter())

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, stream_handler]
)
logger = logging.getLogger(__name__)

resource = Resource(attributes={"service.name": "fastapi-app"})
trace.set_tracer_provider(TracerProvider(resource=resource))
otlp_exporter = OTLPSpanExporter(insecure=True)
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))

FastAPIInstrumentor.instrument_app(app)

@app.get("/")
def read_root():
    logger.info("Root endpoint called")
    return {"Hello": "World"}
