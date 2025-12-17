# Proper Modelfile Setup for Fine-Tuned Models

## Why TEMPLATE Matters

For **fine-tuned models**, the TEMPLATE section is **critical** because:

1. **Base models** (like raw Qwen 2.5) → System prompts work directly
2. **Fine-tuned models** (like your StudyMate) → Need TEMPLATE to map prompts correctly

## Your Training Format

Your model was trained with this JSON structure:
```json
{
  "instruction": "What is X?",
  "input": {
    "academic_info": {...},
    "learning_preferences": {...},
    "rag_chunks": [...],
    "chat_history": []
  },
  "output": {
    "final_answer": "..."
  }
}
```

## Inference Format

During inference, we send:
```
Relevant course materials:
1. file.pdf (relevance: 0.95)
   excerpt text...

Question: What is X?
```

## The TEMPLATE's Job

The TEMPLATE tells Ollama how to format prompts before sending to the model:

```dockerfile
TEMPLATE """{{ if .System }}{{ .System }}
{{ end }}{{ .Prompt }}"""
```

This means:
1. If there's a SYSTEM prompt → include it
2. Then add the user's prompt
3. Model generates response

## Complete Modelfile Structure

```dockerfile
# 1. BASE MODEL
FROM ./studymate_3b_q4_k_m.gguf

# 2. PARAMETERS (match training)
PARAMETER num_ctx 4096
PARAMETER temperature 0.45
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.15
PARAMETER num_predict 1024

# 3. STOP SEQUENCES
PARAMETER stop "<|endoftext|>"

# 4. TEMPLATE (critical!)
TEMPLATE """{{ if .System }}{{ .System }}
{{ end }}{{ .Prompt }}"""

# 5. SYSTEM PROMPT (personality)
SYSTEM """You are StudyMate, a friendly AI study assistant..."""
```

## What Each Part Does

### FROM
Points to your fine-tuned .gguf file

### PARAMETER
- `num_ctx`: How much context to remember
- `temperature`: Creativity level (0.45 = focused)
- `top_p`: Word selection strategy
- `repeat_penalty`: Prevents loops
- `num_predict`: Max response length

### PARAMETER stop
Tells model when to stop generating

### TEMPLATE
**Most important for fine-tuned models!**
- Maps incoming prompts to model's expected format
- Without this, model gets confused

### SYSTEM
The "personality" - matches your training data's style

## Current Flow

```
User Question
    ↓
Backend (context_service.py)
    ↓
Sends JSON: {"instruction": "...", "input": {...}}
    ↓
AI Brain (brain.py)
    ↓
Converts to natural language:
"Relevant materials: ...
Question: ..."
    ↓
Ollama (with TEMPLATE)
    ↓
Applies SYSTEM prompt + user prompt
    ↓
Model generates response
    ↓
Returns to user
```

## Why Your Old Modelfile Didn't Work

**Old Modelfile:**
```dockerfile
from ./studymate_3b_q4_k_m.gguf
system You NEVER ask follow-up questions
parameter num_predict 512
```

**Problems:**
1. ❌ No TEMPLATE → Model doesn't know how to interpret prompts
2. ❌ System prompts contradict training data
3. ❌ num_predict too low (512 vs 1024)

**New Modelfile:**
```dockerfile
FROM ./studymate_3b_q4_k_m.gguf
PARAMETER num_predict 1024
TEMPLATE """{{ if .System }}{{ .System }}
{{ end }}{{ .Prompt }}"""
SYSTEM """You are StudyMate, friendly and helpful..."""
```

**Fixes:**
1. ✅ TEMPLATE maps prompts correctly
2. ✅ SYSTEM matches training personality
3. ✅ num_predict allows complete responses

## Testing

After rebuilding with new Modelfile:

```bash
ollama create studymate -f Modelfile.updated
```

Test:
```python
import ollama

response = ollama.generate(
    model="studymate",
    prompt="What is a variable in programming?"
)

print(response['response'])
```

**Expected:**
- Complete response (not cut off)
- Friendly tone with emojis
- Well-structured markdown
- Follow-up questions
- Examples and explanations

## Key Takeaway

For fine-tuned models:
- **TEMPLATE is mandatory** - tells Ollama how to format prompts
- **SYSTEM should match training** - don't contradict learned behavior
- **PARAMETERS should match training** - use same temp, top_p, etc.

Without TEMPLATE, the model receives raw prompts and gets confused about format.
