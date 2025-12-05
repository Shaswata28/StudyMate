"""
Property-based tests for AI Brain OCR functionality.

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

from services.ai_brain_client import AIBrainClient, AIBrainClientError


@pytest.fixture(scope="module")
def ai_brain_client():
    """Get AI Brain client instance for tests."""
    return AIBrainClient()


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
        font = ImageFont.truetype("arial.ttf", 32)
    except:
        try:
            # Try alternative font paths
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
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
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'),
            min_codepoint=32,
            max_codepoint=126
        ),
        min_size=5,
        max_size=50
    )
)
@settings(
    max_examples=100,  # Run 100 iterations as specified in design
    deadline=120000,  # 120 second timeout per test (OCR can be slow)
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
async def test_property_ocr_extracts_text_from_images(ai_brain_client, text_content):
    """
    Property: For any image containing text, OCR should extract text content.
    
    This property verifies that the extract_text method successfully extracts
    text from images, which is a core requirement for the material processing pipeline.
    
    Requirements validated:
    - 2.1: WHEN a PDF material is processed THEN the System SHALL extract all text content using OCR capabilities
    - 2.2: WHEN an image material is processed THEN the System SHALL extract visible text using OCR capabilities
    """
    # Skip empty or whitespace-only text
    if not text_content or not text_content.strip():
        return
    
    # Create test image with the generated text
    image_bytes = create_test_image_with_text(text_content)
    
    # Extract text using AI Brain OCR
    extracted_text = await ai_brain_client.extract_text(
        file_data=image_bytes,
        filename="test_image.png"
    )
    
    # Property assertion: Extracted text should not be empty
    # Note: We don't require exact match due to OCR imperfections,
    # but we verify that SOME text was extracted
    assert extracted_text is not None, "Extracted text should not be None"
    assert isinstance(extracted_text, str), "Extracted text should be a string"
    assert len(extracted_text) > 0, f"OCR should extract text from image containing: '{text_content}'"
    
    # Log for debugging
    print(f"Original: '{text_content}' -> Extracted: '{extracted_text[:100]}...'")


@pytest.mark.asyncio
async def test_property_ocr_extracts_text_from_simple_cases(ai_brain_client):
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
        extracted_text = await ai_brain_client.extract_text(
            file_data=image_bytes,
            filename="test_image.png"
        )
        
        # Verify text was extracted
        assert extracted_text is not None, f"Extracted text should not be None for: {text}"
        assert isinstance(extracted_text, str), f"Extracted text should be a string for: {text}"
        assert len(extracted_text) > 0, f"OCR should extract text from image containing: '{text}'"
        
        # Log results
        print(f"Original: '{text}' -> Extracted: '{extracted_text}'")


@pytest.mark.asyncio
async def test_property_ocr_handles_empty_images(ai_brain_client):
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
    extracted_text = await ai_brain_client.extract_text(
        file_data=blank_image_bytes,
        filename="blank_image.png"
    )
    
    # Should return a string (possibly empty or whitespace)
    assert extracted_text is not None, "Extracted text should not be None"
    assert isinstance(extracted_text, str), "Extracted text should be a string"
    # Empty or whitespace-only is acceptable for blank images
    print(f"Blank image extracted text: '{extracted_text}'")


@pytest.mark.asyncio
async def test_property_ocr_handles_different_image_formats(ai_brain_client):
    """
    Property: OCR should work with different image formats (PNG, JPEG, etc.).
    
    This verifies requirement 2.2 for image materials.
    """
    text = "Format Test 123"
    
    # Test PNG format
    png_image = create_test_image_with_text(text)
    png_extracted = await ai_brain_client.extract_text(
        file_data=png_image,
        filename="test.png"
    )
    assert len(png_extracted) > 0, "OCR should extract text from PNG images"
    print(f"PNG extraction: '{png_extracted}'")
    
    # Test JPEG format
    image = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 32)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        except:
            font = ImageFont.load_default()
    draw.text((20, 80), text, fill='black', font=font)
    
    jpeg_buffer = BytesIO()
    image.save(jpeg_buffer, format='JPEG')
    jpeg_bytes = jpeg_buffer.getvalue()
    
    jpeg_extracted = await ai_brain_client.extract_text(
        file_data=jpeg_bytes,
        filename="test.jpg"
    )
    assert len(jpeg_extracted) > 0, "OCR should extract text from JPEG images"
    print(f"JPEG extraction: '{jpeg_extracted}'")


# This test is already covered by the async version above
# The sync wrapper is not needed since pytest-asyncio handles async tests with hypothesis


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
