import uuid
import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Float, Boolean, DateTime, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class SchemeCategory(str, enum.Enum):
    CAPITAL_SUBSIDY = "CAPITAL_SUBSIDY"
    INTEREST_SUBVENTION = "INTEREST_SUBVENTION"
    TAX_EXEMPTION = "TAX_EXEMPTION"
    INFRASTRUCTURE_GRANT = "INFRASTRUCTURE_GRANT"
    EXPORT_INCENTIVE = "EXPORT_INCENTIVE"


class Scheme(Base):
    __tablename__ = "government_schemes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str] = mapped_column(String(255), nullable=False)
    
    category: Mapped[SchemeCategory] = mapped_column(
        Enum(SchemeCategory),
        default=SchemeCategory.CAPITAL_SUBSIDY,
        nullable=False,
        index=True
    )
    
    benefit_summary: Mapped[str] = mapped_column(Text, nullable=False)
    max_benefit_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Eligibility criteria JSON: {"sectors": ["FOOD_PROCESSING"], "max_turnover": 50000000, "states": ["MAHARASHTRA", "ALL"]}
    eligibility_conditions: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # Required documents JSON list: ["PAN_CARD", "PROJECT_REPORT"]
    required_documents: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    
    official_portal_url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
