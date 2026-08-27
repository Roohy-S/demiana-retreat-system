from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class SystemSettingsUpdate(BaseModel):
    retreat_name: Optional[str] = None
    monastery_location: Optional[str] = None
    default_retreat_nights: Optional[int] = None
    min_booking_interval_months: Optional[int] = None
    min_applicant_age_years: Optional[int] = None
    default_period_capacity: Optional[int] = None
    allow_waitlist: Optional[bool] = None
    allow_extensions: Optional[bool] = None
    allow_exceptions: Optional[bool] = None
    whatsapp_official_number: Optional[str] = None
    reception_contact_phone: Optional[str] = None
    rules_and_bylaws_text: Optional[str] = None

class SystemSettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    retreat_name: str
    monastery_location: str
    default_retreat_nights: int
    min_booking_interval_months: int
    min_applicant_age_years: int
    default_period_capacity: int
    allow_waitlist: bool
    allow_extensions: bool
    allow_exceptions: bool
    whatsapp_official_number: str
    reception_contact_phone: str
    rules_and_bylaws_text: Optional[str] = None
    updated_at: datetime

class AnnouncementCreate(BaseModel):
    title: str
    content: str
    severity: Optional[str] = "INFO"
    is_active: Optional[bool] = True
    display_from: Optional[datetime] = None
    display_until: Optional[datetime] = None

class AnnouncementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    content: str
    severity: str
    is_active: bool
    display_from: Optional[datetime] = None
    display_until: Optional[datetime] = None
    created_at: datetime
