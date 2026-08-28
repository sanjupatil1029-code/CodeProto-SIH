import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Numeric, Integer, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., 'FOOD_PROCESSING'
    sub_sector: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    investment_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    employee_count: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_turnover: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    operational_stage: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., 'PLANNED', 'REGISTERED', 'OPERATIONAL'
    
    # JSON column for dynamic, sector-specific attributes (e.g. food business specific answers)
    flexible_attributes: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
