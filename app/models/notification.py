import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from app.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

class NotificationType:
    BOOKING_STATUS = "BOOKING_STATUS"
    WAITLIST_UPDATE = "WAITLIST_UPDATE"
    ALERT = "ALERT"
    EXTENSION = "EXTENSION"
    EXCEPTION = "EXCEPTION"
    GENERAL = "GENERAL"

class NotificationSeverity:
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    URGENT = "URGENT"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recipient_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default=NotificationType.GENERAL, nullable=False)
    severity = Column(String(20), default=NotificationSeverity.INFO, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    related_booking_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class CommunicationLog(Base):
    __tablename__ = "communication_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    channel = Column(String(50), default="WHATSAPP", nullable=False)  # WHATSAPP, EMAIL, SMS, IN_APP
    recipient_phone_or_email = Column(String(100), nullable=False)
    message_template_name = Column(String(100), nullable=True)
    message_content = Column(Text, nullable=False)
    delivery_status = Column(String(50), default="SENT", nullable=False)
    sent_at = Column(DateTime, default=utc_now, nullable=False)

    @property
    def created_at(self) -> datetime:
        return self.sent_at

    @property
    def recipient_phone_snapshot(self) -> str:
        return self.recipient_phone_or_email

    @property
    def template_type(self) -> str:
        return self.message_template_name or "CUSTOM"
