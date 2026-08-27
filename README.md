# ⛪ نظام إدارة بيت الخلوة – دير القديسة دميانة ببراري بلقاس
### Demiana Monastery Retreat Management & Gate Automation System

نظام إلكتروني لإدارة طلبات الخلوة، فحص الهويات، منع التسجيل المزدوج، وإدارة الاستقبال والتسكين بدير القديسة دميانة ببراري بلقاس.

---

## 🌟 مميزات المنظومة (Key Features)

- 🔒 **منظومة تسجيل ودخول مرنة وآمنة:**
  - تسجيل الدخول المرن عبر (البريد الإلكتروني، أو رقم الهاتف، أو الرقم القومي المكون من 14 رقماً).
  - التحقق من البريد الإلكتروني عبر رمز الأمان OTP مع حظر الإيميلات الوهمية والمؤقتة واكتشاف الأخطاء الإملائية.
  - محرك ذكي ثلاثي لمنع التكرار (Anti-Duplicate Engine) يدعم معالجة وتوحيد الأسماء العربية وفحص الرقم القومي المصري.

- 👑 **لوحة تحكم الأم المسؤولة والمشرفات:**
  - مراجعة طلبات الخلوة، فحص بطاقات الرقم القومي وخطابات أب الاعتراف.
  - نظام الملاحظات والمخالفات الإدارية وتنبيهات التدقيق الأمني للنزيلات.
  - فرز استثناءات الفواصل الزمنية وإدارة قوائم الانتظار التلقائية.
  - إدارة فترات الخلوة والطاقة الاستيعابية.

- 📋 **منظومة الاستقبال وبوابة الدير:**
  - كشوفات الحضور اليومية، تسكين القلالي والغرف، وتأكيد الوصول والمغادرة.
  - توليد وطباعة كشوفات البوابة اليومية والتقارير بصيغة PDF باللغة العربية.

- 💬 **جسر واتساب المباشر:**
  - إرسال إشعارات القبول، التأكيد، والاعتذار مباشرة للنزيلات بنقرة زر واحدة.

---

## 🛠️ التقنيات المستخدمة (Tech Stack)

- **Backend:** FastAPI (Python 3.12+), SQLAlchemy 2.0 Async, Pydantic v2
- **Database:** Supabase PostgreSQL Cloud / SQLite Async
- **Security:** Argon2 / Bcrypt Password Hashing, JWT Tokens, Role-Based Access Control (RBAC)
- **PDF Engine:** ReportLab with Arabic & Unicode Reshaping Support
- **Frontend:** Vanilla Modern HTML5/CSS3/JavaScript (Dark & Light Glassmorphic Theme, Mobile Responsive)

---

## 🚀 التثبيت والتشغيل المحلي (Local Setup)

1. **استنساخ المستودع:**
   ```bash
   git clone https://github.com/Roohy-S/demiana-retreat-system.git
   cd demiana-retreat-system
   ```

2. **تثبيت الاعتماديات:**
   ```bash
   pip install -r requirements.txt
   ```

3. **تهيئة قاعدة البيانات:**
   ```bash
   python seed_data.py
   ```

4. **تشغيل خادم التطوير:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. **فتح النظام في المتصفح:**
   - بوابة الحجز: `http://localhost:8000`
   - لوحة الإدارة: `http://localhost:8000/admin`
   - توثيق الـ API (Swagger): `http://localhost:8000/docs`

---

## 🧪 الاختبارات الآلية (Automated Tests)

```bash
python -m pytest
```

---

## 📄 التراخيص والبيانات السرية
لمزيد من التفاصيل حول بيانات الحسابات الإدارية والتجريبية، يرجى مراجعة ملف [`CREDENTIALS_AND_ACCESS.md`](./CREDENTIALS_AND_ACCESS.md).
