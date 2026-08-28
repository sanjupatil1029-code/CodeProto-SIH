import uuid
import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, ForeignKey, Integer, Float, JSON, DateTime, Text, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class VerificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    AUTO_VERIFIED = "AUTO_VERIFIED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    document_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus),
        default=VerificationStatus.PENDING,
        nullable=False,
        index=True
    )
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    parent_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Dynamic extracted fields from OCR/Parser
    extracted_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    classification_confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    is_reusable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
