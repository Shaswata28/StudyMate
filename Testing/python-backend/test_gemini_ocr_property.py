"""
Property-based tests for Gemini OCR functionality.

Feature: material-ocr-embedding, Property 4: OCR extracts text from files
Validates: Requirements 2.1, 2.2

This test verifies that for any PDF or image material containing text,
the OCR process extracts text content that can be stored in the database.
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings, HealthCheck
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from services.ai_provider_factory import get_ai_provider, reset_provider
from services.ai_provider import AIProviderError


# Skip tests if Gemini is not configured
pytestmark = pytest.mark.skipif(
    config.AI_PROVIDER != "gemini" or not config.GEMINI_API_KEY,
    reason="Gemini provider not configured"
)


@pytest.fixture(scope="module")
def provider():
    """Get AI provider instance for tests."""
    reset_provider()
    return get_ai_provider()


def create_test_image_with_text(text: str, width: int = 400, height: int = 200) -> bytes:
    """
    Create a simple image with text for testing OCR.
    
    Args:
        text: Text to render on the image
        width: Image width in pixels
        height: Image height in pixels
    
    Returns:
        Image bytes in PNG format
    """
    # Create a white background image
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Try to use a default font, fall back to default if not available
    try:
        # Use a larger font size for better OCR
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        # Fall back to default font
        font = ImageFont.load_default()
    
    # Draw text in black
    text_position = (20, height // 2 - 20)
    draw.text(text_position, text, fill='black', font=font)
    
    # Convert to bytes
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()


# Feature: material-ocr-embedding, Property 4: OCR extracts text from files
@pytest.mark.asyncio
@given(
    text_content=st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'), min_codepoint=32, max_codepoint=126),
        min_size=5,
        max_size=50
    )
)
@settings(
    max_examples=10,  # Run 10 iterations (reduced from 100 for API cost considerations)
    deadline=60000,  # 60 second timeout per test
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
async def test_property_ocr_extracts_text_from_images(provider, text_content):
    """
    Property: For any image containing text, OCR should extract text content.
    
    This property verifies that the extract_text method successfully extracts
    text from images, which is a core requirement for the material processing pipeline.
    """
    # Skip empty or whitespace-only text
    if not text_content or not text_content.strip():
        return
    
    # Create test image with the generated text
    image_bytes = create_test_image_with_text(text_content)
    
    # Extract text using Gemini OCR
    extracted_text = await provider.extract_text(image_bytes, "image/png")
    
    # Property assertion: Extracted text should not be empty
    # Note: We don't require exact match due to OCR imperfections,
    # but we verify that SOME text was extracted
    assert extracted_text is not None, "Extracted text should not be None"
    assert isinstance(extracted_text, str), "Extracted text should be a string"
    assert len(extracted_text) > 0, f"OCR should extract text from image containing: '{text_content}'"


@pytest.mark.asyncio
async def test_property_ocr_extracts_text_from_simple_cases(provider):
    """
    Property test with specific known cases to verify OCR functionality.
    
    This test uses concrete examples to ensure the OCR works for common scenarios.
    """
    test_cases = [
        "Hello World",
        "Testing OCR 123",
        "Machine Learning",
        "Python Programming",
        "Data Science 2024"
    ]
    
    for text in test_cases:
        # Create test image
        image_bytes = create_test_image_with_text(text)
        
        # Extract text
        extracted_text = await provider.extract_text(image_bytes, "image/png")
        
        # Verify text was extracted
        assert extracted_text is not None, f"Extracted text should not be None for: {text}"
        assert isinstance(extracted_text, str), f"Extracted text should be a string for: {text}"
        assert len(extracted_text) > 0, f"OCR should extract text from image containing: '{text}'"
        
        # Optional: Check if extracted text contains some of the original words
        # (OCR might not be perfect, but should get something)
        print(f"Original: '{text}' -> Extracted: '{extracted_text}'")


@pytest.mark.asyncio
async def test_property_ocr_handles_empty_images(provider):
    """
    Edge case: OCR should handle images with no text gracefully.
    
    According to requirements 2.5, when a material contains no extractable text,
    the system should store an empty string and mark status as 'completed'.
    """
    # Create a blank white image with no text
    blank_image = Image.new('RGB', (400, 200), color='white')
    buffer = BytesIO()
    blank_image.save(buffer, format='PNG')
    blank_image_bytes = buffer.getvalue()
    
    # Extract text from blank image
    extracted_text = await provider.extract_text(blank_image_bytes, "image/png")
    
    # Should return empty string or minimal whitespace
    assert extracted_text is not None, "Extracted text should not be None"
    assert isinstance(extracted_text, str), "Extracted text should be a string"
    # Empty or whitespace-only is acceptable for blank images
    assert len(extracted_text.strip()) == 0, "Blank image should produce empty or whitespace-only text"


@pytest.mark.asyncio
async def test_property_ocr_handles_different_image_formats(provider):
    """
    Property: OCR should work with different image formats (PNG, JPEG, etc.).
    
    This verifies requirement 2.2 for image materials.
    """
    text = "Format Test 123"
    
    # Test PNG format
    png_image = create_test_image_with_text(text)
    png_extracted = await provider.extract_text(png_image, "image/png")
    assert len(png_extracted) > 0, "OCR should extract text from PNG images"
    
    # Test JPEG format
    image = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    draw.text((20, 80), text, fill='black', font=font)
    
    jpeg_buffer = BytesIO()
    image.save(jpeg_buffer, format='JPEG')
    jpeg_bytes = jpeg_buffer.getvalue()
    
    jpeg_extracted = await provider.extract_text(jpeg_bytes, "image/jpeg")
    assert len(jpeg_extracted) > 0, "OCR should extract text from JPEG images"


# Synchronous wrapper for hypothesis
def test_property_ocr_extracts_text_from_images_sync(provider):
    """Synchronous wrapper for the async property test."""
    @given(
        text_content=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'), min_codepoint=32, max_codepoint=126),
            min_size=5,
            max_size=50
        )
    )
    @settings(
        max_examples=10,
        deadline=60000,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
    )
    def run_test(text_content):
        asyncio.run(test_property_ocr_extracts_text_from_images(provider, text_content))
    
    run_test()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
