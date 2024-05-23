FROM python:3.9-slim

WORKDIR /app

COPY main.py .

RUN pip install fastapi uvicorn opentelemetry-sdk opentelemetry-api opentelemetry-instrumentation-fastapi opentelemetry-exporter-otlp

CMD ["opentelemetry-instrument", "python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
