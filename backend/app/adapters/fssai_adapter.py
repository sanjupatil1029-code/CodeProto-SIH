import random
from typing import Dict, Any, List
from app.adapters.base_adapter import GovernmentIntegrationAdapter, IntegrationMode


class FSSAIAdapter(GovernmentIntegrationAdapter):
    """
    FSSAI FoSCoS Portal Adapter implementation.
    Mode: PORTAL_HANDOFF (Official G2B Portal Redirect).
    Official Portal: https://foscos.fssai.gov.in
    """

    @property
    def system_name(self) -> str:
        return "FoSCoS (FSSAI)"

    @property
    def integration_mode(self) -> IntegrationMode:
        return IntegrationMode.PORTAL_HANDOFF

    def get_official_portal_url(self) -> str:
        return "https://foscos.fssai.gov.in"

    async def check_eligibility(self, business_context: Dict[str, Any]) -> Dict[str, Any]:
        turnover = float(business_context.get("expected_turnover", 0))
        sector = business_context.get("sector", "").upper()
        
        is_eligible = sector == "FOOD_PROCESSING" or "FOOD" in sector
        license_type = "State / Central Food License" if turnover > 1200000 else "Basic Registration"
        
        return {
            "eligible": is_eligible,
            "license_type": license_type,
            "system": self.system_name,
            "mode": self.integration_mode.value
        }

    async def get_required_documents(self) -> List[str]:
        return ["PAN_CARD", "RENT_AGREEMENT", "GST_IN"]

    async def get_application_status(self, external_ref: str) -> Dict[str, Any]:
        return {
            "external_reference_id": external_ref,
            "system": self.system_name,
            "status": "IN_PROGRESS",
            "remarks": "FoSCoS Officer inspecting food processing facility site plan.",
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
        ref_id = f"FSSAI{random.randint(10000000, 99999999)}"
        return {
            "external_reference_id": ref_id,
            "external_system": self.system_name,
            "integration_mode": self.integration_mode.value,
            "status": "OFFICIAL_PORTAL_HANDOFF",
            "official_portal_url": self.get_official_portal_url(),
            "sla_days": 30,
            "handoff_instructions": (
                f"NIRVAAN has generated your FoSCoS pre-filled handoff package. "
                f"Reference: {ref_id}. Please complete final payment on {self.get_official_portal_url()}."
            )
        }
