"""
extractor.py - Multi-format Document and Image Text Extractor
Supports PDF (digital and scanned via PyMuPDF/pypdf) and Image OCR (Tesseract + PIL).
"""
import os
import io
import re
from typing import Tuple, Optional
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

# PDF libraries
try:
    import pymupdf  # PyMuPDF modern import
    PYMUPDF_AVAILABLE = True
except ImportError:
    try:
        import fitz as pymupdf
        PYMUPDF_AVAILABLE = True
    except ImportError:
        PYMUPDF_AVAILABLE = False

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

# OCR library
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False


def find_tesseract_path() -> Optional[str]:
    """
    Auto-detects Tesseract OCR executable on Windows and Linux/Mac.
    """
    try:
        import shutil
        cmd = shutil.which("tesseract")
        if cmd:
            return cmd
    except Exception:
        pass

    windows_candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe")
    ]
    for path in windows_candidates:
        if os.path.isfile(path):
            return path

    return None


def configure_tesseract(custom_path: Optional[str] = None) -> bool:
    """
    Sets pytesseract command path if available.
    """
    if not PYTESSERACT_AVAILABLE:
        return False

    if custom_path and os.path.isfile(custom_path):
        pytesseract.pytesseract.tesseract_cmd = custom_path
        return True

    detected = find_tesseract_path()
    if detected:
        pytesseract.pytesseract.tesseract_cmd = detected
        return True

    return False


def preprocess_image(image: Image.Image) -> Image.Image:
    """
    Prepares medical report image for optimal OCR extraction:
    Converts to grayscale, boosts contrast, and sharpens text lines.
    """
    gray = ImageOps.exif_transpose(image).convert("L")
    # Upscale small phone photos so character shapes survive OCR.
    if max(gray.size) < 2200:
        scale = min(2.5, 2200 / max(gray.size))
        gray = gray.resize((int(gray.width * scale), int(gray.height * scale)), Image.Resampling.LANCZOS)
    gray = ImageOps.autocontrast(gray)
    enhanced = ImageEnhance.Contrast(gray).enhance(1.7)
    return enhanced.filter(ImageFilter.UnsharpMask(radius=1.5, percent=140, threshold=3))


def extract_text_from_image(image_bytes: bytes, custom_tesseract_path: Optional[str] = None) -> Tuple[str, Optional[str]]:
    """
    Extracts text from image bytes using PIL and Tesseract OCR.
    Returns (extracted_text, error_message).
    """
    if not PYTESSERACT_AVAILABLE:
        return "", "Pytesseract library is not installed. Please run: pip install pytesseract"

    tess_ready = configure_tesseract(custom_tesseract_path)

    try:
        image = Image.open(io.BytesIO(image_bytes))
        processed = preprocess_image(image)

        # Different layouts work better with different page segmentation modes.
        # Pick the longest non-empty extraction; do not concatenate variants (duplicates).
        candidates = []
        for psm in (6, 11, 4):
            try:
                candidate = pytesseract.image_to_string(
                    processed, lang="eng", config=f"--oem 3 --psm {psm}"
                ).strip()
                if candidate:
                    candidates.append(candidate)
            except Exception:
                continue
        text = max(candidates, key=len) if candidates else ""

        clean_text = text.strip()
        if not clean_text:
            return "", "OCR completed but no readable text could be detected from this image. Please ensure the image is bright and legible."
        return clean_text, None

    except pytesseract.TesseractNotFoundError:
        return "", (
            "Tesseract OCR is not installed or not in PATH.\n\n"
            "• On Windows: Install via `winget install UB-Mannheim.TesseractOCR` or download installer.\n"
            "• Or use PDF upload instead (PDF text extraction works natively without Tesseract!).\n"
            "• On Streamlit Community Cloud: Tesseract is configured automatically via `packages.txt`."
        )
    except Exception as e:
        return "", f"Error processing image with OCR: {str(e)}"


def extract_text_from_pdf(pdf_bytes: bytes, custom_tesseract_path: Optional[str] = None) -> Tuple[str, Optional[str]]:
    """
    Extracts text from PDF bytes.
    First tries digital text extraction using PyMuPDF (or pypdf).
    If page text is sparse/scanned, uses OCR on rendered page pixmaps.
    """
    full_text = []

    # 1. Try PyMuPDF
    if PYMUPDF_AVAILABLE:
        try:
            doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()

                if page_text and len(page_text.strip()) > 20:
                    full_text.append(page_text.strip())
                else:
                    # Page seems scanned: render to image and OCR
                    try:
                        pix = page.get_pixmap(dpi=200)
                        ocr_res, err = extract_text_from_image(pix.tobytes("png"), custom_tesseract_path)
                        if ocr_res:
                            full_text.append(ocr_res)
                    except Exception:
                        pass

            doc.close()
            combined = "\n\n".join(full_text).strip()
            if combined:
                return combined, None
        except Exception:
            pass

    # 2. PyPDF Fallback
    if PYPDF_AVAILABLE:
        try:
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                t = page.extract_text()
                if t and t.strip():
                    full_text.append(t.strip())
            combined = "\n\n".join(full_text).strip()
            if combined:
                return combined, None
        except Exception as e:
            return "", f"Failed to extract text from PDF: {str(e)}"

    return "", "Could not extract readable text from this PDF file. Please ensure it is not password protected."


def extract_document_text(file_bytes: bytes, file_name: str, custom_tesseract_path: Optional[str] = None) -> Tuple[str, Optional[str]]:
    """
    Unified extraction dispatcher based on file extension.
    """
    ext = os.path.splitext(file_name)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_bytes, custom_tesseract_path)
    elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"]:
        return extract_text_from_image(file_bytes, custom_tesseract_path)
    elif ext in [".txt", ".log"]:
        try:
            return file_bytes.decode("utf-8", errors="replace"), None
        except Exception as e:
            return "", f"Error decoding text file: {str(e)}"
    else:
        return "", f"Unsupported file extension: {ext}. Please upload a PDF, PNG, or JPG."
