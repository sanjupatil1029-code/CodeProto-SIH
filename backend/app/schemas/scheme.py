import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.scheme import SchemeCategory


class SchemeOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    department: str
    category: SchemeCategory
    benefit_summary: str
    max_benefit_amount: float
    eligibility_conditions: Dict[str, Any] = {}
    required_documents: List[str] = []
    official_portal_url: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SchemeMatchResultOut(BaseModel):
    scheme_id: uuid.UUID
    code: str
    name: str
    department: str
    category: str
    match_status: str  # MATCHED, CONDITIONAL, INELIGIBLE
    eligibility_reasons: List[str] = []
    ineligibility_reasons: List[str] = []
    estimated_benefit_amount: float
    benefit_summary: str
    required_documents: List[str] = []
    official_portal_url: str


class BusinessSchemeMatchesResponse(BaseModel):
    business_id: uuid.UUID
    total_schemes_evaluated: int
    matched_count: int
    conditional_count: int
    total_potential_benefit: float
    matches: List[SchemeMatchResultOut]
