import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class BusinessBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, examples=["Organic Foods Processing Unit"])
    sector: str = Field(..., examples=["FOOD_PROCESSING"])
    sub_sector: str = Field(default="GENERAL", examples=["DAIRY_PRODUCTS"])
    state: str = Field(..., examples=["Maharashtra"])
    district: str = Field(..., examples=["Pune"])
    city: str = Field(default="DEFAULT", examples=["Chinchwad"])
    investment_amount: float = Field(..., gt=0, description="Investment in INR", examples=[15000000.00])
    employee_count: int = Field(..., gt=0, examples=[45])
    expected_turnover: float = Field(..., gt=0, description="Expected annual turnover in INR", examples=[35000000.00])
    operational_stage: str = Field(default="PLANNED", examples=["PLANNED"])  # e.g., PLANNED, REGISTERED, OPERATIONAL
    ownership_type: str = Field(default="PRIVATE_LIMITED", examples=["PRIVATE_LIMITED"])  # e.g. PROPRIETORSHIP, PRIVATE_LIMITED, LLP, PARTNERSHIP
    premises_type: str = Field(default="RENTED", examples=["RENTED"])  # e.g. OWNED, RENTED, LEASED, MIDC_PLOT
    flexible_attributes: Dict[str, Any] = Field(default_factory=dict, description="Custom sector-specific parameters")


class BusinessCreate(BusinessBase):
    pass


class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    sector: Optional[str] = None
    sub_sector: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    investment_amount: Optional[float] = Field(None, gt=0)
    employee_count: Optional[int] = Field(None, gt=0)
    expected_turnover: Optional[float] = Field(None, gt=0)
    operational_stage: Optional[str] = None
    ownership_type: Optional[str] = None
    premises_type: Optional[str] = None
    flexible_attributes: Optional[Dict[str, Any]] = None


class BusinessOut(BusinessBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
