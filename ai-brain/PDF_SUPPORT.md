# PDF OCR Support

## Overview

The AI Brain Service now supports **PDF document scanning** in addition to images. PDFs are automatically detected and processed page-by-page using DeepSeek OCR.

## How It Works

1. **Upload a PDF** - Send PDF file to `/router` endpoint (same as images)
2. **Automatic Detection** - Service detects PDF by file extension or content type
3. **Page-by-Page Processing** - Each page is converted to high-quality image (300 DPI)
4. **OCR Extraction** - DeepSeek OCR processes each page
5. **Combined Output** - All pages are combined with page markers

## Supported File Types

| Type | Extensions | Processing |
|------|-----------|------------|
| Images | .jpg, .jpeg, .png, .gif, .bmp, .webp | Single image OCR |
| PDFs | .pdf | Multi-page OCR |

## Example Usage

### Via API

```python
import requests

# Upload PDF for OCR
with open("document.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8001/router",
        data={"prompt": "Extract all text from this document"},
        files={"image": ("document.pdf", f, "application/pdf")}
    )

result = response.json()
print(result["response"])
```

### Output Format

```
--- Page 1 ---
[Extracted text from page 1]

--- Page 2 ---
[Extracted text from page 2]

--- Page 3 ---
[Extracted text from page 3]
```

## Features

✅ **Multi-page support** - Handles PDFs with any number of pages
✅ **High quality** - 300 DPI conversion for accurate OCR
✅ **Automatic detection** - No need to specify file type
✅ **Page markers** - Clear separation between pages
✅ **Progress logging** - See which page is being processed
✅ **Same endpoint** - Use the same `/router` endpoint as images

## Performance

- **Small PDFs** (1-5 pages): ~10-30 seconds
- **Medium PDFs** (6-20 pages): ~1-3 minutes
- **Large PDFs** (20+ pages): ~3-10 minutes

Processing time depends on:
- Number of pages
- Image complexity
- Text density
- GPU/CPU performance

## Limitations

⚠️ **Memory usage** - Large PDFs may use significant RAM
⚠️ **Processing time** - Each page takes ~5-10 seconds
⚠️ **Text-based PDFs** - For PDFs with selectable text, consider using a PDF text extractor instead (faster)

## Tips

1. **For text-based PDFs**: If the PDF has selectable text, you might want to extract text directly instead of OCR (much faster)
2. **For scanned PDFs**: OCR is perfect for scanned documents or images
3. **Large documents**: Consider splitting very large PDFs into smaller chunks
4. **Quality**: Higher quality scans = better OCR accuracy

## Technical Details

**PDF Processing Pipeline:**
```
PDF Upload
    ↓
Detect PDF (by extension/content-type)
    ↓
Open with PyMuPDF (fitz)
    ↓
For each page:
    - Convert to PNG (300 DPI)
    - Send to DeepSeek OCR
    - Extract text
    ↓
Combine all pages
    ↓
Return combined text
```

**Dependencies:**
- `PyMuPDF` (fitz) - PDF rendering
- `Pillow` - Image processing
- `DeepSeek OCR` - Text extraction

## Error Handling

The service handles common errors gracefully:
- **Corrupted PDFs**: Returns error message
- **Password-protected PDFs**: Returns error (not supported yet)
- **Invalid files**: Returns error message
- **Memory issues**: Logs error and fails gracefully

## Future Enhancements

Potential improvements:
- [ ] Password-protected PDF support
- [ ] Parallel page processing (faster)
- [ ] Direct text extraction for text-based PDFs
- [ ] Table detection and extraction
- [ ] Image extraction from PDFs
- [ ] PDF metadata extraction
