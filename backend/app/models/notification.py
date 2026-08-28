import uuid
import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class NotificationEventType(str, enum.Enum):
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    DOCUMENT_EXPIRING = "DOCUMENT_EXPIRING"
    DOCUMENT_INVALID = "DOCUMENT_INVALID"
    APPROVAL_READY = "APPROVAL_READY"
    APPROVAL_BLOCKED = "APPROVAL_BLOCKED"
    APPLICATION_STATUS_CHANGED = "APPLICATION_STATUS_CHANGED"
    QUERY_RAISED = "QUERY_RAISED"
    INSPECTION_SCHEDULED = "INSPECTION_SCHEDULED"
    SLA_WARNING = "SLA_WARNING"
    SLA_BREACHED = "SLA_BREACHED"
    RENEWAL_DUE = "RENEWAL_DUE"
    GRIEVANCE_ESCALATED = "GRIEVANCE_ESCALATED"
    REGULATION_UPDATED = "REGULATION_UPDATED"


class NotificationSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    SUCCESS = "SUCCESS"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    event_type: Mapped[NotificationEventType] = mapped_column(
        Enum(NotificationEventType),
        default=NotificationEventType.APPLICATION_STATUS_CHANGED,
        nullable=False,
        index=True
    )
    severity: Mapped[NotificationSeverity] = mapped_column(
        Enum(NotificationSeverity),
        default=NotificationSeverity.INFO,
        nullable=False,
        index=True
    )
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    resource_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
