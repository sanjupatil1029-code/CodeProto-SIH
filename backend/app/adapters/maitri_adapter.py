import random
from typing import Dict, Any, List
from app.adapters.base_adapter import GovernmentIntegrationAdapter, IntegrationMode


class MAITRIAdapter(GovernmentIntegrationAdapter):
    """
    Maharashtra MAITRI Single Window Portal Adapter.
    Mode: PORTAL_HANDOFF.
    Official Portal: https://maitri.mahaonline.gov.in
    """

    @property
    def system_name(self) -> str:
        return "MAITRI Single Window (Maharashtra Govt)"

    @property
    def integration_mode(self) -> IntegrationMode:
        return IntegrationMode.PORTAL_HANDOFF

    def get_official_portal_url(self) -> str:
        return "https://maitri.mahaonline.gov.in"

    async def check_eligibility(self, business_context: Dict[str, Any]) -> Dict[str, Any]:
        state = (business_context.get("state") or "").upper()
        return {
            "eligible": state == "MAHARASHTRA",
            "system": self.system_name,
            "mode": self.integration_mode.value
        }

    async def get_required_documents(self) -> List[str]:
        return ["RENT_AGREEMENT", "FIRE_NOC_APPLICATION", "WATER_BILL"]

    async def get_application_status(self, external_ref: str) -> Dict[str, Any]:
        return {
            "external_reference_id": external_ref,
            "system": self.system_name,
            "status": "IN_PROGRESS",
            "remarks": "MAITRI Single Window routed application to MPCB & Maharashtra Fire Services.",
            "portal_url": self.get_official_portal_url()
        }

    async def get_renewal_information(self, external_ref: str) -> Dict[str, Any]:
        return {
            "external_reference_id": external_ref,
            "renewal_required": True,
            "interval_months": 12,
            "portal_url": self.get_official_portal_url()
        }

    async def submit_application(self, business_context: Dict[str, Any], document_keys: List[str]) -> Dict[str, Any]:
        ref_id = f"MAI-MH-2026-{random.randint(10000, 99999)}"
        return {
            "external_reference_id": ref_id,
            "external_system": self.system_name,
            "integration_mode": self.integration_mode.value,
            "status": "OFFICIAL_PORTAL_HANDOFF",
            "official_portal_url": self.get_official_portal_url(),
            "sla_days": 15,
            "handoff_instructions": (
                f"Application routed to MAITRI Single Window Portal. Reference: {ref_id}. "
                f"Access portal at {self.get_official_portal_url()}."
            )
        }
