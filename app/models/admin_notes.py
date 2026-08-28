import uuid
from datetime import datetime, date, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

class NoteSeverity:
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class NoteType:
    BEHAVIOR = "BEHAVIOR"
    ATTENDANCE = "ATTENDANCE"
    SPIRITUAL = "SPIRITUAL"
    RESTRICTION = "RESTRICTION"
    GENERAL = "GENERAL"

class NoteRecommendation:
    NONE = "NONE"
    BAN_BOOKING = "BAN_BOOKING"
    CONDITIONAL_APPROVAL = "CONDITIONAL_APPROVAL"
    SUPERVISOR_ATTENTION = "SUPERVISOR_ATTENTION"

class AdministrativeNote(Base):
    __tablename__ = "administrative_notes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    author_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    author_name_cache = Column(String(100), nullable=True)
    
    note_type = Column(String(50), default=NoteType.GENERAL, nullable=False)
    severity = Column(String(20), default=NoteSeverity.NORMAL, nullable=False)
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    recommendation = Column(String(100), default=NoteRecommendation.NONE, nullable=False)
    
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    profile = relationship("Profile", back_populates="administrative_notes")


class Violation(Base):
    __tablename__ = "violations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    booking_id = Column(String(36), ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True, index=True)
    recorded_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    violation_title = Column(String(200), nullable=False)
    violation_description = Column(Text, nullable=False)
    action_taken = Column(Text, nullable=True)
    is_resolved = Column(Boolean, default=False, nullable=False)
    occurred_at = Column(Date, default=date.today, nullable=False)
    
    created_at = Column(DateTime, default=utc_now, nullable=False)

    profile = relationship("Profile", back_populates="violations")

    @property
    def title(self) -> str:
        return self.violation_title

    @property
    def description(self) -> str:
        return self.violation_description


class Restriction(Base):
    __tablename__ = "restrictions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    restriction_type = Column(String(100), nullable=False)  # BAN_BOOKING, REQUIRES_INTERVIEW, COMPANION_REQUIRED
    reason = Column(Text, nullable=False)
    created_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
