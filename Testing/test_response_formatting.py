"""
Response Formatting Diagnostic Tool
====================================
This script checks for common formatting issues in AI responses.
"""

import asyncio
import json
import logging
from services.ai_brain_client import AIBrainClient
from services.context_service import ContextService
from models.schemas import UserContext

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def test_response_formatting():
    """
    Test various scenarios to identify formatting issues.
    """
    print("\n" + "=" * 80)
    print("RESPONSE FORMATTING DIAGNOSTIC")
    print("=" * 80)
    
    ai_client = AIBrainClient()
    context_service = ContextService()
    
    test_cases = [
        {
            "name": "Simple Question",
            "message": "What is 2+2?",
            "rag_chunks": []
        },
        {
            "name": "Question with RAG",
            "message": "Explain quantum computing",
            "rag_chunks": [
                {
                    "material_id": "test-1",
                    "name": "Quantum Computing 101",
                    "excerpt": "Quantum computing uses qubits instead of classical bits. A qubit can be in superposition, representing both 0 and 1 simultaneously.",
                    "similarity_score": 0.95,
                    "file_type": "pdf"
                }
            ]
        },
        {
            "name": "Math Question",
            "message": "What is the quadratic formula?",
            "rag_chunks": []
        }
    ]
    
    for test_case in test_cases:
        print("\n" + "-" * 80)
        print(f"TEST: {test_case['name']}")
        print("-" * 80)
        
        # Format prompt
        prompt = context_service.format_training_json(
            context=UserContext(),
            user_message=test_case['message'],
            search_results=test_case['rag_chunks'] if test_case['rag_chunks'] else None
        )
        
        print(f"\n📤 Sending prompt:")
        print(f"   Question: {test_case['message']}")
        print(f"   RAG chunks: {len(test_case['rag_chunks'])}")
        
        try:
            # Get response
            response = await ai_client.generate_response(json.dumps(prompt))
            
            print(f"\n📥 Received response:")
            print(f"   Length: {len(response)} characters")
            print(f"   Lines: {len(response.split(chr(10)))}")
            
            # Check for common formatting issues
            issues = []
            
            # Issue 1: Extra whitespace
            if response.startswith(' ') or response.startswith('\n'):
                issues.append("⚠️  Response starts with whitespace")
            if response.endswith(' ') or response.endswith('\n\n\n'):
                issues.append("⚠️  Response ends with excessive whitespace")
            
            # Issue 2: JSON artifacts
            if response.startswith('{') or response.startswith('['):
                issues.append("❌ Response contains JSON structure (not plain text)")
            
            # Issue 3: Training format artifacts
            if '### Instruction:' in response or '### Response:' in response:
                issues.append("❌ Response contains training format headers")
            
            # Issue 4: Repeated content
            lines = response.split('\n')
            if len(lines) != len(set(lines)):
                issues.append("⚠️  Response contains repeated lines")
            
            # Issue 5: Incomplete response
            if response.endswith('...') or len(response) < 10:
                issues.append("⚠️  Response appears incomplete")
            
            # Issue 6: HTML/XML tags
            if '<' in response and '>' in response:
                issues.append("⚠️  Response contains HTML/XML tags")
            
            # Issue 7: Control characters
            if any(ord(c) < 32 and c not in '\n\r\t' for c in response):
                issues.append("⚠️  Response contains control characters")
            
            # Issue 8: Encoding issues
            if '�' in response:
                issues.append("❌ Response contains encoding errors (�)")
            
            if issues:
                print(f"\n🔍 Issues detected:")
                for issue in issues:
                    print(f"   {issue}")
            else:
                print(f"\n✅ No formatting issues detected")
            
            # Show response preview
            print(f"\n📄 Response preview (first 300 chars):")
            print("-" * 80)
            print(response[:300])
            if len(response) > 300:
                print("...")
            print("-" * 80)
            
            # Show response end
            if len(response) > 300:
                print(f"\n📄 Response end (last 100 chars):")
                print("-" * 80)
                print(response[-100:])
                print("-" * 80)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)


async def test_raw_api_response():
    """
    Test the raw API response to see what brain.py actually returns.
    """
    print("\n" + "=" * 80)
    print("RAW API RESPONSE TEST")
    print("=" * 80)
    
    import httpx
    
    # Test prompt
    prompt = {
        "instruction": "What is Python?",
        "input": {
            "academic_info": {"grade": [], "semester_type": "double", "semester": 1, "subject": []},
            "learning_preferences": {
                "detail_level": 0.7, "example_preference": 0.7, "analogy_preference": 0.5,
                "technical_language": 0.6, "structure_preference": 0.8, "visual_preference": 0.5,
                "learning_pace": "moderate", "prior_experience": "intermediate"
            },
            "rag_chunks": [],
            "chat_history": []
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print("\n📤 Sending request to AI Brain...")
            
            response = await client.post(
                "http://localhost:8001/router",
                data={"prompt": json.dumps(prompt)}
            )
            
            print(f"\n📥 Response status: {response.status_code}")
            print(f"📥 Response headers:")
            for key, value in response.headers.items():
                print(f"   {key}: {value}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n📦 Response JSON structure:")
                print(f"   Keys: {list(data.keys())}")
                print(f"   Model: {data.get('model', 'N/A')}")
                
                response_text = data.get('response', '')
                print(f"\n📄 Response text:")
                print(f"   Type: {type(response_text)}")
                print(f"   Length: {len(response_text)}")
                print(f"   First char code: {ord(response_text[0]) if response_text else 'N/A'}")
                print(f"   Last char code: {ord(response_text[-1]) if response_text else 'N/A'}")
                
                print(f"\n📄 Raw response (first 500 chars):")
                print("-" * 80)
                print(repr(response_text[:500]))
                print("-" * 80)
            else:
                print(f"\n❌ Error response:")
                print(response.text)
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🔍 Starting Response Formatting Diagnostics...")
    print("\nThis will test for common formatting issues:")
    print("  - Extra whitespace")
    print("  - JSON artifacts")
    print("  - Training format headers")
    print("  - Repeated content")
    print("  - Incomplete responses")
    print("  - HTML/XML tags")
    print("  - Control characters")
    print("  - Encoding errors")
    
    # Run raw API test first
    asyncio.run(test_raw_api_response())
    
    # Then run formatting tests
    asyncio.run(test_response_formatting())
