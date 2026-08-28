import uuid
import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class GrievanceCategory(str, enum.Enum):
    SLA_BREACH = "SLA_BREACH"
    DOCUMENT_QUERY = "DOCUMENT_QUERY"
    INSPECTION_DELAY = "INSPECTION_DELAY"
    OFFICER_MISCONDUCT = "OFFICER_MISCONDUCT"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    OTHER = "OTHER"


class GrievancePriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class GrievanceStatus(str, enum.Enum):
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"
    CLOSED = "CLOSED"


class Grievance(Base):
    __tablename__ = "grievances"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    approval_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("business_approvals.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    complainant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    assigned_officer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    department: Mapped[str] = mapped_column(String(255), default="General Authority", nullable=False)
    
    category: Mapped[GrievanceCategory] = mapped_column(
        Enum(GrievanceCategory),
        default=GrievanceCategory.SLA_BREACH,
        nullable=False,
        index=True
    )
    priority: Mapped[GrievancePriority] = mapped_column(
        Enum(GrievancePriority),
        default=GrievancePriority.MEDIUM,
        nullable=False,
        index=True
    )
    status: Mapped[GrievanceStatus] = mapped_column(
        Enum(GrievanceStatus),
        default=GrievanceStatus.OPEN,
        nullable=False,
        index=True
    )
    
    escalation_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1 -> Nodal, 2 -> Senior, 3 -> Secretariat
    resolution_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Audit log of escalation history: [{"level": 2, "escalated_at": "...", "reason": "SLA Exceeded"}]
    escalation_history: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
