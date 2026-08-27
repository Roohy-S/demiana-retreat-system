import random
import string
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib
from app.config import settings

logger = logging.getLogger(__name__)

def generate_otp_code() -> str:
    """Generate a secure 6-digit numeric verification code."""
    return "".join(random.choices(string.digits, k=6))

def build_verification_email_html(recipient_name: str, otp_code: str) -> str:
    """Build a spiritual, monastic-themed HTML email template for Saint Demiana Monastery."""
    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <style>
    body {{
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background-color: #0b1a2b;
      color: #333333;
      margin: 0;
      padding: 20px;
      direction: rtl;
    }}
    .email-card {{
      max-width: 550px;
      margin: 0 auto;
      background: #ffffff;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 10px 30px rgba(0,0,0,0.3);
      border: 1px solid #d4af37;
    }}
    .email-header {{
      background: linear-gradient(135deg, #0b1a2b 0%, #1e3a5f 100%);
      color: #ffffff;
      text-align: center;
      padding: 30px 20px;
      border-bottom: 3px solid #d4af37;
    }}
    .cross-symbol {{
      font-size: 32px;
      color: #d4af37;
      margin-bottom: 8px;
    }}
    .monastery-title {{
      font-size: 20px;
      font-weight: bold;
      color: #f3e5ab;
      margin: 0;
    }}
    .monastery-subtitle {{
      font-size: 13px;
      color: #cbd5e1;
      margin-top: 4px;
    }}
    .verse {{
      font-style: italic;
      font-size: 13px;
      color: #d4af37;
      margin-top: 10px;
    }}
    .email-body {{
      padding: 30px;
      line-height: 1.8;
      color: #2c3e50;
    }}
    .greeting {{
      font-size: 16px;
      font-weight: bold;
      margin-bottom: 15px;
    }}
    .otp-container {{
      background: #f8fafc;
      border: 2px dashed #d4af37;
      border-radius: 10px;
      text-align: center;
      padding: 20px;
      margin: 25px 0;
    }}
    .otp-label {{
      font-size: 13px;
      color: #64748b;
      margin-bottom: 8px;
    }}
    .otp-number {{
      font-size: 36px;
      font-weight: 800;
      letter-spacing: 8px;
      color: #0b1a2b;
      font-family: monospace;
    }}
    .expiry-note {{
      font-size: 12px;
      color: #e74c3c;
      margin-top: 8px;
    }}
    .instructions {{
      font-size: 14px;
      color: #475569;
    }}
    .email-footer {{
      background: #f1f5f9;
      text-align: center;
      padding: 18px;
      font-size: 12px;
      color: #64748b;
      border-top: 1px solid #e2e8f0;
    }}
  </style>
</head>
<body>
  <div class="email-card">
    <div class="email-header">
      <div class="cross-symbol">☩</div>
      <h1 class="monastery-title">بيت الخلوة بدير القديسة دميانة</h1>
      <div class="monastery-subtitle">ببراري بلقاس – محافظة الدقهلية</div>
      <div class="verse">«تَعَالَوْا أَنْتُمْ مُنْفَرِدِينَ إِلَى مَوْضِعٍ خَلاَءٍ وَاسْتَرِيحُوا قَلِيلاً»</div>
    </div>
    
    <div class="email-body">
      <div class="greeting">سلام ونعمة بركة القديسة دميانة والأربعين عذراء معكِ يا {recipient_name}،</div>
      <p class="instructions">
        نشكركِ على التسجيل في النظام الإلكتروني لبيت الخلوة بدير القديسة دميانة ببراري بلقاس. 
        لتأكيد حسابكِ وتفعيل تسجيلكِ، يرجى إدخال رمز التحقق التالي في الموقع:
      </p>
      
      <div class="otp-container">
        <div class="otp-label">رمز التحقق لتفعيل الحساب (OTP)</div>
        <div class="otp-number">{otp_code}</div>
        <div class="expiry-note">⏱️ الرمز صالح لمدة {settings.EMAIL_VERIFICATION_EXPIRY_MINUTES} دقيقة فقط للاستخدام لمرة واحدة.</div>
      </div>

      <p class="instructions" style="font-size:12px; color:#94a3b8;">
        إذا لم تقومي بإنشاء حساب في بيت الخلوة، يمكنكِ تجاهل هذه الرسالة بأمان.
      </p>
    </div>

    <div class="email-footer">
      دير الشهيدة العفيفة القديسة دميانة والأربعين عذراء بالبراري<br>
      هذه رسالة آلية صادرة من نظام الحجز الإلكتروني الرسمي
    </div>
  </div>
</body>
</html>
"""

def build_password_reset_email_html(recipient_name: str, otp_code: str) -> str:
    """Build a secure HTML email template for password reset."""
    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <style>
    body {{
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background-color: #0b1a2b;
      color: #333333;
      margin: 0;
      padding: 20px;
      direction: rtl;
    }}
    .email-card {{
      max-width: 550px;
      margin: 0 auto;
      background: #ffffff;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 10px 30px rgba(0,0,0,0.3);
      border: 1px solid #d4af37;
    }}
    .email-header {{
      background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
      color: #ffffff;
      text-align: center;
      padding: 30px 20px;
      border-bottom: 3px solid #d4af37;
    }}
    .cross-symbol {{
      font-size: 32px;
      color: #d4af37;
      margin-bottom: 8px;
    }}
    .monastery-title {{
      font-size: 20px;
      font-weight: bold;
      color: #f3e5ab;
      margin: 0;
    }}
    .monastery-subtitle {{
      font-size: 13px;
      color: #cbd5e1;
      margin-top: 4px;
    }}
    .email-body {{
      padding: 30px;
      line-height: 1.8;
      color: #2c3e50;
    }}
    .greeting {{
      font-size: 16px;
      font-weight: bold;
      margin-bottom: 15px;
    }}
    .otp-container {{
      background: #fffbeb;
      border: 2px dashed #f59e0b;
      border-radius: 10px;
      text-align: center;
      padding: 20px;
      margin: 25px 0;
    }}
    .otp-label {{
      font-size: 13px;
      color: #92400e;
      margin-bottom: 8px;
      font-weight: bold;
    }}
    .otp-number {{
      font-size: 36px;
      font-weight: 800;
      letter-spacing: 8px;
      color: #78350f;
      font-family: monospace;
    }}
    .expiry-note {{
      font-size: 12px;
      color: #dc2626;
      margin-top: 8px;
    }}
    .instructions {{
      font-size: 14px;
      color: #475569;
    }}
    .email-footer {{
      background: #f1f5f9;
      text-align: center;
      padding: 18px;
      font-size: 12px;
      color: #64748b;
      border-top: 1px solid #e2e8f0;
    }}
  </style>
</head>
<body>
  <div class="email-card">
    <div class="email-header">
      <div class="cross-symbol">☩</div>
      <h1 class="monastery-title">بيت الخلوة بدير القديسة دميانة</h1>
      <div class="monastery-subtitle">إعادة تعيين كلمة المرور</div>
    </div>
    
    <div class="email-body">
      <div class="greeting">سلام ونعمة يا {recipient_name}،</div>
      <p class="instructions">
        تلقينا طلباً لإعادة تعيين كلمة المرور الخاصة بحسابكِ في نظام بيت الخلوة بدير القديسة دميانة.
        يرجى استخدام رمز التحقق التالي لإتمام تعيين كلمة المرور الجديدة:
      </p>
      
      <div class="otp-container">
        <div class="otp-label">رمز إعادة تعيين كلمة المرور (OTP)</div>
        <div class="otp-number">{otp_code}</div>
        <div class="expiry-note">⏱️ الرمز صالح لمدة 15 دقيقة فقط. لا تشاركي هذا الرمز مع أي شخص.</div>
      </div>

      <p class="instructions" style="font-size:12px; color:#94a3b8;">
        إذا لم تطلبي استعادة كلمة المرور، يمكنكِ تجاهل هذه الرسالة بأمان وسيظل حسابكِ محمياً.
      </p>
    </div>

    <div class="email-footer">
      دير الشهيدة العفيفة القديسة دميانة والأربعين عذراء بالبراري<br>
      الأمان وخصوصية البيانات
    </div>
  </div>
</body>
</html>
"""

async def send_verification_email(recipient_email: str, recipient_name: str, otp_code: str) -> bool:
    """
    Send OTP verification email via Gmail SMTP or log in dev mode if credentials missing.
    """
    html_content = build_verification_email_html(recipient_name, otp_code)
    
    message = MIMEMultipart("alternative")
    message["Subject"] = f"رمز تأكيد حساب بيت الخلوة بدير القديسة دميانة: {otp_code}"
    message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_USER or 'noreply@demiana-monastery.org'}>"
    message["To"] = recipient_email

    part = MIMEText(html_content, "html", "utf-8")
    message.attach(part)

    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print("\n=========================================================================")
        print(f"📧 [EMAIL SIMULATOR] رسالة تأكيد حساب إلى: {recipient_email}")
        print(f"👤 الاسم: {recipient_name}")
        print(f"🔑 رمز التحقق (OTP): {otp_code}")
        print(f"ℹ️ لتفعيل الإرسال الحقيقي للـ Gmail، ضع SMTP_USER و SMTP_PASSWORD في ملف .env")
        print("=========================================================================\n")
        return True

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            start_tls=settings.SMTP_USE_TLS,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            timeout=15
        )
        print(f"[SUCCESS] Verification email successfully dispatched to {recipient_email} via Gmail SMTP.")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email}: {e}")
        print(f"[ERROR] فشل إرسال البريد عبر Gmail SMTP: {str(e)}")
        print(f"🔑 [FALLBACK OTP] رمز التحقق لحساب {recipient_email} هو: {otp_code}")
        return False

async def send_password_reset_email(recipient_email: str, recipient_name: str, otp_code: str) -> bool:
    """
    Send password reset OTP email via Gmail SMTP or log in dev mode.
    """
    html_content = build_password_reset_email_html(recipient_name, otp_code)
    
    message = MIMEMultipart("alternative")
    message["Subject"] = f"رمز إعادة تعيين كلمة المرور - دير القديسة دميانة: {otp_code}"
    message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_USER or 'noreply@demiana-monastery.org'}>"
    message["To"] = recipient_email

    part = MIMEText(html_content, "html", "utf-8")
    message.attach(part)

    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print("\n=========================================================================")
        print(f"🔒 [EMAIL SIMULATOR] رسالة إعادة تعيين كلمة المرور إلى: {recipient_email}")
        print(f"👤 الاسم: {recipient_name}")
        print(f"🔑 رمز الاستعادة (OTP): {otp_code}")
        print("=========================================================================\n")
        return True

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            start_tls=settings.SMTP_USE_TLS,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            timeout=15
        )
        print(f"[SUCCESS] Password reset email dispatched to {recipient_email} via Gmail SMTP.")
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset email to {recipient_email}: {e}")
        print(f"🔑 [FALLBACK RESET OTP] رمز استعادة الحساب لـ {recipient_email} هو: {otp_code}")
        return False
