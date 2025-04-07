const express = require('express');
const axios = require('axios');
const { trace } = require('@opentelemetry/api');
const router = express.Router();

// Backend API URL from environment variable
const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:5001';

// Get tracer for this file
const tracer = trace.getTracer('routes.api');

// Health check endpoint
router.get('/health', (req, res) => {
  return res.json({ status: 'healthy' });
});

// Proxy API calls to backend
router.get('/problems', async (req, res) => {
  const span = tracer.startSpan('get_problems_api');
  
  try {
    const response = await axios.get(`${BACKEND_URL}/api/problems`);
    res.json(response.data);
  } catch (error) {
    console.error('Error fetching problems from backend:', error.message);
    span.recordException(error);
    
    res.status(500).json({
      error: `Failed to fetch problems from backend: ${error.message}`
    });
  } finally {
    span.end();
  }
});

router.post('/problem/:id', async (req, res) => {
  const { id } = req.params;
  const span = tracer.startSpan('trigger_problem_api', {
    attributes: { 'problem.id': id }
  });
  
  try {
    const response = await axios.post(`${BACKEND_URL}/api/problem/${id}`);
    res.json(response.data);
  } catch (error) {
    console.error(`Error triggering problem ${id} from backend:`, error.message);
    span.recordException(error);
    
    let statusCode = 500;
    let errorResponse = {
      error: `Failed to trigger problem from backend: ${error.message}`
    };
    
    if (error.response) {
      statusCode = error.response.status;
      errorResponse = error.response.data;
    }
    
    res.status(statusCode).json(errorResponse);
  } finally {
    span.end();
  }
});

router.get('/users', async (req, res) => {
  const span = tracer.startSpan('get_users_api');
  
  try {
    const response = await axios.get(`${BACKEND_URL}/api/users`);
    res.json(response.data);
  } catch (error) {
    console.error('Error fetching users from backend:', error.message);
    span.recordException(error);
    
    res.status(500).json({
      error: `Failed to fetch users from backend: ${error.message}`
    });
  } finally {
    span.end();
  }
});

module.exports = router;