# دليل تشغيل نظام بيت الخلوة على Render.com (مجاناً 100% وبدون أي فيزا)

---

## 🌟 لماذا يعتبر Render الخيار الأسهل؟
- **مجاني 100%**.
- **لا يطلب أي بطاقة بنكية أو فيزا إطلاقاً**.
- يمنحك رابطاً سحابياً سريعاً ومشفراً بـ **HTTPS** (`https://demiana-retreat-system.onrender.com`).
- يدعم Python و FastAPI وتوليد ملفات الـ PDF وقواعد البيانات مباشرة.

---

## 🚀 خطوات النشر على Render.com خطوة بخطوة:

### الخطوة 1: التسجيل في موقع Render
1. ادخل على الرابط: [https://dashboard.render.com/register](https://dashboard.render.com/register)
2. سجل باستخدام حساب **GitHub** أو بريدك الإلكتروني **Google (Gmail)** مباشرة.
   *(لن يطلب منك إدخال أي وسيلة دفع أو فيزا).*

---

### الخطوة 2: إنشاء خدمة الويب (Web Service)
1. من لوحة تحكم Render، اضغط على زر **+ New** في الأعلى واختر **Web Service**.
2. اختر مستودع **GitHub** الخاص بالمشروع (أو اربطه به).
3. اضغط **Connect**.

---

### الخطوة 3: ملء إعدادات التشغيل البسيطة:
- **Name (الاسم)**: `demiana-retreat-system`
- **Region (المنطقة)**: `Frankfurt (EU Central)` *(الأسرع لمصر)*
- **Language / Environment**: `Python 3`
- **Branch**: `main` (أو الفرع الحالي)
- **Build Command**:
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command**:
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```
- **Plan Type**: اختر الخطة المجانية **Free ($0/month)**.

---

### الخطوة 4: إضافة المتغيرات البيئية (Environment Variables)
اضغط على **Advanced** ➔ **Add Environment Variable** وأضف:
- `ENVIRONMENT` = `production`
- `SECRET_KEY` = `DemianaMonasteryRetreatSecretKey2026SuperSecure`
- `DATABASE_URL` = `sqlite+aiosqlite:///./data/demiana.db`
- `UPLOAD_DIR` = `./uploads`

---

### الخطوة 5: الضغط على Deploy
- اضغط على زر **Create Web Service**.
- سيبدأ Render تلقائياً في تثبيت المكتبات وتشغيل النظام، وخلال دقيقة سيظهر لك رابط موقعك المباشر في أعلى الصفحة باللون الأخضر مثل:
  `https://demiana-retreat-system.onrender.com`

---

## 🔑 بيانات الدخول للوحة الأم المسؤولة:
- **البريد الإلكتروني**: `mother.superior@demiana.org`
- **كلمة المرور**: `Demiana@2026#Monastery`
