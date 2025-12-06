"""
Context service for retrieving and formatting user context for AI chat.

This service aggregates user preferences, academic information, and chat history
to provide personalized, context-aware AI responses.
"""
from typing import Optional, List, Dict
from supabase import Client
import logging
import asyncio

from models.schemas import (
    UserPreferences,
    AcademicInfo,
    UserContext,
    Message
)
from constants import DEFAULT_PREFERENCES
from services.supabase_client import get_user_client

logger = logging.getLogger(__name__)


class ContextService:
    """
    Service for retrieving user context for AI chat.
    
    This service handles:
    - Retrieving user learning preferences from the personalized table
    - Retrieving user academic information from the academic table
    - Retrieving recent chat history from the chat_history table
    - Formatting all context into an enhanced AI prompt
    
    All database queries use the user's JWT token to enforce RLS policies.
    """
    
    async def get_preferences(
        self,
        user_id: str,
        client: Client
    ) -> Optional[UserPreferences]:
        """
        Retrieve user learning preferences from the personalized table.
        
        Args:
            user_id: User's UUID
            client: Supabase client with user's JWT token
            
        Returns:
            UserPreferences object if found, None otherwise
            
        Example:
            ```python
            prefs = await context_service.get_preferences(user_id, client)
            if prefs:
                print(f"Learning pace: {prefs.learning_pace}")
            ```
        """
        try:
            logger.debug(f"Retrieving preferences for user {user_id}")
            
            result = client.table("personalized")\
                .select("prefs")\
                .eq("id", user_id)\
                .single()\
                .execute()
            
            if result.data and result.data.get("prefs"):
                prefs_data = result.data["prefs"]
                logger.info(f"Preferences retrieved successfully for user {user_id}")
                return UserPreferences(**prefs_data)
            else:
                logger.warning(f"No preferences found for user {user_id}, will use defaults")
                return None
                
        except ValueError as e:
            # Handle validation errors from Pydantic
            logger.error(f"Invalid preference data for user {user_id}: {str(e)}", exc_info=True)
            return None
        except Exception as e:
            # Handle database errors, network issues, etc.
            logger.error(f"Failed to retrieve preferences for user {user_id}: {str(e)}", exc_info=True)
            return None
    
    async def get_academic_info(
        self,
        user_id: str,
        client: Client
    ) -> Optional[AcademicInfo]:
        """
        Retrieve user academic information from the academic table.
        
        Args:
            user_id: User's UUID
            client: Supabase client with user's JWT token
            
        Returns:
            AcademicInfo object if found, None otherwise
            
        Example:
            ```python
            academic = await context_service.get_academic_info(user_id, client)
            if academic:
                print(f"Grade: {academic.grade}, Semester: {academic.semester}")
            ```
        """
        try:
            logger.debug(f"Retrieving academic info for user {user_id}")
            
            result = client.table("academic")\
                .select("grade, semester_type, semester, subject")\
                .eq("id", user_id)\
                .single()\
                .execute()
            
            if result.data:
                logger.info(f"Academic info retrieved successfully for user {user_id}")
                return AcademicInfo(**result.data)
            else:
                logger.warning(f"No academic info found for user {user_id}, will proceed without academic context")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve academic info for user {user_id}: {str(e)}", exc_info=True)
            return None
    
    async def get_chat_history(
        self,
        course_id: str,
        client: Client,
        limit: int = 10
    ) -> List[Message]:
        """
        Retrieve recent chat history for a course.
        
        Messages are returned in chronological order (oldest first) and limited
        to the most recent N messages. This method retrieves all chat_history rows
        for the course, flattens the JSONB arrays, and returns only the last N messages.
        
        Args:
            course_id: Course UUID
            client: Supabase client with user's JWT token
            limit: Maximum number of messages to retrieve (default: 10)
            
        Returns:
            List of Message objects in chronological order (last N messages)
            
        Example:
            ```python
            history = await context_service.get_chat_history(course_id, client, limit=10)
            print(f"Retrieved {len(history)} messages")
            ```
        """
        try:
            logger.debug(f"Retrieving chat history for course {course_id} (limit: {limit})")
            
            # Retrieve all chat_history rows for the course, ordered chronologically
            result = client.table("chat_history")\
                .select("history, created_at")\
                .eq("course_id", course_id)\
                .order("created_at", desc=False)\
                .execute()
            
            if not result.data:
                logger.warning(f"No chat history found for course {course_id}, will proceed with empty history")
                return []
            
            # Flatten JSONB arrays into Message list
            # Each row contains a history array with multiple messages
            all_messages = []
            for row in result.data:
                history_array = row.get("history", [])
                for msg_data in history_array:
                    try:
                        all_messages.append(Message(**msg_data))
                    except Exception as e:
                        logger.warning(f"Failed to parse message in course {course_id}: {str(e)}")
                        continue
            
            # Take only the last N messages (most recent)
            messages = all_messages[-limit:] if len(all_messages) > limit else all_messages
            
            logger.info(f"Chat history retrieved successfully for course {course_id}: {len(messages)} messages (from {len(all_messages)} total)")
            return messages
            
        except Exception as e:
            logger.error(f"Failed to retrieve chat history for course {course_id}: {str(e)}", exc_info=True)
            return []
    
    async def get_user_context(
        self,
        user_id: str,
        course_id: str,
        access_token: str,
        timeout: float = 2.0
    ) -> UserContext:
        """
        Retrieve all context for a user's chat request with timeout support.
        
        This method fetches preferences, academic info, and chat history in parallel
        for optimal performance. If retrieval exceeds the timeout, partial context
        is returned with whatever was successfully retrieved.
        
        Args:
            user_id: User's UUID
            course_id: Course UUID
            access_token: User's JWT token for Supabase
            timeout: Maximum time in seconds to wait for context retrieval (default: 2.0)
            
        Returns:
            UserContext object with all available context (may be partial on timeout)
            
        Example:
            ```python
            context = await context_service.get_user_context(
                user_id="123",
                course_id="456",
                access_token="jwt_token",
                timeout=2.0
            )
            print(f"Has preferences: {context.has_preferences}")
            print(f"Has academic: {context.has_academic}")
            print(f"History length: {len(context.chat_history)}")
            ```
        """
        import time
        start_time = time.time()
        
        logger.info(f"Starting context retrieval for user_id={user_id}, course_id={course_id} (timeout={timeout}s)")
        
        # Initialize partial context variables
        preferences = None
        academic = None
        history = []
        timed_out = False
        
        try:
            # Create user client with JWT token for RLS enforcement
            client = get_user_client(access_token)
            
            # Wrap parallel context retrieval with timeout
            try:
                # Fetch all context in parallel for performance with timeout
                preferences, academic, history = await asyncio.wait_for(
                    asyncio.gather(
                        self.get_preferences(user_id, client),
                        self.get_academic_info(user_id, client),
                        self.get_chat_history(course_id, client, limit=10),
                        return_exceptions=True
                    ),
                    timeout=timeout
                )
                
                # Handle exceptions from parallel execution
                if isinstance(preferences, Exception):
                    logger.error(f"Exception retrieving preferences: {str(preferences)}", exc_info=True)
                    preferences = None
                
                if isinstance(academic, Exception):
                    logger.error(f"Exception retrieving academic info: {str(academic)}", exc_info=True)
                    academic = None
                
                if isinstance(history, Exception):
                    logger.error(f"Exception retrieving chat history: {str(history)}", exc_info=True)
                    history = []
                    
            except asyncio.TimeoutError:
                # Timeout occurred - use partial context retrieved so far
                timed_out = True
                elapsed_time = time.time() - start_time
                logger.warning(
                    f"Context retrieval timeout after {elapsed_time:.3f}s for user {user_id}, course {course_id}. "
                    f"Using partial context: preferences={preferences is not None}, "
                    f"academic={academic is not None}, history={len(history) if isinstance(history, list) else 0}"
                )
            
            # Build UserContext object with whatever context we have
            context = UserContext(
                preferences=preferences,
                academic=academic,
                chat_history=history if isinstance(history, list) else [],
                has_preferences=preferences is not None,
                has_academic=academic is not None,
                has_history=len(history) > 0 if isinstance(history, list) else False
            )
            
            elapsed_time = time.time() - start_time
            
            # Log successful retrieval with detailed counts
            if timed_out:
                logger.warning(
                    f"Context retrieval completed with timeout for user {user_id}, course {course_id}: "
                    f"preferences={'found' if context.has_preferences else 'missing'}, "
                    f"academic={'found' if context.has_academic else 'missing'}, "
                    f"history={len(context.chat_history)} messages, "
                    f"retrieval_time={elapsed_time:.3f}s (TIMED OUT)"
                )
            else:
                logger.info(
                    f"Context retrieval successful for user {user_id}, course {course_id}: "
                    f"preferences={'found' if context.has_preferences else 'missing'}, "
                    f"academic={'found' if context.has_academic else 'missing'}, "
                    f"history={len(context.chat_history)} messages, "
                    f"retrieval_time={elapsed_time:.3f}s"
                )
            
            # Log warnings for missing context components
            if not context.has_preferences:
                logger.warning(f"User {user_id} has no preferences, will use defaults")
            if not context.has_academic:
                logger.warning(f"User {user_id} has no academic info, will proceed without academic context")
            if not context.has_history:
                logger.warning(f"Course {course_id} has no chat history, starting fresh conversation")
            
            # Log performance warning if retrieval is slow (but didn't timeout)
            if not timed_out and elapsed_time > 2.0:
                logger.warning(
                    f"Context retrieval exceeded 2s threshold: {elapsed_time:.3f}s "
                    f"for user {user_id}, course {course_id}"
                )
            
            return context
            
        except Exception as e:
            # Complete failure - log error and return empty context
            elapsed_time = time.time() - start_time
            logger.error(
                f"Failed to retrieve user context for user {user_id}, course {course_id} "
                f"after {elapsed_time:.3f}s: {type(e).__name__}: {str(e)}", 
                exc_info=True
            )
            logger.warning(f"Returning empty context due to complete retrieval failure")
            return UserContext()
    
    def format_context_prompt(
        self,
        context: UserContext,
        user_message: str,
        material_context: Optional[str] = None
    ) -> str:
        """
        Format all context into an enhanced AI prompt.
        
        This method creates a structured prompt with clearly separated sections
        for user profile, academic info, chat history, and materials. Sections
        are omitted if the corresponding context is missing.
        
        Args:
            context: UserContext object with user's context
            user_message: The user's current question/message
            material_context: Optional material excerpts from RAG search
            
        Returns:
            Formatted prompt string ready for AI service
            
        Example:
            ```python
            prompt = context_service.format_context_prompt(
                context=user_context,
                user_message="Explain recursion",
                material_context="Chapter 5: Recursion..."
            )
            ```
        """
        logger.debug(
            f"Formatting context prompt: "
            f"has_preferences={context.has_preferences}, "
            f"has_academic={context.has_academic}, "
            f"has_history={context.has_history}, "
            f"has_materials={material_context is not None}"
        )
        
        prompt_parts = []
        
        # User Learning Profile Section
        if context.has_preferences:
            prefs = context.preferences
            prompt_parts.append("--- USER LEARNING PROFILE ---")
            prompt_parts.append(f"Detail Level: {prefs.detail_level} (0=brief, 1=detailed)")
            prompt_parts.append(f"Example Preference: {prefs.example_preference} (0=few examples, 1=many examples)")
            prompt_parts.append(f"Analogy Preference: {prefs.analogy_preference} (0=direct, 1=use analogies)")
            prompt_parts.append(f"Technical Language: {prefs.technical_language} (0=simple, 1=technical)")
            prompt_parts.append(f"Structure Preference: {prefs.structure_preference} (0=flexible, 1=structured)")
            prompt_parts.append(f"Visual Preference: {prefs.visual_preference} (0=text-only, 1=visual aids)")
            prompt_parts.append(f"Learning Pace: {prefs.learning_pace}")
            prompt_parts.append(f"Prior Experience: {prefs.prior_experience}")
            prompt_parts.append("")
            prompt_parts.append("Please adapt your response style to match these preferences.")
            prompt_parts.append("")
        elif not context.has_preferences:
            # Use default preferences
            logger.debug("Using default preferences in prompt")
            prompt_parts.append("--- USER LEARNING PROFILE ---")
            prompt_parts.append(f"Detail Level: {DEFAULT_PREFERENCES['detail_level']} (0=brief, 1=detailed)")
            prompt_parts.append(f"Example Preference: {DEFAULT_PREFERENCES['example_preference']} (0=few examples, 1=many examples)")
            prompt_parts.append(f"Analogy Preference: {DEFAULT_PREFERENCES['analogy_preference']} (0=direct, 1=use analogies)")
            prompt_parts.append(f"Technical Language: {DEFAULT_PREFERENCES['technical_language']} (0=simple, 1=technical)")
            prompt_parts.append(f"Structure Preference: {DEFAULT_PREFERENCES['structure_preference']} (0=flexible, 1=structured)")
            prompt_parts.append(f"Visual Preference: {DEFAULT_PREFERENCES['visual_preference']} (0=text-only, 1=visual aids)")
            prompt_parts.append(f"Learning Pace: {DEFAULT_PREFERENCES['learning_pace']}")
            prompt_parts.append(f"Prior Experience: {DEFAULT_PREFERENCES['prior_experience']}")
            prompt_parts.append("")
            prompt_parts.append("Please adapt your response style to match these preferences.")
            prompt_parts.append("")
        
        # Academic Profile Section
        if context.has_academic:
            academic = context.academic
            prompt_parts.append("--- ACADEMIC PROFILE ---")
            prompt_parts.append(f"Education Level: {', '.join(academic.grade)}")
            prompt_parts.append(f"Current Semester: {academic.semester} ({academic.semester_type} semester system)")
            if academic.subject:
                prompt_parts.append(f"Subjects: {', '.join(academic.subject)}")
            prompt_parts.append("")
            prompt_parts.append("Please tailor complexity and examples to this academic level.")
            prompt_parts.append("")
        
        # Previous Conversation Section
        if context.has_history:
            prompt_parts.append("--- PREVIOUS CONVERSATION ---")
            for msg in context.chat_history:
                role_label = "Student" if msg.role == "user" else "AI"
                prompt_parts.append(f"{role_label}: {msg.content}")
            prompt_parts.append("")
        
        # Relevant Course Materials Section
        if material_context:
            prompt_parts.append("--- RELEVANT COURSE MATERIALS ---")
            prompt_parts.append(material_context)
            prompt_parts.append("")
        
        # Current Question Section
        prompt_parts.append("--- CURRENT QUESTION ---")
        prompt_parts.append(user_message)
        
        # Join all parts into final prompt
        final_prompt = "\n".join(prompt_parts)
        
        # Log total context size
        logger.info(
            f"Context prompt formatted: {len(final_prompt)} characters, "
            f"sections included: "
            f"profile={'yes' if context.has_preferences else 'defaults'}, "
            f"academic={'yes' if context.has_academic else 'no'}, "
            f"history={'yes' if context.has_history else 'no'}, "
            f"materials={'yes' if material_context else 'no'}"
        )
        
        return final_prompt
