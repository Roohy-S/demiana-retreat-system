# دليل تشغيل نظام بيت الخلوة على سيرفر Oracle Cloud Always Free (مجاناً مدى الحياة)

---

## 🌟 المواصفات المجانية المتاحة من أوراكل (Always Free)
- **المعالج والرامات**: حتى 4 Cores و 24 GB RAM.
- **التخزين**: 200 GB SSD فائق السرعة.
- **التشغيل**: 24 ساعة يومياً طوال العام دون توقف.
- **عنوان IP ثابت وشهادة SSL/HTTPS مجانية**.

---

## 🚀 خطوات الإنشاء والتشغيل خطوة بخطوة:

### الخطوة 1: إنشاء الحساب على Oracle Cloud
1. ادخل على رابط التسجيل المجاني: [https://www.oracle.com/cloud/free/](https://www.oracle.com/cloud/free/)
2. اضغط على **Start for free** واملأ بياناتك (الاسم، البريد الإلكتروني، الدولة).
3. أدخل بطاقة الفيزا/الماستركارد لتأكيد الهوية (يتم خصم ~$1 للتأكيد واسترداده فوراً).

---

### الخطوة 2: إنشاء السيرفر (Compute Instance)
1. من القائمة الرئيسية اختر: **Compute** ➔ **Instances** ➔ اضغط **Create Instance**.
2. **الاسم (Name)**: `demiana-retreat-server`
3. **نظام التشغيل (Image)**: اختر **Ubuntu 22.04 LTS** أو **Ubuntu 24.04 LTS**.
4. **المواصفات (Shape)**: اختر **Ampere (ARM)** أو **AMD (Micro)** وتأكد من وجود شارة *(Always Free Eligible)*.
5. **مفتاح الاتصال (Save SSH Keys)**: اضغط **Save private key** وحفظ الملف على جهازك.
6. اضغط **Create**. (خلال دقيقة سيصبح السيرفر باللون الأخضر *Running* وستحصل على **Public IP Address**).

---

### الخطوة 3: فتح منافذ الويب في أوراكل (Ingress Rules)
1. من صفحة السيرفر اضغط على اسم الشبكة: **Virtual Cloud Network (VCN)**.
2. اضغط على **Security Lists** ➔ ثم **Default Security List**.
3. اضغط **Add Ingress Rules** وأضف المنفذين التاليين:
   - **Source CIDR**: `0.0.0.0/0`
   - **IP Protocol**: `TCP`
   - **Destination Port Range**: `80,443`
4. اضغط **Add Ingress Rules**.

---

### الخطوة 4: تشغيل سكربت الإعداد التلقائي (أمر واحد فقط)
1. اتصل بالسيرفر عبر Terminal أو برنامج **PuTTY / PowerShell**:
   ```bash
   ssh -i /path/to/your-key.key ubuntu@<YOUR_PUBLIC_IP>
   ```
2. انقل ملفات المشروع أو اسحبها من GitHub، ثم ادخل لمجلد المشروع وشغل السكربت التلقائي:
   ```bash
   chmod +x setup_production.sh
   sudo ./setup_production.sh
   ```

---

## 🛠 ماذا سيفعل السكربت تلقائياً؟
1. تثبيت كافة متطلبات النظام وPython ومكتبات توليد ملفات الـ PDF والخطوط القبطية والعربية.
2. إنشاء الخدمة الخلفية المستقلة (`demiana.service`) للتشغيل الدائم وإعادة التشغيل التلقائي عند أي عطل أو إعادة تشغيل للسيرفر.
3. ضبط خادم **Nginx** وتفعيل تسريع ونقل الملفات الكبيرة حتى 50 ميجابايت.
4. ضبط الجدار الناري وحماية السيرفر.
5. توفير أداة الإدارة السريعة `demiana-ctl`:
   - `demiana-ctl status` : عرض حالة السيرفر
   - `demiana-ctl logs`   : متابعة السجلات المباشرة
   - `demiana-ctl restart`: إعادة تشغيل الخدمة
   - `demiana-ctl backup` : أخذ نسخة احتياطية فورية لقاعدة البيانات
   - `demiana-ctl ssl`    : تفعيل شهادة الأمان والتشفير المجانية (HTTPS) لدومينك الرسمي.

---

## 🔑 بيانات الدخول الافتراضية للوحة الأم المسؤولة:
- **الرابط**: `http://<YOUR_PUBLIC_IP>` أو عبر الدومين الخاص بك
- **البريد الإلكتروني**: `mother.superior@demiana.org`
- **كلمة المرور**: `Demiana@2026#Monastery`
