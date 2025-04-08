// test-logging.js - Verify that logs are being sent to the collector

// First initialize tracing so we can correlate logs with traces
const { setupTracing } = require('./tracing');
setupTracing();

// Import our logging implementation
const { setupLogging } = require('./logging');
const { trace } = require('@opentelemetry/api');

async function main() {
  console.log('Starting logging test...');
  
  // Initialize our logger
  const logger = setupLogging();
  
  // Get a tracer to create spans
  const tracer = trace.getTracer('logging-test');
  
  // Create a parent span
  const parentSpan = tracer.startSpan('test-parent-operation');
  
  // Set context for the logs to be properly correlated
  await trace.with(trace.setSpan(trace.context.active(), parentSpan), async () => {
    logger.info('This is a test info log', { test_attribute: 'test_value' });
    logger.warn('This is a test warning log', { another_attribute: 123 });
    
    // Create a child span
    const childSpan = tracer.startSpan('test-child-operation');
    
    // Set context for the child span
    await trace.with(trace.setSpan(trace.context.active(), childSpan), async () => {
      logger.error('This is a test error log inside child span', { error_code: 500 });
      
      // Wait a bit
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // End the child span
      childSpan.end();
    });
    
    // Log after child span is completed
    logger.info('Child operation completed');
    
    // Wait a bit more
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // End the parent span
    parentSpan.end();
  });
  
  // Log something outside of any span
  logger.debug('Test completed, no active span');
  
  // Wait to ensure logs and traces are exported
  console.log('Waiting 2 seconds for logs and traces to be exported...');
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  console.log('Test completed!');
}

// Run the test
main().catch(error => {
  console.error('Error in test:', error);
});