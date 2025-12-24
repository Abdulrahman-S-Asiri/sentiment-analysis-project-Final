# 🚀 دليل تشغيل المشروع | Project Startup Guide

## 📋 المتطلبات | Requirements

1. **Python 3.8+** مثبت على النظام
2. **MySQL** يعمل ومتاح
3. **قاعدة بيانات** باسم `sentiment_db` (سيتم إنشاؤها تلقائياً)

---

## 🔧 خطوات التشغيل | Setup Steps

### 1️⃣ إنشاء بيئة Python الافتراضية (Virtual Environment)

```bash
# إنشاء البيئة
python -m venv venv

# تفعيل البيئة
# على Windows:
venv\Scripts\activate

# على Linux/Mac:
source venv/bin/activate
```

### 2️⃣ تثبيت المكتبات المطلوبة

```bash
pip install -r requirements.txt
```

**ملاحظة:** قد يستغرق التثبيت وقتاً طويلاً بسبب `torch` و `transformers`

### 3️⃣ إعداد قاعدة البيانات

#### أ) تأكد أن MySQL يعمل:
```bash
# تحقق من حالة MySQL
# على Windows (إذا كان مثبت كخدمة):
# افتح Services وابحث عن MySQL

# أو من Command Prompt:
mysql --version
```

#### ب) أنشئ قاعدة البيانات:
```sql
CREATE DATABASE IF NOT EXISTS sentiment_db;
```

أو استخدم MySQL Workbench أو أي أداة أخرى لإنشاء قاعدة البيانات.

### 4️⃣ تعديل ملف `.env` (إذا لزم الأمر)

افتح ملف `.env` وتأكد من:
- ✅ `DATABASE_PASSWORD` - كلمة مرور MySQL الخاصة بك
- ✅ `DATABASE_USERNAME` - اسم المستخدم (افتراضي: root)
- ✅ `DATABASE_HOST` - عنوان الخادم (افتراضي: localhost)
- ✅ `SECRET_KEY` - موجود بالفعل (تم إنشاؤه تلقائياً)

### 5️⃣ تشغيل التطبيق

```bash
uvicorn main:app --reload
```

**الخيارات:**
- `--reload` - لإعادة التحميل التلقائي عند تغيير الكود (للتطوير)
- `--host 0.0.0.0` - للوصول من أجهزة أخرى على الشبكة
- `--port 8000` - لتغيير المنفذ (افتراضي: 8000)

### 6️⃣ الوصول للتطبيق

بعد التشغيل، افتح المتصفح على:

- 🌐 **واجهة API (Swagger):** http://127.0.0.1:8000/docs
- 🏠 **الصفحة الرئيسية:** http://127.0.0.1:8000/home
- 📊 **صفحة التحليل:** http://127.0.0.1:8000/analyze
- 🔐 **صفحة تسجيل الدخول:** http://127.0.0.1:8000/login
- 📝 **صفحة التسجيل:** http://127.0.0.1:8000/register
- 📜 **صفحة التاريخ:** http://127.0.0.1:8000/history-page
- ❤️ **صفحة About:** http://127.0.0.1:8000/about
- ✅ **Health Check:** http://127.0.0.1:8000/health

---

## 🧪 اختبار التطبيق | Testing

### اختبار سريع من Terminal:

```bash
# اختبار Health Check
curl http://127.0.0.1:8000/health

# أو استخدم PowerShell:
Invoke-WebRequest -Uri http://127.0.0.1:8000/health
```

### اختبار من Swagger UI:

1. افتح: http://127.0.0.1:8000/docs
2. جرب endpoint `/auth/register` لإنشاء مستخدم جديد
3. جرب endpoint `/auth/login` للحصول على token
4. استخدم Token في `/predict/` لتحليل نص

---

## ⚠️ حل المشاكل الشائعة | Troubleshooting

### مشكلة: "ModuleNotFoundError"

**الحل:**
```bash
# تأكد من تفعيل البيئة الافتراضية
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# أعد تثبيت المكتبات
pip install -r requirements.txt
```

### مشكلة: "Can't connect to MySQL server"

**الحل:**
1. تأكد أن MySQL يعمل
2. تحقق من بيانات الاتصال في `.env`
3. تأكد من إنشاء قاعدة البيانات `sentiment_db`

### مشكلة: "SECRET_KEY not set"

**الحل:**
- تأكد من وجود ملف `.env` في المجلد الرئيسي
- تحقق من أن `SECRET_KEY` موجود في الملف

### مشكلة: "Port 8000 already in use"

**الحل:**
```bash
# استخدم منفذ آخر
uvicorn main:app --reload --port 8001
```

### مشكلة: بطء تحميل النموذج

**هذا طبيعي!** النموذج كبير ويحتاج وقت للتحميل أول مرة.

---

## 📝 ملاحظات مهمة | Important Notes

1. ✅ ملف `.env` موجود في `.gitignore` ولن يتم رفعه للـ Git
2. ✅ قاعدة البيانات ستُنشأ تلقائياً عند أول تشغيل
3. ✅ الجداول ستُنشأ تلقائياً عند أول تشغيل
4. ⚠️ تأكد من تغيير `SECRET_KEY` و `DATABASE_PASSWORD` في الإنتاج

---

## 🎯 الخطوات السريعة | Quick Start

```bash
# 1. تفعيل البيئة
venv\Scripts\activate

# 2. تشغيل التطبيق
uvicorn main:app --reload

# 3. افتح المتصفح
start http://127.0.0.1:8000/docs
```

---

**تم التحديث:** 2025-01-27  
**الحالة:** ✅ جاهز للتشغيل

