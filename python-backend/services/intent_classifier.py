"""
Intent Classifier Service
Classifies user queries using fine-tuned Gemma 3 270M router model.
"""

import logging
import httpx
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    Service for classifying user query intent using fine-tuned router model.
    Determines what context components are needed for each query.
    """
    
    def __init__(self, brain_url: str = "http://localhost:8001"):
        self.brain_url = brain_url
        self.client = httpx.AsyncClient(timeout=5.0)  # Fast timeout for classification
        logger.info(f"Intent classifier initialized with brain URL: {self.brain_url}")
    
    async def classify(
        self,
        query: str,
        subject: str = "General",
        grade: str = "Bachelor"
    ) -> Dict:
        """
        Classify user query intent using fine-tuned router model.
        
        Args:
            query: User's question/message
            subject: Academic subject (e.g., "Physics", "Computer Science")
            grade: Academic level (e.g., "Bachelor", "Masters")
        
        Returns:
            {
                "intent": "academic" | "chat" | "debug" | "followup" | "safety",
                "needs_rag": bool,
                "needs_history": bool,
                "confidence": float
            }
        """
        try:
            logger.info(f"Classifying query: {query[:50]}...")
            
            response = await self.client.post(
                f"{self.brain_url}/classify",
                data={
                    "query": query,
                    "subject": subject,
                    "grade": grade
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Classification failed with status {response.status_code}: {response.text}")
                return self._safe_default()
            
            result = response.json()
            
            # Validate response structure
            if not isinstance(result, dict):
                logger.error(f"Invalid classification response type: {type(result)}")
                return self._safe_default()
            
            # Ensure required fields exist
            intent = result.get("intent", "academic")
            needs_rag = result.get("needs_rag", True)
            needs_history = result.get("needs_history", True)
            confidence = result.get("confidence", 0.5)
            
            logger.info(
                f"Classification result - Intent: {intent}, "
                f"RAG: {needs_rag}, History: {needs_history}, "
                f"Confidence: {confidence:.2f}"
            )
            
            return {
                "intent": intent,
                "needs_rag": needs_rag,
                "needs_history": needs_history,
                "confidence": confidence
            }
            
        except httpx.TimeoutException:
            logger.warning("Intent classification timed out - using safe defaults")
            return self._safe_default()
        
        except httpx.ConnectError as e:
            logger.error(f"Cannot connect to brain service for classification: {e}")
            return self._safe_default()
        
        except Exception as e:
            logger.error(f"Intent classification error: {e}", exc_info=True)
            return self._safe_default()
    
    def _safe_default(self) -> Dict:
        """
        Return safe default classification when classification fails.
        Assumes academic intent with full context to avoid missing information.
        """
        return {
            "intent": "academic",
            "needs_rag": True,
            "needs_history": True,
            "confidence": 0.0
        }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global instance
intent_classifier = IntentClassifier()
