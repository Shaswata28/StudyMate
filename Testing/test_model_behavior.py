#!/usr/bin/env python3
"""
Test to see if the model is following system prompts
"""
import ollama

print("=" * 60)
print("Testing StudyMate Model Behavior")
print("=" * 60)

# Test 1: Simple question - should NOT have emojis or follow-ups
print("\nTest 1: Simple Question")
print("-" * 60)

response = ollama.generate(
    model="studymate",
    prompt="What is a variable in programming?",
    options={
        "temperature": 0.45,
        "top_p": 0.9,
        "repeat_penalty": 1.15,
        "num_ctx": 4096,
        "num_predict": 512
    }
)

print(f"Response:\n{response['response']}\n")

# Check for violations
violations = []
if "😊" in response['response'] or "🚀" in response['response'] or any(emoji in response['response'] for emoji in ["😊", "🚀", "👍", "💻", "📱"]):
    violations.append("❌ Contains emojis (violates system prompt)")
else:
    print("✅ No emojis")

if "?" in response['response'][-100:]:  # Check last 100 chars for questions
    violations.append("❌ Asks follow-up questions (violates system prompt)")
else:
    print("✅ No follow-up questions")

if "Would you like" in response['response'] or "Do you want" in response['response'] or "Let me know" in response['response']:
    violations.append("❌ Contains chatty phrases (violates system prompt)")
else:
    print("✅ No chatty phrases")

if violations:
    print("\n⚠️  SYSTEM PROMPTS NOT WORKING:")
    for v in violations:
        print(f"  {v}")
    print("\n💡 Solution: The Modelfile system prompts are not being applied.")
    print("   This means the model needs to be recreated with the Modelfile.")
else:
    print("\n✅ Model is following system prompts correctly!")

print("\n" + "=" * 60)
print("Diagnosis:")
print("=" * 60)
if violations:
    print("The model is NOT respecting the Modelfile system prompts.")
    print("This happens when:")
    print("1. The model was created without the Modelfile")
    print("2. The Modelfile wasn't properly applied")
    print("3. The base model doesn't support system prompts")
    print("\nTo fix:")
    print("  ollama create studymate -f Modelfile.updated")
else:
    print("Model behavior is correct. Issue might be elsewhere.")
