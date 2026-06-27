"""
Shared i18n helpers for AstralModules plugins.

Implements the trilingual (en / ru / ua) pattern from FoxUserbot's
``command.py:get_text()`` and the ``LANGUAGES`` dict convention used by the
best CustomModules plugins. Any plugin can declare:

    LANGUAGES = {
        "en": {"hello": "Hello, {name}!"},
        "ru": {"hello": "Привет, {name}!"},
        "ua": {"hello": "Привіт, {name}!"},
    }

and call:

    from modules._i18n import get_text
    text = get_text("myplugin", "hello", LANGUAGES=LANGUAGES, name="Alice")

The current language is read from the AstralBot DB via ``db.get_env("LANG")``
(defaulting to "en").
"""

from __future__ import annotations

from typing import Any

_cache: dict[str, str] = {}


async def get_lang() -> str:
    """Get the current global language (default: 'en')."""
    if "lang" in _cache:
        return _cache["lang"]
    try:
        from astralbot import db
        if db is None:
            return "en"
        lang = await db.get_env("LANG", default="en")
        _cache["lang"] = lang or "en"
        return _cache["lang"]
    except Exception:
        return "en"


def set_lang_cached(lang: str) -> None:
    _cache["lang"] = lang


async def get_text(module: str, key: str, *, LANGUAGES: dict | None = None, **kwargs: Any) -> str:
    """Resolve a localized string for the given module + key.

    Falls back to English, then to the raw key if neither is found.
    """
    if not LANGUAGES:
        return key
    lang = await get_lang()
    text = LANGUAGES.get(lang, {}).get(key) or LANGUAGES.get("en", {}).get(key) or key
    try:
        return text.format(**kwargs)
    except (KeyError, IndexError, ValueError):
        return text


async def get_available_langs(LANGUAGES: dict) -> list[str]:
    return sorted(LANGUAGES.keys())
