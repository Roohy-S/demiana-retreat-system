from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class AdministrativeNoteCreate(BaseModel):
    profile_id: str
    content: str
    severity: Optional[str] = "MEDIUM"
    note_type: Optional[str] = "GENERAL"
    recommendation: Optional[str] = "SUPERVISOR_ATTENTION"

class AdministrativeNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profile_id: str
    author_user_id: str
    author_name_cache: Optional[str] = None
    note_type: str
    severity: str
    content: str
    recommendation: str
    is_active: bool
    created_at: datetime

class ViolationCreate(BaseModel):
    profile_id: str
    booking_id: Optional[str] = None
    title: str
    description: str
    severity: Optional[str] = "MEDIUM"

class ViolationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profile_id: str
    booking_id: Optional[str] = None
    title: str
    description: str
    severity: str
    recorded_by_user_id: str
    recorded_by_name_cache: Optional[str] = None
    created_at: datetime
