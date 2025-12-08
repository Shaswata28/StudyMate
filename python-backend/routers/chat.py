"""
Chat router for handling AI chat requests with Supabase integration.
Delegates logic to the Orchestrator service.
"""

from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Optional
import logging

from models.schemas import ChatRequest, ChatResponse
from services.auth_service import get_current_user, AuthUser
from services.supabase_client import get_user_client
from services.orchestrator import orchestrator
from middleware.rate_limiter import limiter
from config import config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
@limiter.limit(f"{config.RATE_LIMIT_REQUESTS}/{config.RATE_LIMIT_WINDOW}seconds")
async def chat_endpoint(
    request: Request, 
    chat_request: ChatRequest,
    course_id: Optional[str] = None,
    user: AuthUser = Depends(get_current_user)
):
    """
    Unified chat endpoint.
    If course_id is provided, it triggers the full RAG/Orchestrator pipeline.
    If not, it acts as a general chat (but still routed via Orchestrator for consistency).
    """
    try:
        # Hand off to Orchestrator (The "Brain")
        # The Orchestrator handles Intent Classification, RAG, and Personality
        response_text = await orchestrator.process_chat_request(
            user_id=user.id,
            course_id=course_id if course_id else "global", # Handle global chat
            chat_request=chat_request,
            access_token=user.access_token
        )
        
        # Create response with timestamp
        response = ChatResponse(
            response=response_text,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
        return response

    except Exception as e:
        logger.error(f"Global chat error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Something went wrong.", "code": "INTERNAL_ERROR"}
        )


@router.post("/courses/{course_id}/chat", status_code=status.HTTP_201_CREATED)
async def save_chat_message(
    course_id: str,
    request: Request,
    chat_request: ChatRequest,
    user: AuthUser = Depends(get_current_user)
):
    """
    Course-specific chat with History persistence and RAG.
    """
    try:
        client = get_user_client(user.access_token)
        
        # 1. Verify Ownership
        course_result = client.table("courses").select("id").eq("id", course_id).eq("user_id", user.id).execute()
        if not course_result.data:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # 2. Process via Orchestrator
        # This allows handling "Hybrid" questions (e.g. "Explain this slide and tell a joke")
        response_text = await orchestrator.process_chat_request(
            user_id=user.id,
            course_id=course_id,
            chat_request=chat_request,
            access_token=user.access_token
        )
        
        # 3. Save History to Supabase
        user_message = {"role": "user", "content": chat_request.message}
        ai_message = {"role": "model", "content": response_text}
        
        client.table("chat_history").insert({
            "course_id": course_id,
            "history": [user_message, ai_message]
        }).execute()
        
        # 4. Return Response
        return ChatResponse(
            response=response_text,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Course chat error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "code": "INTERNAL_ERROR"}
        )

# Keep the history retrieval endpoint as is (it's purely DB read)
@router.get("/courses/{course_id}/chat")
async def get_chat_history(
    course_id: str,
    user: AuthUser = Depends(get_current_user)
):
    try:
        client = get_user_client(user.access_token)
        # Verify ownership
        course_result = client.table("courses").select("id").eq("id", course_id).eq("user_id", user.id).execute()
        if not course_result.data:
            raise HTTPException(status_code=404, detail="Course not found")
            
        result = client.table("chat_history").select("*").eq("course_id", course_id).order("created_at", desc=False).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve history")