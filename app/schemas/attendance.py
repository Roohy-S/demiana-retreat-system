from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.profile import ProfileOut
from app.schemas.booking import BookingOut

class CheckInRequest(BaseModel):
    booking_id: str
    room_or_cell_number: Optional[str] = None
    reception_notes: Optional[str] = None
    notes: Optional[str] = None

CheckinCreate = CheckInRequest

class DepartureRequest(BaseModel):
    booking_id: str
    departure_notes: Optional[str] = None

AttendanceStatusUpdate = DepartureRequest

class AttendanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    booking_id: str
    period_id: str
    profile_id: str
    checked_in_at: Optional[datetime] = None
    checked_in_by_user_id: Optional[str] = None
    checked_out_at: Optional[datetime] = None
    checked_out_by_user_id: Optional[str] = None
    room_or_cell_number: Optional[str] = None
    attendance_status: str
    reception_notes: Optional[str] = None
    departure_notes: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    profile: Optional[ProfileOut] = None
    booking: Optional[BookingOut] = None

GateSheetItem = AttendanceOut
