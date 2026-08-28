import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class AuditLogCreateSchema(BaseModel):
    actor_id: Optional[uuid.UUID] = None
    actor_role: str = "SYSTEM"
    action: str
    resource_type: str
    resource_id: str
    old_value: Dict[str, Any] = {}
    new_value: Dict[str, Any] = {}
    ip_address: Optional[str] = None
    request_id: Optional[str] = None


class AuditLogOut(BaseModel):
    audit_id: uuid.UUID
    actor_id: Optional[uuid.UUID] = None
    actor_role: str
    action: str
    resource_type: str
    resource_id: str
    old_value: Dict[str, Any]
    new_value: Dict[str, Any]
    timestamp: datetime
    ip_address: Optional[str] = None
    request_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AuditLogQueryResponse(BaseModel):
    total_count: int
    limit: int
    offset: int
    logs: List[AuditLogOut]
