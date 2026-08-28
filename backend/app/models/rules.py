import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Integer, JSON, DateTime, Text, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class RuleStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"


class JurisdictionType(str, enum.Enum):
    CENTRAL = "CENTRAL"
    STATE = "STATE"
    DISTRICT = "DISTRICT"
    LOCAL = "LOCAL"


class ApprovalCategory(str, enum.Enum):
    LICENSE = "LICENSE"
    NOC = "NOC"
    REGISTRATION = "REGISTRATION"
    OTHER = "OTHER"


class DocumentType(Base):
    __tablename__ = "document_types"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class ApprovalRule(Base):
    __tablename__ = "approval_rules"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[ApprovalCategory] = mapped_column(Enum(ApprovalCategory), default=ApprovalCategory.LICENSE, nullable=False)
    jurisdiction: Mapped[JurisdictionType] = mapped_column(Enum(JurisdictionType), default=JurisdictionType.CENTRAL, nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=True)  # Name of state (e.g. Maharashtra) if jurisdiction is STATE
    responsible_authority: Mapped[str] = mapped_column(String(255), nullable=False)
    sla_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    inspection_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    renewal_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    renewal_interval_months: Mapped[int] = mapped_column(Integer, nullable=True)
    
    # JSON containing nested conditions
    conditions: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # JSON list of document type codes, e.g., ["PAN_CARD", "RENT_AGREEMENT"]
    required_document_types: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    
    # JSON list of rule codes this approval depends on, e.g., ["GST_REGISTRATION"]
    dependencies: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    
    explanation: Mapped[str] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)
    status: Mapped[RuleStatus] = mapped_column(Enum(RuleStatus), default=RuleStatus.ACTIVE, nullable=False)
    
    effective_from: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    effective_to: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
