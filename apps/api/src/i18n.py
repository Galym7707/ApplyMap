"""Minimal i18n helper for API error messages.

The backend's responses are mostly machine-readable JSON, so the only
strings we localize are the user-facing ``detail`` fields on common HTTP
errors. The active locale is picked from the ``Accept-Language`` header;
``en`` is always the fallback.

We deliberately keep the dictionary small — large translations should live
on the frontend, where they can be edited and reviewed without a backend
release.
"""
from __future__ import annotations

from typing import Iterable, Optional


SUPPORTED_LOCALES = ("en", "ru", "kk")
DEFAULT_LOCALE = "en"

_MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "auth.invalid_credentials": "Invalid email or password",
        "auth.email_taken": "An account with this email already exists",
        "auth.not_authenticated": "Not authenticated",
        "auth.forbidden": "You don't have permission to perform this action",
        "common.not_found": "Resource not found",
        "common.validation_failed": "Validation failed",
        "common.rate_limited": "Too many requests — please try again shortly",
        "achievements.import_failed": "We couldn't read this file — please enter the activity manually.",
        "ocr.needs_manual_entry": "We couldn't extract text from this image — please enter the data manually.",
        "advisor.no_profile": "Complete your profile to receive bracket recommendations.",
    },
    "ru": {
        "auth.invalid_credentials": "Неверный email или пароль",
        "auth.email_taken": "Аккаунт с таким email уже существует",
        "auth.not_authenticated": "Необходимо войти в систему",
        "auth.forbidden": "У вас нет прав на это действие",
        "common.not_found": "Ресурс не найден",
        "common.validation_failed": "Ошибка валидации",
        "common.rate_limited": "Слишком много запросов — попробуйте через минуту",
        "achievements.import_failed": "Не удалось прочитать файл — введите активность вручную.",
        "ocr.needs_manual_entry": "Не удалось распознать текст — введите данные вручную.",
        "advisor.no_profile": "Заполните профиль, чтобы получить рекомендации по группам университетов.",
    },
    "kk": {
        "auth.invalid_credentials": "Қате email немесе құпиясөз",
        "auth.email_taken": "Бұл email-мен аккаунт бар",
        "auth.not_authenticated": "Жүйеге кіру қажет",
        "auth.forbidden": "Бұл әрекетке құқығыңыз жоқ",
        "common.not_found": "Ресурс табылмады",
        "common.validation_failed": "Валидация қатесі",
        "common.rate_limited": "Тым көп сұраныс — кейінірек қайталаңыз",
        "achievements.import_failed": "Файлды оқу мүмкін болмады — деректерді қолмен енгізіңіз.",
        "ocr.needs_manual_entry": "Суреттен мәтінді тану мүмкін болмады — деректерді қолмен енгізіңіз.",
        "advisor.no_profile": "Профильді толтырыңыз, сонда университеттер бойынша ұсыныстар жасалады.",
    },
}


def _parse_accept_language(header: Optional[str]) -> Iterable[str]:
    """Yield language tags from a standard ``Accept-Language`` header.

    We intentionally ignore quality values — for our small locale set the
    first parsable tag wins.
    """
    if not header:
        return ()
    tags: list[str] = []
    for part in header.split(","):
        tag = part.split(";", 1)[0].strip().lower()
        if not tag:
            continue
        # Normalize ``ru-RU`` -> ``ru``.
        primary = tag.split("-", 1)[0]
        tags.append(primary)
    return tags


def resolve_locale(accept_language: Optional[str]) -> str:
    """Pick the best-matching supported locale or fall back to ``en``."""
    for tag in _parse_accept_language(accept_language):
        if tag in SUPPORTED_LOCALES:
            return tag
    return DEFAULT_LOCALE


def translate(key: str, accept_language: Optional[str] = None) -> str:
    """Return the message for ``key`` in the locale chosen by the header.

    Unknown keys fall back to the key itself so the API never silently
    swallows the error — the caller can still log the raw key.
    """
    locale = resolve_locale(accept_language)
    primary = _MESSAGES.get(locale, {}).get(key)
    if primary:
        return primary
    fallback = _MESSAGES.get(DEFAULT_LOCALE, {}).get(key)
    return fallback if fallback else key
