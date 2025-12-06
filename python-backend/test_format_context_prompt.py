"""
Test for format_context_prompt method.

This test verifies that the context prompt formatting works correctly
with various combinations of context data.
"""
import pytest
from services.context_service import ContextService
from models.schemas import UserContext, UserPreferences, AcademicInfo, Message
from constants import DEFAULT_PREFERENCES


def test_format_context_prompt_complete():
    """Test prompt formatting with all context present."""
    service = ContextService()
    
    # Create complete context
    context = UserContext(
        preferences=UserPreferences(
            detail_level=0.7,
            example_preference=0.8,
            analogy_preference=0.6,
            technical_language=0.5,
            structure_preference=0.7,
            visual_preference=0.4,
            learning_pace="moderate",
            prior_experience="intermediate"
        ),
        academic=AcademicInfo(
            grade=["Bachelor"],
            semester_type="double",
            semester=3,
            subject=["computer science", "english"]
        ),
        chat_history=[
            Message(role="user", content="What is recursion?"),
            Message(role="model", content="Recursion is when a function calls itself.")
        ],
        has_preferences=True,
        has_academic=True,
        has_history=True
    )
    
    user_message = "Can you give me an example?"
    material_context = "Chapter 5: Recursion\nRecursion is a programming technique..."
    
    # Format prompt
    prompt = service.format_context_prompt(context, user_message, material_context)
    
    # Verify all sections are present
    assert "--- USER LEARNING PROFILE ---" in prompt
    assert "Detail Level: 0.7" in prompt
    assert "Learning Pace: moderate" in prompt
    
    assert "--- ACADEMIC PROFILE ---" in prompt
    assert "Education Level: Bachelor" in prompt
    assert "Current Semester: 3 (double semester system)" in prompt
    assert "Subjects: computer science, english" in prompt
    
    assert "--- PREVIOUS CONVERSATION ---" in prompt
    assert "Student: What is recursion?" in prompt
    assert "AI: Recursion is when a function calls itself." in prompt
    
    assert "--- RELEVANT COURSE MATERIALS ---" in prompt
    assert "Chapter 5: Recursion" in prompt
    
    assert "--- CURRENT QUESTION ---" in prompt
    assert "Can you give me an example?" in prompt
    
    print("✓ Complete context prompt formatted correctly")


def test_format_context_prompt_no_preferences():
    """Test prompt formatting when preferences are missing (should use defaults)."""
    service = ContextService()
    
    # Context without preferences
    context = UserContext(
        preferences=None,
        academic=None,
        chat_history=[],
        has_preferences=False,
        has_academic=False,
        has_history=False
    )
    
    user_message = "Hello"
    
    # Format prompt
    prompt = service.format_context_prompt(context, user_message)
    
    # Verify default preferences are used
    assert "--- USER LEARNING PROFILE ---" in prompt
    assert f"Detail Level: {DEFAULT_PREFERENCES['detail_level']}" in prompt
    assert f"Learning Pace: {DEFAULT_PREFERENCES['learning_pace']}" in prompt
    
    # Verify academic section is omitted
    assert "--- ACADEMIC PROFILE ---" not in prompt
    
    # Verify history section is omitted
    assert "--- PREVIOUS CONVERSATION ---" not in prompt
    
    # Verify materials section is omitted
    assert "--- RELEVANT COURSE MATERIALS ---" not in prompt
    
    # Verify current question is present
    assert "--- CURRENT QUESTION ---" in prompt
    assert "Hello" in prompt
    
    print("✓ Prompt with defaults formatted correctly")


def test_format_context_prompt_partial():
    """Test prompt formatting with partial context (only academic)."""
    service = ContextService()
    
    # Context with only academic info
    context = UserContext(
        preferences=None,
        academic=AcademicInfo(
            grade=["Masters"],
            semester_type="tri",
            semester=2,
            subject=["economics"]
        ),
        chat_history=[],
        has_preferences=False,
        has_academic=True,
        has_history=False
    )
    
    user_message = "Explain supply and demand"
    
    # Format prompt
    prompt = service.format_context_prompt(context, user_message)
    
    # Verify default preferences are used
    assert "--- USER LEARNING PROFILE ---" in prompt
    
    # Verify academic section is present
    assert "--- ACADEMIC PROFILE ---" in prompt
    assert "Education Level: Masters" in prompt
    assert "Current Semester: 2 (tri semester system)" in prompt
    assert "Subjects: economics" in prompt
    
    # Verify history section is omitted
    assert "--- PREVIOUS CONVERSATION ---" not in prompt
    
    # Verify current question is present
    assert "--- CURRENT QUESTION ---" in prompt
    assert "Explain supply and demand" in prompt
    
    print("✓ Partial context prompt formatted correctly")


def test_format_context_prompt_with_history():
    """Test prompt formatting with chat history."""
    service = ContextService()
    
    # Context with history
    context = UserContext(
        preferences=None,
        academic=None,
        chat_history=[
            Message(role="user", content="First question"),
            Message(role="model", content="First answer"),
            Message(role="user", content="Second question"),
            Message(role="model", content="Second answer")
        ],
        has_preferences=False,
        has_academic=False,
        has_history=True
    )
    
    user_message = "Third question"
    
    # Format prompt
    prompt = service.format_context_prompt(context, user_message)
    
    # Verify history section is present
    assert "--- PREVIOUS CONVERSATION ---" in prompt
    assert "Student: First question" in prompt
    assert "AI: First answer" in prompt
    assert "Student: Second question" in prompt
    assert "AI: Second answer" in prompt
    
    # Verify current question is present
    assert "--- CURRENT QUESTION ---" in prompt
    assert "Third question" in prompt
    
    print("✓ Prompt with history formatted correctly")


def test_format_context_prompt_minimal():
    """Test prompt formatting with minimal context (just user message)."""
    service = ContextService()
    
    # Empty context
    context = UserContext()
    
    user_message = "Hello AI"
    
    # Format prompt
    prompt = service.format_context_prompt(context, user_message)
    
    # Verify default preferences are included
    assert "--- USER LEARNING PROFILE ---" in prompt
    
    # Verify current question is present
    assert "--- CURRENT QUESTION ---" in prompt
    assert "Hello AI" in prompt
    
    # Verify prompt is not empty
    assert len(prompt) > 0
    
    print("✓ Minimal context prompt formatted correctly")


if __name__ == "__main__":
    test_format_context_prompt_complete()
    test_format_context_prompt_no_preferences()
    test_format_context_prompt_partial()
    test_format_context_prompt_with_history()
    test_format_context_prompt_minimal()
    print("\n✅ All format_context_prompt tests passed!")
