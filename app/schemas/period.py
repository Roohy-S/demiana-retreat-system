from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict

class PeriodCreate(BaseModel):
    period_name: str
    start_date: date
    end_date: date
    departure_date: date
    arrival_time_desc: Optional[str] = "الساعة 12:00 ظهراً"
    departure_time_desc: Optional[str] = "قبل الساعة 9:00 صباحاً"
    nights_count: int = 3
    capacity: int = Field(default=20, ge=1)
    status: Optional[str] = "OPEN"
    is_special_period: Optional[bool] = False
    special_period_notes: Optional[str] = None

class PeriodUpdate(BaseModel):
    period_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    departure_date: Optional[date] = None
    arrival_time_desc: Optional[str] = None
    departure_time_desc: Optional[str] = None
    nights_count: Optional[int] = None
    capacity: Optional[int] = None
    status: Optional[str] = None
    is_special_period: Optional[bool] = None
    special_period_notes: Optional[str] = None

class PeriodOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    period_name: str
    start_date: date
    end_date: date
    departure_date: date
    arrival_time_desc: str
    departure_time_desc: str
    nights_count: int
    capacity: int
    approved_count: int
    pending_count: int
    status: str
    is_special_period: bool
    special_period_notes: Optional[str] = None
    remaining_spots: int
    created_at: datetime

class WaitlistOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    period_id: str
    profile_id: str
    booking_id: str
    queue_number: int
    status: str
    created_at: datetime
