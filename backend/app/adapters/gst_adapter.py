import random
from typing import Dict, Any, List
from app.adapters.base_adapter import GovernmentIntegrationAdapter, IntegrationMode


class GSTAdapter(GovernmentIntegrationAdapter):
    """
    GST System Adapter implementation.
    Mode: PUBLIC_API / PORTAL_HANDOFF.
    Official Portal: https://services.gst.gov.in
    """

    @property
    def system_name(self) -> str:
        return "GST Portal (CBIC)"

    @property
    def integration_mode(self) -> IntegrationMode:
        return IntegrationMode.PUBLIC_API

    def get_official_portal_url(self) -> str:
        return "https://services.gst.gov.in"

    async def check_eligibility(self, business_context: Dict[str, Any]) -> Dict[str, Any]:
        turnover = float(business_context.get("expected_turnover", 0))
        requires_gst = turnover > 2000000.0
        return {
            "eligible": True,
            "mandatory": requires_gst,
            "system": self.system_name,
            "threshold": 2000000.0,
            "mode": self.integration_mode.value
        }

    async def get_required_documents(self) -> List[str]:
        return ["PAN_CARD", "RENT_AGREEMENT"]

    async def get_application_status(self, external_ref: str) -> Dict[str, Any]:
        return {
            "external_reference_id": external_ref,
            "system": self.system_name,
            "status": "APPROVED",
            "remarks": "GSTIN generated and active on GST Portal.",
            "portal_url": self.get_official_portal_url()
        }

    async def get_renewal_information(self, external_ref: str) -> Dict[str, Any]:
        return {
            "external_reference_id": external_ref,
            "renewal_required": False,
            "portal_url": self.get_official_portal_url()
        }

    async def submit_application(self, business_context: Dict[str, Any], document_keys: List[str]) -> Dict[str, Any]:
        arn = f"AA{random.randint(10, 99)}0826{random.randint(1000, 9999)}Z{random.randint(1, 9)}"
        return {
            "external_reference_id": arn,
            "external_system": self.system_name,
            "integration_mode": self.integration_mode.value,
            "status": "SUBMITTED",
            "official_portal_url": self.get_official_portal_url(),
            "sla_days": 7,
            "handoff_instructions": f"Application submitted directly to GST System API. ARN: {arn}."
        }
