"""
Test Response Cleaning Function
================================
Tests the clean_response function with various problematic inputs.
"""

import sys
sys.path.insert(0, 'ai-brain')

from brain import clean_response

def test_cleaning():
    """Test various formatting issues."""
    
    print("\n" + "=" * 80)
    print("RESPONSE CLEANING TESTS")
    print("=" * 80)
    
    test_cases = [
        {
            "name": "Training Header Artifact",
            "input": "### Instruction:\nWhat is Python?\n\n### Response:\nPython is a programming language.",
            "expected_contains": "Python is a programming language",
            "expected_not_contains": "### Response:"
        },
        {
            "name": "Extra Whitespace",
            "input": "\n\n  Python is a programming language.  \n\n\n",
            "expected": "Python is a programming language."
        },
        {
            "name": "Excessive Line Breaks",
            "input": "Python is great.\n\n\n\n\nIt's easy to learn.",
            "expected": "Python is great.\n\nIt's easy to learn."
        },
        {
            "name": "JSON Wrapper",
            "input": '{"answer": "Python is a programming language."}',
            "expected": "Python is a programming language."
        },
        {
            "name": "Multiple Headers",
            "input": "### User Context:\nSome context\n\n### Instruction:\nWhat is Python?\n\n### Response:\nPython is great.",
            "expected_contains": "Python is great",
            "expected_not_contains": "### User Context"
        },
        {
            "name": "Clean Response (No Changes)",
            "input": "Python is a high-level programming language.\n\nIt's great for beginners.",
            "expected": "Python is a high-level programming language.\n\nIt's great for beginners."
        },
        {
            "name": "Trailing Ellipsis",
            "input": "Python is a programming language\n...",
            "expected": "Python is a programming language"
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'-' * 80}")
        print(f"Test {i}: {test['name']}")
        print(f"{'-' * 80}")
        
        print(f"\n📥 Input ({len(test['input'])} chars):")
        print(repr(test['input'][:100]))
        
        result = clean_response(test['input'])
        
        print(f"\n📤 Output ({len(result)} chars):")
        print(repr(result[:100]))
        
        # Check expectations
        success = True
        
        if 'expected' in test:
            if result == test['expected']:
                print(f"\n✅ PASS: Output matches expected")
                passed += 1
            else:
                print(f"\n❌ FAIL: Output doesn't match expected")
                print(f"Expected: {repr(test['expected'][:100])}")
                print(f"Got:      {repr(result[:100])}")
                failed += 1
                success = False
        
        if 'expected_contains' in test:
            if test['expected_contains'] in result:
                print(f"\n✅ PASS: Output contains '{test['expected_contains']}'")
                if success:
                    passed += 1
            else:
                print(f"\n❌ FAIL: Output doesn't contain '{test['expected_contains']}'")
                failed += 1
                success = False
        
        if 'expected_not_contains' in test:
            if test['expected_not_contains'] not in result:
                print(f"\n✅ PASS: Output doesn't contain '{test['expected_not_contains']}'")
            else:
                print(f"\n❌ FAIL: Output still contains '{test['expected_not_contains']}'")
                if success:
                    failed += 1
                    passed -= 1
    
    print(f"\n" + "=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    success = test_cleaning()
    sys.exit(0 if success else 1)
