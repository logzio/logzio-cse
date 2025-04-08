// Fixed tracing configuration to address protocol mismatch
const opentelemetry = require('@opentelemetry/sdk-node');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-http'); // Use HTTP exporter
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');
const { diag, DiagConsoleLogger, DiagLogLevel } = require('@opentelemetry/api');

// Enable console debugging for OpenTelemetry itself
diag.setLogger(new DiagConsoleLogger(), DiagLogLevel.INFO);

// Configure the OpenTelemetry SDK
function setupTracing() {
  try {
    console.log('Setting up tracing with HTTP protocol...');
    
    // Get the collector endpoint and ensure it's using the HTTP port
    const baseEndpoint = process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://otel-collector:4318';
    // If using gRPC port (4317), switch to HTTP port (4318)
    const httpEndpoint = baseEndpoint.includes(':4317') 
      ? baseEndpoint.replace(':4317', ':4318') 
      : baseEndpoint;
    
    const tracesEndpoint = `${httpEndpoint}/v1/traces`;
    
    console.log(`Configuring trace exporter with HTTP endpoint: ${tracesEndpoint}`);
    
    // Create the exporter using HTTP protocol
    const exporter = new OTLPTraceExporter({
      url: tracesEndpoint,
      headers: {},
      timeoutMillis: 15000
    });

    // Create a resource to identify your service
    const resource = new Resource({
      [SemanticResourceAttributes.SERVICE_NAME]: process.env.OTEL_SERVICE_NAME || 'db-problems-frontend',
      [SemanticResourceAttributes.SERVICE_VERSION]: '1.0.0',
      [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: 'demo'
    });

    // Only enable instrumentations that are definitely available
    const instrumentations = [
      getNodeAutoInstrumentations({
        '@opentelemetry/instrumentation-http': { enabled: true },
        '@opentelemetry/instrumentation-express': { enabled: true },
        // Disable instrumentations that might not be available
        '@opentelemetry/instrumentation-ejs': { enabled: false },
        '@opentelemetry/instrumentation-fs': { enabled: true },
        '@opentelemetry/instrumentation-net': { enabled: true },
        '@opentelemetry/instrumentation-winston': { enabled: false },
        '@opentelemetry/instrumentation-pino': { enabled: false },
        '@opentelemetry/instrumentation-axios': { enabled: false },
        '@opentelemetry/instrumentation-grpc': { enabled: false }
      }),
    ];

    // Configure SDK with minimal options
    const sdk = new opentelemetry.NodeSDK({
      resource: resource,
      traceExporter: exporter,
      instrumentations: instrumentations
    });

    // Initialize the SDK
    console.log('Starting OpenTelemetry SDK...');
    sdk.start();
    console.log('✅ OpenTelemetry tracing initialized successfully with HTTP protocol');

    // Gracefully shut down the SDK when the process is terminated
    process.on('SIGTERM', () => {
      sdk.shutdown()
        .then(() => console.log('OpenTelemetry tracing terminated successfully'))
        .catch(err => console.error('Error terminating OpenTelemetry tracing', err))
        .finally(() => process.exit(0));
    });

    return true;
  } catch (error) {
    console.error('❌ Fatal error setting up OpenTelemetry:', error);
    return false;
  }
}

module.exports = { setupTracing };