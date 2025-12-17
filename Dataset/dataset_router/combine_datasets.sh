#!/bin/bash
# Combine all router datasets into a single training file

echo "🔄 Combining router datasets..."

# Combine all JSONL files (excluding utility scripts)
cat academic.jsonl chitchat.jsonl contextual.jsonl debugging.jsonl safety.jsonl tricky.jsonl > combined_router.jsonl

# Count total examples
TOTAL=$(wc -l < combined_router.jsonl)

echo "✅ Combined dataset created: combined_router.jsonl"
echo "📊 Total examples: $TOTAL"
echo ""
echo "Breakdown:"
echo "  - academic.jsonl:    $(wc -l < academic.jsonl) examples"
echo "  - chitchat.jsonl:    $(wc -l < chitchat.jsonl) examples"
echo "  - contextual.jsonl:  $(wc -l < contextual.jsonl) examples"
echo "  - debugging.jsonl:   $(wc -l < debugging.jsonl) examples"
echo "  - safety.jsonl:      $(wc -l < safety.jsonl) examples"
echo "  - tricky.jsonl:      $(wc -l < tricky.jsonl) examples"
echo ""
echo "🎯 Ready for fine-tuning!"
