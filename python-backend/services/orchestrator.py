"""
Orchestrator Service
Acts as the central "Brain" for the AI Agent.
Coordinates Intent Classification, Context Aggregation, Personality Injection, and Synthesis.
"""
import logging
import asyncio
from typing import Optional, List, Dict
from models.schemas import ChatRequest
from services.local_ai_service import local_ai_service
from services.context_service import ContextService
from services.service_manager import service_manager

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        self.context_service = ContextService()

    async def classify_intent(self, message: str) -> str:
        """
        Stage 1: Intent Classification
        Determines if the user's message requires course materials (ACADEMIC) or is just chat (CASUAL).
        """
        classification_prompt = (
            f"Classify the following user message into one of two categories:\n"
            f"1. ACADEMIC: Questions about facts, concepts, definitions, course materials, summaries, or specific study topics.\n"
            f"2. CASUAL: Greetings, small talk, jokes, personal questions not related to study materials, or general motivation.\n\n"
            f"User Message: \"{message}\"\n\n"
            f"Reply with ONLY the word 'ACADEMIC' or 'CASUAL'. Do not add punctuation."
        )
        
        try:
            # Quick call to Qwen/Llama
            response = await local_ai_service.generate_response(classification_prompt)
            intent = response.strip().upper()
            
            # Defensive check: if model output is messy, default to safest option
            if "ACADEMIC" in intent:
                return "ACADEMIC"
            return "CASUAL"
        except Exception as e:
            logger.warning(f"Intent classification failed, defaulting to ACADEMIC: {e}")
            return "ACADEMIC"

    def _get_formatting_rules(self) -> str:
        """
        Defines the strict formatting rules for AI output.
        """
        return (
            "\n**FORMATTING RULES** (STRICTLY FOLLOW):\n"
            "1. **Structure**: Use Markdown headings (###) to separate sections. Never use H1 (#) or H2 (##).\n"
            "2. **Readability**: Do not output walls of text. Break paragraphs often. Use bullet points for lists.\n"
            "3. **Emphasis**: Use **bold** for key concepts or definitions.\n"
            "4. **Citations**: If you use the provided Course Materials, explicitly cite them like: `(Source: Slide 4)` or `[Textbook Ch.2]`.\n"
            "5. **Math Formulas**: YOU MUST WRAP ALL MATH IN LATEX DELIMITERS.\n"
            "   - **Inline Math**: Use single dollar signs. Example: `The variable $x$ represents...`\n"
            "   - **Block Math**: Use double dollar signs. Example:\n"
            "     $$\n"
            "     \\text{Accuracy} = \\frac{\\text{TP} + \\text{TN}}{\\text{Total}}\n"
            "     $$\n"
            "   - DO NOT output plain text formulas like `Accuracy = ...` without delimiters.\n"
        )

    def build_persona_prompt(self, preferences: Optional[dict] = None) -> str:
        """
        Stage 3 (Part A): Personality Layer & Formatting
        Constructs the 'StudyMate' system persona based on user preferences.
        """
        # Base Persona
        persona = (
            "You are StudyMate, a supportive, encouraging, and friendly AI study buddy. "
            "Your goal is to help the student learn effectively. "
            "Be conversational and human-like. Use emojis occasionally if appropriate. 🌟\n"
        )

        # Inject Standard Formatting Rules
        persona += self._get_formatting_rules()

        # Dynamic Adaptation based on Preferences
        if preferences:
            # Learning Style
            style = preferences.get('learning_style', 'general')
            if style == 'visual':
                persona += (
                    "\n**VISUAL LEARNER INSTRUCTION**: "
                    "The user learns best visually. Since you cannot generate images, you MUST use:\n"
                    "- Markdown Tables for comparisons\n"
                    "- Bulleted lists for steps\n"
                    "- ASCII diagrams (e.g., `A -> B -> C`) for flows\n"
                    "- Vivid spatial analogies (e.g., 'Think of the memory heap like a stack of plates...')\n"
                )
            elif style == 'theoretical':
                persona += (
                    "\n**THEORETICAL LEARNER INSTRUCTION**: "
                    "Focus on 'first principles', 'why' things work, and precise definitions. "
                    "Be rigorous but keep the friendly tone.\n"
                )
            elif style == 'practical':
                persona += (
                    "\n**PRACTICAL LEARNER INSTRUCTION**: "
                    "Focus on real-world examples, use cases, and 'how-to' steps.\n"
                )

            # Tone
            tone = preferences.get('tone', 'encouraging')
            if tone == 'direct':
                persona += "\n**TONE**: Keep your responses concise and direct. Skip the fluff.\n"
            elif tone == 'socratic':
                persona += "\n**TONE**: Use the Socratic method. Ask guiding questions to help the user find the answer.\n"

        return persona

    async def process_chat_request(
        self, 
        user_id: str, 
        course_id: str, 
        chat_request: ChatRequest, 
        access_token: str
    ) -> str:
        """
        Main Orchestration Pipeline: 
        Intent -> Context Aggregation -> Prompt Engineering -> Generation
        """
        user_message = chat_request.message
        
        # --- STAGE 1: INTENT CLASSIFICATION ---
        intent = await self.classify_intent(user_message)
        logger.info(f"Orchestrator: Message classified as {intent}")

        # --- STAGE 2: CONTEXT AGGREGATION ---
        # 1. Always fetch User Context
        user_context = await self.context_service.get_user_context(
            user_id=user_id,
            course_id=course_id,
            access_token=access_token
        )

        material_context_str = None
        
        # 2. Conditionally fetch Course Materials
        if intent == "ACADEMIC" and course_id and course_id != "global":
            try:
                logger.info(f"Orchestrator: Executing Vector Search for course {course_id}")
                search_results = await service_manager.processing_service.search_materials(
                    course_id=course_id,
                    query=user_message,
                    limit=3
                )
                
                if search_results:
                    material_parts = []
                    for idx, res in enumerate(search_results, 1):
                        # Format source cleanly for the LLM
                        material_parts.append(f"--- Material {idx}: {res['name']} ---")
                        material_parts.append(f"{res['excerpt']}")
                        material_parts.append("") 
                    
                    material_context_str = "\n".join(material_parts)
                    logger.info(f"Orchestrator: Found {len(search_results)} relevant materials.")
                else:
                    logger.info("Orchestrator: No relevant materials found via vector search.")
            
            except Exception as e:
                logger.error(f"Orchestrator: RAG search failed: {e}")

        # --- STAGE 3: PROMPT ENGINEERING (FIXED) ---
        # 1. Build the Persona (Behavioral Instructions)
        pref_dict = user_context.preferences.model_dump() if user_context.has_preferences else None
        system_persona = self.build_persona_prompt(pref_dict)

        # 2. Format the Data Context
        data_context = self.context_service.format_context_prompt(
            context=user_context,
            user_message=user_message,
            material_context=material_context_str
        )

        # --- CRITICAL FIX: Use Alpaca Format ---
        # We put the Persona + Context into the 'Instruction' block
        # and the User Message into the 'Input' block.
        full_instruction = f"{system_persona}\n\nCONTEXT DATA:\n{data_context}"

        final_prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{full_instruction}

### Input:
{user_message}

### Response:
"""
        
        # --- STAGE 4: SYNTHESIS ---
        response_text = await local_ai_service.generate_response(
            message=final_prompt,
            history=None, # History is embedded in data_context
            attachments=chat_request.attachments
        )

        return response_text

# Global Instance
orchestrator = Orchestrator()