import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

class AttendanceStatus:
    EXPECTED = "EXPECTED"
    CHECKED_IN = "CHECKED_IN"
    COMPLETED = "COMPLETED"
    EXCUSED = "EXCUSED"
    NO_SHOW = "NO_SHOW"

class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id = Column(String(36), ForeignKey("bookings.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    period_id = Column(String(36), ForeignKey("retreat_periods.id", ondelete="CASCADE"), nullable=False, index=True)
    profile_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    checked_in_at = Column(DateTime, nullable=True)
    checked_in_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    checked_out_at = Column(DateTime, nullable=True)
    
    attendance_status = Column(String(50), default=AttendanceStatus.EXPECTED, nullable=False, index=True)
    room_or_cell_number = Column(String(50), nullable=True)
    reception_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships with eager selectin loading
    booking = relationship("Booking", back_populates="attendance", lazy="selectin")
    profile = relationship("Profile", lazy="selectin")
