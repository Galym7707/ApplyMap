"""OCR fallback for diploma / certificate images and scanned PDFs.

The existing ``decode_import_file`` handles selectable-text files (PDF, DOCX,
TXT, MD, CSV, JSON). This module adds:

* ``extract_image_text`` for raster image diplomas / certificates
  (PNG, JPG, JPEG, TIFF, BMP, WEBP) using pytesseract.
* ``extract_scanned_pdf_text`` to rasterize each page of a scanned PDF
  with pdf2image and OCR each page.

Heuristics:
* Tesseract is invoked with ``rus+kaz+eng`` so multilingual diplomas work.
* OpenCV preprocessing (grayscale + adaptive threshold) is applied when
  available; if opencv isn't installed the raw image is sent through.
* Empty or low-confidence output triggers a ``OCRRequiresManualEntry``
  exception so callers can route the user to manual entry.

Heavy imports (cv2, pytesseract, pdf2image) are deferred so unit tests can
patch them without installing the binaries.
"""
from __future__ import annotations

import io
import os
from dataclasses import dataclass


# Public sizing limits (kept consistent with achievement_import_service).
MAX_OCR_IMAGE_BYTES = 10_000_000
MAX_OCR_PDF_PAGES = 12
MAX_OCR_CHARS = 80_000
MIN_OCR_CONFIDENCE = 35  # Tesseract returns 0-100; below this we ask the user.
MIN_OCR_TEXT_CHARS = 12


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}


# Languages we ship in the Docker image. Falls back to "eng" if the others
# are not installed (e.g. running pytest locally without the kaz pack).
DEFAULT_LANGUAGES = "rus+kaz+eng"


class OCRRequiresManualEntry(Exception):
    """Raised when OCR cannot extract usable text and the caller should
    surface a manual-entry form to the user instead of erroring out.
    """

    def __init__(
        self,
        reason: str,
        partial_text: str = "",
        confidence: float | None = None,
    ) -> None:
        super().__init__(reason)
        self.reason = reason
        self.partial_text = partial_text
        self.confidence = confidence


@dataclass
class OCRResult:
    text: str
    confidence: float
    language_used: str
    page_count: int = 1


def _preprocess_image_bytes(raw_bytes: bytes):
    """Best-effort grayscale + adaptive threshold for higher-contrast OCR.

    Returns whatever pytesseract can read directly when opencv-python isn't
    installed.
    """
    try:
        import cv2
        import numpy as np
        from PIL import Image
    except ImportError:
        return None

    array = np.frombuffer(raw_bytes, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        # Fallback: let PIL parse it then convert.
        with Image.open(io.BytesIO(raw_bytes)) as pil_img:
            image = cv2.cvtColor(np.array(pil_img.convert("RGB")), cv2.COLOR_RGB2BGR)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)
    threshold = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        15,
    )
    return Image.fromarray(threshold)


def _run_tesseract(pil_or_bytes, languages: str) -> tuple[str, float]:
    """Invoke pytesseract and return ``(text, mean_confidence)``.

    Confidence is the mean of word-level confidences with values < 0
    discarded (those are tokens tesseract didn't recognize).
    """
    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise OCRRequiresManualEntry(
            "OCR support is not installed on this server. Install pytesseract."
        ) from exc

    if isinstance(pil_or_bytes, (bytes, bytearray)):
        with Image.open(io.BytesIO(pil_or_bytes)) as pil_img:
            return _run_tesseract(pil_img.convert("RGB"), languages)

    text = pytesseract.image_to_string(pil_or_bytes, lang=languages).strip()
    try:
        data = pytesseract.image_to_data(
            pil_or_bytes,
            lang=languages,
            output_type=pytesseract.Output.DICT,
        )
        scores = [int(c) for c in data.get("conf", []) if str(c).lstrip("-").isdigit() and int(c) >= 0]
        confidence = sum(scores) / len(scores) if scores else 0.0
    except Exception:
        # image_to_data is the source of most flaky errors; keep main text.
        confidence = 0.0
    return text, confidence


def extract_image_text(
    raw_bytes: bytes,
    *,
    languages: str = DEFAULT_LANGUAGES,
) -> OCRResult:
    """Run OCR on a raster image and return the extracted text.

    Raises ``OCRRequiresManualEntry`` if the result is empty / unintelligible.
    """
    if len(raw_bytes) > MAX_OCR_IMAGE_BYTES:
        raise OCRRequiresManualEntry(
            "Image is larger than 10 MB. Compress and re-upload, or enter the achievement manually."
        )

    preprocessed = _preprocess_image_bytes(raw_bytes)
    pil_input = preprocessed if preprocessed is not None else raw_bytes

    text, confidence = _run_tesseract(pil_input, languages)
    cleaned = text.strip()

    if len(cleaned) < MIN_OCR_TEXT_CHARS:
        raise OCRRequiresManualEntry(
            "We couldn't find enough text in this image. Enter the details manually.",
            partial_text=cleaned,
            confidence=confidence,
        )
    if confidence and confidence < MIN_OCR_CONFIDENCE:
        raise OCRRequiresManualEntry(
            "OCR confidence is low; please review the extracted text manually.",
            partial_text=cleaned[:MAX_OCR_CHARS],
            confidence=confidence,
        )

    return OCRResult(
        text=cleaned[:MAX_OCR_CHARS],
        confidence=confidence,
        language_used=languages,
        page_count=1,
    )


def extract_scanned_pdf_text(
    raw_bytes: bytes,
    *,
    languages: str = DEFAULT_LANGUAGES,
) -> OCRResult:
    """OCR each page of a scanned PDF.

    Used as a fallback when the regular pdfplumber-based extraction returns
    empty text (i.e. the PDF is just images).
    """
    try:
        from pdf2image import convert_from_bytes
    except ImportError as exc:
        raise OCRRequiresManualEntry(
            "PDF OCR support is not installed (missing pdf2image / poppler). "
            "Try uploading the diploma as an image, or enter details manually."
        ) from exc

    try:
        images = convert_from_bytes(
            raw_bytes,
            fmt="png",
            dpi=200,
            first_page=1,
            last_page=MAX_OCR_PDF_PAGES,
        )
    except Exception as exc:
        raise OCRRequiresManualEntry(
            "Could not rasterize this PDF for OCR. Upload a clearer copy or enter details manually."
        ) from exc

    pages_text: list[str] = []
    confidences: list[float] = []
    for image in images:
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        page_text, page_conf = _run_tesseract(buf.getvalue(), languages)
        page_text = page_text.strip()
        if page_text:
            pages_text.append(page_text)
            confidences.append(page_conf)
        if sum(len(p) for p in pages_text) >= MAX_OCR_CHARS:
            break

    text = "\n\n".join(pages_text).strip()
    confidence = sum(confidences) / len(confidences) if confidences else 0.0

    if len(text) < MIN_OCR_TEXT_CHARS:
        raise OCRRequiresManualEntry(
            "We couldn't read any text from this PDF. Enter the details manually.",
            partial_text=text,
            confidence=confidence,
        )
    if confidence and confidence < MIN_OCR_CONFIDENCE:
        raise OCRRequiresManualEntry(
            "OCR confidence is low; please review the extracted text manually.",
            partial_text=text[:MAX_OCR_CHARS],
            confidence=confidence,
        )

    return OCRResult(
        text=text[:MAX_OCR_CHARS],
        confidence=confidence,
        language_used=languages,
        page_count=len(pages_text),
    )


def is_image_filename(file_name: str) -> bool:
    extension = os.path.splitext(file_name or "")[1].lower()
    return extension in IMAGE_EXTENSIONS
