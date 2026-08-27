from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict

class GuardianOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    guardian_type: str
    full_name: str
    phone_number: str
    created_at: Optional[datetime] = None

class ConfessionFatherOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    father_name: str
    father_phone: str
    church_name: str
    created_at: Optional[datetime] = None

class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_type: str
    file_name: str
    file_size_bytes: int
    is_verified: bool
    verified_at: Optional[datetime] = None
    created_at: datetime

class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str] = None
    full_name: str
    national_id_number: Optional[str] = None
    birth_date: date
    phone_number: str
    governorate: str
    diocese: str
    church: str
    is_minor: bool
    companion_name: Optional[str] = None
    companion_phone: Optional[str] = None
    total_retreats_count: int
    last_retreat_date: Optional[date] = None
    has_active_warning: bool
    created_at: datetime
    guardians: List[GuardianOut] = []
    confession_fathers: List[ConfessionFatherOut] = []
    documents: List[DocumentOut] = []

class ProfileUpdate(BaseModel):
    phone_number: Optional[str] = None
    governorate: Optional[str] = None
    diocese: Optional[str] = None
    church: Optional[str] = None
    companion_name: Optional[str] = None
    companion_phone: Optional[str] = None
