import random
from typing import Dict, Any, List
from app.adapters.base_adapter import GovernmentIntegrationAdapter, IntegrationMode


class MockGovernmentAdapter(GovernmentIntegrationAdapter):
    """
    Mock Government Adapter implementation for prototype simulation & local testing.
    Mode: MOCK.
    """

    def __init__(self, rule_code: str = "DEFAULT"):
        self.rule_code = rule_code

    @property
    def system_name(self) -> str:
        return f"Mock Government Authority ({self.rule_code})"

    @property
    def integration_mode(self) -> IntegrationMode:
        return IntegrationMode.MOCK

    def get_official_portal_url(self) -> str:
        return "http://127.0.0.1:8000/docs"

    async def check_eligibility(self, business_context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "eligible": True,
            "system": self.system_name,
            "mode": self.integration_mode.value
        }

    async def get_required_documents(self) -> List[str]:
        return ["PAN_CARD", "RENT_AGREEMENT"]

    async def get_application_status(self, external_ref: str) -> Dict[str, Any]:
        return {
            "external_reference_id": external_ref,
            "system": self.system_name,
            "status": "IN_PROGRESS",
            "remarks": "Mock prototype status check: Application in progress.",
            "portal_url": self.get_official_portal_url()
        }

    async def get_renewal_information(self, external_ref: str) -> Dict[str, Any]:
        return {
            "external_reference_id": external_ref,
            "renewal_required": False,
            "portal_url": self.get_official_portal_url()
        }

    async def submit_application(self, business_context: Dict[str, Any], document_keys: List[str]) -> Dict[str, Any]:
        ref_id = f"MOCK-REF-{random.randint(100000, 999999)}"
        return {
            "external_reference_id": ref_id,
            "external_system": self.system_name,
            "integration_mode": self.integration_mode.value,
            "status": "SUBMITTED",
            "official_portal_url": self.get_official_portal_url(),
            "sla_days": 14,
            "handoff_instructions": f"Mock application submitted successfully. Reference: {ref_id}."
        }
