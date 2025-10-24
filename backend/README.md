# Query Responder RAG App - Backend

A Flask-based backend API for the Query Responder RAG system, providing a simple endpoint that returns Bhagavad Gita mantras.

## Features

- **Flask API**: Lightweight and fast Python web framework
- **CORS Support**: Enabled for frontend-backend communication
- **Bhagavad Gita Mantras**: Returns spiritual wisdom from the Gita
- **Error Handling**: Proper HTTP status codes and error messages
- **Health Check**: Endpoint for monitoring API status

## API Endpoints

### POST `/api/query`
Submit a query and receive a response.

**Request Body:**
```json
{
  "query": "What is the meaning of karma yoga?"
}
```

**Response:**
```json
{
  "response": "Krishna says in the Bhagavad Gita: 'You have the right to work only, but never to its fruits...'",
  "query": "What is the meaning of karma yoga?",
  "source": "Bhagavad Gita"
}
```

### GET `/health`
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "service": "Query Responder RAG API"
}
```

### GET `/`
Root endpoint with API information.

## Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Flask application:**
   ```bash
   python app.py
   ```

3. **The API will be available at:**
   - Main API: http://localhost:5001
   - Health check: http://localhost:5001/health

## Dependencies

- **Flask**: Web framework for building the API
- **Flask-CORS**: Cross-Origin Resource Sharing support

## Development

The application runs in debug mode by default, which enables:
- Hot reloading on code changes
- Detailed error messages
- Development server

## Production Deployment

For production deployment, consider:
- Using a production WSGI server (Gunicorn, uWSGI)
- Disabling debug mode
- Setting up proper logging
- Using environment variables for configuration 