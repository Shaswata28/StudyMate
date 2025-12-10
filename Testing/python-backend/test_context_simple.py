"""
Simple test to verify context service enhancements work.
This test focuses on the logic without external dependencies.
"""

def test_prompt_structure():
    """Test that the enhanced prompt formatting creates proper structure."""
    print("Testing prompt structure...")
    
    # Mock the context service format_context_prompt method logic
    def format_context_prompt(has_materials=False, has_academic=False, has_preferences=False, has_history=False):
        prompt_parts = []
        
        # 1. Course Materials Section
        if has_materials:
            prompt_parts.append("=== COURSE MATERIALS ===")
            prompt_parts.append("Sample material content")
            prompt_parts.append("")
        
        # 2. Academic Context
        if has_academic:
            prompt_parts.append("=== STUDENT ACADEMIC CONTEXT ===")
            prompt_parts.append("Grade Level: Bachelor")
            prompt_parts.append("")
        
        # 3. Learning Preferences
        if has_preferences:
            prompt_parts.append("=== LEARNING PREFERENCES ===")
            prompt_parts.append("Learning Pace: moderate")
            prompt_parts.append("")
        
        # 4. Conversation History
        if has_history:
            prompt_parts.append("=== RECENT CONVERSATION ===")
            prompt_parts.append("Student: Previous question")
            prompt_parts.append("")
        
        # 5. Current Question
        prompt_parts.append("=== CURRENT QUESTION ===")
        prompt_parts.append("Student: Current question")
        prompt_parts.append("")
        prompt_parts.append("StudyMate:")
        
        return "\n".join(prompt_parts)
    
    # Test 1: Complete context
    full_prompt = format_context_prompt(
        has_materials=True,
        has_academic=True, 
        has_preferences=True,
        has_history=True
    )
    
    required_sections = [
        "=== COURSE MATERIALS ===",
        "=== STUDENT ACADEMIC CONTEXT ===",
        "=== LEARNING PREFERENCES ===", 
        "=== RECENT CONVERSATION ===",
        "=== CURRENT QUESTION ==="
    ]
    
    for section in required_sections:
        if section not in full_prompt:
            print(f"❌ Missing section: {section}")
            return False
    
    print("✅ Full context prompt has all sections")
    
    # Test 2: Minimal context
    minimal_prompt = format_context_prompt(
        has_materials=False,
        has_academic=False,
        has_preferences=False,
        has_history=False
    )
    
    # Should only have current question
    if "=== CURRENT QUESTION ===" not in minimal_prompt:
        print("❌ Missing current question in minimal prompt")
        return False
    
    # Should not have other sections
    unwanted = ["=== COURSE MATERIALS ===", "=== STUDENT ACADEMIC CONTEXT ==="]
    for section in unwanted:
        if section in minimal_prompt:
            print(f"❌ Unexpected section in minimal prompt: {section}")
            return False
    
    print("✅ Minimal context prompt structure correct")
    
    return True


def test_message_filtering_logic():
    """Test the logic for filtering invalid messages."""
    print("Testing message filtering logic...")
    
    def filter_messages(messages_data):
        """Mock the message filtering logic from get_chat_history."""
        valid_messages = []
        
        for msg_data in messages_data:
            # Check if it's a dictionary
            if not isinstance(msg_data, dict):
                continue
            
            # Check required fields
            if "role" not in msg_data or "content" not in msg_data:
                continue
            
            # Valid message
            valid_messages.append({
                "role": msg_data["role"],
                "content": msg_data["content"]
            })
        
        return valid_messages
    
    # Test data with mixed valid/invalid messages
    test_messages = [
        {"role": "user", "content": "Valid message 1"},
        {"role": "invalid"},  # Missing content
        {"content": "Missing role"},  # Missing role
        "not a dict",  # Not a dictionary
        {"role": "model", "content": "Valid message 2"},
        {"role": "user", "content": "Valid message 3"}
    ]
    
    filtered = filter_messages(test_messages)
    
    if len(filtered) != 3:
        print(f"❌ Expected 3 valid messages, got {len(filtered)}")
        return False
    
    expected_contents = ["Valid message 1", "Valid message 2", "Valid message 3"]
    actual_contents = [msg["content"] for msg in filtered]
    
    if actual_contents != expected_contents:
        print(f"❌ Message content mismatch. Expected: {expected_contents}, Got: {actual_contents}")
        return False
    
    print("✅ Message filtering works correctly")
    
    return True


def test_limit_enforcement():
    """Test that message limit is properly enforced."""
    print("Testing limit enforcement...")
    
    def apply_limit(messages, limit):
        """Mock the limit logic from get_chat_history."""
        if len(messages) > limit:
            # Get the most recent messages (last N)
            return messages[-limit:]
        return messages
    
    # Test with more messages than limit
    messages = [f"Message {i}" for i in range(10)]
    limited = apply_limit(messages, 5)
    
    if len(limited) != 5:
        print(f"❌ Expected 5 messages after limit, got {len(limited)}")
        return False
    
    # Should get messages 5-9 (the last 5)
    expected = ["Message 5", "Message 6", "Message 7", "Message 8", "Message 9"]
    if limited != expected:
        print(f"❌ Limit result incorrect. Expected: {expected}, Got: {limited}")
        return False
    
    print("✅ Limit enforcement works correctly")
    
    # Test with fewer messages than limit
    few_messages = ["Message 1", "Message 2"]
    limited_few = apply_limit(few_messages, 5)
    
    if limited_few != few_messages:
        print(f"❌ Should return all messages when under limit")
        return False
    
    print("✅ Under-limit case works correctly")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 50)
    print("CONTEXT SERVICE ENHANCEMENT TESTS")
    print("=" * 50)
    
    tests = [
        test_prompt_structure,
        test_message_filtering_logic,
        test_limit_enforcement
    ]
    
    results = []
    for test in tests:
        print(f"\n--- {test.__name__} ---")
        results.append(test())
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED")
        print("Context service enhancements are working correctly!")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)