"""Minimal, dependency-free i18n system. English and Arabic UI strings live
here as plain dictionaries — no hardcoded strings scattered through templates.
"""
from __future__ import annotations

TRANSLATIONS = {
    "en": {
        "app_name": "AI Life Movie",
        "tagline": "Turn your memories into a cinematic story.",
        "dashboard": "Dashboard",
        "create_movie": "Create Movie",
        "recent_movies": "Recent Movies",
        "projects": "Projects",
        "media_processed": "Media Processed",
        "recent_activity": "Recent Activity",
        "settings": "Settings",
        "upload_media": "Upload Photos & Videos",
        "drag_drop_hint": "Drag & drop files here, or click to browse",
        "analyze": "Analyze Media",
        "timeline": "Timeline",
        "generate_story": "Generate Story",
        "movie_settings": "Movie Settings",
        "generate_movie": "Generate Movie",
        "preview": "Preview",
        "export": "Export MP4",
        "style": "Style",
        "duration": "Duration",
        "aspect_ratio": "Aspect Ratio",
        "narration": "AI Narration",
        "language": "Language",
        "music": "Music",
        "subtitles": "Subtitles",
        "regenerate": "Regenerate",
        "no_movies_yet": "No movies yet — create your first one!",
        "status_draft": "Draft",
        "status_processing": "Processing",
        "status_ready": "Ready",
        "demo_mode_banner": "Demo Mode — Gemini API key not configured. Using intelligent local fallback for story generation.",
    },
    "ar": {
        "app_name": "أفلام الحياة بالذكاء الاصطناعي",
        "tagline": "حوّل ذكرياتك إلى قصة سينمائية.",
        "dashboard": "لوحة التحكم",
        "create_movie": "إنشاء فيلم",
        "recent_movies": "أحدث الأفلام",
        "projects": "المشاريع",
        "media_processed": "الوسائط المعالجة",
        "recent_activity": "النشاط الأخير",
        "settings": "الإعدادات",
        "upload_media": "رفع الصور والفيديوهات",
        "drag_drop_hint": "اسحب وأفلت الملفات هنا، أو انقر للتصفح",
        "analyze": "تحليل الوسائط",
        "timeline": "الخط الزمني",
        "generate_story": "إنشاء القصة",
        "movie_settings": "إعدادات الفيلم",
        "generate_movie": "إنشاء الفيلم",
        "preview": "معاينة",
        "export": "تصدير MP4",
        "style": "الأسلوب",
        "duration": "المدة",
        "aspect_ratio": "نسبة العرض",
        "narration": "السرد بالذكاء الاصطناعي",
        "language": "اللغة",
        "music": "الموسيقى",
        "subtitles": "الترجمة",
        "regenerate": "إعادة الإنشاء",
        "no_movies_yet": "لا توجد أفلام بعد — أنشئ أول فيلم لك!",
        "status_draft": "مسودة",
        "status_processing": "قيد المعالجة",
        "status_ready": "جاهز",
        "demo_mode_banner": "وضع العرض التجريبي — لم يتم إعداد مفتاح Gemini API. يتم استخدام نظام احتياطي محلي ذكي لإنشاء القصة.",
    },
}

RTL_LANGUAGES = {"ar"}


def t(key: str, lang: str = "en") -> str:
    lang = lang if lang in TRANSLATIONS else "en"
    return TRANSLATIONS[lang].get(key, TRANSLATIONS["en"].get(key, key))


def dir_for(lang: str) -> str:
    return "rtl" if lang in RTL_LANGUAGES else "ltr"


def all_strings(lang: str) -> dict:
    lang = lang if lang in TRANSLATIONS else "en"
    return TRANSLATIONS[lang]
