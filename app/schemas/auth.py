import re
from typing import Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, ConfigDict

from app.core.email_validator import validate_and_normalize_email
from app.core.duplicate_detector import (
    validate_egyptian_national_id, clean_egyptian_phone, normalize_arabic_text
)

def strict_email_check(v: str) -> str:
    if not v:
        raise ValueError("البريد الإلكتروني مطلوب.")
    clean, _ = validate_and_normalize_email(v, check_deliverability=True, allow_typo_correction=False)
    return clean

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str
    email: str

class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None

class UserRegister(BaseModel):
    email: str
    password: str = Field(..., min_length=8, description="كلمة المرور يجب أن لا تقل عن 8 خانات")
    full_name: str = Field(..., min_length=6, description="الاسم الرباعي أو الثلاثي كاملاً بالعربية")
    national_id_number: str = Field(..., min_length=14, max_length=14, description="الرقم القومي المصري المكون من 14 رقماً")
    birth_date: str
    phone_number: str
    governorate: str
    diocese: str
    church: str
    guardian_type: str
    guardian_name: str
    guardian_phone: str
    confession_father_name: str
    confession_father_phone: str
    confession_church: str
    companion_name: Optional[str] = None
    companion_phone: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email_field(cls, v: str) -> str:
        return strict_email_check(v)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        v = v.strip()
        parts = v.split()
        if len(parts) < 3:
            raise ValueError("يرجى إدخال الاسم ثلاثياً على الأقل باللغة العربية كما هو مدون ببطاقة الرقم القومي")
        return v

    @field_validator("national_id_number")
    @classmethod
    def validate_national_id(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^\d{14}$", v):
            raise ValueError("الرقم القومي غير صحيح. يجب أن يتكون من 14 رقماً بالتمام والكمال.")
        is_valid, msg, _ = validate_egyptian_national_id(v)
        if not is_valid:
            raise ValueError(msg)
        return v

    @field_validator("phone_number", "guardian_phone", "confession_father_phone")
    @classmethod
    def validate_egyptian_phone(cls, v: str) -> str:
        clean = clean_egyptian_phone(v)
        if not re.match(r"^01[0125][0-9]{8}$", clean):
            raise ValueError("رقم الهاتف غير صحيح. يجب أن يكون رقماً مصرياً صالحاً مكوناً من 11 رقماً يبدأ بـ (010 أو 011 أو 012 أو 015)")
        return clean

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("كلمة المرور يجب أن تتكون من 8 خانات على الأقل")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("كلمة المرور يجب أن تحتوي على أحرف إنجليزية")
        if not re.search(r"\d", v):
            raise ValueError("كلمة المرور يجب أن تحتوي على أرقام")
        return v

    @model_validator(mode="after")
    def validate_nid_and_birthdate_consistency(self) -> "UserRegister":
        """Cross-validate National ID with entered birth date."""
        try:
            b_date = datetime.strptime(self.birth_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("صيغة تاريخ الميلاد غير صحيحة (YYYY-MM-DD)")
        
        is_valid, msg, _ = validate_egyptian_national_id(self.national_id_number, expected_birth_date=b_date)
        if not is_valid:
            raise ValueError(msg)
        return self

class CheckDuplicateRequest(BaseModel):
    field: str  # 'email', 'phone', 'national_id', 'identity'
    email: Optional[str] = None
    phone_number: Optional[str] = None
    national_id_number: Optional[str] = None
    full_name: Optional[str] = None
    birth_date: Optional[str] = None

class CheckDuplicateResponse(BaseModel):
    is_available: bool
    message: str
    typo_suggestion: Optional[str] = None
    duplicate_type: Optional[str] = None

class VerifyEmailRequest(BaseModel):
    email: str
    otp_code: str = Field(..., min_length=6, max_length=6, description="رمز التحقق المكون من 6 أرقام")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return strict_email_check(v)

class ResendOTPRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return strict_email_check(v)

class ForgotPasswordRequest(BaseModel):
    identifier: Optional[str] = None
    email: Optional[str] = None

    @model_validator(mode="after")
    def check_identifier_present(self) -> "ForgotPasswordRequest":
        if not self.identifier and not self.email:
            raise ValueError("يرجى إدخال البريد الإلكتروني أو رقم الهاتف أو الرقم القومي.")
        if not self.identifier and self.email:
            self.identifier = self.email
        return self

class ResetPasswordRequest(BaseModel):
    email: str
    otp_code: str = Field(..., min_length=6, max_length=6, description="رمز التحقق المكون من 6 أرقام")
    new_password: str = Field(..., min_length=8, description="كلمة المرور الجديدة")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return strict_email_check(v)

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("كلمة المرور يجب أن تتكون من 8 خانات على الأقل")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("كلمة المرور يجب أن تحتوي على أحرف إنجليزية")
        if not re.search(r"\d", v):
            raise ValueError("كلمة المرور يجب أن تحتوي على أرقام")
        return v

class RegisterResponse(BaseModel):
    message: str
    email: str
    requires_verification: bool = True
    user_id: str

class UserLogin(BaseModel):
    identifier: Optional[str] = None
    email: Optional[str] = None
    password: str

    @model_validator(mode="after")
    def populate_identifier(self) -> "UserLogin":
        if not self.identifier and not self.email:
            raise ValueError("يرجى إدخال البريد الإلكتروني أو رقم الهاتف أو الرقم القومي.")
        if not self.identifier and self.email:
            self.identifier = self.email.strip()
        elif self.identifier:
            self.identifier = self.identifier.strip()
        return self

class UserPasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
