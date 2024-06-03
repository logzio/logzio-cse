
# Django App with OpenTelemetry

This project demonstrates setting up a Django application with OpenTelemetry instrumentation, deploying it to an EKS cluster, and exporting traces to Logz.io.

## Project Overview

- **Django Application**: A simple [Django](https://www.djangoproject.com/start/) web application. 
- **OpenTelemetry**: [Instrumented](https://opentelemetry-python.readthedocs.io/en/latest/examples/django/README.html) to collect traces. 
- **Export Traces to Logz.io**: Traces are sent to an OpenTelemetry Collector and then exported to [Logz.io](https://docs.logz.io/docs/shipping/other/opentelemetry-data/).
- **Deployment**: The application is containerized using Docker and deployed to Kubernetes (EKS).

## Quick Start

### 1. Clone the Repository

```bash
git clone git@github.com:logzio/logzio-cse.git
cd django_logzio_otel_trace
```

### 2. Build and Run Docker Locally

Build the Docker image:

```bash
docker build -t my-django-app .
```

Run the Docker container:

```bash
docker run -p 8000:8000 my-django-app
```

### 3. Deploy to Kubernetes

Apply the Kubernetes deployment and service files:

```bash
kubectl apply -f django_deployment.yaml

```
#### Note: 
Make sure to update the OTEL_EXPORTER_OTLP_TRACES_ENDPOINT environment variable in your deployment configuration to match your OpenTelemetry Collector service and namespace. For example:

```bash
- name: OTEL_EXPORTER_OTLP_TRACES_ENDPOINT
  value: "http://<otel-collector-service-name>.<Namespace>.svc.cluster.local:4317"
```

### 4. Set Up OpenTelemetry Collector

# Logzio Kubernetes Helm Charts
```bash
helm install -n monitoring \
--set logs.enabled=true \
--set logzio-logs-collector.secrets.logzioLogsToken="<<LOG-SHIPPING-TOKEN>>" \
--set logzio-logs-collector.secrets.logzioRegion="<<LOGZIO-REGION>>" \
--set logzio-logs-collector.secrets.env_id="<<ENV-ID>>" \
--set metricsOrTraces.enabled=true \
--set logzio-k8s-telemetry.metrics.enabled=true \
--set logzio-k8s-telemetry.secrets.MetricsToken="<<PROMETHEUS-METRICS-SHIPPING-TOKEN>>" \
--set logzio-k8s-telemetry.secrets.ListenerHost="https://<<LISTENER-HOST>>:8053" \
--set logzio-k8s-telemetry.secrets.p8s_logzio_name="<<ENV-TAG>>" \
--set logzio-k8s-telemetry.traces.enabled=true \
--set logzio-k8s-telemetry.secrets.TracesToken="<<TRACES-SHIPPING-TOKEN>>" \
--set logzio-k8s-telemetry.secrets.LogzioRegion="<<LOGZIO-REGION>>" \
--set logzio-k8s-telemetry.spm.enabled=true \
--set logzio-k8s-telemetry.secrets.env_id="<<ENV-ID>>" \
--set logzio-k8s-telemetry.secrets.SpmToken=<<SPM-SHIPPING-TOKEN>> \
--set logzio-k8s-telemetry.serviceGraph.enabled=true \
--set logzio-k8s-telemetry.k8sObjectsConfig.enabled=true \
--set logzio-k8s-telemetry.secrets.k8sObjectsLogsToken="<<LOG-SHIPPING-TOKEN>>" \
--set securityReport.enabled=true \
--set logzio-trivy.env_id="<<ENV-ID>>" \
--set logzio-trivy.secrets.logzioShippingToken="<<LOG-SHIPPING-TOKEN>>" \
--set logzio-trivy.secrets.logzioListener="<<LISTENER-HOST>>" \
--set deployEvents.enabled=true \
--set logzio-k8s-events.secrets.env_id="<<ENV-ID>>" \
--set logzio-k8s-events.secrets.logzioShippingToken="<<LOG-SHIPPING-TOKEN>>" \
--set logzio-k8s-events.secrets.logzioListener="<<LISTENER-HOST>>" \
logzio-monitoring logzio-helm/logzio-monitoring
```

## Local Development

For local development with auto-reloading:

```bash
docker run -p 8000:8000 -v $(pwd):/usr/src/app --user $(id -u):$(id -g) my-django-app
```

Access the application at `http://localhost:8000`.
