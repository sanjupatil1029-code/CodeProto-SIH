import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class CertificateDatesUpdate(BaseModel):
    issue_date: datetime = Field(..., description="Date certificate/license was issued")
    validity_years: Optional[float] = Field(None, description="Validity period in years (e.g. 1.0, 5.0). If omitted, expiry_date must be provided.")
    expiry_date: Optional[datetime] = Field(None, description="Explicit expiration date if not using validity_years.")
    renewal_reminder_days: Optional[int] = Field(30, description="Custom reminder threshold in days (e.g. 90, 60, 30, 15).")


class RenewalItemOut(BaseModel):
    approval_id: uuid.UUID
    rule_code: str
    approval_name: str
    responsible_authority: str
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    days_until_expiry: Optional[int] = None
    renewal_status: str  # UP_TO_DATE, RENEWAL_DUE, CRITICAL_RENEWAL, EXPIRED
    renewal_deadline: Optional[datetime] = None
    reminder_threshold_triggered: Optional[int] = None  # 90, 60, 30, 15, 7, 1

    model_config = ConfigDict(from_attributes=True)


class ComplianceDashboardOut(BaseModel):
    business_id: uuid.UUID
    total_licenses: int
    up_to_date_count: int
    renewal_due_count: int
    critical_renewal_count: int
    expired_count: int
    renewals: List[RenewalItemOut]


class SLABreachItemOut(BaseModel):
    approval_id: uuid.UUID
    rule_code: str
    approval_name: str
    responsible_authority: str
    status: str
    started_at: Optional[datetime] = None
    sla_days: int
    sla_deadline: Optional[datetime] = None
    elapsed_days: float
    elapsed_percent: float
    sla_status: str  # ON_TRACK, SLA_WARNING, SLA_BREACHED

    model_config = ConfigDict(from_attributes=True)


class DepartmentBottleneckOut(BaseModel):
    authority: str
    total_applications: int
    in_progress_count: int
    sla_breached_count: int
    average_processing_days: float
    bottleneck_risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL


class SLABottleneckAnalyticsOut(BaseModel):
    business_id: uuid.UUID
    total_active_applications: int
    on_track_count: int
    warning_count: int
    breached_count: int
    overall_sla_health_percent: float
    applications: List[SLABreachItemOut]
    department_bottlenecks: List[DepartmentBottleneckOut]
