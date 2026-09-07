"""Tests for AI story generation fallback and malformed-JSON recovery."""
from __future__ import annotations

import pytest

from app.ai.gemini_service import _extract_json
from app.ai.story_generator import _fallback_story, _validate, generate_story, story_to_narration_script


def test_fallback_story_has_required_shape():
    events = [{"label": "Beach", "media_count": 3}, {"label": "Sunset", "media_count": 2}]
    story = _fallback_story(events, "cinematic", "en", 60)
    assert _validate(story)
    assert story["source"] == "fallback"
    assert len(story["chapters"]) == 2


def test_fallback_story_arabic():
    events = [{"label": "Beach", "media_count": 1}]
    story = _fallback_story(events, "memories", "ar", 30)
    assert story["title"]
    assert isinstance(story["opening"], str) and len(story["opening"]) > 0


def test_generate_story_uses_fallback_when_gemini_not_configured(monkeypatch):
    # In demo mode / no API key, generate_story must never raise and must
    # always return a valid story dict.
    events = [{"label": "City Exploration", "media_count": 4}]
    story = generate_story(events, "dynamic", "en", 45)
    assert _validate(story)
    assert story["source"] == "fallback"


def test_story_to_narration_script_concatenates_in_order():
    story = {
        "opening": "Hello.",
        "chapters": [{"narration": "Chapter one."}, {"narration": "Chapter two."}],
        "ending": "Goodbye.",
    }
    script = story_to_narration_script(story)
    assert script == "Hello. Chapter one. Chapter two. Goodbye."


def test_extract_json_handles_clean_json():
    assert _extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_strips_markdown_fences():
    text = '```json\n{"a": 1, "b": 2}\n```'
    assert _extract_json(text) == {"a": 1, "b": 2}


def test_extract_json_recovers_from_leading_chatter():
    text = 'Sure, here you go:\n{"a": 1}\nHope that helps!'
    assert _extract_json(text) == {"a": 1}


def test_extract_json_raises_on_garbage():
    with pytest.raises(ValueError):
        _extract_json("not json at all")


def test_validate_rejects_missing_keys():
    assert _validate({"title": "x"}) is False
    assert _validate({}) is False
