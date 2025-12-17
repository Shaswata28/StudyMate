"""
Test graceful degradation of context service.

This test verifies that the context service and chat endpoint work correctly
even when various context components are missing.

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from services.context_service import ContextService
from models.schemas import UserContext, UserPreferences, AcademicInfo, Message
from constants import DEFAULT_PREFERENCES


@pytest.fixture
def context_service():
    """Create a ContextService instance for testing."""
    return ContextService()


class TestGracefulDegradation:
    """Test suite for graceful degradation scenarios."""
    
    def test_format_prompt_with_no_preferences_uses_defaults(self, context_service):
        """
        Test that when preferences are missing, DEFAULT_PREFERENCES are used.
        
        Requirements: 8.1
        """
        # Given: UserContext with no preferences
        context = UserContext(
            preferences=None,
            academic=None,
            chat_history=[],
            has_preferences=False,
            has_academic=False,
            has_history=False
        )
        
        user_message = "What is recursion?"
        
        # When: format_context_prompt is called
        prompt = context_service.format_context_prompt(
            context=context,
            user_message=user_message,
            material_context=None
        )
        
        # Then: Prompt should include default preferences
        assert "--- USER LEARNING PROFILE ---" in prompt
        assert f"Detail Level: {DEFAULT_PREFERENCES['detail_level']}" in prompt
        assert f"Learning Pace: {DEFAULT_PREFERENCES['learning_pace']}" in prompt
        assert f"Prior Experience: {DEFAULT_PREFERENCES['prior_experience']}" in prompt
        assert "--- CURRENT QUESTION ---" in prompt
        assert user_message in prompt
    
    def test_format_prompt_with_no_academic_omits_section(self, context_service):
        """
        Test that when academic info is missing, academic section is omitted.
        
        Requirements: 8.2
        """
        # Given: UserContext with no academic info
        context = UserContext(
            preferences=None,
            academic=None,
            chat_history=[],
            has_preferences=False,
            has_academic=False,
            has_history=False
        )
        
        user_message = "Explain loops"
        
        # When: format_context_prompt is called
        prompt = context_service.format_context_prompt(
            context=context,
            user_message=user_message,
            material_context=None
        )
        
        # Then: Prompt should NOT include academic section
        assert "--- ACADEMIC PROFILE ---" not in prompt
        assert "Education Level:" not in prompt
        assert "Current Semester:" not in prompt
        # But should still include other sections
        assert "--- USER LEARNING PROFILE ---" in prompt
        assert "--- CURRENT QUESTION ---" in prompt
    
    def test_format_prompt_with_no_history_omits_section(self, context_service):
        """
        Test that when history is empty, history section is omitted.
        
        Requirements: 8.3
        """
        # Given: UserContext with no history
        context = UserContext(
            preferences=None,
            academic=None,
            chat_history=[],
            has_preferences=False,
            has_academic=False,
            has_history=False
        )
        
        user_message = "What is a variable?"
        
        # When: format_context_prompt is called
        prompt = context_service.format_context_prompt(
            context=context,
            user_message=user_message,
            material_context=None
        )
        
        # Then: Prompt should NOT include history section
        assert "--- PREVIOUS CONVERSATION ---" not in prompt
        # But should still include other sections
        assert "--- USER LEARNING PROFILE ---" in prompt
        assert "--- CURRENT QUESTION ---" in prompt
    
    def test_format_prompt_with_no_materials_omits_section(self, context_service):
        """
        Test that when materials are not found, materials section is omitted.
        
        Requirements: 8.4
        """
        # Given: UserContext with no materials
        context = UserContext(
            preferences=None,
            academic=None,
            chat_history=[],
            has_preferences=False,
            has_academic=False,
            has_history=False
        )
        
        user_message = "Explain functions"
        
        # When: format_context_prompt is called with no material_context
        prompt = context_service.format_context_prompt(
            context=context,
            user_message=user_message,
            material_context=None
        )
        
        # Then: Prompt should NOT include materials section
        assert "--- RELEVANT COURSE MATERIALS ---" not in prompt
        # But should still include other sections
        assert "--- USER LEARNING PROFILE ---" in prompt
        assert "--- CURRENT QUESTION ---" in prompt
    
    def test_format_prompt_with_all_context_missing(self, context_service):
        """
        Test that chat works even if all context is missing.
        
        Requirements: 8.5
        """
        # Given: UserContext with everything missing
        context = UserContext(
            preferences=None,
            academic=None,
            chat_history=[],
            has_preferences=False,
            has_academic=False,
            has_history=False
        )
        
        user_message = "Hello, can you help me?"
        
        # When: format_context_prompt is called with no context
        prompt = context_service.format_context_prompt(
            context=context,
            user_message=user_message,
            material_context=None
        )
        
        # Then: Prompt should still be valid with defaults and user message
        assert prompt is not None
        assert len(prompt) > 0
        assert "--- USER LEARNING PROFILE ---" in prompt  # Should use defaults
        assert "--- CURRENT QUESTION ---" in prompt
        assert user_message in prompt
        # Should NOT include optional sections
        assert "--- ACADEMIC PROFILE ---" not in prompt
        assert "--- PREVIOUS CONVERSATION ---" not in prompt
        assert "--- RELEVANT COURSE MATERIALS ---" not in prompt
    
    def test_format_prompt_with_complete_context(self, context_service):
        """
        Test that all sections are included when complete context is available.
        """
        # Given: UserContext with all components
        preferences = UserPreferences(
            detail_level=0.7,
            example_preference=0.8,
            analogy_preference=0.6,
            technical_language=0.5,
            structure_preference=0.7,
            visual_preference=0.4,
            learning_pace="fast",
            prior_experience="advanced"
        )
        
        academic = AcademicInfo(
            grade=["Bachelor"],
            semester_type="double",
            semester=3,
            subject=["computer science", "english"]
        )
        
        history = [
            Message(role="user", content="What is Python?"),
            Message(role="model", content="Python is a programming language.")
        ]
        
        context = UserContext(
            preferences=preferences,
            academic=academic,
            chat_history=history,
            has_preferences=True,
            has_academic=True,
            has_history=True
        )
        
        user_message = "Tell me more about Python"
        material_context = "[Material 1: Python Basics]\nPython is an interpreted language.\n(Relevance: 0.95)"
        
        # When: format_context_prompt is called with complete context
        prompt = context_service.format_context_prompt(
            context=context,
            user_message=user_message,
            material_context=material_context
        )
        
        # Then: All sections should be present
        assert "--- USER LEARNING PROFILE ---" in prompt
        assert "Detail Level: 0.7" in prompt
        assert "Learning Pace: fast" in prompt
        assert "--- ACADEMIC PROFILE ---" in prompt
        assert "Education Level: Bachelor" in prompt
        assert "--- PREVIOUS CONVERSATION ---" in prompt
        assert "Student: What is Python?" in prompt
        assert "AI: Python is a programming language." in prompt
        assert "--- RELEVANT COURSE MATERIALS ---" in prompt
        assert "Python Basics" in prompt
        assert "--- CURRENT QUESTION ---" in prompt
        assert user_message in prompt
    
    @pytest.mark.anyio
    async def test_get_user_context_returns_empty_on_complete_failure(self, context_service):
        """
        Test that get_user_context returns empty context on complete failure.
        
        Requirements: 8.5
        """
        # Given: Mock client that raises exceptions
        with patch('services.context_service.get_user_client') as mock_get_client:
            mock_get_client.side_effect = Exception("Database connection failed")
            
            # When: get_user_context is called
            context = await context_service.get_user_context(
                user_id="test-user-id",
                course_id="test-course-id",
                access_token="test-token"
            )
            
            # Then: Should return empty UserContext without raising exception
            assert context is not None
            assert isinstance(context, UserContext)
            assert context.has_preferences is False
            assert context.has_academic is False
            assert context.has_history is False
            assert len(context.chat_history) == 0
    
    def test_format_prompt_with_partial_context_preferences_only(self, context_service):
        """
        Test formatting with only preferences available.
        """
        # Given: UserContext with only preferences
        preferences = UserPreferences(
            detail_level=0.6,
            example_preference=0.5,
            analogy_preference=0.7,
            technical_language=0.4,
            structure_preference=0.5,
            visual_preference=0.6,
            learning_pace="moderate",
            prior_experience="intermediate"
        )
        
        context = UserContext(
            preferences=preferences,
            academic=None,
            chat_history=[],
            has_preferences=True,
            has_academic=False,
            has_history=False
        )
        
        user_message = "Explain arrays"
        
        # When: format_context_prompt is called
        prompt = context_service.format_context_prompt(
            context=context,
            user_message=user_message,
            material_context=None
        )
        
        # Then: Should include preferences but not academic or history
        assert "--- USER LEARNING PROFILE ---" in prompt
        assert "Detail Level: 0.6" in prompt
        assert "--- ACADEMIC PROFILE ---" not in prompt
        assert "--- PREVIOUS CONVERSATION ---" not in prompt
        assert "--- CURRENT QUESTION ---" in prompt
    
    def test_format_prompt_with_partial_context_academic_only(self, context_service):
        """
        Test formatting with only academic info available.
        """
        # Given: UserContext with only academic info
        academic = AcademicInfo(
            grade=["Masters"],
            semester_type="tri",
            semester=2,
            subject=["business administration"]
        )
        
        context = UserContext(
            preferences=None,
            academic=academic,
            chat_history=[],
            has_preferences=False,
            has_academic=True,
            has_history=False
        )
        
        user_message = "What is market segmentation?"
        
        # When: format_context_prompt is called
        prompt = context_service.format_context_prompt(
            context=context,
            user_message=user_message,
            material_context=None
        )
        
        # Then: Should include defaults for preferences and academic info
        assert "--- USER LEARNING PROFILE ---" in prompt  # Should use defaults
        assert f"Detail Level: {DEFAULT_PREFERENCES['detail_level']}" in prompt
        assert "--- ACADEMIC PROFILE ---" in prompt
        assert "Education Level: Masters" in prompt
        assert "--- PREVIOUS CONVERSATION ---" not in prompt
        assert "--- CURRENT QUESTION ---" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
