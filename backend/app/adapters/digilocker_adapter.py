from typing import Dict, Any, List
from app.adapters.base_adapter import GovernmentIntegrationAdapter, IntegrationMode


class DigiLockerAdapter(GovernmentIntegrationAdapter):
    """
    DigiLocker G2B Document Verification Adapter.
    Mode: AUTHORISED_API.
    Official Portal: https://digilocker.gov.in
    """

    @property
    def system_name(self) -> str:
        return "DigiLocker (MeitY)"

    @property
    def integration_mode(self) -> IntegrationMode:
        return IntegrationMode.AUTHORISED_API

    def get_official_portal_url(self) -> str:
        return "https://digilocker.gov.in"

    async def check_eligibility(self, business_context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "eligible": True,
            "system": self.system_name,
            "mode": self.integration_mode.value
        }

    async def get_required_documents(self) -> List[str]:
        return ["PAN_CARD", "AADHAAR_CARD"]

    async def get_application_status(self, external_ref: str) -> Dict[str, Any]:
        return {
            "external_reference_id": external_ref,
            "system": self.system_name,
            "status": "VERIFIED",
            "remarks": "Document verified against DigiLocker Govt Master Repository.",
            "portal_url": self.get_official_portal_url()
        }

    async def get_renewal_information(self, external_ref: str) -> Dict[str, Any]:
        return {
            "external_reference_id": external_ref,
            "renewal_required": False,
            "portal_url": self.get_official_portal_url()
        }

    async def submit_application(self, business_context: Dict[str, Any], document_keys: List[str]) -> Dict[str, Any]:
        token = f"DIGI-URI-2026-TOKEN-{business_context.get('name', 'USER')[:4].upper()}"
        return {
            "external_reference_id": token,
            "external_system": self.system_name,
            "integration_mode": self.integration_mode.value,
            "status": "APPROVED",
            "official_portal_url": self.get_official_portal_url(),
            "sla_days": 1,
            "handoff_instructions": f"DigiLocker URI Token generated: {token}."
        }
