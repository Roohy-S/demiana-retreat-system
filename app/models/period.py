import uuid
from datetime import datetime, date, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Date, Integer, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

class PeriodStatus:
    OPEN = "OPEN"
    FULL = "FULL"
    CLOSED = "CLOSED"
    EXCEPTIONAL = "EXCEPTIONAL"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"

class RetreatPeriod(Base):
    __tablename__ = "retreat_periods"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    period_name = Column(String(150), nullable=False)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    departure_date = Column(Date, nullable=False)
    
    arrival_time_desc = Column(String(50), default="الساعة 12:00 ظهراً", nullable=False)
    departure_time_desc = Column(String(50), default="قبل الساعة 9:00 صباحاً", nullable=False)
    nights_count = Column(Integer, default=3, nullable=False)
    capacity = Column(Integer, default=20, nullable=False)
    
    approved_count = Column(Integer, default=0, nullable=False)
    pending_count = Column(Integer, default=0, nullable=False)
    
    status = Column(String(50), default=PeriodStatus.OPEN, nullable=False, index=True)
    is_special_period = Column(Boolean, default=False, nullable=False)
    allows_extension_requests = Column(Boolean, default=True, nullable=False)
    allows_exception_requests = Column(Boolean, default=True, nullable=False)
    admin_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    bookings = relationship("Booking", back_populates="period", cascade="all, delete-orphan", lazy="selectin")
    waitlist_items = relationship("Waitlist", back_populates="period", cascade="all, delete-orphan", lazy="selectin")

    @property
    def remaining_spots(self) -> int:
        return max(0, self.capacity - self.approved_count)

    @property
    def is_full(self) -> bool:
        return self.approved_count >= self.capacity


class WaitlistStatus:
    WAITING = "WAITING"
    PROMOTED = "PROMOTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class Waitlist(Base):
    __tablename__ = "waitlist"
    __table_args__ = (
        UniqueConstraint("period_id", "profile_id", name="uq_waitlist_period_profile"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    period_id = Column(String(36), ForeignKey("retreat_periods.id", ondelete="CASCADE"), nullable=False, index=True)
    profile_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    booking_id = Column(String(36), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    
    queue_number = Column(Integer, nullable=False)
    priority_score = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default=WaitlistStatus.WAITING, nullable=False)
    promoted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    period = relationship("RetreatPeriod", back_populates="waitlist_items")
    booking = relationship("Booking", back_populates="waitlist_item")
