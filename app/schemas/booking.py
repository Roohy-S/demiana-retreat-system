from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.profile import ProfileOut
from app.schemas.period import PeriodOut

class BookingSubmit(BaseModel):
    period_id: str
    agreed_to_rules: bool = True
    has_interval_exception: Optional[bool] = False
    interval_exception_reason: Optional[str] = None

class BookingStatusUpdate(BaseModel):
    status: str
    admin_reason: Optional[str] = None

class BookingTransfer(BaseModel):
    new_period_id: str
    admin_reason: Optional[str] = None

class ExtensionSubmit(BaseModel):
    booking_id: str
    requested_additional_days: int = 1
    reason: str
    detailed_explanation: Optional[str] = None

ExtensionRequestCreate = ExtensionSubmit

class ExtensionDecision(BaseModel):
    status: str
    rejection_reason: Optional[str] = None

ExtensionRequestDecision = ExtensionDecision

class ExceptionDecision(BaseModel):
    decision: str  # APPROVED or REJECTED
    rejection_reason: Optional[str] = None

ExceptionRequestDecision = ExceptionDecision

class StatusHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    previous_status: Optional[str] = None
    new_status: str
    changed_by_user_id: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime

class ExtensionRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    booking_id: str
    profile_id: str
    requested_additional_days: int
    reason: str
    detailed_explanation: Optional[str] = None
    status: str
    decision_by_user_id: Optional[str] = None
    decision_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime

class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    booking_reference: str
    profile_id: str
    period_id: str
    status: str
    has_interval_exception: bool
    interval_exception_reason: Optional[str] = None
    interval_exception_status: str
    agreed_to_rules: bool
    created_at: datetime
    updated_at: datetime
    profile: Optional[ProfileOut] = None
    period: Optional[PeriodOut] = None
    history: List[StatusHistoryOut] = []
    extension_requests: List[ExtensionRequestOut] = []
