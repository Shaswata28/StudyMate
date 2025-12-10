"""
Context service for retrieving and formatting user context for AI chat.
"""
from typing import Optional, List
from supabase import Client
import logging
import asyncio

from models.schemas import (
    UserPreferences,
    AcademicInfo,
    UserContext,
    Message
)
from services.supabase_client import get_user_client

logger = logging.getLogger(__name__)

class ContextService:
    
    # ... (Keep get_preferences, get_academic_info, get_chat_history, get_user_context as they were) ...
    # Those retrieval methods don't affect formatting, only data fetching.

    async def get_preferences(self, user_id: str, client: Client) -> Optional[UserPreferences]:
        try:
            result = client.table("personalized").select("prefs").eq("id", user_id).single().execute()
            if result.data and result.data.get("prefs"):
                return UserPreferences(**result.data["prefs"])
            return None
        except Exception:
            return None
    
    async def get_academic_info(self, user_id: str, client: Client) -> Optional[AcademicInfo]:
        try:
            result = client.table("academic").select("grade, semester_type, semester, subject").eq("id", user_id).single().execute()
            if result.data:
                return AcademicInfo(**result.data)
            return None
        except Exception:
            return None
    
    async def get_chat_history(self, course_id: str, client: Client, limit: int = 10) -> List[Message]:
        """
        FIXED: Retrieve recent chat history with proper error handling.
        
        Improvements:
        - Better error handling and logging
        - Proper message ordering and limiting
        - Graceful degradation on failures
        """
        try:
            logger.info(f"Retrieving chat history for course {course_id}, limit: {limit}")
            
            # Get chat history ordered by creation time (most recent first for limiting)
            result = client.table("chat_history").select("history, created_at").eq("course_id", course_id).order("created_at", desc=True).execute()
            
            all_messages = []
            if result.data:
                logger.debug(f"Found {len(result.data)} chat history records")
                
                # Process records in reverse chronological order to get most recent messages first
                for row in result.data:
                    history_array = row.get("history", [])
                    if not isinstance(history_array, list):
                        logger.warning(f"Invalid history format in record: {type(history_array)}")
                        continue
                    
                    # Process messages in this record
                    for msg_data in history_array:
                        try:
                            if not isinstance(msg_data, dict):
                                logger.warning(f"Invalid message format: {type(msg_data)}")
                                continue
                            
                            # Validate required fields
                            if "role" not in msg_data or "content" not in msg_data:
                                logger.warning(f"Message missing required fields: {msg_data.keys()}")
                                continue
                            
                            message = Message(**msg_data)
                            all_messages.append(message)
                            
                            # Stop if we've reached the limit
                            if len(all_messages) >= limit:
                                break
                                
                        except Exception as e:
                            logger.warning(f"Failed to parse message: {e}")
                            continue
                    
                    # Stop if we've reached the limit
                    if len(all_messages) >= limit:
                        break
            
            # Reverse to get chronological order (oldest first)
            all_messages.reverse()
            
            logger.info(f"Retrieved {len(all_messages)} messages from chat history")
            return all_messages
            
        except Exception as e:
            logger.error(f"Failed to retrieve chat history for course {course_id}: {e}", exc_info=True)
            return []
    
    async def get_user_context(self, user_id: str, course_id: str, access_token: str, timeout: float = 2.0) -> UserContext:
        try:
            client = get_user_client(access_token)
            prefs, academic, history = await asyncio.gather(
                self.get_preferences(user_id, client),
                self.get_academic_info(user_id, client),
                self.get_chat_history(course_id, client, limit=10),
                return_exceptions=True
            )
            
            # Clean up exceptions
            if isinstance(prefs, Exception): prefs = None
            if isinstance(academic, Exception): academic = None
            if isinstance(history, Exception): history = []
            
            return UserContext(
                preferences=prefs,
                academic=academic,
                chat_history=history if isinstance(history, list) else [],
                has_preferences=prefs is not None,
                has_academic=academic is not None,
                has_history=len(history) > 0 if isinstance(history, list) else False
            )
        except Exception:
            return UserContext()

    def format_context_prompt(
        self,
        context: UserContext,
        user_message: str,
        material_context: Optional[str] = None
    ) -> str:
        """
        Format context prompt in proper Alpaca format for fine-tuned StudyMate model.
        
        The fine-tuned model expects strict Alpaca format:
        ### Instruction: (what to do)
        ### Input: (context + question)
        ### Response: (where model generates)
        """
        logger.debug("Formatting Alpaca context prompt for fine-tuned StudyMate model")
        
        # Build the instruction
        instruction_parts = ["You are StudyMate, a helpful AI study assistant."]
        
        # Add learning preferences to instruction if available
        if context.has_preferences and context.preferences:
            p = context.preferences
            instruction_parts.append(f"Adapt your response to the student's learning preferences: {p.learning_pace} pace, {p.prior_experience} experience level.")
        
        instruction = " ".join(instruction_parts)
        
        # Build the input section with all context
        input_parts = []
        
        # 1. Course Materials (highest priority)
        if material_context and material_context.strip():
            input_parts.append("Course Materials:")
            input_parts.append(material_context.strip())
            input_parts.append("")
            logger.debug("Added material context to Alpaca input")
        
        # 2. Academic Context
        if context.has_academic and context.academic:
            academic_info = []
            if context.academic.grade:
                academic_info.append(f"Grade Level: {', '.join(context.academic.grade)}")
            if context.academic.semester_type and context.academic.semester:
                academic_info.append(f"Semester: {context.academic.semester} ({context.academic.semester_type} system)")
            if context.academic.subject:
                academic_info.append(f"Subjects: {', '.join(context.academic.subject)}")
            
            if academic_info:
                input_parts.append("Student Academic Context:")
                input_parts.extend(academic_info)
                input_parts.append("")
                logger.debug("Added academic context to Alpaca input")
        
        # 3. Recent Conversation History
        if context.has_history and context.chat_history:
            recent_messages = context.chat_history[-3:] if len(context.chat_history) > 3 else context.chat_history
            if recent_messages:
                input_parts.append("Recent Conversation:")
                for msg in recent_messages:
                    role_display = "Student" if msg.role == "user" else "StudyMate"
                    content = msg.content[:150] + "..." if len(msg.content) > 150 else msg.content
                    input_parts.append(f"{role_display}: {content}")
                input_parts.append("")
                logger.debug(f"Added {len(recent_messages)} messages to Alpaca input")
        
        # 4. Current Question
        input_parts.append(f"Student Question: {user_message}")
        
        # Combine into proper Alpaca format
        alpaca_prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Input:
{chr(10).join(input_parts)}

### Response:
"""
        
        logger.info(f"Generated Alpaca context prompt with {len(alpaca_prompt)} characters")
        return alpaca_prompt