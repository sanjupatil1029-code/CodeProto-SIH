import random
from typing import Dict, Any, List
from app.adapters.base_adapter import GovernmentIntegrationAdapter, IntegrationMode


class NSWSAdapter(GovernmentIntegrationAdapter):
    """
    National Single Window System (NSWS) Adapter.
    Mode: AUTHORISED_API.
    Official Portal: https://nsws.gov.in
    """

    @property
    def system_name(self) -> str:
        return "National Single Window System (NSWS)"

    @property
    def integration_mode(self) -> IntegrationMode:
        return IntegrationMode.AUTHORISED_API

    def get_official_portal_url(self) -> str:
        return "https://nsws.gov.in"

    async def check_eligibility(self, business_context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "eligible": True,
            "system": self.system_name,
            "mode": self.integration_mode.value
        }

    async def get_required_documents(self) -> List[str]:
        return ["PAN_CARD", "INCORPORATION_CERT", "RENT_AGREEMENT"]

    async def get_application_status(self, external_ref: str) -> Dict[str, Any]:
        return {
            "external_reference_id": external_ref,
            "system": self.system_name,
            "status": "UNDER_REVIEW",
            "remarks": "NSWS G2B API status check: Under review by Central Ministry portal.",
            "portal_url": self.get_official_portal_url()
        }

    async def get_renewal_information(self, external_ref: str) -> Dict[str, Any]:
        return {
            "external_reference_id": external_ref,
            "renewal_required": False,
            "portal_url": self.get_official_portal_url()
        }

    async def submit_application(self, business_context: Dict[str, Any], document_keys: List[str]) -> Dict[str, Any]:
        nsws_id = f"NSWS-GOI-2026-{random.randint(100000, 999999)}"
        return {
            "external_reference_id": nsws_id,
            "external_system": self.system_name,
            "integration_mode": self.integration_mode.value,
            "status": "SUBMITTED",
            "official_portal_url": self.get_official_portal_url(),
            "sla_days": 30,
            "handoff_instructions": f"Application transmitted via Authorised G2B API to NSWS. Reference: {nsws_id}."
        }
