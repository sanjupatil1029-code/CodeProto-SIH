import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class AuditLog(Base):
    """
    Module 17: Immutable Append-Only Audit Log Model.
    Records statutory decisions, state changes, document validations, officer reviews,
    and rule version approvals with complete old vs new JSON diffs.
    """
    __tablename__ = "audit_logs"

    audit_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    actor_role: Mapped[str] = mapped_column(String(50), default="SYSTEM", nullable=False)
    
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # State change JSON diffs
    old_value: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    new_value: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
