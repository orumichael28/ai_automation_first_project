import os
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from openai import OpenAI
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Setting up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

# Global variables
client: Optional[OpenAI] = None
sessions: Dict[str, dict] = {}

# Session cleanup configuration
SESSION_TIMEOUT_MINUTES = 30
MAX_CONTEXT_MESSAGES = 20


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources"""
    global client
    
    # Startup: Initialize OpenAI client
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            raise ValueError("Missing OPENAI_API_KEY environment variable")
        
        client = OpenAI(api_key=api_key)
        logger.info("OpenAI client initialized successfully")
    except Exception as e:
        logger.critical(f"Failed to initialize OpenAI client: {e}")
        raise
    
    yield
    
    # Shutdown: Cleanup
    logger.info("Application shutting down")


app = FastAPI(
    title="Retail Saleswoman Chatbot API",
    description="API for conversational retail sales chatbot powered by OpenAI",
    version="1.0.0",
    lifespan=lifespan
)

# Pydantic models for request/response validation
class CreateSessionRequest(BaseModel):
    price: float = Field(..., gt=0, description="Price of the item in naira")


class UpdatePriceRequest(BaseModel):
    price: float = Field(..., gt=0, description="New price of the item in naira")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User's message")


class ChatResponse(BaseModel):
    reply: str
    intent: str
    confidence_level: str


class SessionInfo(BaseModel):
    session_id: str
    price: float
    created_at: str
    message_count: int
    last_activity: str


def create_initial_context(price: float) -> List[dict]:
    """Create initial conversation context with system prompts"""
    return [
        {"role": "system", "content": "You are a professional retail saleswoman. your goal is to close the sale while remaining polite and confident"},
        {"role": "system", "content": (
            "Respond ONLY in valid JSON with the following fields:\n"
            "- reply (string): what the customer sees\n"
            "- intent (one of: buy, hesitate, ask_question)\n"
            "- confidence_level (one of: low, medium, high)\n"
            "Do not include any extra text outside the JSON."
        )},
        {"role": "system", "content": f"The price of the item is {price} naira."}
    ]


def trim_context(context: List[dict]) -> List[dict]:
    """Trim context to manage token usage"""
    if len(context) > MAX_CONTEXT_MESSAGES:
        system_messages = [msg for msg in context if msg["role"] == "system"]
        conversation_messages = [msg for msg in context if msg["role"] != "system"]
        context = system_messages + conversation_messages[-(MAX_CONTEXT_MESSAGES - len(system_messages)):]
        logger.info("Context trimmed to manage token usage")
    return context


def get_response(context: List[dict], temperature: float = 0.4) -> str:
    """Get response from OpenAI API"""
    try:
        logger.info(f"Making API call with {len(context)} messages in context")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=temperature,
            max_tokens=150,
            messages=context
        )
        
        output = response.choices[0].message.content
        
        # Log token usage
        if hasattr(response, 'usage'):
            logger.info(f"Token usage - Prompt: {response.usage.prompt_tokens}, "
                       f"Completion: {response.usage.completion_tokens}, "
                       f"Total: {response.usage.total_tokens}")
        
        return output
    
    except Exception as e:
        logger.error(f"API call failed: {e}")
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")


def cleanup_expired_sessions():
    """Remove expired sessions based on timeout"""
    now = datetime.now()
    expired_sessions = [
        session_id for session_id, session in sessions.items()
        if now - session["last_activity"] > timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    ]
    
    for session_id in expired_sessions:
        del sessions[session_id]
        logger.info(f"Cleaned up expired session: {session_id}")
    
    return len(expired_sessions)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_sessions": len(sessions),
        "timestamp": datetime.now().isoformat()
    }


@app.post("/sessions", response_model=SessionInfo, status_code=201)
async def create_session(request: CreateSessionRequest, background_tasks: BackgroundTasks):
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    now = datetime.now()
    
    sessions[session_id] = {
        "session_id": session_id,
        "price": request.price,
        "context": create_initial_context(request.price),
        "message_count": 0,
        "created_at": now,
        "last_activity": now
    }
    
    logger.info(f"Created new session {session_id} with price {request.price} naira")
    
    # Schedule cleanup of expired sessions
    background_tasks.add_task(cleanup_expired_sessions)
    
    return SessionInfo(
        session_id=session_id,
        price=request.price,
        created_at=now.isoformat(),
        message_count=0,
        last_activity=now.isoformat()
    )


@app.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """Get session information"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    return SessionInfo(
        session_id=session["session_id"],
        price=session["price"],
        created_at=session["created_at"].isoformat(),
        message_count=session["message_count"],
        last_activity=session["last_activity"].isoformat()
    )


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete/reset a session"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del sessions[session_id]
    logger.info(f"Deleted session {session_id}")
    
    return {"message": "Session deleted successfully"}


@app.put("/sessions/{session_id}/price", response_model=SessionInfo)
async def update_price(session_id: str, request: UpdatePriceRequest):
    """Update the item price for a session"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    session["price"] = request.price
    session["last_activity"] = datetime.now()
    
    # Update price in context
    for i, msg in enumerate(session["context"]):
        if msg["role"] == "system" and "price of the item" in msg["content"]:
            session["context"][i]["content"] = f"The price of the item is {request.price} naira."
    
    logger.info(f"Updated price to {request.price} naira for session {session_id}")
    
    return SessionInfo(
        session_id=session["session_id"],
        price=session["price"],
        created_at=session["created_at"].isoformat(),
        message_count=session["message_count"],
        last_activity=session["last_activity"].isoformat()
    )


@app.post("/sessions/{session_id}/chat", response_model=ChatResponse)
async def chat(session_id: str, request: ChatRequest, background_tasks: BackgroundTasks):
    """Send a message and get a response"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    # Add user message to context
    logger.info(f"Session {session_id} - User: {request.message}")
    session["context"].append({"role": "user", "content": request.message})
    session["message_count"] += 1
    session["last_activity"] = datetime.now()
    
    # Trim context if needed
    session["context"] = trim_context(session["context"])
    
    # Get response from OpenAI
    response = get_response(session["context"])
    
    # Parse JSON response
    try:
        data = json.loads(response)
        logger.info(f"Session {session_id} - AI response - Intent: {data['intent']}, Confidence: {data['confidence_level']}")
    except json.JSONDecodeError:
        logger.warning(f"Session {session_id} - Invalid JSON response: {response}")
        # Return response as-is with unknown values
        data = {"reply": response, "intent": "unknown", "confidence_level": "unknown"}
    
    # Add assistant response to context
    session["context"].append({"role": "assistant", "content": response})
    
    # Schedule cleanup of expired sessions
    background_tasks.add_task(cleanup_expired_sessions)
    
    return ChatResponse(
        reply=data.get("reply", response),
        intent=data.get("intent", "unknown"),
        confidence_level=data.get("confidence_level", "unknown")
    )




