"""AI-driven story/script generation.

Sends a *compact* textual summary of events/media (not full-resolution files)
to Gemini and requests a structured JSON story. Validates the response and
falls back to a deterministic local template if Gemini is unavailable or
returns malformed data — the pipeline must never hard-fail here.
"""
from __future__ import annotations

from app.ai.gemini_service import GeminiUnavailableError, generate_json, is_configured
from app.utils.logging import get_logger

log = get_logger(__name__)

_REQUIRED_KEYS = {"title", "opening", "chapters", "ending", "tone"}

_STYLE_TONE = {
    "cinematic": "cinematic, slow, emotional, dramatic",
    "travel": "energetic travel-documentary",
    "memories": "warm, nostalgic, emotional",
    "dynamic": "fast-paced, upbeat, energetic",
    "minimal": "clean, elegant, understated",
    "social": "punchy, short-form, attention-grabbing",
}


def build_compact_summary(events: list[dict], language: str) -> str:
    """Build a small, privacy-conscious text summary of events for the AI prompt.
    Only compact metadata is sent — never full-resolution media.
    """
    lines = []
    for i, ev in enumerate(events, 1):
        lines.append(
            f"Event {i}: '{ev['label']}' — {ev.get('media_count', 0)} moments "
            f"({ev.get('photo_count', 0)} photos, {ev.get('video_count', 0)} videos), "
            f"tags: {', '.join(ev.get('tags', [])[:6]) or 'none'}, "
            f"people present: {'yes' if ev.get('has_people') else 'no'}, "
            f"time: {ev.get('start_time', 'unknown')}"
        )
    return "\n".join(lines) if lines else "A single collection of personal photos and videos."


def _prompt(summary: str, style: str, language: str, duration_seconds: int) -> str:
    tone = _STYLE_TONE.get(style, "cinematic")
    lang_name = "Arabic" if language == "ar" else "English"
    return f"""You are a professional documentary film narrator and editor.
Based on the following chronological event summary from someone's personal
photos and videos, write a short personal-documentary style story.

Events:
{summary}

Movie style/tone: {tone}
Target movie length: about {duration_seconds} seconds
Narration language: {lang_name}

Respond with ONLY a valid JSON object (no markdown, no commentary) with this
exact shape:
{{
  "title": "a short evocative movie title",
  "opening": "1-2 sentence opening narration line",
  "chapters": [
    {{"event_label": "matches an event above", "narration": "1-2 sentence narration for this chapter"}}
  ],
  "ending": "1-2 sentence closing narration line",
  "tone": "{style}"
}}
Write the "opening", "ending", and each chapter's "narration" text in {lang_name}.
Keep the whole narration concise enough to comfortably fit in {duration_seconds} seconds when read aloud.
"""


def _validate(data: dict) -> bool:
    if not isinstance(data, dict):
        return False
    if not _REQUIRED_KEYS.issubset(data.keys()):
        return False
    if not isinstance(data.get("chapters"), list):
        return False
    return True


def generate_story(events: list[dict], style: str, language: str, duration_seconds: int) -> dict:
    """Returns a story dict with an added 'source' key: 'gemini' or 'fallback'."""
    summary = build_compact_summary(events, language)

    if is_configured():
        try:
            prompt = _prompt(summary, style, language, duration_seconds)
            data = generate_json(prompt)
            if _validate(data):
                data["source"] = "gemini"
                return data
            log.warning("Gemini story response failed validation, using fallback.")
        except GeminiUnavailableError as exc:
            log.warning("Gemini unavailable for story generation: %s", exc)
        except Exception as exc:
            log.warning("Unexpected error generating story via Gemini: %s", exc)

    return _fallback_story(events, style, language, duration_seconds)


def _fallback_story(events: list[dict], style: str, language: str, duration_seconds: int) -> dict:
    """Deterministic local template — used in demo mode or if Gemini fails."""
    is_ar = language == "ar"
    title = "ذكريات لا تُنسى" if is_ar else "A Journey to Remember"
    opening = (
        "هذه لحظات من رحلتنا، جُمعت هنا لتُروى من جديد." if is_ar
        else "These are moments from our journey, gathered together to be told once more."
    )
    ending = (
        "وهكذا تبقى الذكريات، أجمل مما كانت عليه." if is_ar
        else "And so the memories remain — even more beautiful in the retelling."
    )

    chapters = []
    for ev in events:
        label = ev["label"]
        if is_ar:
            narration = f"في {label}، عشنا لحظات لن ننساها."
        else:
            narration = f"At {label.lower()}, we lived moments we won't forget."
        chapters.append({"event_label": label, "narration": narration})

    return {
        "title": title,
        "opening": opening,
        "chapters": chapters,
        "ending": ending,
        "tone": style,
        "source": "fallback",
    }


def story_to_narration_script(story: dict) -> str:
    """Flatten a story dict into a single narration script (in order)."""
    parts = [story.get("opening", "")]
    for ch in story.get("chapters", []):
        parts.append(ch.get("narration", ""))
    parts.append(story.get("ending", ""))
    return " ".join(p.strip() for p in parts if p and p.strip())
