"""
Quick RAG Check - Simple verification that RAG chunks reach the AI
"""

import json
import logging
from services.context_service import ContextService
from models.schemas import UserContext

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def check_rag_formatting():
    """
    Quick check to see how RAG chunks are formatted in the prompt.
    """
    print("\n" + "=" * 80)
    print("QUICK RAG FORMATTING CHECK")
    print("=" * 80)
    
    context_service = ContextService()
    
    # Simulate search results with unique content
    test_search_results = [
        {
            "material_id": "test-123",
            "name": "Quantum Physics Chapter 5",
            "excerpt": "The Heisenberg Uncertainty Principle states that ΔxΔp ≥ ℏ/2, where Δx is position uncertainty and Δp is momentum uncertainty.",
            "similarity_score": 0.95,
            "file_type": "pdf"
        },
        {
            "material_id": "test-456",
            "name": "Quantum Mechanics Notes",
            "excerpt": "Werner Heisenberg formulated this principle in 1927, fundamentally changing our understanding of quantum measurements.",
            "similarity_score": 0.87,
            "file_type": "text"
        }
    ]
    
    test_question = "What is the Heisenberg Uncertainty Principle?"
    
    # Test 1: WITHOUT RAG
    print("\n" + "-" * 80)
    print("TEST 1: Prompt WITHOUT RAG chunks")
    print("-" * 80)
    
    prompt_no_rag = context_service.format_training_json(
        context=UserContext(),
        user_message=test_question,
        search_results=None
    )
    
    print(f"\nRAG chunks in prompt: {len(prompt_no_rag['input']['rag_chunks'])}")
    print(f"Prompt size: {len(json.dumps(prompt_no_rag))} characters")
    print(f"\nFull JSON structure:")
    print(json.dumps(prompt_no_rag, indent=2))
    
    # Test 2: WITH RAG
    print("\n" + "-" * 80)
    print("TEST 2: Prompt WITH RAG chunks")
    print("-" * 80)
    
    prompt_with_rag = context_service.format_training_json(
        context=UserContext(),
        user_message=test_question,
        search_results=test_search_results
    )
    
    print(f"\nRAG chunks in prompt: {len(prompt_with_rag['input']['rag_chunks'])}")
    print(f"Prompt size: {len(json.dumps(prompt_with_rag))} characters")
    print(f"\nFull JSON structure:")
    print(json.dumps(prompt_with_rag, indent=2))
    
    # Test 3: Simulate what brain.py does
    print("\n" + "-" * 80)
    print("TEST 3: What brain.py converts this to")
    print("-" * 80)
    
    # This is what brain.py does with the JSON
    instruction = prompt_with_rag["instruction"]
    input_data = prompt_with_rag["input"]
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
    
    print("\nFinal natural language prompt sent to Ollama:")
    print("=" * 80)
    print(final_prompt)
    print("=" * 80)
    
    # Analysis
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    
    has_rag_in_json = len(prompt_with_rag['input']['rag_chunks']) > 0
    has_rag_in_final = "Relevant course materials:" in final_prompt
    has_content = "Heisenberg" in final_prompt
    
    print(f"\n✓ RAG chunks in JSON: {has_rag_in_json}")
    print(f"✓ RAG context in final prompt: {has_rag_in_final}")
    print(f"✓ Actual content present: {has_content}")
    
    if has_rag_in_json and has_rag_in_final and has_content:
        print("\n🎉 SUCCESS! RAG chunks are properly formatted and included.")
        print("\nNext step: Test if the AI actually uses this information.")
        print("Run: python test_rag_verification.py")
        return True
    else:
        print("\n❌ PROBLEM! RAG chunks are not being formatted correctly.")
        if not has_rag_in_json:
            print("   - RAG chunks missing from JSON structure")
        if not has_rag_in_final:
            print("   - RAG context not in final prompt")
        if not has_content:
            print("   - Content not being included")
        return False


if __name__ == "__main__":
    check_rag_formatting()
