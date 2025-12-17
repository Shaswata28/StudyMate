# Corrected Approach - Model Input Format

## The Problem

Your model was **fine-tuned** with JSON structure as training metadata, but it expects **natural language prompts** during inference, not JSON strings.

### Training vs Inference

**During Training:**
```json
{
  "instruction": "Compare merge sort and quick sort",
  "input": {
    "academic_info": {...},
    "learning_preferences": {...},
    "rag_chunks": [{...}],
    "chat_history": [...]
  },
  "output": {
    "final_answer": "## Merge Sort vs Quick Sort..."
  }
}
```

**During Inference (What the model expects):**
```
Question: Compare merge sort and quick sort
```

OR with context:
```
Relevant course materials:
1. sorting_algorithms.pdf
   Merge sort is stable and preferred for linked lists...

Question: Compare merge sort and quick sort
```

## Current Issues

1. **Sending JSON as text** → Model treats it as literal text, gets confused
2. **num_predict 512** → Too short for detailed answers
3. **Hallucinating** → Model confused by JSON format, ignores system prompts
4. **Incomplete responses** → Cuts off mid-sentence due to low num_predict
5. **Previous question bleed** → Context contamination from malformed prompts

## Solution

### Option 1: Simple Natural Language (Recommended)

Send clean, natural language prompts with context embedded naturally:

```python
# In ai-brain/brain.py
final_prompt = f"""Relevant course materials:
1. {material_name}
   {excerpt}

Recent conversation:
Student: {previous_question}
Assistant: {previous_answer}

Question: {current_question}
"""
```

### Option 2: Keep JSON in Backend, Convert in Brain

- Backend sends JSON (for structure)
- Brain converts JSON → natural language prompt
- Model receives natural language

This is what I just implemented in the updated `brain.py`.

## Testing

Run the test script:
```bash
python test_model_format.py
```

Compare the three outputs:
- Test 1 (simple) should be clean
- Test 2 (with context) should incorporate materials
- Test 3 (JSON) will likely be confused

## Recommended Settings

```dockerfile
# Modelfile
parameter temperature 0.45
parameter top_p 0.9
parameter repeat_penalty 1.15
parameter num_ctx 4096
parameter num_predict 1024  # Increased from 512
```

## Next Steps

1. **Test the model** with `test_model_format.py`
2. **Update Modelfile** with `num_predict 1024`
3. **Rebuild model**: `ollama create studymate -f Modelfile.updated`
4. **Restart brain service**
5. **Test in app** - responses should be cleaner and complete

## Why This Happens

Fine-tuning with JSON metadata teaches the model:
- **What** to learn (preferences, academic level, etc.)
- **How** to respond (format, style, depth)

But during inference, the model expects:
- **Natural language input**
- The learned patterns kick in automatically

Sending JSON during inference confuses the model because it's trying to parse literal JSON text instead of answering the question.
