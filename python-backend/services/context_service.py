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
        try:
            result = client.table("chat_history").select("history").eq("course_id", course_id).order("created_at", desc=False).execute()
            all_messages = []
            if result.data:
                for row in result.data:
                    history_array = row.get("history", [])
                    for msg_data in history_array:
                        try:
                            all_messages.append(Message(**msg_data))
                        except: continue
            return all_messages[-limit:] if len(all_messages) > limit else all_messages
        except Exception:
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
        Formats the DATA sections for the prompt.
        """
        prompt_parts = []
        
        # 1. User Profile Data
        prompt_parts.append("\n--- USER CONTEXT ---")
        if context.has_preferences:
            p = context.preferences
            prompt_parts.append(f"Learning Style: {p.learning_pace} pace, {p.visual_preference}/1 visual, {p.detail_level}/1 detail")
            prompt_parts.append(f"Expertise Level: {p.prior_experience}")
        
        if context.has_academic:
            a = context.academic
            prompt_parts.append(f"Academic Level: {', '.join(a.grade)}, Semester {a.semester}")
            if a.subject: prompt_parts.append(f"Subjects: {', '.join(a.subject)}")
        
        # 2. Materials (RAG)
        if material_context:
            prompt_parts.append("\n--- AVAILABLE COURSE MATERIALS (Use these to answer) ---")
            prompt_parts.append(material_context)
        
        # 3. Conversation History
        if context.has_history:
            prompt_parts.append("\n--- CONVERSATION HISTORY ---")
            for msg in context.chat_history:
                role = "Student" if msg.role == "user" else "StudyMate"
                prompt_parts.append(f"{role}: {msg.content}")
        
        # 4. The Request
        prompt_parts.append("\n--- LATEST REQUEST ---")
        prompt_parts.append(f"Student: {user_message}")
        prompt_parts.append("StudyMate (Respond in Markdown):") 
        
        return "\n".join(prompt_parts)