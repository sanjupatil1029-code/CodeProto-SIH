import uuid
import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class InspectionStatus(str, enum.Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    RESCHEDULED = "RESCHEDULED"
    FAILED = "FAILED"


class Inspection(Base):
    __tablename__ = "inspections"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    approval_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("business_approvals.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    officer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[InspectionStatus] = mapped_column(
        Enum(InspectionStatus),
        default=InspectionStatus.PENDING,
        nullable=False,
        index=True
    )
    
    scheduled_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    actual_inspection_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    location_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    inspector_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    findings_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # JSON list of checklist items: [{"check": "Fire Extinguisher Present", "passed": true}, ...]
    checklist_results: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
