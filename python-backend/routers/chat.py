"""
Chat router for handling AI chat requests with Supabase integration.
Direct integration with fine-tuned StudyMate model (bypassing orchestrator).
"""

from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Optional
import logging

from models.schemas import ChatRequest, ChatResponse
from services.auth_service import get_current_user, AuthUser
from services.supabase_client import get_user_client
from services.local_ai_service import local_ai_service
from services.context_service import ContextService
from services.service_manager import service_manager
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
    Simplified chat endpoint using fine-tuned StudyMate model directly.
    No orchestrator - just context + RAG + direct model call.
    """
    try:
        # Get user context (preferences, academic info, history)
        user_context = await context_service.get_user_context(
            user_id=user.id,
            course_id=course_id if course_id else "global",
            access_token=user.access_token
        )
        
        # For course-specific chats, search for relevant materials
        material_context = None
        if course_id and course_id != "global":
            try:
                search_results = await service_manager.processing_service.search_materials(
                    course_id=course_id,
                    query=chat_request.message,
                    limit=3
                )
                
                if search_results:
                    material_parts = []
                    for idx, res in enumerate(search_results, 1):
                        material_parts.append(f"--- Material {idx}: {res['name']} ---")
                        material_parts.append(f"{res['excerpt']}")
                        material_parts.append("")
                    material_context = "\n".join(material_parts)
                    logger.info(f"Found {len(search_results)} relevant materials")
            except Exception as e:
                logger.warning(f"Material search failed: {e}")
        
        # For fine-tuned StudyMate model, use simple Alpaca format
        if material_context:
            # Include materials in the input
            alpaca_prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
You are StudyMate, a helpful AI study assistant. Use the provided course materials to help answer the student's question.

### Input:
Course Materials:
{material_context}

Student Question: {chat_request.message}

### Response:
"""
        else:
            # Simple question without materials
            alpaca_prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
You are StudyMate, a helpful AI study assistant.

### Input:
{chat_request.message}

### Response:
"""
        
        # Direct call to fine-tuned StudyMate model
        response_text = await local_ai_service.generate_response(
            message=alpaca_prompt,
            history=user_context.chat_history if user_context.has_history else None,
            attachments=chat_request.attachments
        )
        
        return ChatResponse(
            response=response_text,
            timestamp=datetime.utcnow().isoformat() + "Z"
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
    Enhanced course-specific chat with reliable RAG and history persistence.
    
    Improvements:
    - Comprehensive error handling for all RAG operations
    - Enhanced logging for debugging
    - Reliable material search with fallback
    - Improved context integration
    - Graceful degradation when components fail
    """
    rag_start_time = datetime.utcnow()
    logger.info(f"=" * 60)
    logger.info(f"Starting RAG-enhanced chat for course {course_id}")
    logger.info(f"User: {user.id}, Message length: {len(chat_request.message)} chars")
    logger.info(f"=" * 60)
    
    try:
        client = get_user_client(user.access_token)
        
        # 1. Verify Course Ownership with enhanced error handling
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
        
        # 2. Get User Context with comprehensive error handling and timing
        logger.info(f"Course {course_id}: Retrieving user context (preferences, academic, history)")
        context_start_time = datetime.utcnow()
        
        try:
            user_context = await context_service.get_user_context(
                user_id=user.id,
                course_id=course_id,
                access_token=user.access_token
            )
            
            context_duration = (datetime.utcnow() - context_start_time).total_seconds()
            logger.info(
                f"Course {course_id}: User context retrieved in {context_duration:.2f}s - "
                f"Preferences: {user_context.has_preferences}, "
                f"Academic: {user_context.has_academic}, "
                f"History: {len(user_context.chat_history) if user_context.has_history else 0} messages"
            )
        except Exception as e:
            logger.error(f"Course {course_id}: Failed to retrieve user context: {e}", exc_info=True)
            # Create empty context for graceful degradation
            from models.schemas import UserContext
            user_context = UserContext()
            logger.warning(f"Course {course_id}: Using empty context due to retrieval failure")
        
        # 3. Perform Material Search with comprehensive edge case handling and graceful degradation
        logger.info(f"Course {course_id}: Starting material search for RAG")
        search_start_time = datetime.utcnow()
        material_context = None
        search_results = []
        
        # Check if RAG functionality is enabled before attempting search
        if not service_manager.is_rag_enabled():
            logger.warning(f"Course {course_id}: RAG functionality disabled - skipping material search")
            logger.info(f"Course {course_id}: Check /health/rag endpoint for component status")
            logger.info(f"Course {course_id}: Graceful degradation - proceeding with conversation history only")
        else:
            try:
                # Enhanced edge case handling for search queries (Requirements 8.1, 8.2, 8.3)
                query_message = chat_request.message
                
                # Edge case: Empty or whitespace-only queries (Requirement 8.3)
                if not query_message or not query_message.strip():
                    logger.info(f"Course {course_id}: Empty or whitespace-only query - skipping material search")
                    logger.info(f"Course {course_id}: Graceful degradation - proceeding with conversation history only (Requirement 8.3)")
                # Edge case: Very short queries (Requirement 8.3)
                elif len(query_message.strip()) < 3:
                    logger.info(f"Course {course_id}: Very short query ('{query_message.strip()}') - skipping material search")
                    logger.info(f"Course {course_id}: Graceful degradation - proceeding with conversation history only (Requirement 8.3)")
                else:
                    logger.info(f"Course {course_id}: Performing semantic search with query: '{query_message[:100]}{'...' if len(query_message) > 100 else ''}'")
                    
                    # The search_materials method now handles all edge cases internally:
                    # - Requirement 8.1: Courses without materials
                    # - Requirement 8.2: Unprocessed materials
                    # - Requirement 8.3: Short/empty queries (double-checked here for clarity)
                    search_results = await service_manager.processing_service.search_materials(
                        course_id=course_id,
                        query=query_message,
                        limit=3
                    )
                    
                    search_duration = (datetime.utcnow() - search_start_time).total_seconds()
                    
                    if search_results:
                        logger.info(f"Course {course_id}: Material search completed in {search_duration:.2f}s - Found {len(search_results)} relevant materials")
                        
                        # Format materials for AI prompt with enhanced structure
                        material_parts = []
                        for idx, res in enumerate(search_results, 1):
                            similarity_score = res.get('similarity_score', 0.0)
                            material_parts.append(f"--- Material {idx}: {res['name']} (Relevance: {similarity_score:.2f}) ---")
                            material_parts.append(f"{res['excerpt']}")
                            material_parts.append("")
                        
                        material_context = "\n".join(material_parts)
                        logger.info(f"Course {course_id}: Material context formatted ({len(material_context)} characters)")
                    else:
                        logger.info(f"Course {course_id}: Material search completed in {search_duration:.2f}s - No relevant materials found")
                        logger.info(f"Course {course_id}: This could be due to: no materials uploaded, materials still processing, or no semantic matches")
                    
            except Exception as e:
                search_duration = (datetime.utcnow() - search_start_time).total_seconds()
                logger.error(f"Course {course_id}: Material search failed after {search_duration:.2f}s: {e}", exc_info=True)
                logger.warning(f"Course {course_id}: Graceful degradation - continuing without material context")
                # Continue without material context (graceful degradation)
        
        # 4. Format Enhanced Context Prompt with better structure
        logger.info(f"Course {course_id}: Formatting enhanced context prompt")
        prompt_start_time = datetime.utcnow()
        
        try:
            # Use the enhanced context service formatting
            enhanced_prompt = context_service.format_context_prompt(
                context=user_context,
                user_message=chat_request.message,
                material_context=material_context
            )
            
            prompt_duration = (datetime.utcnow() - prompt_start_time).total_seconds()
            logger.info(f"Course {course_id}: Enhanced prompt formatted in {prompt_duration:.2f}s ({len(enhanced_prompt)} characters)")
            
        except Exception as e:
            logger.error(f"Course {course_id}: Enhanced prompt formatting failed: {e}", exc_info=True)
            logger.warning(f"Course {course_id}: Falling back to basic prompt format")
            
            # Fallback to basic Alpaca format for fine-tuned model
            if material_context:
                enhanced_prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
You are StudyMate, a helpful AI study assistant. Use the provided course materials to help answer the student's question.

### Input:
Course Materials:
{material_context}

Student Question: {chat_request.message}

### Response:
"""
            else:
                enhanced_prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
You are StudyMate, a helpful AI study assistant.

### Input:
{chat_request.message}

### Response:
"""
        
        # 5. Generate AI Response with enhanced error handling
        logger.info(f"Course {course_id}: Generating AI response")
        ai_start_time = datetime.utcnow()
        
        try:
            response_text = await local_ai_service.generate_response(
                message=enhanced_prompt,
                history=user_context.chat_history if user_context.has_history else None,
                attachments=chat_request.attachments
            )
            
            ai_duration = (datetime.utcnow() - ai_start_time).total_seconds()
            logger.info(f"Course {course_id}: AI response generated in {ai_duration:.2f}s ({len(response_text)} characters)")
            
        except Exception as e:
            logger.error(f"Course {course_id}: AI response generation failed: {e}", exc_info=True)
            # Return error response instead of crashing
            raise HTTPException(
                status_code=500, 
                detail="AI service temporarily unavailable. Please try again."
            )
        
        # 6. Save Chat History with enhanced error handling
        logger.info(f"Course {course_id}: Saving conversation to chat history")
        history_start_time = datetime.utcnow()
        
        try:
            user_message = {"role": "user", "content": chat_request.message}
            ai_message = {"role": "model", "content": response_text}
            
            client.table("chat_history").insert({
                "course_id": course_id,
                "history": [user_message, ai_message]
            }).execute()
            
            history_duration = (datetime.utcnow() - history_start_time).total_seconds()
            logger.info(f"Course {course_id}: Chat history saved in {history_duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Course {course_id}: Failed to save chat history: {e}", exc_info=True)
            logger.warning(f"Course {course_id}: Continuing without saving history (graceful degradation)")
            # Don't fail the request if history saving fails
        
        # 7. Log RAG Pipeline Summary
        total_duration = (datetime.utcnow() - rag_start_time).total_seconds()
        logger.info(f"=" * 60)
        logger.info(
            f"RAG-enhanced chat completed successfully for course {course_id} "
            f"(Total time: {total_duration:.2f}s)"
        )
        logger.info(
            f"RAG Summary - Materials found: {len(search_results)}, "
            f"Context available: {user_context.has_preferences or user_context.has_academic or user_context.has_history}, "
            f"Response length: {len(response_text)} chars"
        )
        logger.info(f"=" * 60)
        
        # 8. Return Enhanced Response
        return ChatResponse(
            response=response_text,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404, 500) without modification
        raise
    except Exception as e:
        total_duration = (datetime.utcnow() - rag_start_time).total_seconds()
        logger.error(f"Course {course_id}: RAG-enhanced chat failed after {total_duration:.2f}s: {e}", exc_info=True)
        
        # Return structured error response with graceful degradation
        return JSONResponse(
            status_code=500,
            content={
                "error": "Chat service temporarily unavailable. Please try again.", 
                "code": "RAG_PIPELINE_ERROR",
                "details": "The system encountered an error while processing your request."
            }
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