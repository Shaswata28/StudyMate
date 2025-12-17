"""
Chat router for handling AI chat requests with Supabase integration.
Direct integration with fine-tuned StudyMate model.
"""

from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Optional
import logging

from models.schemas import ChatRequest, ChatResponse, TestAccuracyInfo
from services.auth_service import get_current_user, AuthUser
from services.supabase_client import get_user_client
from services.local_ai_service import local_ai_service
from services.context_service import ContextService
from services.service_manager import service_manager
from services.test_accuracy_service import test_accuracy_service
from middleware.rate_limiter import limiter
from config import config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])
context_service = ContextService()


@router.post("/chat", response_model=ChatResponse)
@limiter.limit(f"{config.RATE_LIMIT_REQUESTS}/{config.RATE_LIMIT_WINDOW}seconds")
async def chat_endpoint(
    request: Request, 
    chat_request: ChatRequest,
    course_id: Optional[str] = None,
    user: AuthUser = Depends(get_current_user)
):
    """
    Global chat endpoint (no course context).
    Uses ChatML format matching core model training.
    """
    try:
        # Build context matching core model training format
        messages = await context_service.build_simple_context(
            user_id=user.id,
            user_message=chat_request.message,
            access_token=user.access_token
        )
        
        # Generate response with core model
        response_text = await local_ai_service.generate_chat_response(
            messages=messages,
            attachments=chat_request.attachments
        )
        
        # Check for test accuracy
        test_accuracy = None
        accuracy_result = test_accuracy_service.evaluate_response(
            chat_request.message, 
            response_text
        )
        if accuracy_result:
            test_accuracy = TestAccuracyInfo(**accuracy_result)
            logger.info(f"Test question matched - Accuracy: {accuracy_result['accuracy']}%")
        
        return ChatResponse(
            response=response_text,
            timestamp=datetime.utcnow().isoformat() + "Z",
            test_accuracy=test_accuracy
        )

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
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
    Course-specific chat with RAG support.
    
    Flow:
    1. Search course materials (RAG)
    2. Build ChatML context matching training format
    3. Generate response with core model
    4. Save history
    """
    rag_start_time = datetime.utcnow()
    logger.info(f"=" * 60)
    logger.info(f"Starting RAG chat for course {course_id}")
    logger.info(f"User: {user.id}, Message: {chat_request.message[:100]}...")
    logger.info(f"=" * 60)
    
    try:
        client = get_user_client(user.access_token)
        
        # 1. Verify Course Ownership
        logger.info(f"Course {course_id}: Verifying ownership for user {user.id}")
        try:
            course_result = client.table("courses").select("id").eq("id", course_id).eq("user_id", user.id).execute()
            if not course_result.data:
                logger.warning(f"Course {course_id}: Access denied for user {user.id}")
                raise HTTPException(status_code=404, detail="Course not found")
            logger.info(f"Course {course_id}: Ownership verified successfully")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Course {course_id}: Ownership verification failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to verify course access")
        
        # 2. Search Course Materials (RAG)
        search_results = []
        search_start_time = datetime.utcnow()
        
        if not service_manager.is_rag_enabled():
            logger.warning(f"Course {course_id}: RAG functionality disabled - skipping material search")
        else:
            try:
                query_message = chat_request.message
                
                if query_message and query_message.strip() and len(query_message.strip()) >= 3:
                    logger.info(f"Course {course_id}: Performing semantic search")
                    
                    search_results = await service_manager.processing_service.search_materials(
                        course_id=course_id,
                        query=query_message,
                        limit=3
                    )
                    
                    search_duration = (datetime.utcnow() - search_start_time).total_seconds()
                    logger.info(f"Course {course_id}: Material search completed in {search_duration:.2f}s - Found {len(search_results)} materials")
                else:
                    logger.info(f"Course {course_id}: Query too short - skipping material search")
                    
            except Exception as e:
                search_duration = (datetime.utcnow() - search_start_time).total_seconds()
                logger.error(f"Course {course_id}: Material search failed after {search_duration:.2f}s: {e}", exc_info=True)
                logger.warning(f"Course {course_id}: Continuing without material context")
        
        # 3. Build ChatML Context (matching training format)
        logger.info("Building ChatML context...")
        context_start = datetime.utcnow()
        
        try:
            messages = await context_service.build_rag_context(
                user_id=user.id,
                course_id=course_id,
                user_message=chat_request.message,
                access_token=user.access_token,
                search_results=search_results
            )
            
            context_duration = (datetime.utcnow() - context_start).total_seconds()
            logger.info(f"Context built in {context_duration:.2f}s ({len(messages)} messages)")
            
        except Exception as e:
            logger.error(f"Context building failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to build context")
        
        # 4. Generate AI Response
        logger.info("Generating response with core model...")
        ai_start_time = datetime.utcnow()
        
        try:
            response_text = await local_ai_service.generate_chat_response(
                messages=messages,
                attachments=chat_request.attachments
            )
            
            ai_duration = (datetime.utcnow() - ai_start_time).total_seconds()
            logger.info(f"AI response generated in {ai_duration:.2f}s ({len(response_text)} characters)")
            
        except Exception as e:
            logger.error(f"AI response generation failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, 
                detail="AI service temporarily unavailable. Please try again."
            )
        
        # 5. Save Chat History
        logger.info("Saving conversation to chat history")
        history_start_time = datetime.utcnow()
        
        try:
            user_message = {"role": "user", "content": chat_request.message}
            ai_message = {"role": "model", "content": response_text}
            
            client.table("chat_history").insert({
                "course_id": course_id,
                "history": [user_message, ai_message]
            }).execute()
            
            history_duration = (datetime.utcnow() - history_start_time).total_seconds()
            logger.info(f"Chat history saved in {history_duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to save chat history: {e}", exc_info=True)
            logger.warning("Continuing without saving history")
        
        # 6. Check for test accuracy
        test_accuracy = None
        accuracy_result = test_accuracy_service.evaluate_response(
            chat_request.message, 
            response_text
        )
        if accuracy_result:
            test_accuracy = TestAccuracyInfo(**accuracy_result)
            logger.info(f"Test question matched - Accuracy: {accuracy_result['accuracy']}%")
        
        # 7. Log Performance Summary
        total_duration = (datetime.utcnow() - rag_start_time).total_seconds()
        logger.info(f"=" * 60)
        logger.info(
            f"RAG chat completed in {total_duration:.2f}s - "
            f"Materials: {len(search_results)}, "
            f"Response: {len(response_text)} chars"
        )
        logger.info(f"=" * 60)
        
        return ChatResponse(
            response=response_text,
            timestamp=datetime.utcnow().isoformat() + "Z",
            test_accuracy=test_accuracy
        )
        
    except HTTPException:
        raise
    except Exception as e:
        total_duration = (datetime.utcnow() - rag_start_time).total_seconds()
        logger.error(f"RAG chat failed after {total_duration:.2f}s: {e}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Chat service temporarily unavailable. Please try again.", 
                "code": "RAG_ERROR",
                "details": "The system encountered an error while processing your request."
            }
        )


@router.get("/courses/{course_id}/chat")
async def get_chat_history(
    course_id: str,
    user: AuthUser = Depends(get_current_user)
):
    """Retrieve chat history for a course."""
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
