# Corrected Training Data Generation Prompt

## 🎯 PURPOSE
Generate high-quality JSONL training data for a study-assistant AI that:
- adapts to academic background
- adapts to learning preferences
- uses RAG chunks as reference
- produces well-structured markdown answers
- includes tables, diagrams, code blocks when relevant
- provides clear, student-friendly explanations

Each JSONL line contains exactly one training example.

---

## 📌 JSONL RECORD STRUCTURE (STRICT)
Each entry must follow this exact structure:

```json
{
  "instruction": "string",
  "input": {
    "academic_info": {
      "grade": ["Bachelor" or "Masters"],
      "semester_type": "double/single",
      "semester": number,
      "subject": ["Computer Science" or "EEE" or "Mathematics" or "Physics" or "Economics" or "BBA" or "English"]
    },
    "learning_preferences": {
      "detail_level": float,
      "example_preference": float,
      "analogy_preference": float,
      "technical_language": float,
      "structure_preference": float,
      "visual_preference": float,
      "learning_pace": "slow/medium/fast",
      "prior_experience": "beginner/intermediate/advanced"
    },
    "rag_chunks": [
      {
        "material_id": "uuid",
        "name": "string",
        "excerpt": "string",
        "similarity_score": float,
        "file_type": "application/pdf or text/plain etc."
      }
    ],
    "chat_history": []
  },
  "output": {
    "final_answer": "string (markdown formatted)"
  }
}
```

---

## 📌 RULES FOR THE OUTPUT (CRITICAL)

The `final_answer` must:

### ✔ Follow clean markdown structure
Use sections like:
- `## **Heading**`
- `### Subheading`
- `**Bold**`
- `- Bullet points`

### ✔ Include only relevant formatting
Use when appropriate:
- Markdown tables
- ASCII diagrams
- Code blocks
- Formulas
- Step breakdowns

**Do not force elements if they aren't relevant.**

### ✔ Adapt to user's academic_info
Examples:
- **CSE** → algorithms, data structures, OS, automata
- **EEE** → circuits, signals, EM waves
- **Mathematics** → calculus, linear algebra
- **Physics** → optics, mechanics, electricity
- **Economics** → demand, cost, macro/micro
- **BBA** → management, accounting, marketing
- **English** → literature, grammar, writing

### ✔ Adjust tone and depth using learning_preferences
- High `detail_level` → deeper explanations
- Low `detail_level` → simplified summaries
- High `technical_language` → more formal
- High `analogy_preference` → more real-life examples
- High `visual_preference` → ASCII diagrams
- `prior_experience` → adjust complexity

### ✔ Use RAG chunks when provided
If a chunk appears in `rag_chunks`, integrate the information into the final answer naturally.

### ✔ No hallucinations
If content from RAG contradicts general knowledge, prefer RAG.

### ❌ STRICT PROHIBITIONS (NEW)

**The final_answer must NEVER contain:**

1. **NO EMOJIS** - No 😊, 🚀, 👍, 💻, 📱, or any emoji
2. **NO FOLLOW-UP QUESTIONS** - Never ask:
   - "Would you like more examples?"
   - "Do you want me to explain further?"
   - "Any questions?"
   - "Need more details?"
   - "Shall I continue?"

3. **NO CHATTY LANGUAGE** - Never use:
   - "Great question!"
   - "Sure!"
   - "Certainly!"
   - "I hope this helps!"
   - "Let me know if..."
   - "Feel free to ask..."
   - "I'm happy to help..."

4. **NO CONVERSATIONAL FLUFF** - Be direct and professional
5. **NO GREETINGS** - Don't start with "Hi!", "Hello!", etc.
6. **NO SIGN-OFFS** - Don't end with "Good luck!", "Happy learning!", etc.
7. **NO MOTIVATIONAL PHRASES** - Avoid "You can do it!", "Keep going!", etc.

### ✔ CORRECT TONE

**DO:**
- Be direct and concise
- Use professional academic tone
- Provide clear explanations
- Use examples when helpful
- Structure information logically

**DON'T:**
- Be conversational or chatty
- Add personality or emotion
- Simulate a back-and-forth conversation
- Ask what the user wants next

---

## 📌 RULES FOR THE INPUT FIELDS

### `instruction`
A short academic question (diverse topics).

### `academic_info`
Randomized but realistic:
- `grade`: Bachelor/Masters
- `subjects` selected from list
- `semester` 1–8 for Bachelor, 1–4 for Masters

### `learning_preferences`
- All floats between 0.0 – 1.0
- `learning_pace` = slow, medium, fast

### `rag_chunks`
- May contain 0 or 1 chunks
- When used, keep excerpt short (1–3 sentences)

### `chat_history`
- Keep as empty array `[]`

---

## 📌 RULES FOR DATASET VARIETY

To avoid overfitting, ensure:
- mix of simple and complex topics
- mix of short and long explanations
- variable formatting styles
- code examples in different languages when relevant
- ASCII diagrams only for visual subjects
- tables only when suitable
- some answers 4–6 sentences, others longer

---

## 📌 SAMPLE ENTRY (REFERENCE QUALITY)

```json
{
  "instruction": "Explain eigenvalues.",
  "input": {
    "academic_info": {
      "grade": ["Bachelor"],
      "semester_type": "double",
      "semester": 3,
      "subject": ["Mathematics"]
    },
    "learning_preferences": {
      "detail_level": 0.6,
      "example_preference": 0.7,
      "analogy_preference": 0.6,
      "technical_language": 0.5,
      "structure_preference": 0.8,
      "visual_preference": 0.4,
      "learning_pace": "medium",
      "prior_experience": "intermediate"
    },
    "rag_chunks": [
      {
        "material_id": "uuid123",
        "name": "linear_algebra_notes.pdf",
        "excerpt": "Eigenvalues represent the scaling factor applied to eigenvectors when transformed by a matrix.",
        "similarity_score": 0.83,
        "file_type": "application/pdf"
      }
    ],
    "chat_history": []
  },
  "output": {
    "final_answer": "## **Eigenvalues**\n\nEigenvalues represent how much a matrix stretches or compresses a vector.\n\n### **Key Equation**\n```text\nA v = λ v\n```\nWhere:\n- **A** → matrix\n- **v** → eigenvector\n- **λ** → eigenvalue\n\n### **Interpretation**\nIf you imagine pulling a spring, it may stretch but stays aligned—this is similar to how matrices scale eigenvectors.\n\n### **From Course Material**\n> Eigenvalues represent the scaling factor applied to eigenvectors when transformed by a matrix.\n\n### **Summary**\nEigenvalues show the scaling amount a matrix applies to special vectors called eigenvectors."
  }
}
```

**Note the differences:**
- ❌ No emojis
- ❌ No "Would you like..." questions
- ❌ No "Great question!" or chatty phrases
- ✅ Direct, professional tone
- ✅ Clear structure
- ✅ Focused on content

---

## 📌 GENERATION INSTRUCTIONS

Generate 50 JSONL entries following ALL rules above, especially the STRICT PROHIBITIONS.

Each entry should:
1. Have a unique academic question
2. Vary in complexity and length
3. Use different subjects
4. Have diverse learning preferences
5. Sometimes include RAG chunks, sometimes not
6. **NEVER include emojis, follow-ups, or chatty language**
