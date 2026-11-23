from pathlib import Path
from shutil import which
from subprocess import DEVNULL, PIPE, SubprocessError, run

from fastapi import HTTPException

IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


class OCRService:
    @staticmethod
    def recognize_image(content: bytes, executable: str) -> str:
        try:
            result = run(
                [executable, "stdin", "stdout"],
                input=content, stdout=PIPE, stderr=DEVNULL, timeout=30, check=True,
            )
        except (OSError, SubprocessError) as error:
            raise HTTPException(status_code=422, detail="Local OCR could not read this image.") from error
        return result.stdout.decode("utf-8", errors="replace").strip()

    def pages(self, path: Path, filename: str, mime_type: str):
        executable = which("tesseract")
        if mime_type == "application/pdf" or filename.lower().endswith(".pdf"):
            try:
                import pymupdf
            except ImportError as error:
                raise HTTPException(status_code=503, detail="Install PyMuPDF 1.24.3 or newer for PDF support.") from error
            found = False
            try:
                with pymupdf.open(path, filetype="pdf") as document:
                    if document.needs_pass:
                        raise HTTPException(status_code=422, detail="Upload an unlocked copy of this PDF.")
                    for number, page in enumerate(document, start=1):
                        text = page.get_text().strip()
                        if not text and executable:
                            scale = min(2, 2000 / max(page.rect.width, page.rect.height, 1))
                            image = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale)).tobytes("png")
                            text = self.recognize_image(image, executable)
                        if text:
                            found = True
                            yield number, text
            except (RuntimeError, ValueError) as error:
                raise HTTPException(status_code=422, detail="Could not read this PDF.") from error
            if not found and not executable:
                raise HTTPException(status_code=422, detail="This PDF needs OCR. Install Tesseract and retry.")
        elif mime_type in IMAGE_TYPES:
            if not executable:
                raise HTTPException(status_code=422, detail="Install Tesseract to read scans and images.")
            try:
                result = run([executable, str(path), "stdout"], stdout=PIPE, stderr=DEVNULL, timeout=30, check=True)
            except (OSError, SubprocessError) as error:
                raise HTTPException(status_code=422, detail="Local OCR could not read this image.") from error
            yield 0, result.stdout.decode("utf-8", errors="replace")
        elif mime_type.startswith("text/") or filename.lower().endswith((".txt", ".md")):
            with path.open(encoding="utf-8-sig", errors="replace") as source:
                for number, block in enumerate(iter(lambda: source.read(16000), ""), start=1):
                    yield -number, block
        else:
            raise HTTPException(status_code=422, detail="This file type is not supported.")


ocr_service = OCRService()
