// collector-check.js - Tool to verify OpenTelemetry Collector connectivity

const http = require('http');
const https = require('https');
const { URL } = require('url');

async function checkCollectorHealth() {
  console.log('===== OpenTelemetry Collector Health Check =====');
  
  // Get the collector configuration
  const baseEndpoint = process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://otel-collector:4318';
  console.log(`Base OTLP endpoint: ${baseEndpoint}`);
  
  const url = new URL(baseEndpoint);
  const protocol = url.protocol === 'https:' ? https : http;
  const hostname = url.hostname;
  
  // List of endpoints to check
  const endpointsToCheck = [
    { port: 13133, path: '/', description: 'Health Check API' },
    { port: url.port || (url.protocol === 'https:' ? 443 : 80), path: '/v1/traces', description: 'Traces Endpoint' },
    { port: url.port || (url.protocol === 'https:' ? 443 : 80), path: '/v1/metrics', description: 'Metrics Endpoint' },
    { port: url.port || (url.protocol === 'https:' ? 443 : 80), path: '/v1/logs', description: 'Logs Endpoint' },
    { port: 8889, path: '/metrics', description: 'Prometheus Metrics Endpoint' },
    { port: 55679, path: '/debug/servicez', description: 'zPages Endpoint' },
  ];
  
  // Check each endpoint
  for (const endpoint of endpointsToCheck) {
    try {
      const result = await checkEndpoint(protocol, hostname, endpoint.port, endpoint.path);
      console.log(`${endpoint.description} (${hostname}:${endpoint.port}${endpoint.path}): ${result.status} ${result.message}`);
    } catch (error) {
      console.error(`${endpoint.description} (${hostname}:${endpoint.port}${endpoint.path}): ERROR - ${error.message}`);
    }
  }
  
  console.log('\n===== Connectivity Summary =====');
  console.log('If the Health Check API is accessible, the collector is running correctly.');
  console.log('If the other endpoints are accessible, the collector is properly configured to receive telemetry.');
  console.log('\nNext Steps:');
  console.log('1. Check if the collector is exporting data correctly to your backend (LogzIO)');
  console.log('2. Run the debug-telemetry.js script to generate test telemetry');
  console.log('3. Check for any errors in the collector logs: docker logs otel-collector');
}

function checkEndpoint(protocol, hostname, port, path) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: hostname,
      port: port,
      path: path,
      method: 'GET',
      timeout: 5000,
      headers: {
        'Accept': 'application/json',
      }
    };
    
    const req = protocol.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve({ status: 'SUCCESS', message: `Status: ${res.statusCode}` });
        } else {
          resolve({ status: 'FAILED', message: `Status: ${res.statusCode}, Response: ${data.substring(0, 100)}` });
        }
      });
    });
    
    req.on('error', (error) => {
      reject(error);
    });
    
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Connection timed out'));
    });
    
    req.end();
  });
}

// Run the health check
checkCollectorHealth().catch(error => {
  console.error('Fatal error:', error);
});