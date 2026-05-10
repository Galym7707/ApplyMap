"""Unit tests for the OCR service.

These tests run without tesseract installed by stubbing pytesseract via
``sys.modules`` injection. The goal is to verify routing, fallback behavior,
and confidence handling — not to verify tesseract itself.
"""
from __future__ import annotations

import io
import sys
import types

import pytest

from src.services import ocr_service


def _install_fake_pytesseract(text: str, confidences: list[int]):
    fake = types.SimpleNamespace()
    fake.image_to_string = lambda image, lang=None: text
    fake.image_to_data = lambda image, lang=None, output_type=None: {"conf": confidences}
    fake.Output = types.SimpleNamespace(DICT="dict")
    sys.modules["pytesseract"] = fake
    return fake


def _uninstall_fake_pytesseract():
    sys.modules.pop("pytesseract", None)


def _png_bytes() -> bytes:
    """Produce a tiny in-memory PNG so PIL.Image.open succeeds in the
    fallback (non-opencv) path.
    """
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (32, 32), "white").save(buf, format="PNG")
    return buf.getvalue()


def test_extract_image_text_returns_clean_text(monkeypatch):
    _install_fake_pytesseract("Diploma of Excellence — 2024 — Almaty Olympiad", [80, 85, 90])
    # Force the cv2 path off so we exercise the bytes->PIL fallback.
    monkeypatch.setattr(ocr_service, "_preprocess_image_bytes", lambda b: None)
    try:
        result = ocr_service.extract_image_text(_png_bytes())
    finally:
        _uninstall_fake_pytesseract()
    assert "Diploma of Excellence" in result.text
    assert result.confidence > 70
    assert result.page_count == 1


def test_extract_image_text_raises_manual_entry_when_empty(monkeypatch):
    _install_fake_pytesseract("", [])
    monkeypatch.setattr(ocr_service, "_preprocess_image_bytes", lambda b: None)
    try:
        with pytest.raises(ocr_service.OCRRequiresManualEntry) as exc:
            ocr_service.extract_image_text(_png_bytes())
    finally:
        _uninstall_fake_pytesseract()
    assert "manually" in str(exc.value).lower()


def test_extract_image_text_raises_manual_entry_when_low_confidence(monkeypatch):
    _install_fake_pytesseract("garbled noise output that should be reviewed", [10, 12, 15])
    monkeypatch.setattr(ocr_service, "_preprocess_image_bytes", lambda b: None)
    try:
        with pytest.raises(ocr_service.OCRRequiresManualEntry) as exc:
            ocr_service.extract_image_text(_png_bytes())
    finally:
        _uninstall_fake_pytesseract()
    assert exc.value.confidence is not None
    assert exc.value.confidence < ocr_service.MIN_OCR_CONFIDENCE
    assert exc.value.partial_text  # we keep what we got for the manual draft


def test_extract_image_text_rejects_oversized_input():
    huge_payload = b"x" * (ocr_service.MAX_OCR_IMAGE_BYTES + 1)
    with pytest.raises(ocr_service.OCRRequiresManualEntry) as exc:
        ocr_service.extract_image_text(huge_payload)
    assert "10 MB" in str(exc.value) or "larger" in str(exc.value).lower()


def test_is_image_filename_recognizes_common_extensions():
    assert ocr_service.is_image_filename("diploma.PNG")
    assert ocr_service.is_image_filename("certificate.jpg")
    assert ocr_service.is_image_filename("scan.tiff")
    assert not ocr_service.is_image_filename("transcript.pdf")
    assert not ocr_service.is_image_filename("notes.txt")
    assert not ocr_service.is_image_filename("")


def test_extract_scanned_pdf_text_falls_through_when_pdf2image_missing(monkeypatch):
    # Hide pdf2image to simulate environments without poppler.
    monkeypatch.setitem(sys.modules, "pdf2image", None)
    with pytest.raises(ocr_service.OCRRequiresManualEntry) as exc:
        ocr_service.extract_scanned_pdf_text(b"%PDF-fake")
    assert "pdf2image" in str(exc.value).lower() or "manually" in str(exc.value).lower()
