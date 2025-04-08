import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import time
import random
import traceback
import logging

# Setup OpenTelemetry
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.mysql import MySQLInstrumentor

# Import our custom OpenTelemetry configurations
from logging_config import setup_otel_logging, setup_logger, force_flush_logs
from metrics_config import setup_otel_metrics, get_metric

# Import our database modules
from database import get_db_connection, initialize_db
from db_problems import DB_PROBLEMS, simulate_db_problem

# Create a common resource for all telemetry signals
resource = Resource(attributes={
    SERVICE_NAME: os.environ.get("OTEL_SERVICE_NAME", "db-problems-backend"),
    "service.version": "1.0.0",
    "deployment.environment": "demo"
})

# Configure Tracing with the resource
trace_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(trace_provider)

# Configure the OTLP exporter for traces
otlp_trace_exporter = OTLPSpanExporter(
    endpoint=os.environ.get("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
                          os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317"))
)
trace_processor = BatchSpanProcessor(
    otlp_trace_exporter,
    max_export_batch_size=512,
    schedule_delay_millis=5000  # 5 seconds
)
trace_provider.add_span_processor(trace_processor)

# Setup Logging - initialized in logging_config.py
logger = setup_logger(__name__)

# Setup Metrics
meter_provider = setup_otel_metrics()

# Create Flask app
app = Flask(__name__)
CORS(app)

# Instrument Flask with OpenTelemetry
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()
MySQLInstrumentor().instrument()

# Get a tracer for our service
tracer = trace.get_tracer(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    logger.info("Health check endpoint called")
    force_flush_logs()  # Force flush logs to the collector
    return jsonify({"status": "healthy"})

@app.route('/api/problems', methods=['GET'])
def get_problems():
    with tracer.start_as_current_span("get_all_db_problems") as span:
        logger.info("Fetching list of database problems")
        problems = list(DB_PROBLEMS.keys())
        span.set_attribute("problem_count", len(problems))
        force_flush_logs()  # Force flush logs
        return jsonify({"problems": problems})

@app.route('/api/problem/<problem_id>', methods=['POST'])
def trigger_problem(problem_id):
    with tracer.start_as_current_span("trigger_db_problem") as span:
        span.set_attribute("problem.id", problem_id)
        
        if problem_id not in DB_PROBLEMS:
            logger.error(f"Invalid problem ID requested: {problem_id}")
            span.set_attribute("problem.error", "invalid_problem_id")
            force_flush_logs()  # Force flush logs
            return jsonify({"error": "Invalid problem ID"}), 400
        
        logger.info(f"Triggering database problem: {problem_id}")
        # Increment the problem simulation counter
        problem_counter = get_metric("problem_simulations")
        if problem_counter:
            problem_counter.add(1, {"problem_type": problem_id})
        
        try:
            result = simulate_db_problem(problem_id)
            logger.info(f"Problem simulation completed: {problem_id}")
            force_flush_logs()  # Force flush logs
            return jsonify(result)
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Error simulating problem {problem_id}: {error_trace}")
            span.set_attribute("problem.error", str(e))
            span.record_exception(e)
            force_flush_logs()  # Force flush logs
            return jsonify({"error": str(e), "trace": error_trace}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    with tracer.start_as_current_span("get_all_users") as span:
        logger.info("Fetching all users from database")
        query_counter = get_metric("db_queries_total")
        if query_counter:
            query_counter.add(1, {"query_type": "SELECT", "table": "users"})
        
        start_time = time.time()
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Record query duration
            duration_ms = (time.time() - start_time) * 1000
            query_duration = get_metric("db_query_duration")
            if query_duration:
                query_duration.record(duration_ms, {"query_type": "SELECT", "table": "users"})
            
            logger.info(f"Retrieved {len(users)} users from database")
            span.set_attribute("user_count", len(users))
            force_flush_logs()  # Force flush logs
            return jsonify({"users": users})
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Error fetching users: {error_trace}")
            
            # Record connection error
            conn_errors = get_metric("db_connection_errors")
            if conn_errors:
                conn_errors.add(1, {"operation": "query", "table": "users"})
            
            span.record_exception(e)
            force_flush_logs()  # Force flush logs
            return jsonify({"error": str(e), "trace": error_trace}), 500
@app.route('/api/users/search', methods=['GET'])
def search_users():
    with tracer.start_as_current_span("search_users") as span:
        # Get parameters from request
        filters = {}
        if request.args.get('username'):
            filters['username'] = request.args.get('username')
        if request.args.get('email'):
            filters['email'] = request.args.get('email')
            
        limit = request.args.get('limit')
        if limit:
            limit = int(limit)
            
        # Use the efficient query function
        logger.info(f"Searching users with filters: {filters}, limit: {limit}")
        start_time = time.time()
        users = efficient_bulk_query('users', filters, limit)
        duration_ms = (time.time() - start_time) * 1000
        
        # Record metrics and log
        span.set_attribute("user_count", len(users))
        span.set_attribute("query_duration_ms", duration_ms)
        logger.info(f"Found {len(users)} users in {duration_ms:.2f}ms")
        
        return jsonify({"users": users})

if __name__ == '__main__':
    # Initialize the database with test data
    initialize_db()
    
    # Record app startup in logs
    logger.info("Application starting up with OpenTelemetry instrumentation")
    force_flush_logs()  # Force flush logs
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5001, debug=True)