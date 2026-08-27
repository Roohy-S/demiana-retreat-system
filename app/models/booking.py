import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

class BookingStatus:
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    WAITING_LIST = "WAITING_LIST"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    CHECKED_IN = "CHECKED_IN"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"
    EXTENSION_REQUESTED = "EXTENSION_REQUESTED"
    EXTENSION_APPROVED = "EXTENSION_APPROVED"
    EXTENSION_REJECTED = "EXTENSION_REJECTED"

class ExceptionStatus:
    NONE = "NONE"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        UniqueConstraint("profile_id", "period_id", name="uq_booking_profile_period"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_reference = Column(String(50), unique=True, nullable=False, index=True)
    profile_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    period_id = Column(String(36), ForeignKey("retreat_periods.id", ondelete="CASCADE"), nullable=False, index=True)
    
    status = Column(String(50), default=BookingStatus.SUBMITTED, nullable=False, index=True)
    
    # Exception Request for Minimum Booking Interval
    has_interval_exception = Column(Boolean, default=False, nullable=False)
    interval_exception_reason = Column(Text, nullable=True)
    interval_exception_status = Column(String(50), default=ExceptionStatus.NONE, nullable=False)
    
    # Rejection Notes
    rejection_reason = Column(Text, nullable=True)
    show_rejection_reason_to_user = Column(Boolean, default=False, nullable=False)
    
    agreed_to_rules = Column(Boolean, default=True, nullable=False)
    
    # Period transfer tracking
    original_period_id = Column(String(36), nullable=True)
    transferred_by_user_id = Column(String(36), nullable=True)
    transfer_reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    profile = relationship("Profile", back_populates="bookings", lazy="selectin")
    period = relationship("RetreatPeriod", back_populates="bookings", lazy="selectin")
    history = relationship("BookingStatusHistory", back_populates="booking", cascade="all, delete-orphan", lazy="selectin")
    waitlist_item = relationship("Waitlist", back_populates="booking", uselist=False, cascade="all, delete-orphan", lazy="selectin")
    extension_requests = relationship("ExtensionRequest", back_populates="booking", cascade="all, delete-orphan", lazy="selectin")
    attendance = relationship("Attendance", back_populates="booking", uselist=False, cascade="all, delete-orphan", lazy="selectin")


class BookingStatusHistory(Base):
    __tablename__ = "booking_status_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id = Column(String(36), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    changed_by_user_id = Column(String(36), nullable=True)
    change_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    booking = relationship("Booking", back_populates="history")


class ExtensionStatus:
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class ExtensionRequest(Base):
    __tablename__ = "extension_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id = Column(String(36), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    profile_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    requested_additional_days = Column(Integer, default=1, nullable=False)
    reason = Column(Text, nullable=False)
    detailed_explanation = Column(Text, nullable=True)
    status = Column(String(50), default=ExtensionStatus.PENDING, nullable=False)
    admin_response_notes = Column(Text, nullable=True)
    decided_by_user_id = Column(String(36), nullable=True)
    decided_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    booking = relationship("Booking", back_populates="extension_requests")
