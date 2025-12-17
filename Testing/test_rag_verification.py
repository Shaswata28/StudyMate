"""
RAG System Verification Test
=============================
This test verifies that the AI is actually using RAG chunks in its responses.

Test Strategy:
1. Upload a material with unique, specific information
2. Ask a question that can ONLY be answered from that material
3. Verify the AI's response contains information from the RAG chunks
4. Test with and without RAG to confirm the difference
"""

import asyncio
import json
import logging
from uuid import uuid4
from services.material_processing_service import MaterialProcessingService
from services.context_service import ContextService
from services.ai_brain_client import AIBrainClient
from models.schemas import UserContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Unique test data that won't be in the model's training data
UNIQUE_TEST_CONTENT = """
Professor Zephyr's Quantum Computing Course - Lecture 7

Today we discuss the Zephyr-Quantum Algorithm (ZQA), a revolutionary approach 
to quantum error correction developed in 2024. The ZQA uses a unique 
three-phase process:

1. Entanglement Stabilization Phase (ESP): Uses 17 qubits in a hexagonal lattice
2. Error Detection Phase (EDP): Applies the Zephyr Transform with coefficient 0.847
3. Correction Phase (CP): Implements adaptive feedback using the Quantum Zephyr Gate

Key Formula: ZQA Efficiency = (ESP × 0.847) + (EDP × 1.23) - (CP × 0.5)

The algorithm achieves 99.7% error correction rate, which is 15% better than 
traditional surface codes. Professor Zephyr won the 2024 Quantum Innovation Award 
for this breakthrough.

Important: The Zephyr Transform coefficient MUST be exactly 0.847 for optimal results.
"""

CONTROL_QUESTION = "What is the Zephyr Transform coefficient in the ZQA algorithm?"
EXPECTED_ANSWER_FRAGMENT = "0.847"

async def test_rag_integration():
    """
    Main test function to verify RAG is working.
    """
    logger.info("=" * 80)
    logger.info("RAG SYSTEM VERIFICATION TEST")
    logger.info("=" * 80)
    
    # Initialize services
    processing_service = MaterialProcessingService()
    context_service = ContextService()
    ai_client = AIBrainClient()
    
    # Test course and user IDs (you'll need to replace with real ones)
    test_course_id = str(uuid4())
    test_user_id = str(uuid4())
    
    try:
        # ============================================================
        # STEP 1: Test WITHOUT RAG (baseline)
        # ============================================================
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: Testing AI WITHOUT RAG (Baseline)")
        logger.info("=" * 80)
        
        # Create empty context (no RAG chunks)
        empty_context = UserContext()
        
        # Format prompt without RAG
        prompt_without_rag = context_service.format_training_json(
            context=empty_context,
            user_message=CONTROL_QUESTION,
            search_results=None  # No RAG chunks
        )
        
        logger.info(f"\nPrompt structure (no RAG):")
        logger.info(f"  - RAG chunks: {len(prompt_without_rag['input']['rag_chunks'])}")
        
        # Send to AI
        logger.info("\nSending to AI...")
        response_without_rag = await ai_client.generate_response(
            json.dumps(prompt_without_rag)
        )
        
        logger.info(f"\n📝 AI Response WITHOUT RAG:")
        logger.info(f"{response_without_rag}")
        logger.info(f"\n✓ Contains expected answer: {EXPECTED_ANSWER_FRAGMENT in response_without_rag}")
        
        # ============================================================
        # STEP 2: Simulate RAG chunks
        # ============================================================
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: Testing AI WITH RAG")
        logger.info("=" * 80)
        
        # Create mock search results with our unique content
        mock_search_results = [
            {
                "material_id": "test-material-1",
                "name": "Professor Zephyr's Quantum Computing - Lecture 7",
                "excerpt": UNIQUE_TEST_CONTENT[:500],  # First 500 chars
                "similarity_score": 0.95,
                "file_type": "text"
            },
            {
                "material_id": "test-material-2",
                "name": "Quantum Algorithms Reference",
                "excerpt": "The Zephyr Transform uses coefficient 0.847 for optimal quantum error correction.",
                "similarity_score": 0.88,
                "file_type": "text"
            }
        ]
        
        # Format prompt WITH RAG
        prompt_with_rag = context_service.format_training_json(
            context=empty_context,
            user_message=CONTROL_QUESTION,
            search_results=mock_search_results
        )
        
        logger.info(f"\nPrompt structure (with RAG):")
        logger.info(f"  - RAG chunks: {len(prompt_with_rag['input']['rag_chunks'])}")
        logger.info(f"  - Total context length: {len(json.dumps(prompt_with_rag))} chars")
        
        # Log what the AI will receive
        logger.info(f"\n📦 RAG Chunks being sent to AI:")
        for i, chunk in enumerate(prompt_with_rag['input']['rag_chunks'], 1):
            logger.info(f"\n  Chunk {i}:")
            logger.info(f"    - Name: {chunk['name']}")
            logger.info(f"    - Similarity: {chunk['similarity_score']}")
            logger.info(f"    - Excerpt preview: {chunk['excerpt'][:100]}...")
        
        # Send to AI
        logger.info("\nSending to AI with RAG chunks...")
        response_with_rag = await ai_client.generate_response(
            json.dumps(prompt_with_rag)
        )
        
        logger.info(f"\n📝 AI Response WITH RAG:")
        logger.info(f"{response_with_rag}")
        logger.info(f"\n✓ Contains expected answer: {EXPECTED_ANSWER_FRAGMENT in response_with_rag}")
        
        # ============================================================
        # STEP 3: Analysis
        # ============================================================
        logger.info("\n" + "=" * 80)
        logger.info("ANALYSIS")
        logger.info("=" * 80)
        
        without_rag_has_answer = EXPECTED_ANSWER_FRAGMENT in response_without_rag
        with_rag_has_answer = EXPECTED_ANSWER_FRAGMENT in response_with_rag
        
        logger.info(f"\n📊 Results:")
        logger.info(f"  - Without RAG: {'✅ Found answer' if without_rag_has_answer else '❌ No answer'}")
        logger.info(f"  - With RAG: {'✅ Found answer' if with_rag_has_answer else '❌ No answer'}")
        
        if not without_rag_has_answer and with_rag_has_answer:
            logger.info("\n🎉 SUCCESS! RAG system is working correctly!")
            logger.info("   The AI could NOT answer without RAG but COULD answer with RAG.")
            logger.info("   This proves the AI is using the RAG chunks.")
            return True
        elif without_rag_has_answer and with_rag_has_answer:
            logger.warning("\n⚠️  INCONCLUSIVE: AI answered correctly in both cases.")
            logger.warning("   The question might be too easy or in the model's training data.")
            logger.warning("   Try a more specific/unique question.")
            return None
        elif not without_rag_has_answer and not with_rag_has_answer:
            logger.error("\n❌ PROBLEM: AI couldn't answer even WITH RAG!")
            logger.error("   Possible issues:")
            logger.error("   1. AI is not reading the RAG chunks")
            logger.error("   2. Prompt format is incorrect")
            logger.error("   3. RAG chunks are not being passed properly")
            return False
        else:  # with_rag but not without_rag
            logger.error("\n❌ STRANGE: AI answered WITHOUT RAG but not WITH RAG!")
            logger.error("   This suggests RAG might be interfering with responses.")
            return False
            
    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}", exc_info=True)
        return False


async def test_rag_prompt_inspection():
    """
    Inspect what the AI actually receives when RAG is enabled.
    """
    logger.info("\n" + "=" * 80)
    logger.info("RAG PROMPT INSPECTION")
    logger.info("=" * 80)
    
    context_service = ContextService()
    
    # Create sample RAG chunks
    sample_chunks = [
        {
            "material_id": "mat-1",
            "name": "Introduction to Python",
            "excerpt": "Python is a high-level programming language...",
            "similarity_score": 0.92,
            "file_type": "pdf"
        }
    ]
    
    # Format the prompt
    prompt = context_service.format_training_json(
        context=UserContext(),
        user_message="What is Python?",
        search_results=sample_chunks
    )
    
    logger.info("\n📋 Full prompt structure:")
    logger.info(json.dumps(prompt, indent=2))
    
    # Check what brain.py will do with this
    logger.info("\n🧠 How brain.py processes this:")
    logger.info("1. Receives JSON string")
    logger.info("2. Parses 'instruction' and 'input' fields")
    logger.info("3. Extracts 'rag_chunks' from input")
    logger.info("4. Builds natural language prompt with RAG context")
    
    # Simulate what brain.py does
    instruction = prompt["instruction"]
    input_data = prompt["input"]
    rag_chunks = input_data.get("rag_chunks", [])
    
    context_parts = []
    if rag_chunks:
        context_parts.append("Relevant course materials:")
        for idx, chunk in enumerate(rag_chunks[:3], 1):
            context_parts.append(
                f"\n{idx}. {chunk.get('name', 'Material')} "
                f"(relevance: {chunk.get('similarity_score', 0):.2f})"
            )
            excerpt = chunk.get('excerpt', '')[:300]
            context_parts.append(f"   {excerpt}...")
        context_parts.append("")
    
    final_prompt = "\n".join(context_parts) + f"\n\nQuestion: {instruction}"
    
    logger.info("\n📝 Final prompt sent to Ollama:")
    logger.info("-" * 80)
    logger.info(final_prompt)
    logger.info("-" * 80)


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("RAG VERIFICATION TEST SUITE")
    print("=" * 80)
    print("\nThis test will verify if your AI is actually using RAG chunks.")
    print("\nRunning tests...\n")
    
    # Run inspection first
    asyncio.run(test_rag_prompt_inspection())
    
    # Then run integration test
    result = asyncio.run(test_rag_integration())
    
    print("\n" + "=" * 80)
    if result is True:
        print("✅ RAG SYSTEM IS WORKING CORRECTLY")
    elif result is False:
        print("❌ RAG SYSTEM HAS ISSUES")
    else:
        print("⚠️  TEST RESULTS INCONCLUSIVE")
    print("=" * 80)
