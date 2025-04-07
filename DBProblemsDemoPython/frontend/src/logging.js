// Enhanced logging with direct OTLP exporter - no external dependencies
const { trace } = require('@opentelemetry/api');
const os = require('os');
const http = require('http');
const https = require('https');
const { URL } = require('url');

function setupLogging() {
  try {
    console.log('Setting up direct OTLP log exporter...');
    
    // Service information
    const serviceName = process.env.OTEL_SERVICE_NAME || 'db-problems-frontend';
    const serviceVersion = '1.0.0';
    const hostName = os.hostname();
    
    // Extract OTLP endpoint for logs
    const baseEndpoint = process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://otel-collector:4318';
    const logsEndpoint = `${baseEndpoint.includes(':4317') ? baseEndpoint.replace(':4317', ':4318') : baseEndpoint}/v1/logs`;
    
    console.log(`Configuring log exporter with endpoint: ${logsEndpoint}`);
    
    // Parse the endpoint URL for http/https requests
    const parsedUrl = new URL(logsEndpoint);
    const httpModule = parsedUrl.protocol === 'https:' ? https : http;
    
    // Create a logger that exports directly to OTLP
    const logger = {
      info: (message, attributes = {}) => {
        logWithLevel('INFO', message, attributes);
      },
      
      warn: (message, attributes = {}) => {
        logWithLevel('WARN', message, attributes);
      },
      
      error: (message, attributes = {}) => {
        logWithLevel('ERROR', message, attributes);
      },
      
      debug: (message, attributes = {}) => {
        logWithLevel('DEBUG', message, attributes);
      }
    };
    
    // Helper function to log with trace context and export to OTLP
    function logWithLevel(level, message, attributes = {}) {
      // Create a structured log record
      const timestamp = new Date();
      const timeUnixNano = timestamp.getTime() * 1000000; // Convert to nanoseconds
      
      // Get severity number from level
      const severityNumber = getSeverityNumber(level);
      
      // Build attribute array for OTLP format
      const otlpAttributes = [
        { key: 'service.name', value: { stringValue: serviceName } },
        { key: 'service.version', value: { stringValue: serviceVersion } },
        { key: 'host.name', value: { stringValue: hostName } },
      ];
      
      // Add custom attributes
      for (const [key, value] of Object.entries(attributes)) {
        if (key !== 'message' && key !== 'level') {
          otlpAttributes.push({
            key,
            value: { stringValue: typeof value === 'object' ? JSON.stringify(value) : String(value) }
          });
        }
      }
      
      // Try to get current trace context
      let traceId, spanId;
      try {
        const currentSpan = trace.getActiveSpan();
        if (currentSpan) {
          const spanContext = currentSpan.spanContext();
          if (spanContext) {
            traceId = spanContext.traceId;
            spanId = spanContext.spanId;
          }
        }
      } catch (e) {
        // Ignore errors getting trace context
      }
      
      // Create OTLP log record
      const logRecord = {
        timeUnixNano,
        severityNumber,
        severityText: level,
        body: { stringValue: message },
        attributes: otlpAttributes,
        traceId,
        spanId
      };
      
      // Create OTLP log payload
      const otlpPayload = {
        resourceLogs: [{
          resource: {
            attributes: [
              { key: 'service.name', value: { stringValue: serviceName } },
              { key: 'service.version', value: { stringValue: serviceVersion } },
              { key: 'host.name', value: { stringValue: hostName } }
            ]
          },
          scopeLogs: [{
            scope: {},
            logRecords: [logRecord]
          }]
        }]
      };
      
      // Send to OTLP endpoint
      sendToOTLP(otlpPayload, httpModule, parsedUrl);
      
      // Also log to console for debugging
      const consoleLogObj = {
        timestamp: timestamp.toISOString(),
        level,
        message,
        service: serviceName,
        host: hostName,
        trace_id: traceId,
        span_id: spanId,
        ...attributes
      };
      
      // Log to console based on level
      switch (level) {
        case 'DEBUG':
          console.debug(JSON.stringify(consoleLogObj));
          break;
        case 'INFO':
          console.info(JSON.stringify(consoleLogObj));
          break;
        case 'WARN':
          console.warn(JSON.stringify(consoleLogObj));
          break;
        case 'ERROR':
          console.error(JSON.stringify(consoleLogObj));
          break;
        default:
          console.log(JSON.stringify(consoleLogObj));
      }
    }
    
    // Helper function to get OpenTelemetry severity number
    function getSeverityNumber(level) {
      const severities = {
        TRACE: 1,
        DEBUG: 5,
        INFO: 9,
        WARN: 13,
        ERROR: 17,
        FATAL: 21
      };
      
      return severities[level] || 9;
    }
    
    // Function to send logs to OTLP endpoint
    function sendToOTLP(payload, httpModule, parsedUrl) {
      // Prepare request options
      const options = {
        method: 'POST',
        hostname: parsedUrl.hostname,
        port: parsedUrl.port || (parsedUrl.protocol === 'https:' ? 443 : 80),
        path: parsedUrl.pathname + parsedUrl.search,
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 2000 // 2 second timeout
      };
      
      try {
        // Create HTTP request
        const req = httpModule.request(options, (res) => {
          if (res.statusCode >= 400) {
            let data = '';
            res.on('data', (chunk) => { data += chunk; });
            res.on('end', () => {
              console.error(`Error sending log to OTLP: status=${res.statusCode}, response=${data}`);
            });
          }
        });
        
        // Handle errors
        req.on('error', (error) => {
          console.error(`Error sending log to OTLP: ${error.message}`);
        });
        
        req.on('timeout', () => {
          req.destroy();
          console.error('Timeout sending log to OTLP');
        });
        
        // Send the payload
        req.write(JSON.stringify(payload));
        req.end();
      } catch (error) {
        console.error(`Exception sending log to OTLP: ${error.message}`);
      }
    }
    
    console.log('✅ Direct OTLP log exporter initialized successfully');
    return logger;
  } catch (error) {
    console.error('❌ Error setting up logging:', error);
    
    // Fallback to simple logger
    return {
      info: (message, attributes = {}) => console.info(`INFO: ${message}`, attributes),
      warn: (message, attributes = {}) => console.warn(`WARN: ${message}`, attributes),
      error: (message, attributes = {}) => console.error(`ERROR: ${message}`, attributes),
      debug: (message, attributes = {}) => console.debug(`DEBUG: ${message}`, attributes)
    };
  }
}

module.exports = { setupLogging };