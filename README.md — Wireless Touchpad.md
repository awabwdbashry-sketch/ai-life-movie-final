# 🖱️ Wireless Touchpad

<div align="center">

## 📱 حوّل هاتفك إلى لوحة لمس لاسلكية للتحكم في الكمبيوتر 🚀

**Wireless Touchpad** هو مشروع يسمح لك باستخدام هاتفك كلوحة لمس لاسلكية للتحكم في الكمبيوتر بسهولة وسرعة عبر شبكة Wi-Fi.

</div>

---

# 🇸🇩 النسخة العربية

## 📖 عن المشروع

**Wireless Touchpad** هو تطبيق ويب يحوّل هاتفك إلى **Wireless Touchpad** للتحكم في الكمبيوتر بدون الحاجة إلى تثبيت تطبيق على الهاتف.

يعتمد المشروع على **Python + FastAPI + WebSocket** لإنشاء اتصال مباشر وسريع بين الهاتف والكمبيوتر عبر الشبكة المحلية.

كل ما عليك فعله:

📱 شغّل المشروع على الكمبيوتر  
🔳 امسح QR Code من الهاتف  
📡 اتصل بنفس شبكة Wi-Fi  
🖱️ ابدأ التحكم في الكمبيوتر

---

## ✨ المميزات

- 🖱️ التحكم الكامل في الماوس
- 👆 Touchpad للهاتف
- 🖱️ Left Click
- 🖱️ Right Click
- 📜 التمرير لأعلى وأسفل
- ⌨️ التحكم في لوحة المفاتيح
- 🇸🇩 دعم الكتابة باللغة العربية
- 🇬🇧 دعم اللغة الإنجليزية
- 🔢 دعم الأرقام
- ⌫ Backspace
- ↵ Enter
- 🎵 التحكم في الوسائط
- 🔊 رفع وخفض الصوت
- 🔇 كتم الصوت
- ▶️ تشغيل وإيقاف الوسائط
- ⏭️ التالي
- ⏮️ السابق
- 🎤 Presentation Mode
- 🔳 الاتصال باستخدام QR Code
- ⚡ اتصال لحظي باستخدام WebSocket
- 📱 واجهة مناسبة للهواتف
- 🖥️ واجهة تحكم للكمبيوتر
- 🔐 إدارة جلسات الاتصال

---

## 🛠️ التقنيات المستخدمة

### Backend

- 🐍 Python
- ⚡ FastAPI
- 🔌 WebSocket
- 🌐 Uvicorn
- 🖱️ PyAutoGUI
- 🔳 QRCode
- 🖼️ Pillow

### Frontend

- HTML5
- CSS3
- JavaScript
- WebSocket API

---

## 🚀 طريقة التشغيل

### 1️⃣ تحميل المشروع

```bash
git clone https://github.com/awabwdbashry-sketch/Wireless-touchpad.git
cd Wireless-touchpad
```

### 2️⃣ إنشاء البيئة الافتراضية

```powershell
python -m venv .venv
```

### 3️⃣ تشغيل البيئة

```powershell
.\.venv\Scripts\activate
```

### 4️⃣ تثبيت المكتبات

```powershell
pip install -r requirements.txt
```

### 5️⃣ تشغيل المشروع

```powershell
python run.py
```

بعد التشغيل سيظهر لك عنوان المشروع على الشبكة المحلية.

مثال:

```text
http://192.168.x.x:8000
```

📱 يجب أن يكون الهاتف والكمبيوتر متصلين **بنفس شبكة Wi-Fi**.

بعد ذلك:

**امسح QR Code → افتح الرابط → استخدم هاتفك كـ Touchpad. 🚀**

---

## 📂 هيكل المشروع

```text
Wireless-touchpad/
│
├── app/
│   ├── __init__.py
│   ├── input_controller.py
│   ├── logging_config.py
│   ├── main.py
│   ├── network.py
│   ├── qr.py
│   ├── sessions.py
│   └── signaling.py
│
├── static/
│   ├── css/
│   │   ├── desktop.css
│   │   └── mobile.css
│   │
│   └── js/
│       ├── controller.js
│       └── desktop.js
│
├── templates/
│   ├── controller.html
│   ├── desktop.html
│   └── error.html
│
├── tests/
│   ├── __init__.py
│   └── test_core.py
│
├── requirements.txt
├── run.py
├── README.md
└── .gitignore
```

---

## 🧪 الاختبارات

المشروع يحتوي على اختبارات آلية باستخدام **Pytest**.

لتشغيل الاختبارات:

```powershell
pytest -q
```

الاختبارات تغطي أجزاء مهمة من المشروع مثل:

- 🖱️ التحكم في الإدخال
- ⌨️ لوحة المفاتيح
- 🔌 WebSocket
- 📡 الشبكة
- 🔳 QR Code
- 🔐 Sessions
- 🌐 Routes

---

## 🎤 Presentation Mode

يمكن استخدام الهاتف كـ **Remote للتحكم في العروض التقديمية**.

مفيد مع:

- 📊 PowerPoint
- 📑 PDF
- 🌐 Google Slides
- 🖥️ العروض التقديمية

---

## 🔐 الأمان والخصوصية

المشروع مصمم للعمل داخل الشبكة المحلية.

⚠️ لا يُنصح بتعريض السيرفر مباشرة للإنترنت بدون إضافة وسائل حماية مناسبة مثل:

- Authentication
- HTTPS
- Secure WebSocket
- Access Control

---

## 🚧 التطوير المستقبلي

من الأفكار المستقبلية:

- 🔐 نظام تسجيل دخول
- 🔑 Secure Pairing
- 🔒 HTTPS
- 📱 Progressive Web App
- 📳 Haptic Feedback
- 🎨 Themes
- 👥 دعم أكثر من جهاز
- 🖥️ Multi-Monitor
- 🎮 Game Controller Mode
- 📋 Clipboard Sync
- 📂 File Transfer

---

## 👨‍💻 Developer

**Awab Bashary | AwabBuilds**

GitHub: **awabwdbashry-sketch**

---

# 🇬🇧 English Version

## 📖 About the Project

**Wireless Touchpad** is a web-based application that turns your smartphone into a **wireless touchpad and remote controller** for your computer.

The project uses **Python + FastAPI + WebSocket** to establish fast real-time communication between your phone and computer over the same local network.

No mobile application installation is required.

Simply:

🖥️ Run the project on your computer  
🔳 Scan the QR Code with your phone  
📡 Connect both devices to the same Wi-Fi network  
🖱️ Start controlling your computer

---

## ✨ Features

- 🖱️ Full mouse control
- 👆 Smartphone touchpad
- 🖱️ Left Click
- 🖱️ Right Click
- 📜 Scrolling
- ⌨️ Keyboard control
- 🇸🇩 Arabic typing support
- 🇬🇧 English typing support
- 🔢 Number input
- ⌫ Backspace
- ↵ Enter
- 🎵 Media controls
- 🔊 Volume control
- 🔇 Mute
- ▶️ Play / Pause
- ⏭️ Next
- ⏮️ Previous
- 🎤 Presentation Mode
- 🔳 QR Code pairing
- ⚡ Real-time WebSocket communication
- 📱 Mobile-friendly interface
- 🖥️ Desktop control interface
- 🔐 Session management

---

## 🛠️ Technologies

### Backend

- 🐍 Python
- ⚡ FastAPI
- 🔌 WebSocket
- 🌐 Uvicorn
- 🖱️ PyAutoGUI
- 🔳 QRCode
- 🖼️ Pillow

### Frontend

- HTML5
- CSS3
- JavaScript
- WebSocket API

---

## 🚀 Installation

### 1️⃣ Clone the repository

```bash
git clone https://github.com/awabwdbashry-sketch/Wireless-touchpad.git
cd Wireless-touchpad
```

### 2️⃣ Create a virtual environment

```powershell
python -m venv .venv
```

### 3️⃣ Activate the environment

```powershell
.\.venv\Scripts\activate
```

### 4️⃣ Install dependencies

```powershell
pip install -r requirements.txt
```

### 5️⃣ Run the project

```powershell
python run.py
```

The application will display a local network address.

Example:

```text
http://192.168.x.x:8000
```

📱 Make sure your phone and computer are connected to the **same Wi-Fi network**.

Then:

**Scan the QR Code → Open the link → Start using your phone as a Touchpad. 🚀**

---

## 📂 Project Structure

```text
Wireless-touchpad/
│
├── app/
│   ├── __init__.py
│   ├── input_controller.py
│   ├── logging_config.py
│   ├── main.py
│   ├── network.py
│   ├── qr.py
│   ├── sessions.py
│   └── signaling.py
│
├── static/
│   ├── css/
│   │   ├── desktop.css
│   │   └── mobile.css
│   │
│   └── js/
│       ├── controller.js
│       └── desktop.js
│
├── templates/
│   ├── controller.html
│   ├── desktop.html
│   └── error.html
│
├── tests/
│   ├── __init__.py
│   └── test_core.py
│
├── requirements.txt
├── run.py
├── README.md
└── .gitignore
```

---

## 🧪 Testing

The project includes automated tests using **Pytest**.

Run:

```powershell
pytest -q
```

The tests cover important parts of the application, including:

- 🖱️ Input control
- ⌨️ Keyboard input
- 🔌 WebSocket communication
- 📡 Network functionality
- 🔳 QR Code generation
- 🔐 Session management
- 🌐 Application routes

---

## 🎤 Presentation Mode

Your smartphone can also be used as a **presentation remote**.

Useful for:

- 📊 Microsoft PowerPoint
- 📑 PDF presentations
- 🌐 Google Slides
- 🖥️ Presentations

---

## 🔐 Security & Privacy

The project is designed primarily for use within a local network.

⚠️ Do not expose the server directly to the public internet without implementing appropriate security measures such as:

- Authentication
- HTTPS
- Secure WebSocket
- Access Control

---

## 🚧 Future Improvements

Possible future improvements include:

- 🔐 Authentication
- 🔑 Secure Pairing
- 🔒 HTTPS
- 📱 Progressive Web App
- 📳 Haptic Feedback
- 🎨 Custom Themes
- 👥 Multiple Device Support
- 🖥️ Multi-Monitor Support
- 🎮 Game Controller Mode
- 📋 Clipboard Synchronization
- 📂 File Transfer

---

## 👨‍💻 Developer

**Awab Bashary | AwabBuilds**

GitHub: **awabwdbashry-sketch**

---

<div align="center">

## 🖱️ Wireless Touchpad

### 📱 Your Phone. Your Touchpad. Your Control. 🚀

**Built with Python, FastAPI & WebSocket ❤️**

</div>