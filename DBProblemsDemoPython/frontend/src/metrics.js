// Fixed metrics configuration to address protocol mismatch
const { metrics } = require('@opentelemetry/api');
const { MeterProvider, PeriodicExportingMetricReader } = require('@opentelemetry/sdk-metrics');
const { Resource } = require('@opentelemetry/resources');
const { OTLPMetricExporter } = require('@opentelemetry/exporter-metrics-otlp-http'); // Use HTTP exporter
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');

// Store meters and instruments
let _meter;
let _instruments = {};

function setupMetrics() {
  try {
    console.log('Setting up metrics with HTTP protocol...');
    
    // Get the collector endpoint and ensure it's using the HTTP port
    const baseEndpoint = process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://otel-collector:4318';
    // If using gRPC port (4317), switch to HTTP port (4318)
    const httpEndpoint = baseEndpoint.includes(':4317') 
      ? baseEndpoint.replace(':4317', ':4318') 
      : baseEndpoint;
    
    const metricsEndpoint = `${httpEndpoint}/v1/metrics`;
    
    console.log(`Configuring metrics exporter with HTTP endpoint: ${metricsEndpoint}`);
    
    // Create a resource that identifies your service
    const resource = new Resource({
      [SemanticResourceAttributes.SERVICE_NAME]: process.env.OTEL_SERVICE_NAME || 'db-problems-frontend',
      [SemanticResourceAttributes.SERVICE_VERSION]: '1.0.0',
      [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: 'demo'
    });

    // Create an OTLP exporter using HTTP protocol
    const exporter = new OTLPMetricExporter({
      url: metricsEndpoint,
      headers: {},
      timeoutMillis: 15000
    });

    // Create a metric reader with configurable interval
    const metricReader = new PeriodicExportingMetricReader({
      exporter,
      exportIntervalMillis: 15000, // Export metrics every 15 seconds
      exportTimeoutMillis: 10000   // Timeout after 10 seconds
    });

    // Create a meter provider
    const meterProvider = new MeterProvider({
      resource: resource,
      readers: [metricReader]
    });

    // Set the meter provider as global
    metrics.setGlobalMeterProvider(meterProvider);

    // Create a meter for our service
    _meter = metrics.getMeter('db-problems-frontend');

    // Create common metrics for frontend
    _instruments.httpRequests = _meter.createCounter('http_requests_total', {
      description: 'Total number of HTTP requests made',
      unit: '1'
    });

    _instruments.httpRequestDuration = _meter.createHistogram('http_request_duration', {
      description: 'HTTP request duration',
      unit: 'ms'
    });

    _instruments.httpErrors = _meter.createCounter('http_errors_total', {
      description: 'Total number of HTTP errors',
      unit: '1'
    });

    _instruments.problemTriggered = _meter.createCounter('problem_triggered_total', {
      description: 'Number of times each database problem has been triggered',
      unit: '1'
    });

    _instruments.pageViews = _meter.createCounter('page_views_total', {
      description: 'Number of page views',
      unit: '1'
    });

    // Test the metrics by recording one immediately
    _instruments.pageViews.add(1, {
      route: '/metrics-test',
      test: 'true'
    });

    console.log('✅ OpenTelemetry metrics initialized successfully with HTTP protocol');
    return true;
  } catch (error) {
    console.error('❌ Error setting up OpenTelemetry metrics:', error);
    return false;
  }
}

function getMetric(name) {
  return _instruments[name];
}

function recordHttpRequest(method, route, statusCode, durationMs) {
  try {
    if (_instruments.httpRequests) {
      _instruments.httpRequests.add(1, {
        method,
        route,
        status_code: statusCode
      });
    }

    if (_instruments.httpRequestDuration) {
      _instruments.httpRequestDuration.record(durationMs, {
        method,
        route,
        status_code: statusCode
      });
    }

    if (statusCode >= 400 && _instruments.httpErrors) {
      _instruments.httpErrors.add(1, {
        method,
        route,
        status_code: statusCode
      });
    }
  } catch (error) {
    console.error('Error recording HTTP metrics:', error);
  }
}

function recordProblemTriggered(problemId) {
  try {
    if (_instruments.problemTriggered) {
      _instruments.problemTriggered.add(1, {
        problem_id: problemId
      });
    }
  } catch (error) {
    console.error('Error recording problem trigger metrics:', error);
  }
}

function recordPageView(route) {
  try {
    if (_instruments.pageViews) {
      _instruments.pageViews.add(1, {
        route
      });
    }
  } catch (error) {
    console.error('Error recording page view metrics:', error);
  }
}

module.exports = {
  setupMetrics,
  getMetric,
  recordHttpRequest,
  recordProblemTriggered,
  recordPageView
};