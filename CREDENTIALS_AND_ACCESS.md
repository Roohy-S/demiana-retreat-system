# 🔐 دليل بيانات تسجيل الدخول والوصول للنظام
# Demiana Retreat Management System - Access & Credentials Reference

هذا الملف يحتوي على كافة البيانات السرية وحسابات تسجيل الدخول الخاصة بنظام بيت الخلوة بدير القديسة دميانة ببراري بلقاس وقاعدة بيانات Supabase السحابية.

---

## 1. 🗄️ بيانات قاعدة بيانات سوبابيز (Supabase Cloud PostgreSQL)

- **رابط مشروع سوبابيز (Supabase Project URL):**
  `https://ekxcvnkgkueiqkttikwp.supabase.co`
- **معرف المشروع (Project Reference ID):**
  `ekxcvnkgkueiqkttikwp`
- **منطقة الاستضافة (Region):**
  `AWS EU Central 1 (Frankfurt / ألمانيا)`
- **اسم المستخدم لقاعدة البيانات (DB User):**
  `postgres.ekxcvnkgkueiqkttikwp`
- **كلمة مرور قاعدة البيانات (DB Password):**
  `Demiana@2026`
- **رابط الاتصال الكامل (SQLAlchemy / Backend Async Connection String):**
  `postgresql://postgres.ekxcvnkgkueiqkttikwp:Demiana%402026@aws-0-eu-central-1.pooler.supabase.com:6543/postgres`
- **رابط الاتصال المباشر (Direct Session Mode - Port 5432):**
  `postgresql://postgres.ekxcvnkgkueiqkttikwp:Demiana%402026@aws-0-eu-central-1.pooler.supabase.com:5432/postgres`

---

## 2. 👑 حسابات الأم المسؤولة (Mother Superior Admin Dashboard)

تتيح هذه الحسابات الصلاحية الإدارية الكاملة: إدارة المشرفات، قبول/رفض طلبات الاستثناء، إضافة وتعديل الملاحظات السلوكية والمخالفات، إدارة الفترات، وإعدادات بيت الخلوة.

### الحساب الرسمي الأول:
- **البريد الإلكتروني:** `mother@stdemiana.org`
- **كلمة المرور:** `MotherAdmin@123`
- **الدور الوظيفي:** الأم المسؤولة (`MOTHER_SUPERIOR`)

### الحساب الإضافي:
- **البريد الإلكتروني:** `mother.superior@demiana-monastery.org`
- **كلمة المرور:** `MotherSuperior2026!`
- **الدور الوظيفي:** الأم المسؤولة (`MOTHER_SUPERIOR`)

---

## 3. 👩‍💼 حسابات المشرفات ولجنة الحجوزات والاستقبال (Staff & Supervisors)

### أ. مشرفة الحجوزات الرئيسية (Booking Supervisor):
- **البريد الإلكتروني:** `supervisor@stdemiana.org`
- **كلمة المرور:** `Supervisor@123`
- **الدور الوظيفي:** مشرفة حجوزات (`BOOKING_SUPERVISOR`)
- **الصلاحيات:** فحص الطلبات، مراجعة المستندات والبطاقات، فرز قوائم الانتظار، إرسال رسائل واتساب.

### ب. مسؤولة الاستقبال وبوابة الدير (Reception Supervisor):
- **البريد الإلكتروني:** `reception@demiana-monastery.org`
- **كلمة المرور:** `Reception2026!`
- **الدور الوظيفي:** مسؤولة الاستقبال (`RECEPTION_SUPERVISOR`)
- **الصلاحيات:** تسجيل الوصول والانصراف في كشف البوابة اليومي، تسكين القلالي والغرف، تحميل كشوف الحضور PDF.

### ج. مسؤولة فرز الحجوزات الإضافية:
- **البريد الإلكتروني:** `booking.staff@demiana-monastery.org`
- **كلمة المرور:** `BookingStaff2026!`
- **الدور الوظيفي:** مشرفة حجوزات (`BOOKING_SUPERVISOR`)

---

## 4. 🙋‍♀️ حسابات تجريبية للمتقدمات (Applicant Test Accounts)

| الاسم الكامل | البريد الإلكتروني | الهاتف | الرقم القومي | كلمة المرور | الحالة التجريبية |
|---|---|---|---|---|---|
| **ماريا فايز حبيب** | `maria@example.com` | `01012345678` | `29904120101248` | `Guest@12345` | حجز مقبول في الفترة القادمة |
| **ليلى عبد المسيح** | `laila@example.com` | `01223344556` | `30010050201242` | `Guest@12345` | عليها ملاحظة سلوكية سابقة وتنبيه نشط |
| **رانيا جرجس أسعد** | `rania@example.com` | `01144556677` | `29706202401244` | `Guest@12345` | طلب استثناء فاصل زمني (أقل من 3 أشهر) |
| **سارة يوسف حنا** | `sarah@example.com` | `01098765432` | `30208151201246` | `Guest@12345` | مدرجة في قائمة الانتظار (Waitlist #1) |
| **فيرينا سمير رشدي** | `verena@example.com` | `01555667788` | `29811301401248` | `Guest@12345` | مقيمة حالياً بالقلاية 7 ولديها طلب تمديد |

*(ملاحظة: يدعم النظام تسجيل الدخول بالبريد الإلكتروني، أو برقم الهاتف، أو بالرقم القومي مع نفس كلمة المرور).*

---

## 5. 🛡️ مفاتيح الأمان والتشفير (System Security & Tokens)

- **JWT Secret Key:** `demiana_monastery_retreat_super_secret_jwt_key_2026_prod`
- **خوارزمية التشفير:** `HS256`
- **مدة صلاحية الجلسة:** 7 أيام (`60 * 24 * 7` دقيقة)

---

## 6. 🚀 أوامر التشغيل السريع للمشروع

### تشغيل خادم النظام (FastAPI Server):
```powershell
python -m uvicorn app.main:app --reload --port 8000
```
- **الواجهة الرئيسية للنظام:** `http://127.0.0.1:8000`
- **لوحة التحكم الإدارية:** `http://127.0.0.1:8000/admin`
- **التوثيق التفاعلي للـ API (Swagger UI):** `http://127.0.0.1:8000/docs`

### إعادة تهيئة وتحديث قاعدة بيانات Supabase:
```powershell
python seed_data.py
```

### تشغيل حزمة الاختبارات الآلية (Pytest):
```powershell
python -m pytest
```

---

## 7. 📧 إعدادات خادم البريد الإلكتروني الحقيقي (Production Gmail SMTP)

- **مزود الخدمة:** `Google Gmail SMTP (TLS 587)`
- **حساب الإرسال (Sender Email):** `roohhamza25@gmail.com`
- **اسم المرسل:** `بيت الخلوة – دير القديسة دميانة ببراري بلقاس`
- **كلمة مرور التطبيق (App Password):** `bhmizaqnmdkjyoem`
- **حالة التحقق الحقيقي:** مفعلة وشغالة 100% وتصل مباشرة إلى صندوق الوارد (Inbox).
