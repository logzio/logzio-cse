# DBProblemsDemoPython

A comprehensive database problem analysis tool that identifies and troubleshoots database performance issues in real-time.

## Overview

This project combines backend monitoring capabilities with a frontend visualization dashboard to help database administrators and developers quickly identify bottlenecks, slow queries, and other performance issues. The system is containerized with Docker for easy deployment.

## Features

- Real-time database performance monitoring
- Automatic identification of slow queries
- Load testing with customizable parameters
- Metric collection and visualization
- OTEL collector integration for distributed tracing
- Comprehensive reporting

## Project Structure

```
DBProblemsDemoPython/
├── backend/              # Python backend service
│   ├── app.py            # Main application entry point
│   ├── database.py       # Database connection and queries
│   ├── db_problems.py    # Problem detection algorithms
│   ├── logging_config.py # Logging configuration
│   ├── metrics_config.py # Metrics collection setup
│   ├── requirements.txt  # Python dependencies
│   └── Dockerfile        # Backend container definition
├── frontend/             # JavaScript/React frontend
│   ├── public/           # Static assets
│   ├── src/              # React components and logic
│   └── Dockerfile        # Frontend container definition
├── load-generator/       # Load testing tools
│   ├── load_generator.py # Load simulation script
│   └── Dockerfile        # Load generator container
├── mysql-init/           # Database initialization
│   └── init.sql          # Initial schema and data
├── docker-compose.yaml   # Multi-container orchestration
└── otel-collector-config.yaml # OpenTelemetry configuration
```

## Prerequisites

- Docker and Docker Compose
- Git (for cloning the repository)
- Internet connection (for pulling Docker images)

## Getting Started

### Clone the Repository

```bash
git clone https://github.com/logzio/DBProblemsDemoPython.git
cd DBProblemsDemoPython
```

### Start the Application

```bash
docker-compose up -d
```

This command will:
1. Build all necessary Docker images
2. Start the MySQL database with initialization data
3. Launch the backend service
4. Start the frontend web interface
5. Initialize the OpenTelemetry collector
6. Run a sample load generator

### Access the Application

- Frontend Dashboard: http://localhost:3000
- Backend API: http://localhost:5000

### Run Load Tests

To simulate database load:

```bash
docker-compose run load-generator
```

### View Logs

```bash
# All logs
docker-compose logs

# Specific service logs
docker-compose logs backend
docker-compose logs frontend
```

## Development

### Backend Development

```bash
cd backend
pip install -r requirements.txt
python app.py
```

### Frontend Development

```bash
cd frontend
npm install
npm start
```

## Troubleshooting

If you encounter any issues:

1. Ensure all required ports are available (3000, 5000, 3306)
2. Check container logs for specific error messages
3. Verify database connectivity from the backend container

## License

[Add your license information here]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.