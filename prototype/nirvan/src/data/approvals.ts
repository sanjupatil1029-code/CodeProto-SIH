import type { ApprovalDef, ProjectProfile } from "../types";
import { sugarFactorySteps, jewelleryShopSteps } from "./curatedRoadmaps";

const isIndustry = (p: ProjectProfile) =>
  ["food", "textile", "metal", "sugar"].includes(p.businessTypeId);

export const approvals: ApprovalDef[] = [
  {
    id: "biz-reg",
    name: "Business Registration",
    why: "Every legal business entity must be registered before it can apply for sector-specific approvals. This establishes your PAN, GST and Udyam/company identity.",
    applicability: "Mandatory for all shops and industries, regardless of size.",
    documents: ["PAN Card", "Aadhaar Card", "Business Address Proof", "Passport-size Photo"],
    authority: "Ministry of Corporate Affairs / Udyam Registration Portal",
    dependsOn: [],
    inspectionRequired: false,
    slaDays: 3,
    renewal: "One-time (no renewal)",
    source: "Udyam Registration Portal / MCA21",
    ruleVersion: "v2.3",
    effectiveDate: "01 Apr 2026",
    appliesTo: () => true,
  },
  {
    id: "gst-reg",
    name: "GST Registration",
    why: "Required to legally collect tax on goods/services and issue tax invoices once turnover crosses the prescribed threshold.",
    applicability: "Mandatory for all shops and industries above the GST turnover threshold.",
    documents: ["PAN Card", "Business Registration Certificate", "Bank Account Proof", "Address Proof"],
    authority: "Goods & Services Tax Network (GSTN)",
    dependsOn: ["biz-reg"],
    inspectionRequired: false,
    slaDays: 5,
    renewal: "Annual return filing",
    source: "GST Portal",
    ruleVersion: "v1.9",
    effectiveDate: "01 Apr 2026",
    appliesTo: () => true,
  },
  {
    id: "shop-establishment",
    name: "Shop & Establishment Registration",
    why: "Registers your commercial premises with the local labour department, governing working hours, holidays and employee welfare.",
    applicability: "Applicable to retail shops, hotels and other commercial establishments.",
    documents: ["Business Registration Certificate", "Address Proof of Premises", "List of Employees"],
    authority: "State Labour Department (Municipal Corporation)",
    dependsOn: ["biz-reg"],
    inspectionRequired: false,
    slaDays: 7,
    renewal: "Every 5 years",
    source: "State Shops & Establishments Act",
    ruleVersion: "v3.1",
    effectiveDate: "01 Jan 2026",
    appliesTo: (p) => !isIndustry(p),
  },
  {
    id: "trade-license",
    name: "Trade Licence",
    why: "Local municipal authorisation confirming the trade carried out at the premises complies with zoning and civic safety norms.",
    applicability: "Required for all retail shops operating from a fixed premises.",
    documents: ["Shop & Establishment Certificate", "Ownership/Rent Agreement", "Property Tax Receipt"],
    authority: "Municipal Corporation",
    dependsOn: ["shop-establishment"],
    inspectionRequired: true,
    slaDays: 15,
    renewal: "Annual",
    source: "Municipal Corporation Trade Licence Rules",
    ruleVersion: "v2.0",
    effectiveDate: "01 Jan 2026",
    appliesTo: (p) => !isIndustry(p),
  },
  {
    id: "land-building",
    name: "Land & Building Plan Approval",
    why: "Confirms land use classification and sanctions the building plan before industrial construction begins.",
    applicability: "Required for new industrial setups constructing or modifying a factory building.",
    documents: ["Land Ownership Documents", "Site Layout Plan", "Building Plan Drawings"],
    authority: "State Industrial Development Corporation / Town Planning Dept.",
    dependsOn: ["biz-reg"],
    inspectionRequired: true,
    slaDays: 25,
    renewal: "One-time (no renewal)",
    source: "State Industrial Land Allotment & Building Regulations",
    ruleVersion: "v1.4",
    effectiveDate: "01 Feb 2026",
    appliesTo: (p) => isIndustry(p) && p.projectType === "New Setup",
  },
  {
    id: "pollution-consent",
    name: "Pollution Consent (CTE/CTO)",
    why: "Consent to Establish/Operate from the Pollution Control Board is mandatory for manufacturing activity that generates emissions, effluent or waste.",
    applicability: "Required for food, textile, metal and sugar manufacturing units above small-scale thresholds.",
    documents: ["Business Registration Certificate", "Site Layout Plan", "Effluent/Emission Details", "Project Report"],
    authority: "State Pollution Control Board",
    dependsOn: ["biz-reg"],
    inspectionRequired: true,
    slaDays: 30,
    renewal: "Every 5 years",
    source: "Water (Prevention & Control of Pollution) Act / Air Act",
    ruleVersion: "v4.2",
    effectiveDate: "15 Mar 2026",
    appliesTo: (p) => isIndustry(p),
  },
  {
    id: "fire-noc",
    name: "Fire NOC",
    why: "Certifies that the premises meets fire safety norms — exits, extinguishers, hydrant systems — before occupation or manufacturing begins.",
    applicability: "Required for hotels, factories and any premises with public occupancy or manufacturing activity.",
    documents: ["Building Plan Approval", "Fire Safety Layout", "Fire-fighting Equipment List"],
    authority: "State Fire & Emergency Services Department",
    dependsOn: ["biz-reg"],
    inspectionRequired: true,
    slaDays: 20,
    renewal: "Annual",
    source: "State Fire Prevention & Life Safety Measures Act",
    ruleVersion: "v2.7",
    effectiveDate: "01 Mar 2026",
    appliesTo: (p) => isIndustry(p) || p.businessTypeId === "hotel" || p.size !== "Small",
  },
  {
    id: "labour-registration",
    name: "Labour Registration",
    why: "Registers the establishment under labour welfare law once the employee count crosses the statutory threshold, covering wages, safety and welfare compliance.",
    applicability: "Required where employee count is 10 or more (20+ for units without power).",
    documents: ["Business Registration Certificate", "Employee List with Details", "Factory/Premises Layout"],
    authority: "State Labour & Factories Department",
    dependsOn: ["biz-reg"],
    inspectionRequired: false,
    slaDays: 10,
    renewal: "Annual",
    source: "Factories Act / State Labour Welfare Rules",
    ruleVersion: "v1.6",
    effectiveDate: "01 Apr 2026",
    appliesTo: (p) => p.employees >= 10,
  },
  {
    id: "factory-licence",
    name: "Factory Licence",
    why: "The core operating licence for a manufacturing unit, confirming that pollution, fire and labour conditions are satisfied before production starts.",
    applicability: "Mandatory for industrial units with 10+ workers using power, or 20+ without power.",
    documents: ["Pollution Consent", "Fire NOC", "Building Plan Approval", "Machinery Layout"],
    authority: "State Directorate of Industrial Safety & Health",
    dependsOn: ["pollution-consent", "fire-noc"],
    inspectionRequired: true,
    slaDays: 30,
    renewal: "Annual",
    source: "Factories Act, 1948",
    ruleVersion: "v3.5",
    effectiveDate: "01 Mar 2026",
    appliesTo: (p) => isIndustry(p) && p.employees >= 10,
  },
  {
    id: "fssai",
    name: "FSSAI Licence / Registration",
    why: "Certifies that food handled, manufactured or sold at the premises meets food-safety standards. Basic registration applies to small turnover; a full licence applies above the threshold.",
    applicability: "Required for food-processing units, hotels, medical stores and general stores handling food items.",
    documents: ["Business Registration Certificate", "Water Test Report", "Food Safety Management Plan"],
    authority: "Food Safety and Standards Authority of India (FSSAI)",
    dependsOn: ["biz-reg"],
    inspectionRequired: true,
    slaDays: 20,
    renewal: "1 or 5 years (licence tenure chosen at application)",
    source: "Food Safety and Standards Act, 2006",
    ruleVersion: "v2.9",
    effectiveDate: "01 Jan 2026",
    appliesTo: (p) => ["food", "hotel", "general-store", "medical-store"].includes(p.businessTypeId),
  },
  {
    id: "drug-licence",
    name: "Drug Licence (Retail)",
    why: "Legally required to stock and sell scheduled pharmaceutical drugs, ensuring a registered pharmacist oversees dispensing.",
    applicability: "Mandatory for all medical/pharmacy retail stores.",
    documents: ["Pharmacist Registration Certificate", "Premises Layout", "Cold Storage Details"],
    authority: "State Drugs Control Department",
    dependsOn: ["shop-establishment"],
    inspectionRequired: true,
    slaDays: 20,
    renewal: "Every 5 years",
    source: "Drugs and Cosmetics Act, 1940",
    ruleVersion: "v2.1",
    effectiveDate: "01 Feb 2026",
    appliesTo: (p) => p.businessTypeId === "medical-store",
  },
  {
    id: "hallmarking",
    name: "BIS Hallmarking Registration",
    why: "Mandatory certification confirming the purity of gold/silver jewellery sold, protecting consumers from under-carat sales.",
    applicability: "Mandatory for all jewellery retailers selling hallmarked gold/silver articles.",
    documents: ["Business Registration Certificate", "GST Certificate", "Premises Photographs"],
    authority: "Bureau of Indian Standards (BIS)",
    dependsOn: ["gst-reg"],
    inspectionRequired: false,
    slaDays: 12,
    renewal: "Every 3 years",
    source: "BIS Hallmarking Scheme",
    ruleVersion: "v1.8",
    effectiveDate: "01 Apr 2026",
    appliesTo: (p) => p.businessTypeId === "jewelry",
  },
  {
    id: "legal-metrology",
    name: "Legal Metrology (Weights & Measures) Licence",
    why: "Certifies that all weighing/measuring instruments used at the premises are calibrated and stamped for accuracy.",
    applicability: "Required for retailers who weigh or measure goods for sale.",
    documents: ["Business Registration Certificate", "List of Weighing Instruments"],
    authority: "State Legal Metrology Department",
    dependsOn: ["biz-reg"],
    inspectionRequired: true,
    slaDays: 10,
    renewal: "Annual",
    source: "Legal Metrology Act, 2009",
    ruleVersion: "v1.5",
    effectiveDate: "01 Jan 2026",
    appliesTo: (p) => ["jewelry", "general-store"].includes(p.businessTypeId),
  },
  {
    id: "electricity-approval",
    name: "Electricity Load Sanction",
    why: "Approves the sanctioned power load for industrial machinery and connects the unit to the grid at an industrial tariff.",
    applicability: "Required for industrial units drawing power above domestic/commercial thresholds.",
    documents: ["Building Plan Approval", "Machinery Load Details", "Site Layout Plan"],
    authority: "State Electricity Distribution Company",
    dependsOn: ["biz-reg"],
    inspectionRequired: true,
    slaDays: 18,
    renewal: "One-time (no renewal)",
    source: "State Electricity Supply Code",
    ruleVersion: "v1.3",
    effectiveDate: "01 Mar 2026",
    appliesTo: (p) => isIndustry(p),
  },
];

function computeDepths(applicable: ApprovalDef[]): Map<string, number> {
  const idSet = new Set(applicable.map((a) => a.id));
  const depths = new Map<string, number>();
  const depth = (a: ApprovalDef, seen: Set<string> = new Set()): number => {
    if (depths.has(a.id)) return depths.get(a.id)!;
    if (seen.has(a.id)) return 0;
    seen.add(a.id);
    const deps = a.dependsOn.filter((d) => idSet.has(d));
    let d = 0;
    if (deps.length > 0) {
      const parents = deps.map((dep) => applicable.find((x) => x.id === dep)!).filter(Boolean);
      d = 1 + Math.max(...parents.map((p) => depth(p, seen)));
    }
    depths.set(a.id, d);
    return d;
  };
  applicable.forEach((a) => depth(a));
  return depths;
}

export function getApplicableApprovals(profile: ProjectProfile): ApprovalDef[] {
  if (profile.businessTypeId === "sugar") return sugarFactorySteps;
  if (profile.businessTypeId === "jewelry") return jewelleryShopSteps;
  const applicable = approvals.filter((a) => a.appliesTo(profile));
  const depths = computeDepths(applicable);
  return [...applicable].sort((a, b) => (depths.get(a.id)! - depths.get(b.id)!));
}

/** Groups applicable approvals into ordered levels (rows) for the vertical roadmap. */
export function getRoadmapLevels(profile: ProjectProfile): ApprovalDef[][] {
  if (profile.businessTypeId === "sugar") return sugarFactorySteps.map((s) => [s]);
  if (profile.businessTypeId === "jewelry") return jewelleryShopSteps.map((s) => [s]);
  const applicable = approvals.filter((a) => a.appliesTo(profile));
  const depths = computeDepths(applicable);
  const maxDepth = Math.max(0, ...Array.from(depths.values()));
  const levels: ApprovalDef[][] = Array.from({ length: maxDepth + 1 }, () => []);
  applicable.forEach((a) => levels[depths.get(a.id)!].push(a));
  return levels;
}

/** All approval definitions across the generic engine and both curated roadmaps — used for document matching. */
export function getAllApprovalDefs(): ApprovalDef[] {
  return [...approvals, ...sugarFactorySteps, ...jewelleryShopSteps];
}

/** Looks up a single approval definition by id across the generic list and both curated roadmaps. */
export function findApprovalById(id: string): ApprovalDef | undefined {
  return (
    approvals.find((a) => a.id === id) ||
    sugarFactorySteps.find((a) => a.id === id) ||
    jewelleryShopSteps.find((a) => a.id === id)
  );
}
