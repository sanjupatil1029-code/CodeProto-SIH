from typing import Dict, Type
from app.adapters.base_adapter import GovernmentIntegrationAdapter
from app.adapters.fssai_adapter import FSSAIAdapter
from app.adapters.gst_adapter import GSTAdapter
from app.adapters.maitri_adapter import MAITRIAdapter
from app.adapters.nsws_adapter import NSWSAdapter
from app.adapters.digilocker_adapter import DigiLockerAdapter
from app.adapters.mock_adapter import MockGovernmentAdapter


class AdapterFactory:
    """
    Factory for resolving and instantiating the appropriate GovernmentIntegrationAdapter (Module 9).
    """

    _RULE_ADAPTER_MAP: Dict[str, Type[GovernmentIntegrationAdapter]] = {
        "FSSAI_LICENSE": FSSAIAdapter,
        "GST_REGISTRATION": GSTAdapter,
        "FIRE_NOC": MAITRIAdapter,
        "WATER_CONSENT": MAITRIAdapter,
        "LOCAL_MUNICIPAL_NOC": MAITRIAdapter,
        "NSWS": NSWSAdapter,
        "DIGILOCKER": DigiLockerAdapter,
    }

    @classmethod
    def get_adapter(cls, rule_code_or_system: str) -> GovernmentIntegrationAdapter:
        """
        Dynamically returns the matching adapter instance for a rule code or system name.
        Defaults to MockGovernmentAdapter if no specific adapter is configured.
        """
        code_upper = rule_code_or_system.upper().strip()
        
        # Check rule mapping
        if code_upper in cls._RULE_ADAPTER_MAP:
            return cls._RULE_ADAPTER_MAP[code_upper]()

        # Check system keyword matches
        if "FSSAI" in code_upper or "FOSCOS" in code_upper:
            return FSSAIAdapter()
        elif "GST" in code_upper:
            return GSTAdapter()
        elif "MAITRI" in code_upper or "FIRE" in code_upper or "WATER" in code_upper:
            return MAITRIAdapter()
        elif "NSWS" in code_upper:
            return NSWSAdapter()
        elif "DIGILOCKER" in code_upper:
            return DigiLockerAdapter()

        return MockGovernmentAdapter(rule_code=code_upper)

    @classmethod
    def list_registered_adapters(cls) -> Dict[str, dict]:
        """List all available adapters, their target systems, modes, and portal URLs."""
        adapters = [
            FSSAIAdapter(),
            GSTAdapter(),
            MAITRIAdapter(),
            NSWSAdapter(),
            DigiLockerAdapter(),
            MockGovernmentAdapter(),
        ]

        return {
            a.system_name: {
                "system_name": a.system_name,
                "integration_mode": a.integration_mode.value,
                "official_portal_url": a.get_official_portal_url(),
            }
            for a in adapters
        }
