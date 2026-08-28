from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.models.workflows import IntegrationMode


class GovernmentIntegrationAdapter(ABC):
    """
    Abstract Base Class for Government Integration Adapter Layer (Module 9).
    Decouples core business logic from direct government API calls or portal handoffs.
    """

    @property
    @abstractmethod
    def system_name(self) -> str:
        """Name of the external government portal / system (e.g., FoSCoS, GST_PORTAL, MAITRI)."""
        pass

    @property
    @abstractmethod
    def integration_mode(self) -> IntegrationMode:
        """Integration type: PUBLIC_API, AUTHORISED_API, PORTAL_HANDOFF, or MOCK."""
        pass

    @abstractmethod
    async def check_eligibility(self, business_context: Dict[str, Any]) -> Dict[str, Any]:
        """Check business eligibility against government rules."""
        pass

    @abstractmethod
    async def get_required_documents(self) -> List[str]:
        """Retrieve required document type codes for this approval/license."""
        pass

    @abstractmethod
    async def get_application_status(self, external_ref: str) -> Dict[str, Any]:
        """Fetch latest application status from external government system."""
        pass

    @abstractmethod
    async def get_renewal_information(self, external_ref: str) -> Dict[str, Any]:
        """Fetch renewal due dates, fees, and requirements."""
        pass

    @abstractmethod
    async def submit_application(self, business_context: Dict[str, Any], document_keys: List[str]) -> Dict[str, Any]:
        """
        Submit application to external system (or prepare handoff package).
        Returns dict containing external_reference_id, status, official_portal_url, and SLA.
        """
        pass

    @abstractmethod
    def get_official_portal_url(self) -> str:
        """Return the official government portal URL for handoff or direct user access."""
        pass
