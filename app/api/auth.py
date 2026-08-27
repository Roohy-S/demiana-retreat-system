from datetime import datetime, date, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from app.config import settings
from app.database import get_db
from app.models.user import User, UserRole
from app.models.profile import Profile, Guardian, ConfessionFather
from app.models.email_verification import EmailVerificationCode
from app.schemas.auth import (
    UserRegister, UserLogin, Token, UserOut, UserPasswordChange,
    VerifyEmailRequest, ResendOTPRequest, ForgotPasswordRequest, ResetPasswordRequest,
    CheckDuplicateRequest, CheckDuplicateResponse
)
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, get_current_active_user
)
from app.core.audit import record_audit_log
from app.core.email_service import (
    generate_otp_code, send_verification_email, send_password_reset_email
)
from app.core.email_validator import validate_and_normalize_email
from app.core.duplicate_detector import (
    check_registration_duplicates, find_user_and_profile_by_identifier,
    validate_egyptian_national_id, clean_egyptian_phone, normalize_arabic_text
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

@router.post("/check-duplicate", response_model=CheckDuplicateResponse)
async def check_duplicate_field(payload: CheckDuplicateRequest, db: AsyncSession = Depends(get_db)):
    """
    Live real-time pre-check endpoint for client-side form validation:
    - Checks email validity, deliverability, typos, and availability.
    - Checks phone number uniqueness.
    - Checks national ID validity and uniqueness.
    - Checks identity match (name + birth date).
    """
    field = payload.field.lower()

    if field == "email":
        if not payload.email:
            return CheckDuplicateResponse(is_available=False, message="البريد الإلكتروني مطلوب.")
        try:
            clean_email, typo = validate_and_normalize_email(
                payload.email,
                check_deliverability=True,
                allow_typo_correction=False
            )
        except ValueError as e:
            return CheckDuplicateResponse(
                is_available=False,
                message=str(e),
                duplicate_type="INVALID_EMAIL"
            )

        # Check DB
        stmt = select(User).where(User.email == clean_email)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if user:
            if not user.is_verified:
                return CheckDuplicateResponse(
                    is_available=False,
                    message="هذا البريد مسجل مسبقاً وغير مفعّل. سيتم إرسال رمز تحقق لتفعيله.",
                    duplicate_type="EMAIL_UNVERIFIED"
                )
            return CheckDuplicateResponse(
                is_available=False,
                message="البريد الإلكتروني مسجل بالفعل لنظام بيت الخلوة. يمكنكِ تسجيل الدخول مباشرة.",
                duplicate_type="EMAIL_EXISTS"
            )
        return CheckDuplicateResponse(
            is_available=True,
            message="البريد الإلكتروني متاح وصالح للاستخدام.",
            typo_suggestion=typo
        )

    elif field == "phone":
        if not payload.phone_number:
            return CheckDuplicateResponse(is_available=False, message="رقم الهاتف مطلوب.")
        clean_phone = clean_egyptian_phone(payload.phone_number)
        stmt = select(Profile).where(Profile.phone_number == clean_phone)
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            return CheckDuplicateResponse(
                is_available=False,
                message="رقم الهاتف مسجل بالفعل باسم متقدمة أخرى في النظام.",
                duplicate_type="PHONE_EXISTS"
            )
        return CheckDuplicateResponse(is_available=True, message="رقم الهاتف متاح.")

    elif field == "national_id":
        if not payload.national_id_number:
            return CheckDuplicateResponse(is_available=False, message="الرقم القومي مطلوب.")
        b_date = None
        if payload.birth_date:
            try:
                b_date = datetime.strptime(payload.birth_date, "%Y-%m-%d").date()
            except ValueError:
                pass
        
        is_valid, msg, _ = validate_egyptian_national_id(payload.national_id_number, expected_birth_date=b_date)
        if not is_valid:
            return CheckDuplicateResponse(
                is_available=False,
                message=msg,
                duplicate_type="INVALID_NATIONAL_ID"
            )
        
        stmt = select(Profile).where(Profile.national_id_number == payload.national_id_number.strip())
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            return CheckDuplicateResponse(
                is_available=False,
                message="الرقم القومي مسجل بالفعل بالنظام لحساب آخر.",
                duplicate_type="NATIONAL_ID_EXISTS"
            )
        return CheckDuplicateResponse(is_available=True, message="الرقم القومي صالح ومتاح.")

    elif field == "identity":
        if not payload.full_name or not payload.birth_date:
            return CheckDuplicateResponse(is_available=True, message="")
        try:
            b_date = datetime.strptime(payload.birth_date, "%Y-%m-%d").date()
        except ValueError:
            return CheckDuplicateResponse(is_available=False, message="صيغة تاريخ الميلاد غير صحيحة.")

        stmt = select(Profile).where(Profile.birth_date == b_date)
        res = await db.execute(stmt)
        profiles = res.scalars().all()
        norm_new_name = normalize_arabic_text(payload.full_name)

        for p in profiles:
            norm_exist = normalize_arabic_text(p.full_name)
            if norm_exist == norm_new_name or (len(norm_new_name.split()) >= 3 and norm_new_name.split()[:3] == norm_exist.split()[:3]):
                return CheckDuplicateResponse(
                    is_available=False,
                    message=f"توجد بيانات مسجلة بالفعل لنفس المتقدمة ({p.full_name}) بنفس تاريخ الميلاد.",
                    duplicate_type="IDENTITY_EXISTS"
                )
        return CheckDuplicateResponse(is_available=True, message="البيانات الشخصية جديدة ومتاحة.")

    return CheckDuplicateResponse(is_available=True, message="حقل غير معروف.")

@router.post("/register")
async def register_applicant(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    # 1. Parse birth date
    try:
        b_date = datetime.strptime(payload.birth_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="صيغة تاريخ الميلاد غير صحيحة (YYYY-MM-DD)")

    # 2. Check age requirement
    age = (date.today() - b_date).days // 365
    is_minor = age < 18
    if age < 14:
        raise HTTPException(status_code=400, detail="السن الأدنى للخلوة هو بداية المرحلة الثانوية (14-15 سنة على الأقل)")
    
    if is_minor and (not payload.companion_name or not payload.companion_phone):
        raise HTTPException(
            status_code=400,
            detail="المتقدمة قاصر (أقل من 18 عاماً)، يجب تسجيل اسم ورقم هاتف المرافقة المسؤولة (تاسوني أو أخت كبرى)."
        )

    # 3. Comprehensive Multi-Level Duplicate Detection
    has_dup, dup_msg, dup_type = await check_registration_duplicates(
        db=db,
        email=payload.email,
        phone_number=payload.phone_number,
        national_id_number=payload.national_id_number,
        full_name=payload.full_name,
        birth_date=b_date
    )

    if has_dup:
        if dup_type == "EMAIL_UNVERIFIED":
            # User previously registered but did not verify email -> send fresh OTP code
            stmt_user = select(User).where(User.email == payload.email)
            res_u = await db.execute(stmt_user)
            existing_user = res_u.scalar_one_or_none()
            
            otp = generate_otp_code()
            expiry = get_utc_now() + timedelta(minutes=settings.EMAIL_VERIFICATION_EXPIRY_MINUTES)
            db_code = EmailVerificationCode(
                user_id=existing_user.id,
                email=existing_user.email,
                otp_code=otp,
                expires_at=expiry
            )
            db.add(db_code)
            await db.commit()
            
            # Fetch profile name
            stmt_prof = select(Profile.full_name).where(Profile.user_id == existing_user.id)
            prof_res = await db.execute(stmt_prof)
            name = prof_res.scalar_one_or_none() or payload.full_name
            await send_verification_email(existing_user.email, name, otp)

            return {
                "message": "البريد مسجل مسبقاً وغير مفعّل. تم إرسال رمز تحقق جديد إلى بريدكِ الإلكتروني لتأكيد التسجيل.",
                "requires_verification": True,
                "email": existing_user.email
            }

        # Raise explicit, descriptive duplicate rejection error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=dup_msg
        )

    # 4. Create User Account (Unverified by default until OTP is confirmed)
    is_verified_init = not settings.REQUIRE_EMAIL_VERIFICATION
    user = User(
        email=payload.email.strip().lower(),
        password_hash=get_password_hash(payload.password),
        role=UserRole.APPLICANT,
        is_active=True,
        is_verified=is_verified_init
    )
    db.add(user)
    await db.flush()

    # 5. Create Profile with National ID
    profile = Profile(
        user_id=user.id,
        full_name=payload.full_name.strip(),
        national_id_number=payload.national_id_number.strip(),
        birth_date=b_date,
        phone_number=clean_egyptian_phone(payload.phone_number),
        governorate=payload.governorate.strip(),
        diocese=payload.diocese.strip(),
        church=payload.church.strip(),
        is_minor=is_minor,
        companion_name=payload.companion_name.strip() if is_minor and payload.companion_name else None,
        companion_phone=clean_egyptian_phone(payload.companion_phone) if is_minor and payload.companion_phone else None
    )
    db.add(profile)
    await db.flush()

    # 6. Create Guardian
    guardian = Guardian(
        profile_id=profile.id,
        guardian_type=payload.guardian_type.strip(),
        full_name=payload.guardian_name.strip(),
        phone_number=clean_egyptian_phone(payload.guardian_phone)
    )
    db.add(guardian)

    # 7. Create Confession Father
    confession_father = ConfessionFather(
        profile_id=profile.id,
        father_name=payload.confession_father_name.strip(),
        father_phone=clean_egyptian_phone(payload.confession_father_phone),
        church_name=payload.confession_church.strip()
    )
    db.add(confession_father)

    # 8. Generate & Send OTP Code if verification required
    if settings.REQUIRE_EMAIL_VERIFICATION:
        otp = generate_otp_code()
        expiry = get_utc_now() + timedelta(minutes=settings.EMAIL_VERIFICATION_EXPIRY_MINUTES)
        db_code = EmailVerificationCode(
            user_id=user.id,
            email=user.email,
            otp_code=otp,
            expires_at=expiry
        )
        db.add(db_code)
        await db.commit()

        # Dispatch real email
        await send_verification_email(user.email, payload.full_name, otp)

        resp_data = {
            "message": "تم إنشاء الحساب بنجاح. تم إرسال رمز التحقق (OTP) إلى بريدكِ الإلكتروني لتأكيد التسجيل.",
            "requires_verification": True,
            "email": user.email,
            "user_id": user.id
        }
        if not settings.SMTP_USER:
            resp_data["dev_otp"] = otp
        return resp_data

    # If verification not strictly required, commit & return access token immediately
    await db.commit()
    access_token = create_access_token(
        data={"sub": user.id, "role": user.role, "email": user.email}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id,
        "email": user.email,
        "requires_verification": False
    }

@router.post("/verify-email", response_model=Token)
async def verify_email_otp(payload: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    """Verify 6-digit OTP code and activate account."""
    clean_email = payload.email.strip().lower()
    stmt_user = select(User).where(User.email == clean_email)
    res_user = await db.execute(stmt_user)
    user = res_user.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="البريد الإلكتروني غير مسجل بالنظام.")

    if user.is_verified:
        # Already verified -> generate token
        access_token = create_access_token(
            data={"sub": user.id, "role": user.role, "email": user.email}
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": user.role,
            "user_id": user.id,
            "email": user.email
        }

    # Find latest unexpired unused code
    now = get_utc_now()
    stmt_code = select(EmailVerificationCode).where(
        and_(
            EmailVerificationCode.user_id == user.id,
            EmailVerificationCode.is_used == False,
            EmailVerificationCode.expires_at > now
        )
    ).order_by(desc(EmailVerificationCode.created_at))
    res_code = await db.execute(stmt_code)
    code_record = res_code.scalars().first()

    if not code_record:
        raise HTTPException(
            status_code=400,
            detail="انتهت صلاحية رمز التحقق أو لم يتم إرساله. يرجى الضغط على 'إعادة إرسال الرمز'."
        )

    code_record.attempts_count += 1
    if code_record.attempts_count > 5:
        code_record.is_used = True
        await db.commit()
        raise HTTPException(
            status_code=400,
            detail="تم تجاوز الحد الأقصى للمحاولات الخاطئة. يرجى طلب رمز تحقق جديد."
        )

    if code_record.otp_code != payload.otp_code.strip():
        await db.commit()
        raise HTTPException(
            status_code=400,
            detail=f"رمز التحقق غير صحيح. متبقي لكِ {5 - code_record.attempts_count} محاولات."
        )

    # Valid OTP! Mark verified
    code_record.is_used = True
    user.is_verified = True
    user.last_login_at = now
    await db.commit()

    access_token = create_access_token(
        data={"sub": user.id, "role": user.role, "email": user.email}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id,
        "email": user.email
    }

@router.post("/resend-verification-code")
async def resend_verification_code(payload: ResendOTPRequest, db: AsyncSession = Depends(get_db)):
    """Resend a fresh 6-digit OTP code to the user's email."""
    clean_email = payload.email.strip().lower()
    stmt_user = select(User).where(User.email == clean_email)
    res_user = await db.execute(stmt_user)
    user = res_user.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="البريد الإلكتروني غير مسجل بالنظام.")

    if user.is_verified:
        raise HTTPException(status_code=400, detail="هذا الحساب مفعّل بالفعل. يمكنكِ تسجيل الدخول مباشرة.")

    # Rate limiting: check if last code was sent less than 60 seconds ago
    now = get_utc_now()
    stmt_last = select(EmailVerificationCode).where(
        EmailVerificationCode.user_id == user.id
    ).order_by(desc(EmailVerificationCode.created_at))
    res_last = await db.execute(stmt_last)
    last_code = res_last.scalars().first()

    if last_code and (now - last_code.created_at).total_seconds() < 60:
        remaining = int(60 - (now - last_code.created_at).total_seconds())
        raise HTTPException(
            status_code=429,
            detail=f"يرجى الانتظار {remaining} ثانية قبل طلب رمز جديد."
        )

    # Generate new OTP code
    otp = generate_otp_code()
    expiry = now + timedelta(minutes=settings.EMAIL_VERIFICATION_EXPIRY_MINUTES)
    db_code = EmailVerificationCode(
        user_id=user.id,
        email=user.email,
        otp_code=otp,
        expires_at=expiry
    )
    db.add(db_code)
    await db.commit()

    stmt_prof = select(Profile.full_name).where(Profile.user_id == user.id)
    prof_res = await db.execute(stmt_prof)
    name = prof_res.scalar_one_or_none() or "المتقدمة"

    await send_verification_email(user.email, name, otp)

    resp_data = {
        "message": "تم إرسال رمز تحقق جديد إلى بريدكِ الإلكتروني بنجاح.",
        "email": user.email
    }
    if not settings.SMTP_USER:
        resp_data["dev_otp"] = otp
    return resp_data

@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Request password reset OTP code using Email, Phone number, or National ID."""
    identifier = payload.identifier or payload.email
    user, profile, id_type = await find_user_and_profile_by_identifier(db, identifier)

    if not user:
        # Prevent account enumeration by returning a general success message
        return {
            "message": "إذا كانت هذه البيانات مسجلة لدينا، فقد تم إرسال رمز التحقق (OTP) لاستعادة الحساب إلى البريد المسجل.",
            "email": identifier
        }

    now = get_utc_now()
    otp = generate_otp_code()
    expiry = now + timedelta(minutes=15)

    db_code = EmailVerificationCode(
        user_id=user.id,
        email=user.email,
        otp_code=otp,
        expires_at=expiry
    )
    db.add(db_code)
    await db.commit()

    name = profile.full_name if profile else "المستخدمة"
    await send_password_reset_email(user.email, name, otp)

    # Mask email for user reassurance (e.g. m***a@gmail.com)
    email_parts = user.email.split("@")
    masked_email = email_parts[0][0] + "***" + (email_parts[0][-1] if len(email_parts[0]) > 1 else "") + "@" + email_parts[1]

    resp_data = {
        "message": f"تم إرسال رمز إعادة تعيين كلمة المرور إلى البريد المسجل ({masked_email}) بنجاح.",
        "email": user.email
    }
    if not settings.SMTP_USER:
        resp_data["dev_otp"] = otp
    return resp_data

@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password using 6-digit OTP code."""
    clean_email = payload.email.strip().lower()
    stmt_user = select(User).where(User.email == clean_email)
    res_user = await db.execute(stmt_user)
    user = res_user.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="البريد الإلكتروني غير مسجل بالنظام.")

    now = get_utc_now()
    stmt_code = select(EmailVerificationCode).where(
        and_(
            EmailVerificationCode.user_id == user.id,
            EmailVerificationCode.is_used == False,
            EmailVerificationCode.expires_at > now
        )
    ).order_by(desc(EmailVerificationCode.created_at))
    res_code = await db.execute(stmt_code)
    code_record = res_code.scalars().first()

    if not code_record:
        raise HTTPException(
            status_code=400,
            detail="انتهت صلاحية رمز التحقق أو لم يتم إرساله. يرجى طلب رمز جديد."
        )

    code_record.attempts_count += 1
    if code_record.attempts_count > 5:
        code_record.is_used = True
        await db.commit()
        raise HTTPException(
            status_code=400,
            detail="تم تجاوز الحد الأقصى للمحاولات الخاطئة. يرجى طلب رمز تحقق جديد."
        )

    if code_record.otp_code != payload.otp_code.strip():
        await db.commit()
        raise HTTPException(
            status_code=400,
            detail=f"رمز التحقق غير صحيح. متبقي لكِ {5 - code_record.attempts_count} محاولات."
        )

    # Valid OTP -> Update password
    code_record.is_used = True
    user.password_hash = get_password_hash(payload.new_password)
    user.is_verified = True  # Verified by OTP proof
    await db.commit()

    return {
        "message": "تم إعادة تعيين كلمة المرور بنجاح! يمكنكِ الآن تسجيل الدخول بكلمة المرور الجديدة."
    }

@router.post("/login")
async def login(payload: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Professional multi-identifier login:
    Supports authentication via:
    1. Email Address (example@gmail.com)
    2. Egyptian Mobile Phone Number (01012345678)
    3. Egyptian National ID Number (14 digits)
    """
    identifier = payload.identifier or payload.email
    user, profile, id_type = await find_user_and_profile_by_identifier(db, identifier)

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="بيانات الدخول (البريد / الهاتف / الرقم القومي) أو كلمة المرور غير صحيحة"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="هذا الحساب موقوف، يرجى التواصل مع إدارة بيت الخلوة بالدير"
        )

    # If applicant has not verified their email yet -> block login and prompt verification
    if settings.REQUIRE_EMAIL_VERIFICATION and not user.is_verified and user.role == UserRole.APPLICANT:
        # Generate fresh OTP code
        otp = generate_otp_code()
        expiry = get_utc_now() + timedelta(minutes=settings.EMAIL_VERIFICATION_EXPIRY_MINUTES)
        db_code = EmailVerificationCode(
            user_id=user.id,
            email=user.email,
            otp_code=otp,
            expires_at=expiry
        )
        db.add(db_code)
        await db.commit()

        stmt_prof = select(Profile.full_name).where(Profile.user_id == user.id)
        prof_res = await db.execute(stmt_prof)
        name = prof_res.scalar_one_or_none() or "المتقدمة"
        await send_verification_email(user.email, name, otp)

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="EMAIL_NOT_VERIFIED: الحساب غير مفعّل. تم إرسال رمز تحقق إلى بريدكِ الإلكتروني لتأكيد التسجيل."
        )

    user.last_login_at = get_utc_now()
    await db.commit()

    await record_audit_log(
        db=db,
        action="LOGIN",
        target_entity="User",
        target_entity_id=user.id,
        user=user,
        request=request,
        details={
            "ip": request.client.host if request.client else "unknown",
            "login_type": id_type
        }
    )

    access_token = create_access_token(
        data={"sub": user.id, "role": user.role, "email": user.email}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id,
        "email": user.email
    }

@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.post("/change-password")
async def change_password(
    payload: UserPasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="كلمة المرور الحالية غير صحيحة")
    
    current_user.password_hash = get_password_hash(payload.new_password)
    await db.commit()

    return {"message": "تم تغيير كلمة المرور بنجاح"}
