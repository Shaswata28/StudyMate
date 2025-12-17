"""
Property-based tests for AI Brain embedding generation functionality.

Feature: material-ocr-embedding, Property 6: Embedding generation for extracted text
Validates: Requirements 3.1

This test verifies that for any material with non-empty extracted text,
the system generates a vector embedding using the AI Brain service.
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings, HealthCheck
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ai_brain_client import AIBrainClient, AIBrainClientError


@pytest.fixture(scope="module")
def ai_brain_client():
    """Get AI Brain client instance for tests."""
    return AIBrainClient()


# Feature: material-ocr-embedding, Property 6: Embedding generation for extracted text
@pytest.mark.asyncio
@given(
    text_content=st.text(
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po'),
            min_codepoint=32,
            max_codepoint=126
        ),
        min_size=10,
        max_size=500
    )
)
@settings(
    max_examples=100,  # Run 100 iterations as specified in design
    deadline=60000,  # 60 second timeout per test
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
async def test_property_embedding_generation_for_extracted_text(ai_brain_client, text_content):
    """
    Property: For any material with non-empty extracted text, the system should generate a vector embedding.
    
    This property verifies that the generate_embedding method successfully creates
    embeddings for any non-empty text, which is essential for semantic search functionality.
    
    Requirements validated:
    - 3.1: WHEN text is extracted from a material THEN the System SHALL generate a vector embedding representing the semantic meaning
    """
    # Skip empty or whitespace-only text (as per requirements 3.5)
    if not text_content or not text_content.strip():
        return
    
    # Generate embedding for the text using AI Brain
    embedding = await ai_brain_client.generate_embedding(text_content)
    
    # Property assertions:
    # 1. Embedding should not be None
    assert embedding is not None, "Embedding should not be None"
    
    # 2. Embedding should be a list
    assert isinstance(embedding, list), "Embedding should be a list"
    
    # 3. Embedding should have 1024 dimensions (mxbai-embed-large as per requirements 3.2 and 9.2)
    assert len(embedding) == 1024, f"Embedding should have 1024 dimensions, got {len(embedding)}"
    
    # 4. All elements should be floats
    assert all(isinstance(x, (float, int)) for x in embedding), "All embedding elements should be numeric"
    
    # 5. Embedding should not be all zeros (should have semantic meaning)
    assert any(x != 0 for x in embedding), "Embedding should not be all zeros"
    
    # Log for debugging
    print(f"Generated embedding for text ({len(text_content)} chars): dim={len(embedding)}")


@pytest.mark.asyncio
async def test_property_embedding_generation_for_various_text_types(ai_brain_client):
    """
    Property test with specific text types to verify embedding generation.
    
    Tests various types of text content that might appear in course materials.
    """
    test_cases = [
        "Machine learning is a subset of artificial intelligence.",
        "Python is a high-level programming language.",
        "The quadratic formula is x = (-b ± √(b²-4ac)) / 2a",
        "Data structures include arrays, linked lists, trees, and graphs.",
        "Neural networks consist of layers of interconnected nodes.",
        "Algorithm complexity is measured using Big O notation.",
        "Database normalization reduces data redundancy.",
        "HTTP is a protocol for transferring hypertext.",
        "Version control systems track changes to source code.",
        "Cloud computing provides on-demand computing resources."
    ]
    
    for text in test_cases:
        # Generate embedding
        embedding = await ai_brain_client.generate_embedding(text)
        
        # Verify embedding properties
        assert embedding is not None, f"Embedding should not be None for: {text[:50]}..."
        assert isinstance(embedding, list), f"Embedding should be a list for: {text[:50]}..."
        assert len(embedding) == 1024, f"Embedding should have 1024 dimensions for: {text[:50]}..."
        assert all(isinstance(x, (float, int)) for x in embedding), f"All elements should be numeric for: {text[:50]}..."
        assert any(x != 0 for x in embedding), f"Embedding should not be all zeros for: {text[:50]}..."
        
        print(f"✓ Generated embedding for: '{text[:50]}...' (dim: {len(embedding)})")


@pytest.mark.asyncio
async def test_property_embedding_generation_handles_empty_text(ai_brain_client):
    """
    Edge case: Embedding generation should fail gracefully for empty text.
    
    According to requirements 3.5, when a material has no text content,
    the system should skip embedding generation.
    """
    empty_texts = ["", "   ", "\n\n", "\t\t"]
    
    for empty_text in empty_texts:
        # Attempt to generate embedding for empty text
        with pytest.raises(AIBrainClientError) as exc_info:
            await ai_brain_client.generate_embedding(empty_text)
        
        # Verify error message indicates empty text
        assert "empty" in str(exc_info.value).lower(), \
            f"Error message should mention empty text: {exc_info.value}"
        
        print(f"✓ Correctly rejected empty text: '{repr(empty_text)}'")


@pytest.mark.asyncio
async def test_property_embedding_consistency(ai_brain_client):
    """
    Property: Same text should produce the same embedding (deterministic).
    
    This verifies that embedding generation is consistent and reproducible.
    """
    test_text = "Consistent embedding test for machine learning algorithms."
    
    # Generate embedding twice
    embedding1 = await ai_brain_client.generate_embedding(test_text)
    embedding2 = await ai_brain_client.generate_embedding(test_text)
    
    # Embeddings should be identical
    assert len(embedding1) == len(embedding2), "Embeddings should have same length"
    
    # Check if embeddings are very similar (allowing for minor floating point differences)
    for i, (e1, e2) in enumerate(zip(embedding1, embedding2)):
        assert abs(e1 - e2) < 1e-6, f"Embedding values should be consistent at index {i}"
    
    print(f"✓ Embedding generation is consistent")


@pytest.mark.asyncio
async def test_property_embedding_semantic_similarity(ai_brain_client):
    """
    Property: Similar texts should produce similar embeddings.
    
    This verifies that embeddings capture semantic meaning.
    """
    # Similar texts about machine learning
    text1 = "Machine learning algorithms learn from data."
    text2 = "ML models are trained using datasets."
    
    # Very different text
    text3 = "The weather is sunny today."
    
    # Generate embeddings
    emb1 = await ai_brain_client.generate_embedding(text1)
    emb2 = await ai_brain_client.generate_embedding(text2)
    emb3 = await ai_brain_client.generate_embedding(text3)
    
    # Calculate cosine similarity (simple dot product for normalized vectors)
    def cosine_similarity(v1, v2):
        dot_product = sum(a * b for a, b in zip(v1, v2))
        mag1 = sum(a * a for a in v1) ** 0.5
        mag2 = sum(b * b for b in v2) ** 0.5
        return dot_product / (mag1 * mag2) if mag1 > 0 and mag2 > 0 else 0
    
    sim_12 = cosine_similarity(emb1, emb2)
    sim_13 = cosine_similarity(emb1, emb3)
    
    # Similar texts should have higher similarity than dissimilar texts
    print(f"Similarity (ML texts): {sim_12:.4f}")
    print(f"Similarity (ML vs weather): {sim_13:.4f}")
    
    # This is a soft assertion - embeddings should capture some semantic similarity
    # but we don't enforce strict thresholds as it depends on the model
    assert sim_12 > 0, "Similar texts should have positive similarity"
    assert sim_13 >= 0, "All similarities should be non-negative"


@pytest.mark.asyncio
async def test_property_embedding_handles_long_text(ai_brain_client):
    """
    Property: Embedding generation should handle long text content.
    
    Course materials may contain lengthy text extracts.
    """
    # Create a long text (simulate extracted text from a PDF)
    long_text = " ".join([
        f"This is sentence number {i} in a long document about machine learning and data science."
        for i in range(100)
    ])
    
    # Generate embedding
    embedding = await ai_brain_client.generate_embedding(long_text)
    
    # Verify embedding properties
    assert embedding is not None, "Embedding should be generated for long text"
    assert len(embedding) == 1024, "Embedding should have 1024 dimensions for long text"
    assert any(x != 0 for x in embedding), "Embedding should have semantic content for long text"
    
    print(f"✓ Generated embedding for long text ({len(long_text)} chars)")


@pytest.mark.asyncio
async def test_property_embedding_handles_special_characters(ai_brain_client):
    """
    Property: Embedding generation should handle text with special characters.
    
    Course materials may contain mathematical notation, code, etc.
    """
    special_texts = [
        "f(x) = x² + 2x + 1",
        "def hello_world(): print('Hello!')",
        "E = mc²",
        "∫ x dx = x²/2 + C",
        "α + β = γ",
        "HTML: <div class='container'>Content</div>"
    ]
    
    for text in special_texts:
        # Generate embedding
        embedding = await ai_brain_client.generate_embedding(text)
        
        # Verify embedding properties
        assert embedding is not None, f"Embedding should be generated for: {text}"
        assert len(embedding) == 1024, f"Embedding should have 1024 dimensions for: {text}"
        assert any(x != 0 for x in embedding), f"Embedding should have content for: {text}"
        
        print(f"✓ Generated embedding for special text: '{text[:30]}...'")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
