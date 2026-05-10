"""Tests for the unified decode_import_file dispatcher with OCR routing."""
from __future__ import annotations

import pytest

from src.services import achievement_import_service as ais
from src.services import ocr_service


def test_decode_routes_image_files_through_ocr(monkeypatch):
    captured = {}

    def fake_image_ocr(raw_bytes):
        captured["called_with_size"] = len(raw_bytes)
        return ocr_service.OCRResult(
            text="Almaty City Mathematics Olympiad — 2nd place",
            confidence=82.0,
            language_used="rus+kaz+eng",
        )

    monkeypatch.setattr(ais, "extract_image_text", fake_image_ocr)
    text = ais.decode_import_file("diploma.png", b"\x89PNG fake bytes")
    assert "Olympiad" in text
    assert captured["called_with_size"] == len(b"\x89PNG fake bytes")


def test_decode_falls_back_to_ocr_for_scanned_pdf(monkeypatch):
    def fake_text_pdf(_raw):
        # Simulate a scanned PDF that pdfplumber cannot read.
        raise ValueError("This PDF has no selectable text.")

    def fake_ocr_pdf(_raw):
        return ocr_service.OCRResult(
            text="Olympiad of Informatics — Gold Medal",
            confidence=72.0,
            language_used="rus+kaz+eng",
            page_count=2,
        )

    monkeypatch.setattr(ais, "_extract_pdf_text", fake_text_pdf)
    monkeypatch.setattr(ais, "extract_scanned_pdf_text", fake_ocr_pdf)
    text = ais.decode_import_file("scan.pdf", b"%PDF-fake")
    assert "Gold Medal" in text


def test_decode_propagates_pdf_text_error_when_ocr_also_fails(monkeypatch):
    def fake_text_pdf(_raw):
        raise ValueError("Could not extract text from this PDF.")

    def fake_ocr_pdf(_raw):
        raise ocr_service.OCRRequiresManualEntry("OCR is unavailable.")

    monkeypatch.setattr(ais, "_extract_pdf_text", fake_text_pdf)
    monkeypatch.setattr(ais, "extract_scanned_pdf_text", fake_ocr_pdf)
    with pytest.raises(ValueError) as exc:
        ais.decode_import_file("bad.pdf", b"%PDF-broken")
    assert "extract text" in str(exc.value).lower()


def test_decode_rejects_unsupported_extension():
    with pytest.raises(ValueError) as exc:
        ais.decode_import_file("notes.xls", b"some bytes")
    assert "image" in str(exc.value).lower() or "supports" in str(exc.value).lower()


def test_decode_propagates_ocr_manual_entry_for_image(monkeypatch):
    def fake_image_ocr(_raw):
        raise ocr_service.OCRRequiresManualEntry(
            "We couldn't find enough text in this image. Enter the details manually."
        )

    monkeypatch.setattr(ais, "extract_image_text", fake_image_ocr)
    with pytest.raises(ocr_service.OCRRequiresManualEntry):
        ais.decode_import_file("blank.png", b"\x89PNG empty")
