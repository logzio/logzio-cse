// Initialize OpenTelemetry before all other imports
const { setupTracing } = require('./tracing');
setupTracing();

// Import our custom OpenTelemetry logging and metrics
const { setupLogging } = require('./logging');
const { setupMetrics, recordHttpRequest, recordPageView } = require('./metrics');

const express = require('express');
const path = require('path');
const morgan = require('morgan');
const { trace } = require('@opentelemetry/api');

// Import routes
const indexRoutes = require('./routes/index');
const apiRoutes = require('./routes/api');

// Setup logging and metrics
const logger = setupLogging();
const metricsInitialized = setupMetrics();

// Create Express app
const app = express();
const port = process.env.PORT || 3000;

// Set view engine and views path
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Configure middleware
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(morgan('dev'));
app.use(express.static(path.join(__dirname, '../public')));

// Add request tracing middleware
app.use((req, res, next) => {
  const tracer = trace.getTracer('db-problems-frontend');
  const span = tracer.startSpan(`${req.method} ${req.path}`);
  
  // Add custom attributes to the span
  span.setAttributes({
    'http.method': req.method,
    'http.url': req.url,
    'http.user_agent': req.headers['user-agent'] || '',
  });
  
  // Record page view
  if (req.method === 'GET' && !req.path.startsWith('/api')) {
    recordPageView(req.path);
  }
  
  // Log the request
  logger.info(`Received ${req.method} request for ${req.path}`, {
    method: req.method,
    path: req.path,
    query: JSON.stringify(req.query),
  });
  
  // Track request start time
  const startTime = Date.now();
  
  // Record the span when the response is completed
  res.on('finish', () => {
    // Calculate request duration
    const duration = Date.now() - startTime;
    
    span.setAttributes({
      'http.status_code': res.statusCode,
      'http.duration_ms': duration,
    });
    span.end();
    
    // Record HTTP metrics
    recordHttpRequest(req.method, req.path, res.statusCode, duration);
    
    // Log the response
    if (res.statusCode >= 400) {
      logger.error(`${req.method} ${req.path} responded with ${res.statusCode}`, {
        method: req.method,
        path: req.path,
        status_code: res.statusCode,
        duration_ms: duration,
      });
    } else {
      logger.info(`${req.method} ${req.path} responded with ${res.statusCode}`, {
        method: req.method,
        path: req.path,
        status_code: res.statusCode,
        duration_ms: duration,
      });
    }
  });
  
  next();
});

// Register routes
app.use('/', indexRoutes);
app.use('/api', apiRoutes);

// Handle 404
app.use((req, res) => {
  logger.warn(`404 Not Found: ${req.method} ${req.path}`, {
    method: req.method,
    path: req.path,
  });
  
  res.status(404).render('index', { 
    title: 'Page Not Found',
    error: 'The requested page could not be found.',
    problems: [],
    users: [],
    results: null
  });
});

// Handle errors
app.use((err, req, res, next) => {
  logger.error(`Error processing ${req.method} ${req.path}: ${err.message}`, {
    method: req.method,
    path: req.path,
    error: err.message,
    stack: err.stack,
  });
  
  res.status(500).render('index', { 
    title: 'Server Error',
    error: 'An internal server error occurred.',
    problems: [],
    users: [],
    results: null
  });
});

// Start the server
app.listen(port, () => {
  logger.info(`Frontend server running on http://localhost:${port}`, {
    port: port,
    environment: process.env.NODE_ENV || 'development',
    otel_endpoint: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://otel-collector:4318',
  });
});