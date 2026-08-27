import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from app.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

class AuditAction:
    VIEW_ID_CARD = "VIEW_ID_CARD"
    VIEW_PHONE = "VIEW_PHONE"
    VIEW_CONFESSION_LETTER = "VIEW_CONFESSION_LETTER"
    APPROVE_BOOKING = "APPROVE_BOOKING"
    REJECT_BOOKING = "REJECT_BOOKING"
    CANCEL_BOOKING = "CANCEL_BOOKING"
    TRANSFER_BOOKING = "TRANSFER_BOOKING"
    PROMOTE_WAITLIST = "PROMOTE_WAITLIST"
    APPROVE_EXTENSION = "APPROVE_EXTENSION"
    REJECT_EXTENSION = "REJECT_EXTENSION"
    APPROVE_EXCEPTION = "APPROVE_EXCEPTION"
    REJECT_EXCEPTION = "REJECT_EXCEPTION"
    CREATE_PERIOD = "CREATE_PERIOD"
    UPDATE_PERIOD = "UPDATE_PERIOD"
    CANCEL_PERIOD = "CANCEL_PERIOD"
    ADD_ADMIN_NOTE = "ADD_ADMIN_NOTE"
    ADD_VIOLATION = "ADD_VIOLATION"
    CHECKIN_ATTENDANCE = "CHECKIN_ATTENDANCE"
    SEND_WHATSAPP = "SEND_WHATSAPP"
    UPDATE_SYSTEM_SETTINGS = "UPDATE_SYSTEM_SETTINGS"
    CREATE_STAFF = "CREATE_STAFF"
    UPDATE_STAFF = "UPDATE_STAFF"

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user_email_cache = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    target_entity = Column(String(50), nullable=False, index=True)  # PROFILE, BOOKING, PERIOD, SETTINGS, STAFF
    target_entity_id = Column(String(100), nullable=False, index=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
