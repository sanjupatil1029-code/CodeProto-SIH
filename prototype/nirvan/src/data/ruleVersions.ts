import type { ProjectProfile } from "../types";

export interface RuleVersionRecord {
  ruleCode: string;
  name: string;
  version: string;
  status: "ACTIVE" | "SUPERSEDED";
  isLatest: boolean;
  effectiveFrom: string;
  effectiveTo?: string;
  slaDays: number;
  changeSummary: string;
}

export function getRuleVersionsForProfile(profile: ProjectProfile | null): RuleVersionRecord[] {
  if (!profile) return getGenericRuleVersions();

  const bizType = (profile.businessTypeId || "").toLowerCase();
  const sector = (profile.sector || "").toLowerCase();
  const isJewellery = bizType === "jewelry" || sector.includes("jewel");
  const isFood = bizType === "food" || bizType === "sugar" || sector.includes("food");
  const isShop = !["food", "textile", "metal", "sugar"].includes(bizType);

  if (isJewellery) {
    return [
      {
        ruleCode: "BIS_HALLMARKING_REG",
        name: "BIS Hallmarking Registration (Bureau of Indian Standards)",
        version: "2.0",
        status: "ACTIVE",
        isLatest: true,
        effectiveFrom: "2026-04-01",
        slaDays: 12,
        changeSummary: "Mandatory Hallmarking Order 2026: Mandates hallmarking of 14, 18, 20, 22, 23 & 24 carat gold jewellery articles with unique HUID (Hallmark Unique Identification) code.",
      },
      {
        ruleCode: "BIS_HALLMARKING_REG",
        name: "BIS Hallmarking Registration (Bureau of Indian Standards)",
        version: "1.0",
        status: "SUPERSEDED",
        isLatest: false,
        effectiveFrom: "2023-01-01",
        effectiveTo: "2026-03-31",
        slaDays: 30,
        changeSummary: "Voluntary hallmarking registration scheme for precious metal jewelers.",
      },
      {
        ruleCode: "LEGAL_METROLOGY_LICENCE",
        name: "Legal Metrology Weights & Measures Registration",
        version: "1.8",
        status: "ACTIVE",
        isLatest: true,
        effectiveFrom: "2026-01-01",
        slaDays: 10,
        changeSummary: "Legal Metrology Enforcement Rules 2026: Mandates annual digital calibration certificate & stamping for electronic precision balances used in bullion & retail jewellery trade.",
      },
      {
        ruleCode: "SHOP_ESTABLISHMENT_LICENCE",
        name: "Shop & Establishment Registration (State Labour Dept)",
        version: "3.1",
        status: "ACTIVE",
        isLatest: true,
        effectiveFrom: "2026-01-01",
        slaDays: 7,
        changeSummary: "Updated Shops & Commercial Establishments Act 2026: Single-window auto-renewals & 24x7 operation clearance for registered retail establishments.",
      },
      {
        ruleCode: "GST_REGISTRATION",
        name: "GST Registration & e-Invoicing Compliance",
        version: "1.9",
        status: "ACTIVE",
        isLatest: true,
        effectiveFrom: "2026-04-01",
        slaDays: 5,
        changeSummary: "GST Rules 2026: Mandatory biometric authentication & real-time e-Invoicing integration for precious metal sales.",
      },
    ];
  }

  if (isFood) {
    return [
      {
        ruleCode: "FSSAI_LICENSE",
        name: "FSSAI Food Business License",
        version: "2.0",
        status: "ACTIVE",
        isLatest: true,
        effectiveFrom: "2026-08-28",
        slaDays: 15,
        changeSummary: "Updated via Official Gazette Notification 2026: Fast-Track SLA reduced from 30d to 15d; added mandatory Water Quality Test Report requirement.",
      },
      {
        ruleCode: "FSSAI_LICENSE",
        name: "FSSAI Food Business License",
        version: "1.0",
        status: "SUPERSEDED",
        isLatest: false,
        effectiveFrom: "2025-01-01",
        effectiveTo: "2026-08-28",
        slaDays: 30,
        changeSummary: "Initial statutory baseline rule definition under Food Safety & Standards Act, 2006.",
      },
      {
        ruleCode: "POLLUTION_CONTROL_CONSENT",
        name: "Consent to Establish/Operate (Pollution Control Board)",
        version: "4.2",
        status: "ACTIVE",
        isLatest: true,
        effectiveFrom: "2026-03-15",
        slaDays: 30,
        changeSummary: "Water & Air Pollution Control Rules 2026: Online continuous emission & effluent monitoring system (OCEMS) mandate for food processing units.",
      },
      {
        ruleCode: "FIRE_SAFETY_NOC",
        name: "Fire Safety NOC (Maharashtra Fire Services)",
        version: "2.7",
        status: "ACTIVE",
        isLatest: true,
        effectiveFrom: "2026-03-01",
        slaDays: 20,
        changeSummary: "Fire Prevention & Life Safety Act 2026: Updated building height, extinguisher coverage & sprinkler pressure testing specifications.",
      },
    ];
  }

  if (isShop) {
    return [
      {
        ruleCode: "SHOP_ESTABLISHMENT_LICENCE",
        name: "Shop & Establishment Registration (State Labour Dept)",
        version: "3.1",
        status: "ACTIVE",
        isLatest: true,
        effectiveFrom: "2026-01-01",
        slaDays: 7,
        changeSummary: "Updated Shops & Commercial Establishments Act 2026: Single-window auto-renewals & 24x7 operation clearance for registered retail establishments.",
      },
      {
        ruleCode: "MUNICIPAL_TRADE_LICENCE",
        name: "Municipal Trade Licence",
        version: "2.0",
        status: "ACTIVE",
        isLatest: true,
        effectiveFrom: "2026-01-01",
        slaDays: 15,
        changeSummary: "Municipal Trade Licensing Guidelines 2026: Fast-track commercial premises clearance with online property tax receipt validation.",
      },
      {
        ruleCode: "GST_REGISTRATION",
        name: "GST Registration & Returns Compliance",
        version: "1.9",
        status: "ACTIVE",
        isLatest: true,
        effectiveFrom: "2026-04-01",
        slaDays: 5,
        changeSummary: "GST Rules 2026: Paperless instant registration & real-time GSTR return integration.",
      },
    ];
  }

  return getGenericRuleVersions();
}

function getGenericRuleVersions(): RuleVersionRecord[] {
  return [
    {
      ruleCode: "FACTORY_OPERATING_LICENCE",
      name: "Factory Operating Licence (DISH)",
      version: "3.5",
      status: "ACTIVE",
      isLatest: true,
      effectiveFrom: "2026-03-01",
      slaDays: 30,
      changeSummary: "Factories Act 2026 Rules: Integrated safety audit requirement & annual digital machine layout verification.",
    },
    {
      ruleCode: "POLLUTION_CONTROL_CONSENT",
      name: "Consent to Establish/Operate (Pollution Control Board)",
      version: "4.2",
      status: "ACTIVE",
      isLatest: true,
      effectiveFrom: "2026-03-15",
      slaDays: 30,
      changeSummary: "Water & Air Pollution Control Rules 2026: Online continuous emission & effluent monitoring system (OCEMS) mandate for industrial units.",
    },
    {
      ruleCode: "FIRE_SAFETY_NOC",
      name: "Fire Safety NOC (Maharashtra Fire Services)",
      version: "2.7",
      status: "ACTIVE",
      isLatest: true,
      effectiveFrom: "2026-03-01",
      slaDays: 20,
      changeSummary: "Fire Prevention & Life Safety Act 2026: Updated building height, extinguisher coverage & sprinkler pressure testing specifications.",
    },
  ];
}
