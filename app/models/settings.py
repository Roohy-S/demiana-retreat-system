import uuid
from datetime import datetime, date, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Date, Integer, Text
from app.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    retreat_name = Column(String(255), default="بيت الخلوة بدير القديسة دميانة", nullable=False)
    monastery_location = Column(String(255), default="ببراري بلقاس", nullable=False)
    
    default_retreat_nights = Column(Integer, default=3, nullable=False)
    min_booking_interval_months = Column(Integer, default=3, nullable=False)
    min_applicant_age_years = Column(Integer, default=15, nullable=False)
    default_period_capacity = Column(Integer, default=20, nullable=False)
    
    allow_waitlist = Column(Boolean, default=True, nullable=False)
    allow_extensions = Column(Boolean, default=True, nullable=False)
    allow_exceptions = Column(Boolean, default=True, nullable=False)
    
    whatsapp_official_number = Column(String(50), default="201000000000", nullable=False)
    reception_contact_phone = Column(String(50), default="201000000001", nullable=False)
    
    privacy_mode_enabled_default = Column(Boolean, default=True, nullable=False)
    data_retention_years = Column(Integer, default=10, nullable=False)
    
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class GeneralAnnouncement(Base):
    __tablename__ = "general_announcements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    target_audience = Column(String(50), default="ALL", nullable=False)  # ALL, APPLICANTS, STAFF, RECEPTION
    is_active = Column(Boolean, default=True, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
