import uuid
from datetime import datetime, date, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Date, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True, index=True)
    
    full_name = Column(String(255), nullable=False, index=True)
    national_id_number = Column(String(14), unique=True, nullable=True, index=True)
    birth_date = Column(Date, nullable=False)
    phone_number = Column(String(20), nullable=False, index=True)
    
    governorate = Column(String(100), nullable=False, index=True)
    diocese = Column(String(150), nullable=False, index=True)
    church = Column(String(200), nullable=False, index=True)
    education_or_job = Column(String(150), nullable=True)
    
    is_minor = Column(Boolean, default=False, nullable=False)
    companion_name = Column(String(255), nullable=True)
    companion_phone = Column(String(20), nullable=True)
    
    last_retreat_date = Column(Date, nullable=True)
    total_retreats_count = Column(Integer, default=0, nullable=False)
    has_active_warning = Column(Boolean, default=False, nullable=False)
    is_blocked_from_booking = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    guardians = relationship("Guardian", back_populates="profile", cascade="all, delete-orphan", lazy="selectin")
    confession_fathers = relationship("ConfessionFather", back_populates="profile", cascade="all, delete-orphan", lazy="selectin")
    documents = relationship("IdentityDocument", back_populates="profile", cascade="all, delete-orphan", lazy="selectin")
    bookings = relationship("Booking", back_populates="profile", cascade="all, delete-orphan", lazy="selectin")
    administrative_notes = relationship("AdministrativeNote", back_populates="profile", cascade="all, delete-orphan", lazy="selectin")
    violations = relationship("Violation", back_populates="profile", cascade="all, delete-orphan", lazy="selectin")


class Guardian(Base):
    __tablename__ = "guardians"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    guardian_type = Column(String(50), nullable=False)  # أب, أم, أخ, زوج, أخرى
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    profile = relationship("Profile", back_populates="guardians")


class ConfessionFather(Base):
    __tablename__ = "confession_fathers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    father_name = Column(String(255), nullable=False)
    father_phone = Column(String(20), nullable=False)
    church_name = Column(String(200), nullable=False)
    approval_letter_doc_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    profile = relationship("Profile", back_populates="confession_fathers")


class IdentityDocument(Base):
    __tablename__ = "identity_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    doc_type = Column(String(50), nullable=False)  # NATIONAL_ID_FRONT, NATIONAL_ID_BACK, CONFESSION_LETTER, OTHER
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, default=0, nullable=False)
    mime_type = Column(String(100), default="application/octet-stream", nullable=False)
    uploaded_at = Column(DateTime, default=utc_now, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)

    profile = relationship("Profile", back_populates="documents")

    @property
    def document_type(self) -> str:
        return self.doc_type

    @property
    def created_at(self) -> datetime:
        return self.uploaded_at

    @property
    def is_verified(self) -> bool:
        return not self.is_archived

