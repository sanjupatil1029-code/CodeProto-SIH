import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.notification import NotificationEventType, NotificationSeverity


class NotificationCreateSchema(BaseModel):
    user_id: uuid.UUID
    event_type: NotificationEventType
    severity: NotificationSeverity = NotificationSeverity.INFO
    title: str = Field(..., max_length=255)
    message: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    send_email: bool = True


class NotificationOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    event_type: NotificationEventType
    severity: NotificationSeverity
    title: str
    message: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    is_read: bool
    read_at: Optional[datetime] = None
    email_sent: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationFeedResponse(BaseModel):
    total_count: int
    unread_count: int
    notifications: List[NotificationOut]
