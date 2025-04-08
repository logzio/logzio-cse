const express = require('express');
const axios = require('axios');
const { trace } = require('@opentelemetry/api');
const router = express.Router();

// Backend API URL from environment variable
const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:5001';

// Get tracer for this file
const tracer = trace.getTracer('routes.index');

// Home page
router.get('/', async (req, res) => {
  const span = tracer.startSpan('get_index_page');
  
  try {
    // Fetch database problems from backend
    const response = await axios.get(`${BACKEND_URL}/api/problems`);
    const problems = response.data.problems || [];
    
    // Fetch users as a sample of database data
    let users = [];
    try {
      const usersResponse = await axios.get(`${BACKEND_URL}/api/users`);
      users = usersResponse.data.users || [];
    } catch (userError) {
      console.warn('Error fetching users (continuing anyway):', userError.message);
    }
    
    res.render('index', {
      title: 'Database Problems Demo',
      problems: problems.map(id => ({
        id,
        name: formatProblemName(id),
        description: getDescription(id)
      })),
      users,
      error: null,
      results: null
    });
  } catch (error) {
    console.error('Error fetching data from backend:', error.message);
    span.recordException(error);
    
    res.render('index', {
      title: 'Database Problems Demo',
      problems: [],
      users: [],
      error: `Error connecting to backend: ${error.message}`,
      results: null
    });
  } finally {
    span.end();
  }
});

// Trigger a specific database problem
router.post('/problem/:id', async (req, res) => {
  const { id } = req.params;
  const span = tracer.startSpan('trigger_db_problem', {
    attributes: { 'problem.id': id }
  });
  
  try {
    const response = await axios.post(`${BACKEND_URL}/api/problem/${id}`);
    
    res.render('index', {
      title: 'Database Problems Demo',
      problems: [], // We'll fetch these again on the next page load
      users: [],
      error: null,
      results: {
        problem: id,
        name: formatProblemName(id),
        data: response.data
      }
    });
  } catch (error) {
    console.error(`Error triggering problem ${id}:`, error.message);
    span.recordException(error);
    
    let errorMessage = `Error triggering database problem: ${error.message}`;
    if (error.response) {
      errorMessage = `Error from backend: ${JSON.stringify(error.response.data)}`;
    }
    
    res.render('index', {
      title: 'Database Problems Demo',
      problems: [], // We'll fetch these again on the next page load
      users: [],
      error: errorMessage,
      results: null
    });
  } finally {
    span.end();
  }
});

// Helper functions
function formatProblemName(id) {
  return id
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function getDescription(id) {
  const descriptions = {
    'connection_timeout': 'Simulates a database connection timeout',
    'slow_query': 'Executes a very inefficient query that takes a long time to complete',
    'connection_pool_exhaustion': 'Opens many connections without closing them, exhausting the connection pool',
    'deadlock': 'Creates two transactions that deadlock with each other',
    'table_lock': 'Locks a table for a long time, blocking other operations',
    'memory_leak': 'Simulates a memory leak by fetching large result sets',
    'connection_drop': 'Abruptly closes a connection during a transaction',
    'query_error': 'Executes a query with syntax or semantic errors'
  };
  
  return descriptions[id] || 'No description available';
}

module.exports = router;