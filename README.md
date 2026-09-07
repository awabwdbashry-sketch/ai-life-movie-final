# 🎬 AI Life Movie

> **حوّل ذكرياتك إلى فيلم سينمائي بالذكاء الاصطناعي.**  
> ارفع صورك وفيديوهاتك، ودع النظام يحللها، يرتبها، يكتب قصتك، ويبني لك فيلماً متكاملاً.

---



## 📖 عن المشروع

**AI Life Movie** هو تطبيق ذكي مبني باستخدام **Python وFastAPI** لإنشاء أفلام شخصية من الصور والفيديوهات باستخدام الذكاء الاصطناعي.

المشروع يقوم بتحليل الوسائط المرفوعة، اكتشاف أفضل اللحظات، تنظيمها زمنياً، توليد قصة مناسبة باستخدام **Google Gemini**، ثم بناء فيلم سينمائي نهائي باستخدام **FFmpeg**.

الفكرة الأساسية هي تحويل مجموعة من الذكريات والصور والفيديوهات إلى **قصة مرئية متكاملة** بدلاً من مجرد عرضها كملفات منفصلة.

---

## ✨ المميزات

- 📸 رفع الصور والفيديوهات
- 🧠 تحليل الوسائط باستخدام تقنيات الذكاء الاصطناعي
- 👤 تحليل الوجوه
- 🔎 اكتشاف العناصر داخل الصور
- 🎞️ تحليل المشاهد
- ⭐ تحليل جودة الصور والفيديوهات
- 🔄 اكتشاف الملفات المكررة
- 🤖 توليد القصص باستخدام Google Gemini
- 📝 إنشاء Timeline للفيلم
- 🎬 بناء فيلم سينمائي تلقائياً
- 🎨 انتقالات بين المشاهد
- 🎵 إضافة الموسيقى
- 🎙️ دعم التعليق الصوتي
- 💬 دعم الترجمة Subtitles
- 🖼️ إنشاء Thumbnails
- 📊 متابعة تقدم عملية إنشاء الفيلم
- 🌙 الوضع الليلي
- ☀️ الوضع النهاري
- 🌍 دعم العربية والإنجليزية
- 📱 واجهة Web سهلة الاستخدام
- 💾 SQLite لتخزين بيانات المشروع
- ⚡ FastAPI API Architecture
- 🪟 دعم Windows ومسارات الملفات بشكل صحيح
- 🧪 اختبارات آلية للمشروع

---

## 🧠 كيف يعمل المشروع؟

```text
📸 Photos / 🎥 Videos
        │
        ▼
   📂 Media Upload
        │
        ▼
   🔍 Media Analysis
        │
        ├── 👤 Face Analysis
        ├── 🔎 Object Detection
        ├── 🎞️ Scene Analysis
        ├── ⭐ Quality Analysis
        └── 🔄 Duplicate Detection
        │
        ▼
   🏆 Best Media Selection
        │
        ▼
   🤖 Google Gemini
        │
        ▼
   📖 Story Generation
        │
        ▼
   🕐 Timeline Builder
        │
        ▼
   🎬 Movie Builder
        │
        ├── 🎨 Transitions
        ├── 🎵 Music
        ├── 🎙️ Narration
        └── 💬 Subtitles
        │
        ▼
   🎞️ Final Movie
```

---

## 🛠️ التقنيات المستخدمة

### Backend

- Python
- FastAPI
- Uvicorn
- SQLAlchemy
- Pydantic

### AI

- Google Gemini
- Computer Vision
- Face Analysis
- Object Detection
- Scene Analysis
- Media Quality Analysis

### Media Processing

- FFmpeg
- OpenCV
- Pillow
- NumPy
- ImageHash
- piexif

### Database

- SQLite
- SQLAlchemy

### Frontend

- HTML
- CSS
- JavaScript
- Jinja2

### Testing

- Pytest
- HTTPX

---

## 📁 هيكل المشروع

```text
ai-life-movie/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── routes_projects.py
│   │   ├── routes_media.py
│   │   ├── routes_analysis.py
│   │   ├── routes_movies.py
│   │   └── routes_settings.py
│   │
│   ├── ai/
│   │   ├── gemini_service.py
│   │   ├── media_analyzer.py
│   │   ├── story_generator.py
│   │   └── narration.py
│   │
│   ├── vision/
│   │   ├── face_analysis.py
│   │   ├── object_detection.py
│   │   ├── quality_analysis.py
│   │   └── scene_analysis.py
│   │
│   ├── media/
│   │   ├── metadata.py
│   │   ├── image_processor.py
│   │   ├── video_processor.py
│   │   ├── scene_detector.py
│   │   └── duplicate_detector.py
│   │
│   ├── movie/
│   │   ├── timeline_builder.py
│   │   ├── movie_builder.py
│   │   ├── transitions.py
│   │   ├── music.py
│   │   └── renderer.py
│   │
│   ├── database/
│   │   ├── database.py
│   │   ├── models.py
│   │   └── repositories.py
│   │
│   ├── workers/
│   │   └── jobs.py
│   │
│   ├── utils/
│   │   ├── config.py
│   │   ├── files.py
│   │   └── logging.py
│   │
│   ├── i18n/
│   │   └── translations.py
│   │
│   ├── templates/
│   └── static/
│
├── assets/
│   ├── music/
│   └── fonts/
│
├── data/
│
├── tests/
│
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
└── run.py
```

---

## ⚙️ المتطلبات

قبل تشغيل المشروع تأكد من وجود:

- Python 3.12+
- FFmpeg
- Google Gemini API Key

> يفضل استخدام Python 3.12 لتجنب مشاكل توافق بعض المكتبات.

---

## 🚀 تشغيل المشروع

### 1️⃣ تحميل المشروع

```bash
git clone https://github.com/YOUR_USERNAME/ai-life-movie.git
cd ai-life-movie
```

### 2️⃣ إنشاء Virtual Environment

Windows:

```powershell
py -3.12 -m venv .venv
```

تفعيل البيئة:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3️⃣ تثبيت المكتبات

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🎞️ تثبيت FFmpeg

يحتاج المشروع إلى **FFmpeg** لمعالجة الفيديو وإنشاء الفيلم النهائي.

يمكن التأكد من أن FFmpeg يعمل بواسطة:

```powershell
ffmpeg -version
```

إذا ظهر إصدار FFmpeg، فأنت جاهز.

---

## 🤖 إعداد Gemini

أنشئ ملف:

```text
.env
```

وأضف:

```env
GEMINI_API_KEY=YOUR_API_KEY_HERE
```

⚠️ **مهم جداً:** لا ترفع ملف `.env` إلى GitHub.

استخدم `.env.example` بدلاً منه.

---

## ▶️ تشغيل التطبيق

بعد تفعيل البيئة الافتراضية:

```powershell
python run.py
```

ثم افتح:

```text
http://localhost:8000
```

---

## 🎬 إنشاء فيلم

العملية الأساسية:

```text
Create Project
      ↓
Upload Media
      ↓
Analyze Media
      ↓
Select Best Moments
      ↓
Generate Story
      ↓
Build Timeline
      ↓
Add Music / Narration / Subtitles
      ↓
Render Movie
      ↓
🎬 Final Movie
```

---

## 🧪 الاختبارات

المشروع يحتوي على مجموعة اختبارات للتأكد من عمل المكونات الأساسية.

آخر اختبار كامل:

```text
72 passed
```

وتم اختبار:

- API
- Media processing
- Movie pipeline
- File URLs
- Windows paths
- Rendering
- Generated movie files

---

## 🪟 دعم Windows

تم تصميم التعامل مع مسارات الملفات بحيث يعمل بشكل صحيح على Windows وLinux، خصوصاً عند تحويل المسارات الداخلية إلى URLs يمكن للمتصفح الوصول إليها.

مثال:

```text
C:\project\data\projects\p1\renders\movie.mp4
```

يتم تحويله إلى:

```text
/data/projects/p1/renders/movie.mp4
```

---

## 📦 تخزين البيانات

يستخدم المشروع مجلد:

```text
data/
```

لتخزين:

- المشاريع
- الملفات المرفوعة
- الصور المصغرة
- نتائج التحليل
- ملفات الفيديو
- الأفلام النهائية
- بيانات SQLite

هذه البيانات المحلية **لا يجب رفعها إلى GitHub**.

---

## 🔐 الأمان

يجب عدم رفع أي من الآتي إلى GitHub:

```text
.env
API Keys
Generated Movies
Uploaded Media
SQLite Database
Temporary Files
Virtual Environment
```

ويجب أن يبقى:

```text
.env.example
```

بدون أي مفاتيح حقيقية.

---

## 🗺️ التطوير المستقبلي

من الأفكار المستقبلية:

- 👤 حسابات المستخدمين
- ☁️ Cloud Storage
- 📱 تطبيق Android / iOS
- 🎨 قوالب أفلام متعددة
- 🎵 مكتبة موسيقى أكبر
- 🧠 تحسين اختيار الذكريات
- 🎙️ أصوات AI متعددة
- 🌍 دعم لغات إضافية
- 📤 مشاركة الأفلام مباشرة
- ☁️ معالجة الفيديو على Cloud
- 🎬 قوالب سينمائية متقدمة

---

## 📌 حالة المشروع

**AI Life Movie** في مرحلة تطوير متقدمة، ويحتوي على نظام متكامل لمعالجة الوسائط وتحليلها وبناء فيلم نهائي.

```text
Backend              ✅
Media Upload         ✅
Media Analysis       ✅
AI Story Generation  ✅
Timeline Builder     ✅
Movie Builder        ✅
FFmpeg Rendering     ✅
Subtitles            ✅
Music                ✅
Testing              ✅
Windows Support      ✅
```

---



## 📖 About

**AI Life Movie** is an AI-powered application built with **Python and FastAPI** for turning personal photos and videos into cinematic movies.

The application analyzes uploaded media, identifies important moments, generates a personalized story using **Google Gemini**, builds a cinematic timeline, and renders the final movie using **FFmpeg**.

The goal is to transform a collection of memories into a **complete visual story**.

---

## ✨ Features

- 📸 Photo and video uploads
- 🧠 AI-powered media analysis
- 👤 Face analysis
- 🔎 Object detection
- 🎞️ Scene analysis
- ⭐ Media quality analysis
- 🔄 Duplicate detection
- 🤖 Google Gemini story generation
- 📝 Automatic timeline generation
- 🎬 Cinematic movie building
- 🎨 Scene transitions
- 🎵 Background music
- 🎙️ Optional narration
- 💬 Subtitles
- 🖼️ Movie thumbnails
- 📊 Progress tracking
- 🌙 Dark mode
- ☀️ Light mode
- 🌍 Arabic and English support
- 📱 Web interface
- 💾 SQLite database
- ⚡ FastAPI architecture
- 🪟 Windows path compatibility
- 🧪 Automated tests

---

## 🧠 Architecture

```text
📸 Photos / 🎥 Videos
        │
        ▼
   📂 Media Upload
        │
        ▼
   🔍 Media Analysis
        │
        ├── 👤 Face Analysis
        ├── 🔎 Object Detection
        ├── 🎞️ Scene Analysis
        ├── ⭐ Quality Analysis
        └── 🔄 Duplicate Detection
        │
        ▼
   🏆 Best Media Selection
        │
        ▼
   🤖 Google Gemini
        │
        ▼
   📖 Story Generation
        │
        ▼
   🕐 Timeline Builder
        │
        ▼
   🎬 Movie Builder
        │
        ├── 🎨 Transitions
        ├── 🎵 Music
        ├── 🎙️ Narration
        └── 💬 Subtitles
        │
        ▼
   🎞️ Final Movie
```

---

## 🛠️ Tech Stack

### Backend

- Python
- FastAPI
- Uvicorn
- SQLAlchemy
- Pydantic

### AI

- Google Gemini
- Computer Vision
- Face Analysis
- Object Detection
- Scene Analysis
- Media Quality Analysis

### Media Processing

- FFmpeg
- OpenCV
- Pillow
- NumPy
- ImageHash
- piexif

### Database

- SQLite
- SQLAlchemy

### Frontend

- HTML
- CSS
- JavaScript
- Jinja2

### Testing

- Pytest
- HTTPX

---

## 🚀 Installation

### Requirements

- Python 3.12+
- FFmpeg
- Google Gemini API Key

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/ai-life-movie.git
cd ai-life-movie
```

Create a virtual environment:

```powershell
py -3.12 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🤖 Gemini Configuration

Create:

```text
.env
```

Add:

```env
GEMINI_API_KEY=YOUR_API_KEY_HERE
```

Never commit your real API key to GitHub.

---

## ▶️ Run

Start the application:

```powershell
python run.py
```

Open:

```text
http://localhost:8000
```

---

## 🧪 Testing

The project includes automated tests covering the core application.

Latest full test result:

```text
72 passed
```

Tests cover:

- API functionality
- Media processing
- Movie pipeline
- URL generation
- Windows path handling
- Rendering
- Generated movie files

---

## 🎬 Movie Pipeline

```text
Create Project
      ↓
Upload Media
      ↓
Analyze Media
      ↓
Select Best Moments
      ↓
Generate Story
      ↓
Build Timeline
      ↓
Add Music / Narration / Subtitles
      ↓
Render Movie
      ↓
🎬 Final Movie
```

---

## 🔐 Security

Never commit:

```text
.env
API Keys
Uploaded Media
Generated Movies
SQLite Database
Temporary Files
.venv
```

Use `.env.example` for configuration examples.

---

## 🗺️ Roadmap

- 👤 User accounts
- ☁️ Cloud storage
- 📱 Android / iOS application
- 🎨 Multiple movie templates
- 🎵 Extended music library
- 🧠 Smarter memory selection
- 🎙️ Multiple AI voices
- 🌍 More languages
- 📤 Direct movie sharing
- ☁️ Cloud rendering
- 🎬 Advanced cinematic templates

---

## 📌 Project Status

**AI Life Movie** is an advanced work-in-progress project with an integrated media-analysis and cinematic movie-generation pipeline.

```text
Backend              ✅
Media Upload         ✅
Media Analysis       ✅
AI Story Generation  ✅
Timeline Builder     ✅
Movie Builder        ✅
FFmpeg Rendering     ✅
Subtitles            ✅
Music                ✅
Testing              ✅
Windows Support      ✅
```

---

## 👨‍💻 Developer

**Awab Bashary | AwabBuilds**

GitHub: **awabwdbashry-sketch**

---

⭐ If you find this project interesting, consider giving it a star and following the development.