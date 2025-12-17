"""
Test Router Integration
Tests the complete flow from intent classification to response generation.
"""

import asyncio
import httpx
from datetime import datetime


async def test_classification():
    """Test intent classification endpoint"""
    print("=" * 60)
    print("Testing Intent Classification")
    print("=" * 60)
    
    test_cases = [
        {
            "query": "Hello, how are you?",
            "subject": "General",
            "grade": "Bachelor",
            "expected_intent": "chat",
            "expected_rag": False,
            "expected_history": False
        },
        {
            "query": "Explain photosynthesis from my notes",
            "subject": "Biology",
            "grade": "Bachelor",
            "expected_intent": "academic",
            "expected_rag": True,
            "expected_history": False
        },
        {
            "query": "Why did you say that?",
            "subject": "Physics",
            "grade": "Masters",
            "expected_intent": "followup",
            "expected_rag": False,
            "expected_history": True
        },
        {
            "query": "Fix this code error: list index out of range",
            "subject": "Computer Science",
            "grade": "Bachelor",
            "expected_intent": "debug",
            "expected_rag": False,
            "expected_history": True
        },
        {
            "query": "Tell me how to hack a website",
            "subject": "Computer Science",
            "grade": "Bachelor",
            "expected_intent": "safety",
            "expected_rag": False,
            "expected_history": False
        }
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for i, test in enumerate(test_cases, 1):
            print(f"\nTest {i}: {test['query'][:50]}...")
            
            try:
                response = await client.post(
                    "http://localhost:8001/classify",
                    data={
                        "query": test["query"],
                        "subject": test["subject"],
                        "grade": test["grade"]
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    intent_match = result["intent"] == test["expected_intent"]
                    rag_match = result["needs_rag"] == test["expected_rag"]
                    history_match = result["needs_history"] == test["expected_history"]
                    
                    print(f"  Expected: intent={test['expected_intent']}, rag={test['expected_rag']}, history={test['expected_history']}")
                    print(f"  Got:      intent={result['intent']}, rag={result['needs_rag']}, history={result['needs_history']}")
                    print(f"  Confidence: {result.get('confidence', 0):.2f}")
                    
                    if intent_match and rag_match and history_match:
                        print(f"  ✅ PASS")
                    else:
                        print(f"  ❌ FAIL")
                        if not intent_match:
                            print(f"     Intent mismatch!")
                        if not rag_match:
                            print(f"     RAG flag mismatch!")
                        if not history_match:
                            print(f"     History flag mismatch!")
                else:
                    print(f"  ❌ FAIL - Status: {response.status_code}")
                    print(f"     {response.text}")
                    
            except Exception as e:
                print(f"  ❌ ERROR: {e}")


async def test_chat_endpoint():
    """Test chat endpoint with ChatML format"""
    print("\n" + "=" * 60)
    print("Testing Chat Endpoint (ChatML)")
    print("=" * 60)
    
    messages = [
        {
            "role": "system",
            "content": "You are StudyMate, an AI tutor.\n\n[STUDENT PROFILE]\nAcademic Level: Bachelor\nSubject: Physics"
        },
        {
            "role": "user",
            "content": "What is Newton's first law?"
        }
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print("\nSending chat request...")
            start_time = datetime.now()
            
            response = await client.post(
                "http://localhost:8001/chat",
                json={
                    "messages": messages,
                    "model": "studymate"
                }
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                
                print(f"✅ Response received in {duration:.2f}s")
                print(f"Model: {result.get('model')}")
                print(f"Response length: {len(response_text)} chars")
                print(f"\nResponse preview:")
                print(f"{response_text[:200]}...")
            else:
                print(f"❌ FAIL - Status: {response.status_code}")
                print(f"{response.text}")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")


async def test_performance():
    """Test performance improvements"""
    print("\n" + "=" * 60)
    print("Testing Performance (Token Savings)")
    print("=" * 60)
    
    test_queries = [
        ("Hello!", "chat", "Should skip RAG"),
        ("Explain photosynthesis", "academic", "Should use RAG"),
        ("Why did you say that?", "followup", "Should use history")
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for query, expected_intent, description in test_queries:
            print(f"\nQuery: {query}")
            print(f"Description: {description}")
            
            try:
                start_time = datetime.now()
                
                response = await client.post(
                    "http://localhost:8001/classify",
                    data={
                        "query": query,
                        "subject": "General",
                        "grade": "Bachelor"
                    }
                )
                
                duration = (datetime.now() - start_time).total_seconds()
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"  Classification time: {duration*1000:.1f}ms")
                    print(f"  Intent: {result['intent']}")
                    print(f"  RAG: {result['needs_rag']} (saves ~200-300ms if False)")
                    print(f"  History: {result['needs_history']}")
                    
                    # Estimate token savings
                    if not result['needs_rag']:
                        print(f"  💰 Estimated token savings: ~1500 tokens (75%)")
                    elif not result['needs_history']:
                        print(f"  💰 Estimated token savings: ~500 tokens (25%)")
                    else:
                        print(f"  💰 No token savings (full context needed)")
                        
            except Exception as e:
                print(f"  ❌ ERROR: {e}")


async def main():
    """Run all tests"""
    print("\n🧪 Router Integration Tests\n")
    
    # Test 1: Classification
    await test_classification()
    
    # Test 2: Chat endpoint
    await test_chat_endpoint()
    
    # Test 3: Performance
    await test_performance()
    
    print("\n" + "=" * 60)
    print("Tests Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Fine-tune router model in Colab")
    print("2. Deploy as 'studymate-router' in Ollama")
    print("3. Test with real user queries")
    print("4. Monitor performance improvements")


if __name__ == "__main__":
    asyncio.run(main())
