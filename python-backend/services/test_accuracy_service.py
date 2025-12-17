"""
Test Accuracy Service - Compares AI responses with test dataset responses.
Calculates similarity/accuracy when user questions match test dataset.
"""

import json
import logging
import os
from typing import Optional, Tuple
from difflib import SequenceMatcher
import re

logger = logging.getLogger(__name__)


class TestAccuracyService:
    """Service to compare AI responses against test dataset for accuracy measurement."""
    
    def __init__(self):
        self.test_data: list[dict] = []
        self.question_map: dict[str, str] = {}  # normalized_question -> expected_response
        self._load_test_dataset()
    
    def _load_test_dataset(self):
        """Load test dataset from JSONL file."""
        dataset_path = os.path.join(
            os.path.dirname(__file__), 
            "../../Dataset/dataset_core/TestingSamples.jsonl"
        )
        
        # Try alternative path if first doesn't exist
        if not os.path.exists(dataset_path):
            dataset_path = os.path.join(
                os.path.dirname(__file__),
                "../../../Dataset/dataset_core/TestingSamples.jsonl"
            )
        
        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entry = json.loads(line)
                        self.test_data.append(entry)
                        
                        # Extract user question and expected response
                        messages = entry.get("messages", [])
                        user_msg = None
                        assistant_msg = None
                        
                        for msg in messages:
                            if msg.get("role") == "user":
                                user_msg = msg.get("content", "")
                            elif msg.get("role") == "assistant":
                                assistant_msg = msg.get("content", "")
                        
                        if user_msg and assistant_msg:
                            normalized = self._normalize_text(user_msg)
                            self.question_map[normalized] = assistant_msg
            
            logger.info(f"Loaded {len(self.test_data)} test samples, {len(self.question_map)} questions indexed")
        
        except FileNotFoundError:
            logger.warning(f"Test dataset not found at {dataset_path}")
        except Exception as e:
            logger.error(f"Error loading test dataset: {e}")
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        return text
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using multiple methods."""
        # Normalize both texts
        norm1 = self._normalize_text(text1)
        norm2 = self._normalize_text(text2)
        
        # 1. Sequence matching (structural similarity)
        seq_ratio = SequenceMatcher(None, norm1, norm2).ratio()
        
        # 2. Word overlap (content similarity)
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if not words1 or not words2:
            word_overlap = 0.0
        else:
            intersection = words1 & words2
            union = words1 | words2
            word_overlap = len(intersection) / len(union) if union else 0.0
        
        # 3. Key phrase matching (important content)
        key_phrases_score = self._key_phrase_match(text1, text2)
        
        # Weighted average
        accuracy = (seq_ratio * 0.3) + (word_overlap * 0.4) + (key_phrases_score * 0.3)
        
        return round(accuracy * 100, 1)
    
    def _key_phrase_match(self, text1: str, text2: str) -> float:
        """Check for matching key phrases like code blocks, formulas, etc."""
        score = 0.0
        checks = 0
        
        # Check code blocks
        code1 = re.findall(r'```[\s\S]*?```', text1)
        code2 = re.findall(r'```[\s\S]*?```', text2)
        if code1 or code2:
            checks += 1
            if code1 and code2:
                # Compare code content
                code_content1 = ' '.join(code1)
                code_content2 = ' '.join(code2)
                score += SequenceMatcher(None, code_content1, code_content2).ratio()
        
        # Check for formulas/equations
        formula1 = re.findall(r'[A-Za-z]\s*=\s*[^,\n]+', text1)
        formula2 = re.findall(r'[A-Za-z]\s*=\s*[^,\n]+', text2)
        if formula1 or formula2:
            checks += 1
            if formula1 and formula2:
                score += len(set(formula1) & set(formula2)) / max(len(formula1), len(formula2))
        
        # Check bullet points/lists
        bullets1 = re.findall(r'[-*]\s+.+', text1)
        bullets2 = re.findall(r'[-*]\s+.+', text2)
        if bullets1 or bullets2:
            checks += 1
            if bullets1 and bullets2:
                score += min(len(bullets1), len(bullets2)) / max(len(bullets1), len(bullets2))
        
        return score / checks if checks > 0 else 0.5
    
    def find_matching_question(self, user_question: str) -> Optional[str]:
        """Find if user question matches any test dataset question."""
        normalized_query = self._normalize_text(user_question)
        
        # Exact match
        if normalized_query in self.question_map:
            return self.question_map[normalized_query]
        
        # Fuzzy match - find best match above threshold
        best_match = None
        best_score = 0.0
        threshold = 0.75  # 75% similarity required
        
        for stored_question, expected_response in self.question_map.items():
            score = SequenceMatcher(None, normalized_query, stored_question).ratio()
            if score > best_score and score >= threshold:
                best_score = score
                best_match = expected_response
        
        return best_match
    
    def evaluate_response(self, user_question: str, ai_response: str) -> Optional[dict]:
        """
        Evaluate AI response against test dataset.
        
        Returns:
            dict with accuracy info if question matches test data, None otherwise
        """
        expected_response = self.find_matching_question(user_question)
        
        if expected_response is None:
            return None
        
        accuracy = self._calculate_similarity(ai_response, expected_response)
        
        return {
            "is_test_question": True,
            "accuracy": accuracy,
            "expected_response": expected_response[:200] + "..." if len(expected_response) > 200 else expected_response
        }


# Global service instance
test_accuracy_service = TestAccuracyService()
