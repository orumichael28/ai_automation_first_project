# Retail Saleswoman Chatbot API

A FastAPI-powered conversational chatbot that simulates a professional retail saleswoman. The API uses OpenAI's GPT-4o-mini model to generate contextual responses with intent analysis and confidence levels.

## Features

- **Multi-session support**: Handle multiple concurrent conversations with isolated contexts
- **Structured responses**: Get JSON responses with reply, intent, and confidence level
- **Dynamic pricing**: Update item prices during conversations
- **Session management**: Create, retrieve, update, and delete chat sessions
- **Auto-cleanup**: Expired sessions are automatically removed after 30 minutes of inactivity
- **Context management**: Maintains conversation history with automatic trimming to optimize token usage

## Installation

1. Install dependencies:
```bash
pip install fastapi uvicorn pydantic python-dotenv openai
```

2. Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Running the Server

Start the server with:
```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`

Interactive API documentation: `http://127.0.0.1:8000/docs`

## API Endpoints

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "active_sessions": 0,
  "timestamp": "2025-12-31T15:25:00.000000"
}
```

### Create Session
```http
POST /sessions
Content-Type: application/json

{
  "price": 5000
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "price": 5000,
  "created_at": "2025-12-31T15:25:00.000000",
  "message_count": 0,
  "last_activity": "2025-12-31T15:25:00.000000"
}
```

### Get Session Info
```http
GET /sessions/{session_id}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "price": 5000,
  "created_at": "2025-12-31T15:25:00.000000",
  "message_count": 3,
  "last_activity": "2025-12-31T15:26:00.000000"
}
```

### Send Chat Message
```http
POST /sessions/{session_id}/chat
Content-Type: application/json

{
  "message": "What are you selling?"
}
```

**Response:**
```json
{
  "reply": "Hello! I'm offering a fantastic product at 5000 naira. It's a great value and I'm confident you'll love it. What would you like to know about it?",
  "intent": "ask_question",
  "confidence_level": "high"
}
```

### Update Price
```http
PUT /sessions/{session_id}/price
Content-Type: application/json

{
  "price": 4500
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "price": 4500,
  "created_at": "2025-12-31T15:25:00.000000",
  "message_count": 3,
  "last_activity": "2025-12-31T15:27:00.000000"
}
```

### Delete Session
```http
DELETE /sessions/{session_id}
```

**Response:**
```json
{
  "message": "Session deleted successfully"
}
```

## Response Fields

All chat responses include:

- **reply** (string): The message shown to the customer
- **intent** (string): One of `buy`, `hesitate`, or `ask_question`
- **confidence_level** (string): One of `low`, `medium`, or `high`

## Configuration

- **SESSION_TIMEOUT_MINUTES**: 30 (sessions expire after 30 minutes of inactivity)
- **MAX_CONTEXT_MESSAGES**: 20 (maximum messages in conversation context)
- **Temperature**: 0.4 (controls response randomness)
- **Max Tokens**: 150 (maximum tokens per response)
- **Model**: gpt-4o-mini


## Logging

All API calls and OpenAI interactions are logged to the console with:
- Timestamp
- Log level (INFO, WARNING, ERROR)
- Session IDs
- Token usage statistics
- Request/response details
