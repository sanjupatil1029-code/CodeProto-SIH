import uuid
import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class UpdateStatus(str, enum.Enum):
    DRAFT_PENDING_REVIEW = "DRAFT_PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class RegulatoryUpdate(Base):
    __tablename__ = "regulatory_updates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_authority: Mapped[str] = mapped_column(String(255), nullable=False)
    rule_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    
    # AI-extracted changes JSON: {"sla_days": {"old": 30, "new": 15}, "added_documents": ["WATER_TEST_REPORT"]}
    extracted_changes: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    impact_summary: Mapped[str] = mapped_column(Text, nullable=False)
    
    status: Mapped[UpdateStatus] = mapped_column(
        Enum(UpdateStatus),
        default=UpdateStatus.DRAFT_PENDING_REVIEW,
        nullable=False,
        index=True
    )
    
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
