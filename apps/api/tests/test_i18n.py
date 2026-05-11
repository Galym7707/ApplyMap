"""Tests for the backend i18n helper."""
from __future__ import annotations

import pytest

from src.i18n import (
    DEFAULT_LOCALE,
    SUPPORTED_LOCALES,
    _MESSAGES,
    resolve_locale,
    translate,
)


def test_supported_locales_are_three():
    assert set(SUPPORTED_LOCALES) == {"en", "ru", "kk"}


def test_every_locale_has_every_key():
    """All locales must define the same key set so the fallback path is
    only hit for unknown (i.e. mis-typed) keys, not for missing translations."""
    en_keys = set(_MESSAGES["en"].keys())
    assert en_keys, "english dictionary should be non-empty"
    for locale in SUPPORTED_LOCALES:
        assert set(_MESSAGES[locale].keys()) == en_keys, (
            f"{locale} is missing or has extra keys vs en"
        )


@pytest.mark.parametrize(
    "header,expected",
    [
        (None, "en"),
        ("", "en"),
        ("en-US,en;q=0.9", "en"),
        ("ru-RU,ru;q=0.9,en;q=0.8", "ru"),
        ("kk-KZ,kk;q=0.9", "kk"),
        ("fr-FR,fr;q=0.9,ru;q=0.8", "ru"),
        ("zh-CN", "en"),  # unsupported -> fallback
    ],
)
def test_resolve_locale(header, expected):
    assert resolve_locale(header) == expected


def test_translate_returns_localized_message():
    assert translate("auth.invalid_credentials", "ru") == (
        "Неверный email или пароль"
    )
    assert translate("auth.invalid_credentials", "kk").startswith("Қате email")
    assert (
        translate("auth.invalid_credentials", "en")
        == "Invalid email or password"
    )


def test_translate_falls_back_to_english_when_locale_unknown():
    assert (
        translate("auth.invalid_credentials", "ja-JP")
        == "Invalid email or password"
    )


def test_translate_returns_key_for_unknown_message():
    assert translate("nonexistent.key", "en") == "nonexistent.key"
    assert translate("nonexistent.key", "ru") == "nonexistent.key"


def test_default_locale_is_english():
    assert DEFAULT_LOCALE == "en"
