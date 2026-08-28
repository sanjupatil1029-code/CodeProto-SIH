import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class ApprovalStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    READY = "READY"
    BLOCKED = "BLOCKED"
    IN_PROGRESS = "IN_PROGRESS"
    UNDER_REVIEW = "UNDER_REVIEW"
    QUERY_RAISED = "QUERY_RAISED"
    INSPECTION_PENDING = "INSPECTION_PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    RENEWAL_DUE = "RENEWAL_DUE"


class BusinessApproval(Base):
    __tablename__ = "business_approvals"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    rule_code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    responsible_authority: Mapped[str] = mapped_column(String(255), nullable=False)
    
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus), 
        default=ApprovalStatus.NOT_STARTED, 
        nullable=False
    )
    
    sla_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    sla_deadline: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
