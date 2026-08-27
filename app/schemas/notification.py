from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    recipient_user_id: str
    title: str
    message: str
    notification_type: str
    severity: str
    is_read: bool
    read_at: Optional[datetime] = None
    related_booking_id: Optional[str] = None
    created_at: datetime

class CommunicationDispatch(BaseModel):
    profile_id: str
    booking_id: Optional[str] = None
    template_type: str  # APPROVAL, REJECTION, REMINDER, EXTENSION_DECISION, CUSTOM
    custom_message: Optional[str] = None

CommunicationSend = CommunicationDispatch

class CommunicationLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    booking_id: Optional[str] = None
    profile_id: str
    sender_user_id: str
    channel: str
    template_type: Optional[str] = None
    recipient_phone_snapshot: str
    message_content: str
    delivery_status: str
    created_at: datetime
