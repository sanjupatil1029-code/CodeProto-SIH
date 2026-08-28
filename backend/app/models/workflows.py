import uuid
import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class ApprovalStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    READY = "READY"
    BLOCKED = "BLOCKED"
    READY_FOR_SUBMISSION = "READY_FOR_SUBMISSION"
    OFFICIAL_PORTAL_HANDOFF = "OFFICIAL_PORTAL_HANDOFF"
    SUBMITTED = "SUBMITTED"
    IN_PROGRESS = "IN_PROGRESS"
    UNDER_REVIEW = "UNDER_REVIEW"
    QUERY_RAISED = "QUERY_RAISED"
    INSPECTION_PENDING = "INSPECTION_PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    RENEWAL_DUE = "RENEWAL_DUE"


class IntegrationMode(str, enum.Enum):
    PUBLIC_API = "PUBLIC_API"
    AUTHORISED_API = "AUTHORISED_API"
    PORTAL_HANDOFF = "PORTAL_HANDOFF"
    MOCK = "MOCK"


class BusinessApproval(Base):
    __tablename__ = "business_approvals"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, nullable=False, index=True)
    business_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    rule_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    responsible_authority: Mapped[str] = mapped_column(String(255), nullable=False)
    
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus), 
        default=ApprovalStatus.NOT_STARTED, 
        nullable=False,
        index=True
    )
    
    # Module 8 & 9 Fields: Workflow Tracking & Government Adapter Integration
    external_system: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # e.g., 'FoSCoS', 'GST_PORTAL', 'MAITRI'
    external_reference_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)  # e.g., 'FSSAI123456'
    integration_mode: Mapped[str] = mapped_column(String(50), default="PORTAL_HANDOFF", nullable=False)
    official_portal_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    sla_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    sla_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Audit trail of stage transitions: [{"status": "OFFICIAL_PORTAL_HANDOFF", "timestamp": "...", "notes": "..."}]
    stage_history: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    additional_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
