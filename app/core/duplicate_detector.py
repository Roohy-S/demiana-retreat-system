import re
from datetime import datetime, date
from typing import Optional, Tuple, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_

from app.models.user import User
from app.models.profile import Profile, Guardian, ConfessionFather

# Egyptian Governorate codes mapping in National ID
GOVERNORATE_CODES = {
    "01": "القاهرة",
    "02": "الإسكندرية",
    "03": "بورسعيد",
    "04": "السويس",
    "11": "دمياط",
    "12": "الدقهلية",
    "13": "الشرقية",
    "14": "القليوبية",
    "15": "كفر الشيخ",
    "16": "الغربية",
    "17": "المنوفية",
    "18": "البحيرة",
    "19": "الإسماعيلية",
    "21": "الجيزة",
    "22": "بني سويف",
    "23": "الفيوم",
    "24": "المنيا",
    "25": "أسيوط",
    "26": "سوهاج",
    "27": "قنا",
    "28": "أسوان",
    "29": "الأقصر",
    "31": "البحر الأحمر",
    "32": "الوادي الجديد",
    "33": "مطروح",
    "34": "شمال سيناء",
    "35": "جنوب سيناء",
    "88": "مواليد خارج الجمهورية"
}

def normalize_arabic_text(text: str) -> str:
    """
    Standardize Arabic text to eliminate orthographic variations:
    - Normalizes Hamzas (أ, إ, آ, ٱ -> ا)
    - Normalizes Taa Marbouta (ة -> ه)
    - Normalizes Alef Maqsura (ى -> ي)
    - Removes all Arabic diacritics / Tashkeel & Tatweel
    - Collapses whitespaces and strips punctuation
    """
    if not text:
        return ""
    
    s = text.strip()
    # Remove Tashkeel
    s = re.sub(r"[\u064B-\u0652\u0670\u0640]", "", s)
    # Normalize Alef forms
    s = re.sub(r"[أإآٱ]", "ا", s)
    # Normalize Taa Marbouta
    s = re.sub(r"ة", "ه", s)
    # Normalize Alef Maqsura
    s = re.sub(r"ى", "ي", s)
    # Remove non-alphanumeric punctuation
    s = re.sub(r"[^\w\s]", " ", s)
    # Collapse multiple whitespaces
    s = re.sub(r"\s+", " ", s).strip()
    return s.lower()

def clean_egyptian_phone(phone: str) -> str:
    """Standardize Egyptian phone number to 11 digits format (01XXXXXXXXX)."""
    if not phone:
        return ""
    p = phone.strip().replace(" ", "").replace("+2", "").replace("-", "").replace("(", "").replace(")", "")
    if p.startswith("002"):
        p = p[3:]
    return p

def validate_egyptian_national_id(
    national_id: str,
    expected_birth_date: Optional[date] = None,
    expected_governorate: Optional[str] = None
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validate an Egyptian 14-digit National ID card number:
    - Must be exactly 14 digits.
    - Century digit: 2 for 1900-1999, 3 for 2000-2099.
    - Encoded Birth date: YY MM DD.
    - Governorate code: 2 digits.
    - Gender digit: 13th digit (even for females, odd for males).
    
    Returns (is_valid, error_or_success_message, metadata_dict).
    """
    nid = national_id.strip() if national_id else ""
    if not re.match(r"^\d{14}$", nid):
        return False, "الرقم القومي يجب أن يتكون من 14 رقماً بالتمام والكمال.", {}

    century_digit = nid[0]
    if century_digit not in ("2", "3"):
        return False, "الرقم القومي غير صحيح (خانة القرن غير صالحة).", {}

    year_prefix = "19" if century_digit == "2" else "20"
    year_str = year_prefix + nid[1:3]
    month_str = nid[3:5]
    day_str = nid[5:7]

    try:
        birth_year = int(year_str)
        birth_month = int(month_str)
        birth_day = int(day_str)
        extracted_birth_date = date(birth_year, birth_month, birth_day)
    except ValueError:
        return False, "الرقم القومي يحتوي على تاريخ ميلاد غير صحيح أو غير منطقي.", {}

    # Check future or improbable birth date
    if extracted_birth_date > date.today() or extracted_birth_date < date(1920, 1, 1):
        return False, "تاريخ الميلاد المستخرج من الرقم القومي غير منطقي.", {}

    gov_code = nid[7:9]
    gov_name = GOVERNORATE_CODES.get(gov_code, "غير معروف")

    # Check if birth date matches supplied expected birth date
    if expected_birth_date and extracted_birth_date != expected_birth_date:
        return False, (
            f"تاريخ الميلاد المدخل ({expected_birth_date}) غير متطابق مع تاريخ الميلاد المسجل بالرقم القومي ({extracted_birth_date}). "
            "يرجى التأكد من كتابة الرقم القومي وتاريخ الميلاد بشكل صحيح."
        ), {}

    meta = {
        "birth_date": extracted_birth_date,
        "governorate_code": gov_code,
        "governorate_name": gov_name,
        "gender_digit": int(nid[12]),
        "is_female": int(nid[12]) % 2 == 0
    }

    return True, "الرقم القومي صحيح ومطابق.", meta

async def check_registration_duplicates(
    db: AsyncSession,
    email: str,
    phone_number: str,
    national_id_number: Optional[str],
    full_name: str,
    birth_date: date
) -> Tuple[bool, str, Optional[str]]:
    """
    Perform a comprehensive multi-layered duplicate detection check:
    1. Check for existing User by Email.
    2. Check for existing Profile by Phone Number.
    3. Check for existing Profile by National ID Number.
    4. Check for existing Profile by Identity Profile Match (Normalized Arabic Name + Birth Date).
    
    Returns (has_duplicate, error_message, duplicate_type).
    """
    clean_email = email.strip().lower()
    clean_phone = clean_egyptian_phone(phone_number)
    clean_nid = national_id_number.strip() if national_id_number else None
    norm_new_name = normalize_arabic_text(full_name)

    # 1. Exact Email Check
    stmt_email = select(User).where(User.email == clean_email)
    res_email = await db.execute(stmt_email)
    existing_user_email = res_email.scalar_one_or_none()
    if existing_user_email:
        if not existing_user_email.is_verified:
            return True, "EMAIL_UNVERIFIED", "EMAIL_UNVERIFIED"
        return True, "البريد الإلكتروني مسجل ومفعّل بالفعل لحساب قائم. يرجى تسجيل الدخول مباشرة أو طلب استعادة كلمة المرور.", "EMAIL_EXISTS"

    # 2. Exact Phone Number Check
    stmt_phone = select(Profile).where(Profile.phone_number == clean_phone)
    res_phone = await db.execute(stmt_phone)
    existing_profile_phone = res_phone.scalar_one_or_none()
    if existing_profile_phone:
        return True, (
            f"رقم الهاتف ({clean_phone}) مسجل بالفعل باسم متقدمة أخرى في النظام. "
            "لا يمكن استخدام نفس رقم الهاتف لإنشاء حساب ثانٍ. إذا كنتِ صاحبة الحساب، يمكنكِ تسجيل الدخول برقم هاتفكِ مباشرة."
        ), "PHONE_EXISTS"

    # 3. Exact National ID Check
    if clean_nid:
        stmt_nid = select(Profile).where(Profile.national_id_number == clean_nid)
        res_nid = await db.execute(stmt_nid)
        existing_profile_nid = res_nid.scalar_one_or_none()
        if existing_profile_nid:
            return True, (
                f"الرقم القومي ({clean_nid}) مسجل بالفعل بالنظام. "
                "لا يمكن تسجيل نفس المتقدمة أكثر من مرة بالرقم القومي الخاص بها. يرجى تسجيل الدخول أو التواصل مع إدارة الدير."
            ), "NATIONAL_ID_EXISTS"

    # 4. Identity Match: Normalized Arabic Name + Birth Date Check
    stmt_identity = select(Profile).where(Profile.birth_date == birth_date)
    res_identity = await db.execute(stmt_identity)
    same_birthdate_profiles = res_identity.scalars().all()

    for p in same_birthdate_profiles:
        norm_existing_name = normalize_arabic_text(p.full_name)
        # Check if normalized names are identical or have strong sub-sequence match
        if norm_existing_name == norm_new_name:
            return True, (
                f"توجد بيانات مسجلة بالفعل لنفس المتقدمة بالاسم ({p.full_name}) وتاريخ الميلاد ({birth_date}). "
                "يمنع النظام تسجيل أكثر من حساب لنفس الشخص. يرجى تسجيل الدخول للحساب السابق أو استعادة كلمة المرور."
            ), "IDENTITY_EXISTS"
        
        # Word-level overlap check (if first 3 words match exactly)
        words_new = norm_new_name.split()
        words_exist = norm_existing_name.split()
        if len(words_new) >= 3 and len(words_exist) >= 3:
            if words_new[:3] == words_exist[:3]:
                return True, (
                    f"توجد بيانات متطابقة لنفس المتقدمة ({p.full_name}) بنفس تاريخ الميلاد. "
                    "يرجى تسجيل الدخول بحسابكِ المسجل مسبقاً بدلاً من إنشاء حساب جديد."
                ), "IDENTITY_SIMILAR"

    return False, "", None

async def find_user_and_profile_by_identifier(
    db: AsyncSession,
    identifier: str
) -> Tuple[Optional[User], Optional[Profile], str]:
    """
    Find user and profile using either:
    1. Email Address (contains @)
    2. Egyptian Mobile Phone Number (11 digits starting with 01)
    3. National ID Card Number (14 digits)
    
    Returns (User, Profile, identifier_type)
    """
    clean_id = identifier.strip()

    # Case 1: Email Address
    if "@" in clean_id:
        clean_email = clean_id.lower()
        stmt = select(User).where(User.email == clean_email)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        profile = None
        if user:
            stmt_prof = select(Profile).where(Profile.user_id == user.id)
            profile = (await db.execute(stmt_prof)).scalar_one_or_none()
        return user, profile, "EMAIL"

    # Case 2: 14-digit National ID
    clean_digits = re.sub(r"\D", "", clean_id)
    if len(clean_digits) == 14:
        stmt_prof = select(Profile).where(Profile.national_id_number == clean_digits)
        res_prof = await db.execute(stmt_prof)
        profile = res_prof.scalar_one_or_none()
        user = None
        if profile and profile.user_id:
            stmt_u = select(User).where(User.id == profile.user_id)
            user = (await db.execute(stmt_u)).scalar_one_or_none()
        return user, profile, "NATIONAL_ID"

    # Case 3: Egyptian Phone Number
    clean_phone = clean_egyptian_phone(clean_id)
    if re.match(r"^01[0125]\d{8}$", clean_phone):
        stmt_prof = select(Profile).where(Profile.phone_number == clean_phone)
        res_prof = await db.execute(stmt_prof)
        profile = res_prof.scalar_one_or_none()
        user = None
        if profile and profile.user_id:
            stmt_u = select(User).where(User.id == profile.user_id)
            user = (await db.execute(stmt_u)).scalar_one_or_none()
        return user, profile, "PHONE"

    # Fallback to direct email search
    stmt = select(User).where(User.email == clean_id.lower())
    user = (await db.execute(stmt)).scalar_one_or_none()
    profile = None
    if user:
        stmt_prof = select(Profile).where(Profile.user_id == user.id)
        profile = (await db.execute(stmt_prof)).scalar_one_or_none()
    return user, profile, "UNKNOWN"
