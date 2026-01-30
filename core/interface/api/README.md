# Blackbox 5 REST API

FastAPI-based REST interface for the Blackbox 5 Multi-Agent Orchestration System.

## Overview

This API provides HTTP endpoints to interact with the Blackbox 5 system, including:
- Processing chat messages through the multi-agent pipeline
- Listing and querying available agents
- Managing and discovering skills
- Searching for guides and intent-based operations

## Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the API

Start the server:

```bash
python3 main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, access the interactive API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints

### Health Check

```bash
GET /health
```

Returns API health status and version.

### Chat

```bash
POST /chat
Content-Type: application/json

{
  "message": "Create a Python function to calculate fibonacci",
  "session_id": "optional-session-id",
  "context": {}
}
```

Processes a message through the Blackbox 5 pipeline and returns:
- `result`: Execution result from the agent
- `routing`: Routing decision metadata (strategy, agent, complexity)
- `guide_suggestions`: Proactive guide suggestions

### List Agents

```bash
GET /agents
```

Returns all available agents with their roles, descriptions, and categories.

### Get Agent Details

```bash
GET /agents/{agent_name}
```

Returns detailed information about a specific agent.

### List Skills

```bash
GET /skills
GET /skills?category=development
```

Lists all skills, optionally filtered by category.

### Search Guides

```bash
GET /guides/search?q=python
```

Searches for guides by keyword.

### Find Guides by Intent

```bash
GET /guides/intent?intent=how%20to%20create%20a%20function
```

Finds guides matching natural language intent.

## Testing

Run the included test script:

```bash
./test_api.sh
```

Or test individual endpoints with curl:

```bash
# Health check
curl http://localhost:8000/health

# Send a chat message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, Blackbox 5!"}'

# List agents
curl http://localhost:8000/agents
```

## Architecture

The API is built on:
- **FastAPI**: Modern, fast web framework for building APIs
- **Pydantic**: Data validation using Python type annotations
- **Uvicorn**: ASGI server for running the application

The API integrates with the main Blackbox 5 system via:
- `get_blackbox5()`: Singleton accessor for the Blackbox5 instance
- `process_request()`: Main pipeline for processing user requests

## Pipeline Flow

When a chat request is received:

1. **Request Parsing**: Convert request into Task object
2. **Task Routing**: TaskRouter determines optimal execution strategy
3. **Execution**: Single-agent or multi-agent orchestration
4. **Guide Suggestions**: Proactive suggestions based on result
5. **Response**: Return result with routing metadata

## Error Handling

The API returns appropriate HTTP status codes:
- `200`: Success
- `404`: Resource not found (e.g., agent doesn't exist)
- `422`: Validation error (malformed request)
- `500`: Internal server error

## CORS Configuration

The API is configured to allow CORS from all origins for development. For production, update the CORS middleware configuration:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Production Deployment

For production deployment, consider:

1. Use a production ASGI server:
   ```bash
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

2. Set up environment variables for configuration
3. Enable HTTPS/TLS
4. Configure proper CORS origins
5. Set up authentication/authorization
6. Enable request logging and monitoring

## Development

### Adding New Endpoints

1. Define Pydantic models for request/response
2. Add the endpoint function with proper type hints
3. Use `get_blackbox5()` to access the Blackbox5 instance
4. Update this README with documentation

### Running Tests

```bash
# Syntax check
python -m py_compile main.py

# Start server
python3 main.py

# In another terminal, run tests
./test_api.sh
```

## Troubleshooting

### Import Errors

If you encounter import errors, ensure the engine root is in the Python path:

```python
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
```

### Port Already in Use

If port 8000 is already in use, either:
- Stop the process using port 8000
- Change the port in the `uvicorn.run()` call

### Blackbox5 Initialization Issues

Check that all dependencies are installed and the Blackbox5 system can initialize properly by reviewing the logs on startup.
