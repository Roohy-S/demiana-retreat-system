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
    doc_type: Optional[str] = "OTHER"
    document_type: Optional[str] = "OTHER"
    file_name: Optional[str] = ""
    file_size_bytes: Optional[int] = 0
    mime_type: Optional[str] = None
    is_verified: Optional[bool] = True
    verified_at: Optional[datetime] = None
    uploaded_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    is_archived: Optional[bool] = False

class ProfileViolationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    violation_title: Optional[str] = None
    violation_description: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    action_taken: Optional[str] = None
    occurred_at: Optional[date] = None

class ProfileBriefOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str] = None
    full_name: str
    national_id_number: Optional[str] = None
    birth_date: Optional[date] = None
    phone_number: Optional[str] = None
    governorate: Optional[str] = None
    diocese: Optional[str] = None
    church: Optional[str] = None
    education_or_job: Optional[str] = None
    is_minor: Optional[bool] = False
    companion_name: Optional[str] = None
    companion_phone: Optional[str] = None
    total_retreats_count: Optional[int] = 0
    last_retreat_date: Optional[date] = None
    has_active_warning: Optional[bool] = False
    is_blocked_from_booking: Optional[bool] = False
    created_at: Optional[datetime] = None
    guardians: Optional[List[GuardianOut]] = []
    confession_fathers: Optional[List[ConfessionFatherOut]] = []
    documents: Optional[List[DocumentOut]] = []
    violations: Optional[List[ProfileViolationOut]] = []

class ProfileOut(ProfileBriefOut):
    model_config = ConfigDict(from_attributes=True)

class ProfileUpdate(BaseModel):
    phone_number: Optional[str] = None
    governorate: Optional[str] = None
    diocese: Optional[str] = None
    church: Optional[str] = None
    companion_name: Optional[str] = None
    companion_phone: Optional[str] = None

GuardianOut.model_rebuild()
ConfessionFatherOut.model_rebuild()
DocumentOut.model_rebuild()
ProfileViolationOut.model_rebuild()
ProfileBriefOut.model_rebuild()
ProfileOut.model_rebuild()
ProfileUpdate.model_rebuild()
