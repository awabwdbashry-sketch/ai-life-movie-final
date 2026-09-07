"""Isolated Gemini API service layer.

All calls to Google's Gemini API go through this module. The API key is
never hardcoded — it is read from settings (which loads it from `.env`).
Every public function degrades gracefully (returns None / raises a typed
error) if the API is unavailable, misconfigured, or returns malformed data,
so callers can apply their own local fallback.
"""
from __future__ import annotations

import json
import re

from app.utils.config import get_settings
from app.utils.logging import get_logger

log = get_logger(__name__)


class GeminiUnavailableError(RuntimeError):
    pass


def is_configured() -> bool:
    return get_settings().gemini_configured


def _get_client():
    settings = get_settings()
    if not settings.gemini_configured:
        raise GeminiUnavailableError("Gemini API key is not configured.")
    try:
        from google import genai
    except ImportError as exc:
        raise GeminiUnavailableError(f"google-genai SDK not installed: {exc}") from exc
    return genai.Client(api_key=settings.gemini_api_key)


def _extract_json(text: str) -> dict:
    """Extract the first valid JSON object from a model response, tolerating
    markdown code fences or leading/trailing chatter.
    """
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned.strip())
    cleaned = re.sub(r"```$", "", cleaned.strip())
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Fall back to locating the outermost braces
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ValueError(f"Could not parse JSON from Gemini response: {exc}") from exc
    raise ValueError("No JSON object found in Gemini response.")


def generate_json(prompt: str, model: str = "gemini-2.0-flash") -> dict:
    """Send a prompt requesting structured JSON output; parse and validate it."""
    client = _get_client()
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        text = response.text or ""
    except Exception as exc:
        raise GeminiUnavailableError(f"Gemini request failed: {exc}") from exc

    return _extract_json(text)


def generate_text(prompt: str, model: str = "gemini-2.0-flash") -> str:
    client = _get_client()
    try:
        response = client.models.generate_content(model=model, contents=prompt)
        return (response.text or "").strip()
    except Exception as exc:
        raise GeminiUnavailableError(f"Gemini request failed: {exc}") from exc
