#!/usr/bin/env python3
"""
Test script to verify the correct input format for the fine-tuned StudyMate model.
"""
import ollama
import json

# Test 1: Simple question (how the model should be used)
print("=" * 60)
print("TEST 1: Simple Question")
print("=" * 60)

simple_prompt = "What is a data structure?"

response = ollama.generate(
    model="studymate",
    prompt=simple_prompt,
    options={
        "temperature": 0.45,
        "top_p": 0.9,
        "repeat_penalty": 1.15,
        "num_ctx": 4096,
        "num_predict": 512
    }
)

print(f"Prompt: {simple_prompt}")
print(f"\nResponse:\n{response['response']}")
print("\n")

# Test 2: Question with context
print("=" * 60)
print("TEST 2: Question with Context")
print("=" * 60)

context_prompt = """Relevant course materials:
1. sorting_algorithms.pdf (relevance: 0.95)
   Merge sort is stable and preferred for linked lists due to sequential access...

Question: Compare merge sort and quick sort."""

response = ollama.generate(
    model="studymate",
    prompt=context_prompt,
    options={
        "temperature": 0.45,
        "top_p": 0.9,
        "repeat_penalty": 1.15,
        "num_ctx": 4096,
        "num_predict": 512
    }
)

print(f"Prompt: {context_prompt[:100]}...")
print(f"\nResponse:\n{response['response']}")
print("\n")

# Test 3: JSON format (what we're currently sending - likely wrong)
print("=" * 60)
print("TEST 3: JSON Format (Current Approach)")
print("=" * 60)

json_prompt = json.dumps({
    "instruction": "What is a data structure?",
    "input": {
        "academic_info": {"grade": ["Bachelor"], "semester_type": "double", "semester": 1, "subject": []},
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
        "rag_chunks": [],
        "chat_history": []
    }
}, indent=2)

response = ollama.generate(
    model="studymate",
    prompt=json_prompt,
    options={
        "temperature": 0.45,
        "top_p": 0.9,
        "repeat_penalty": 1.15,
        "num_ctx": 4096,
        "num_predict": 512
    }
)

print(f"Prompt: {json_prompt[:100]}...")
print(f"\nResponse:\n{response['response']}")
print("\n")

print("=" * 60)
print("ANALYSIS")
print("=" * 60)
print("Compare the three responses above:")
print("- Test 1 should give a clean, direct answer")
print("- Test 2 should incorporate the context naturally")
print("- Test 3 will likely be confused or repeat the JSON")
print("\nThe model was trained WITH JSON metadata, but expects")
print("natural language prompts during inference.")
