"""Input normalization and resume text cleaning utilities.

Use this module before model inference or heuristic resume analysis. It accepts
plain text, JSON-like dictionaries, JSON strings, and parser output.
"""

from __future__ import annotations

import json
import re
from typing import Any


_URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", flags=re.IGNORECASE)
_EMAIL_PATTERN = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_CONTROL_PATTERN = re.compile(r"[\r\t]+")
_NON_WORD_PATTERN = re.compile(r"[^A-Za-z0-9+#.\-\s]")
_SPACE_PATTERN = re.compile(r"\s+")


def cleanResume(text: str) -> str:
    """Clean resume text for TF-IDF/classifier inference.

    Keeps useful technical tokens such as C++, C#, .NET, Node.js-like dots, and
    hyphenated words while removing emails, URLs, noisy symbols, and extra space.
    """

    if not text:
        return ""

    text = str(text)
    text = _URL_PATTERN.sub(" ", text)
    text = _EMAIL_PATTERN.sub(" ", text)
    text = _CONTROL_PATTERN.sub(" ", text)
    text = _NON_WORD_PATTERN.sub(" ", text)
    return _SPACE_PATTERN.sub(" ", text).strip()


def _flatten_json(value: Any) -> str:
    """Convert nested JSON-like resume data into searchable plain text."""

    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return " ".join(_flatten_json(item) for item in value)
    if isinstance(value, dict):
        parts: list[str] = []
        for key, item in value.items():
            parts.append(str(key))
            parts.append(_flatten_json(item))
        return " ".join(parts)
    return str(value)


def preprocess_input(resume_input: str | dict[str, Any]) -> dict[str, Any]:
    """Normalize raw text, JSON strings, or dictionaries for the pipeline.

    Returns both the raw text and the cleaned text because parsing/feedback
    benefits from original line breaks, while classification needs cleaned text.
    """

    parsed_json: dict[str, Any] | None = None

    if isinstance(resume_input, dict):
        parsed_json = resume_input
        raw_text = _flatten_json(resume_input)
    elif isinstance(resume_input, str):
        stripped = resume_input.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            try:
                loaded = json.loads(stripped)
                parsed_json = loaded if isinstance(loaded, dict) else {"items": loaded}
                raw_text = _flatten_json(loaded)
            except json.JSONDecodeError:
                raw_text = resume_input
        else:
            raw_text = resume_input
    else:
        raw_text = str(resume_input)

    return {
        "raw_text": raw_text,
        "clean_text": cleanResume(raw_text),
        "json": parsed_json,
    }

