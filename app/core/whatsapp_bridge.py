import urllib.parse
import re
from datetime import datetime, timezone
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.profile import Profile
from app.models.user import User
from app.models.notification import CommunicationLog

WHATSAPP_TEMPLATES: Dict[str, str] = {
    "APPROVAL": "سلام ونعمة من دير القديسة دميانة ببراري بلقاس. يسرنا إبلاغكِ بالموافقة على طلب الخلوة رقم {ref} للفترة {period} (من {start_date} إلى {end_date}). موعد الوصول الساعة 12:00 ظهراً. برجاء إحضار أصل البطاقة الشخصية والأجبية والكتاب المقدس.",
    "WAITLIST": "سلام ونعمة من بيت الخلوة بدير القديسة دميانة. تم تسجيل طلبكِ رقم {ref} لفترة {period} في قائمة الانتظار لاكتمال السعة الاستيعابية. سيصلكِ إشعار فور توفر أي مكان.",
    "REJECTION": "سلام ونعمة من دير القديسة دميانة. نعتذر عن عدم إمكانية قبول طلب الخلوة رقم {ref} لهذه الفترة. نرجو لكِ كل البركة والنعمة.",
    "EXTENSION_APPROVED": "سلام ونعمة. تمت موافقة الأم المسؤولة على طلب تمديد فترة الخلوة الخاص بكِ.",
    "ADMIN_CONTACT": "سلام ونعمة من إدارة بيت الخلوة بدير القديسة دميانة. نرجو التواصل معنا للأهمية بخصوص حجزكِ.",
}

def format_whatsapp_message(template_name: str, params: dict, custom_text: Optional[str] = None) -> str:
    if custom_text:
        return custom_text
    template = WHATSAPP_TEMPLATES.get(template_name, WHATSAPP_TEMPLATES["ADMIN_CONTACT"])
    
    # Safe formatting that does not raise KeyError on missing keys
    def replacer(match):
        key = match.group(1)
        return str(params.get(key, ""))

    return re.sub(r"\{([a-zA-Z0-9_]+)\}", replacer, template)

async def dispatch_whatsapp_message(
    db: AsyncSession,
    profile: Profile,
    admin_user: User,
    template_name: Optional[str],
    custom_message: Optional[str] = None,
    template_params: Optional[dict] = None
) -> Dict[str, str]:
    params = template_params or {}
    params.setdefault("name", profile.full_name)
    params.setdefault("ref", "")
    params.setdefault("period", "")
    params.setdefault("start_date", "")
    params.setdefault("end_date", "")

    final_text = format_whatsapp_message(template_name or "ADMIN_CONTACT", params, custom_message)
    
    # Format phone number for WhatsApp URL (e.g. 010... -> 2010...)
    clean_phone = profile.phone_number.replace("+", "").replace(" ", "").replace("-", "")
    if clean_phone.startswith("0"):
        clean_phone = "2" + clean_phone
    elif not clean_phone.startswith("2") and len(clean_phone) == 10:
        clean_phone = "20" + clean_phone

    encoded_text = urllib.parse.quote(final_text)
    wa_direct_link = f"https://wa.me/{clean_phone}?text={encoded_text}"

    # Record log
    log = CommunicationLog(
        profile_id=profile.id,
        sender_user_id=admin_user.id,
        channel="WHATSAPP",
        recipient_phone_or_email=clean_phone,
        message_template_name=template_name or "CUSTOM",
        message_content=final_text,
        delivery_status="SENT",
        sent_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    db.add(log)
    await db.flush()

    return {
        "log_id": log.id,
        "phone": clean_phone,
        "message": final_text,
        "direct_link": wa_direct_link,
        "delivery_status": "SENT"
    }
