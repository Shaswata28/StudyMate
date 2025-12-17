"""
Context service for retrieving and formatting user context for AI chat.
Builds prompts matching the exact training format of the fine-tuned model.
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
    """
    Service for building context that matches the core model's training format.
    
    Training format:
    - System: "You are StudyMate. \n[PROFILE]\n- Subject: X\n- grade: Y\n\n[COURSE MATERIALS]\nSource 1: ..."
    - User: "question"
    - Assistant: "response"
    """

    async def get_preferences(self, user_id: str, client: Client) -> Optional[UserPreferences]:
        """Retrieve user preferences from database."""
        try:
            result = client.table("personalized").select("prefs").eq("id", user_id).single().execute()
            if result.data and result.data.get("prefs"):
                return UserPreferences(**result.data["prefs"])
            return None
        except Exception:
            return None
    
    async def get_academic_info(self, user_id: str, client: Client) -> Optional[AcademicInfo]:
        """Retrieve academic info from database."""
        try:
            result = client.table("academic").select("grade, semester_type, semester, subject").eq("id", user_id).single().execute()
            if result.data:
                return AcademicInfo(**result.data)
            return None
        except Exception:
            return None
    
    async def get_chat_history(self, course_id: str, client: Client, limit: int = 10) -> List[Message]:
        """Retrieve recent chat history."""
        try:
            logger.info(f"Retrieving chat history for course {course_id}, limit: {limit}")
            
            result = client.table("chat_history").select("history, created_at").eq("course_id", course_id).order("created_at", desc=True).execute()
            
            all_messages = []
            if result.data:
                for row in result.data:
                    history_array = row.get("history", [])
                    if not isinstance(history_array, list):
                        continue
                    
                    for msg_data in history_array:
                        try:
                            if not isinstance(msg_data, dict):
                                continue
                            if "role" not in msg_data or "content" not in msg_data:
                                continue
                            
                            message = Message(**msg_data)
                            all_messages.append(message)
                            
                            if len(all_messages) >= limit:
                                break
                        except Exception:
                            continue
                    
                    if len(all_messages) >= limit:
                        break
            
            all_messages.reverse()
            logger.info(f"Retrieved {len(all_messages)} messages from chat history")
            return all_messages
            
        except Exception as e:
            logger.error(f"Failed to retrieve chat history for course {course_id}: {e}", exc_info=True)
            return []
    
    async def get_user_context(self, user_id: str, course_id: str, access_token: str, timeout: float = 2.0) -> UserContext:
        """Retrieve all user context in parallel."""
        try:
            client = get_user_client(access_token)
            prefs, academic, history = await asyncio.gather(
                self.get_preferences(user_id, client),
                self.get_academic_info(user_id, client),
                self.get_chat_history(course_id, client, limit=10),
                return_exceptions=True
            )
            
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

    async def build_simple_context(
        self,
        user_id: str,
        user_message: str,
        access_token: str
    ) -> List[dict]:
        """
        Build simple ChatML context for global chat (no course/RAG).
        Matches training format exactly.
        
        Training format:
        System: "You are StudyMate. \n[PROFILE]\n- Subject: General\n- grade: Bachelor\n\n[COURSE MATERIALS]\nNone"
        """
        messages = []
        client = get_user_client(access_token)
        
        # Get academic info for profile
        academic = await self.get_academic_info(user_id, client)
        subject = academic.subject[0] if academic and academic.subject else "General"
        grade = academic.grade[0] if academic and academic.grade else "Bachelor"
        
        # Build system prompt (EXACT training format)
        system_content = f"You are StudyMate. \n[PROFILE]\n- Subject: {subject}\n- grade: {grade}\n\n[COURSE MATERIALS]\nNone"
        
        messages.append({
            "role": "system",
            "content": system_content
        })
        
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        logger.info(f"Built simple context: {len(messages)} messages")
        return messages

    async def build_rag_context(
        self,
        user_id: str,
        course_id: str,
        user_message: str,
        access_token: str,
        search_results: Optional[List[dict]] = None
    ) -> List[dict]:
        """
        Build ChatML context with RAG for course-specific chat.
        Matches training format exactly. No chat history to avoid hallucinations.
        
        Training format with RAG:
        System: "You are StudyMate. \n[PROFILE]\n- Subject: X\n- grade: Y\n\n[COURSE MATERIALS]\nSource 1: ..."
        """
        messages = []
        client = get_user_client(access_token)
        
        # Get academic info for profile
        academic = await self.get_academic_info(user_id, client)
        subject = academic.subject[0] if academic and academic.subject else "General"
        grade = academic.grade[0] if academic and academic.grade else "Bachelor"
        
        # Build course materials section
        if search_results and len(search_results) > 0:
            materials_parts = []
            for idx, result in enumerate(search_results[:3], 1):
                excerpt = result.get('excerpt', '')
                if len(excerpt) > 500:
                    excerpt = excerpt[:500]
                materials_parts.append(f"Source {idx}: {excerpt}")
            materials_content = "\n".join(materials_parts)
        else:
            materials_content = "None"
        
        # Build system prompt (EXACT training format)
        system_content = f"You are StudyMate. \n[PROFILE]\n- Subject: {subject}\n- grade: {grade}\n\n[COURSE MATERIALS]\n{materials_content}"
        
        messages.append({
            "role": "system",
            "content": system_content
        })
        
        # No chat history - causes hallucinations
        
        # Add current user query
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        logger.info(f"Built RAG context: {len(messages)} messages, materials: {len(search_results) if search_results else 0}")
        return messages

    # Keep old method for backward compatibility
    async def build_core_model_context(
        self,
        user_id: str,
        course_id: str,
        user_message: str,
        access_token: str,
        intent: dict,
        search_results: Optional[List[dict]] = None
    ) -> List[dict]:
        """
        Backward compatible method - delegates to build_rag_context.
        """
        return await self.build_rag_context(
            user_id=user_id,
            course_id=course_id,
            user_message=user_message,
            access_token=access_token,
            search_results=search_results
        )
