"""
Test script to verify enhanced ContextService methods.

This script tests:
- Enhanced get_chat_history() method with better error handling
- Enhanced format_context_prompt() method with better structure
- Property tests for chat history and prompt formatting

Requirements: 2.1, 2.3, 2.5, 1.3, 2.2, 5.1, 5.2, 5.3, 5.4
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'python-backend'))

from models.schemas import Message, UserContext, UserPreferences, AcademicInfo
from services.context_service import ContextService
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_enhanced_prompt_formatting():
    """Test enhanced prompt formatting with various context combinations."""
    print("\n" + "=" * 70)
    print("TEST: Enhanced prompt formatting")
    print("=" * 70)
    
    try:
        context_service = ContextService()
        
        # Test 1: Complete context with all components
        print("\n1. Testing with complete context")
        
        preferences = UserPreferences(
            detail_level=0.8,
            example_preference=0.7,
            analogy_preference=0.6,
            technical_language=0.9,
            structure_preference=0.8,
            visual_preference=0.5,
            learning_pace="moderate",
            prior_experience="intermediate"
        )
        
        academic = AcademicInfo(
            grade=["Bachelor"],
            semester_type="double",
            semester=3,
            subject=["Computer Science", "Mathematics"]
        )
        
        chat_history = [
            Message(role="user", content="What is machine learning?"),
            Message(role="model", content="Machine learning is a subset of AI that enables computers to learn from data."),
            Message(role="user", content="Can you give me an example?")
        ]
        
        context = UserContext(
            preferences=preferences,
            academic=academic,
            chat_history=chat_history,
            has_preferences=True,
            has_academic=True,
            has_history=True
        )
        
        material_context = "Chapter 3: Introduction to Neural Networks\nNeural networks are computational models inspired by biological neural networks."
        
        prompt = context_service.format_context_prompt(
            context=context,
            user_message="How do neural networks work?",
            material_context=material_context
        )
        
        print(f"Generated prompt length: {len(prompt)} characters")
        
        # Verify prompt structure
        required_sections = [
            "=== COURSE MATERIALS ===",
            "=== STUDENT ACADEMIC CONTEXT ===", 
            "=== LEARNING PREFERENCES ===",
            "=== RECENT CONVERSATION ===",
            "=== CURRENT QUESTION ==="
        ]
        
        for section in required_sections:
            if section not in prompt:
                print(f"❌ Missing section: {section}")
                return False
        
        print("✅ All required sections present")
        
        # Test 2: Minimal context (no materials, no history)
        print("\n2. Testing with minimal context")
        
        minimal_context = UserContext(
            preferences=None,
            academic=None,
            chat_history=[],
            has_preferences=False,
            has_academic=False,
            has_history=False
        )
        
        minimal_prompt = context_service.format_context_prompt(
            context=minimal_context,
            user_message="What is Python?",
            material_context=None
        )
        
        # Should only have current question section
        if "=== CURRENT QUESTION ===" not in minimal_prompt:
            print("❌ Missing current question section in minimal prompt")
            return False
        
        # Should not have other sections
        unwanted_sections = [
            "=== COURSE MATERIALS ===",
            "=== STUDENT ACADEMIC CONTEXT ===", 
            "=== LEARNING PREFERENCES ===",
            "=== RECENT CONVERSATION ==="
        ]
        
        for section in unwanted_sections:
            if section in minimal_prompt:
                print(f"❌ Unexpected section in minimal prompt: {section}")
                return False
        
        print("✅ Minimal prompt structure correct")
        
        # Test 3: Long message truncation
        print("\n3. Testing message truncation")
        
        long_message = "This is a very long message that should be truncated. " * 10  # 500+ chars
        long_history = [Message(role="user", content=long_message)]
        
        truncation_context = UserContext(
            preferences=None,
            academic=None,
            chat_history=long_history,
            has_preferences=False,
            has_academic=False,
            has_history=True
        )
        
        truncation_prompt = context_service.format_context_prompt(
            context=truncation_context,
            user_message="Short question",
            material_context=None
        )
        
        # Check if message was truncated (should end with "...")
        if "..." not in truncation_prompt:
            print("❌ Long message was not truncated")
            return False
        
        print("✅ Long message truncation works")
        
        print("\n✅ TEST PASSED: Enhanced prompt formatting works correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_chat_history_message_validation():
    """Test chat history retrieval with message validation."""
    print("\n" + "=" * 70)
    print("TEST: Chat history message validation")
    print("=" * 70)
    
    try:
        context_service = ContextService()
        
        # Mock client that returns various message formats
        class MockClient:
            def __init__(self, test_data):
                self.test_data = test_data
            
            def table(self, table_name):
                return self
            
            def select(self, fields):
                return self
            
            def eq(self, field, value):
                return self
            
            def order(self, field, desc=False):
                return self
            
            def execute(self):
                class MockResult:
                    def __init__(self, data):
                        self.data = data
                return MockResult(self.test_data)
        
        # Test 1: Valid messages
        print("\n1. Testing with valid messages")
        valid_data = [
            {
                "history": [
                    {"role": "user", "content": "Hello"},
                    {"role": "model", "content": "Hi there!"}
                ],
                "created_at": "2024-01-01T10:00:00Z"
            }
        ]
        
        mock_client = MockClient(valid_data)
        messages = await context_service.get_chat_history("course123", mock_client, limit=10)
        
        if len(messages) != 2:
            print(f"❌ Expected 2 messages, got {len(messages)}")
            return False
        
        if messages[0].role != "user" or messages[0].content != "Hello":
            print(f"❌ First message incorrect: {messages[0]}")
            return False
        
        print("✅ Valid messages processed correctly")
        
        # Test 2: Invalid message formats (should be filtered out)
        print("\n2. Testing with invalid message formats")
        invalid_data = [
            {
                "history": [
                    {"role": "user", "content": "Valid message"},
                    {"role": "invalid"},  # Missing content
                    {"content": "Missing role"},  # Missing role
                    "not a dict",  # Not a dictionary
                    {"role": "user", "content": "Another valid message"}
                ],
                "created_at": "2024-01-01T10:00:00Z"
            }
        ]
        
        mock_client = MockClient(invalid_data)
        messages = await context_service.get_chat_history("course123", mock_client, limit=10)
        
        # Should only get the 2 valid messages
        if len(messages) != 2:
            print(f"❌ Expected 2 valid messages, got {len(messages)}")
            return False
        
        print("✅ Invalid messages filtered out correctly")
        
        # Test 3: Empty/null history
        print("\n3. Testing with empty history")
        empty_data = [
            {
                "history": [],
                "created_at": "2024-01-01T10:00:00Z"
            }
        ]
        
        mock_client = MockClient(empty_data)
        messages = await context_service.get_chat_history("course123", mock_client, limit=10)
        
        if len(messages) != 0:
            print(f"❌ Expected 0 messages for empty history, got {len(messages)}")
            return False
        
        print("✅ Empty history handled correctly")
        
        # Test 4: Limit enforcement
        print("\n4. Testing limit enforcement")
        many_messages = [{"role": "user", "content": f"Message {i}"} for i in range(15)]
        limit_data = [
            {
                "history": many_messages,
                "created_at": "2024-01-01T10:00:00Z"
            }
        ]
        
        mock_client = MockClient(limit_data)
        messages = await context_service.get_chat_history("course123", mock_client, limit=5)
        
        if len(messages) != 5:
            print(f"❌ Expected 5 messages due to limit, got {len(messages)}")
            return False
        
        # Should get the last 5 messages (10-14)
        if messages[0].content != "Message 10":
            print(f"❌ Expected first message to be 'Message 10', got '{messages[0].content}'")
            return False
        
        print("✅ Limit enforcement works correctly")
        
        print("\n✅ TEST PASSED: Chat history message validation works correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("ENHANCED CONTEXT SERVICE TESTS")
    print("=" * 70)
    
    results = []
    
    # Test 1: Enhanced prompt formatting
    results.append(test_enhanced_prompt_formatting())
    
    # Test 2: Chat history message validation
    results.append(await test_chat_history_message_validation())
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)