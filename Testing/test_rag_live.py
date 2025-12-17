"""
Live RAG Test - Test with actual API calls
This requires your backend to be running.
"""

import asyncio
import httpx
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

BACKEND_URL = "http://localhost:8000"
AI_BRAIN_URL = "http://localhost:8001"

async def test_live_rag():
    """
    Test RAG with actual API calls to verify end-to-end flow.
    """
    print("\n" + "=" * 80)
    print("LIVE RAG TEST")
    print("=" * 80)
    print("\nThis test will:")
    print("1. Check if AI Brain is responding")
    print("2. Send a prompt WITHOUT RAG chunks")
    print("3. Send a prompt WITH RAG chunks")
    print("4. Compare the responses")
    print("\n" + "=" * 80)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        # Step 1: Check AI Brain health
        print("\n📡 Step 1: Checking AI Brain service...")
        try:
            response = await client.get(f"{AI_BRAIN_URL}/")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ AI Brain is running")
                print(f"   - Core model: {data.get('core_model')}")
                print(f"   - Embedding model: {data.get('embedding_model')}")
            else:
                print(f"❌ AI Brain returned status {response.status_code}")
                return
        except Exception as e:
            print(f"❌ Cannot connect to AI Brain: {e}")
            print(f"   Make sure it's running on {AI_BRAIN_URL}")
            return
        
        # Step 2: Test WITHOUT RAG
        print("\n📝 Step 2: Testing WITHOUT RAG chunks...")
        
        prompt_no_rag = {
            "instruction": "What is the capital of France?",
            "input": {
                "academic_info": {
                    "grade": [],
                    "semester_type": "double",
                    "semester": 1,
                    "subject": []
                },
                "learning_preferences": {
                    "detail_level": 0.7,
                    "example_preference": 0.7,
                    "analogy_preference": 0.5,
                    "technical_language": 0.6,
                    "structure_preference": 0.8,
                    "visual_preference": 0.5,
                    "learning_pace": "moderate",
                    "prior_experience": "intermediate"
                },
                "rag_chunks": [],  # NO RAG
                "chat_history": []
            }
        }
        
        try:
            response = await client.post(
                f"{AI_BRAIN_URL}/router",
                data={"prompt": json.dumps(prompt_no_rag)}
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                print(f"✅ Response received ({len(response_text)} chars)")
                print(f"\n📄 AI Response WITHOUT RAG:")
                print("-" * 80)
                print(response_text)
                print("-" * 80)
            else:
                print(f"❌ Request failed: {response.status_code}")
                print(response.text)
                return
        except Exception as e:
            print(f"❌ Error: {e}")
            return
        
        # Step 3: Test WITH RAG
        print("\n📝 Step 3: Testing WITH RAG chunks...")
        
        prompt_with_rag = {
            "instruction": "What is the Zephyr Coefficient used in quantum computing?",
            "input": {
                "academic_info": {
                    "grade": [],
                    "semester_type": "double",
                    "semester": 1,
                    "subject": []
                },
                "learning_preferences": {
                    "detail_level": 0.7,
                    "example_preference": 0.7,
                    "analogy_preference": 0.5,
                    "technical_language": 0.6,
                    "structure_preference": 0.8,
                    "visual_preference": 0.5,
                    "learning_pace": "moderate",
                    "prior_experience": "intermediate"
                },
                "rag_chunks": [  # WITH RAG
                    {
                        "material_id": "test-123",
                        "name": "Quantum Computing Lecture Notes",
                        "excerpt": "The Zephyr Coefficient is a critical parameter in quantum error correction, with an optimal value of 0.847. This coefficient was discovered by Professor Zephyr in 2024 and is used in the Zephyr-Quantum Algorithm (ZQA).",
                        "similarity_score": 0.95,
                        "file_type": "pdf"
                    },
                    {
                        "material_id": "test-456",
                        "name": "Advanced Quantum Algorithms",
                        "excerpt": "When implementing the ZQA algorithm, ensure the Zephyr Coefficient is set to exactly 0.847 for optimal quantum gate fidelity. Deviations from this value can reduce error correction efficiency by up to 15%.",
                        "similarity_score": 0.89,
                        "file_type": "text"
                    }
                ],
                "chat_history": []
            }
        }
        
        try:
            response = await client.post(
                f"{AI_BRAIN_URL}/router",
                data={"prompt": json.dumps(prompt_with_rag)}
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = response.get("response", "")
                print(f"✅ Response received ({len(response_text)} chars)")
                print(f"\n📄 AI Response WITH RAG:")
                print("-" * 80)
                print(response_text)
                print("-" * 80)
                
                # Analysis
                print("\n" + "=" * 80)
                print("ANALYSIS")
                print("=" * 80)
                
                mentions_zephyr = "zephyr" in response_text.lower()
                mentions_coefficient = "0.847" in response_text
                mentions_material = any(keyword in response_text.lower() for keyword in ["lecture", "notes", "material"])
                
                print(f"\n✓ Mentions Zephyr: {mentions_zephyr}")
                print(f"✓ Mentions coefficient 0.847: {mentions_coefficient}")
                print(f"✓ References source material: {mentions_material}")
                
                if mentions_coefficient:
                    print("\n🎉 SUCCESS! The AI is using RAG chunks!")
                    print("   The response contains specific information from the RAG chunks.")
                elif mentions_zephyr:
                    print("\n⚠️  PARTIAL: AI mentions Zephyr but not the specific coefficient.")
                    print("   The AI might be using RAG but not extracting details correctly.")
                else:
                    print("\n❌ PROBLEM: AI doesn't seem to be using RAG chunks.")
                    print("   The response doesn't contain information from the provided materials.")
                    print("\n   Possible issues:")
                    print("   1. brain.py is not parsing rag_chunks correctly")
                    print("   2. The prompt format is not being recognized")
                    print("   3. The model is ignoring the context")
                
            else:
                print(f"❌ Request failed: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("\n🚀 Starting Live RAG Test...")
    print("\nMake sure both services are running:")
    print(f"  - Backend: {BACKEND_URL}")
    print(f"  - AI Brain: {AI_BRAIN_URL}")
    
    asyncio.run(test_live_rag())
