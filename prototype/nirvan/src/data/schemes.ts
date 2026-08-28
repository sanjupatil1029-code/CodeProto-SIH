import type { SchemeDef, ProjectProfile } from "../types";

const isIndustry = (p: ProjectProfile) =>
  ["food", "textile", "metal", "sugar"].includes(p.businessTypeId);

export const schemes: SchemeDef[] = [
  {
    id: "msme-support",
    name: "MSME Support & Credit Guarantee Scheme",
    matchLevel: "Strong Match",
    why: "Your business qualifies as an MSME based on declared investment and employee size.",
    eligibility: ["Registered as Udyam/MSME", "Investment within MSME threshold", "Any sector"],
    benefits: ["Collateral-free loans up to ₹2 Cr", "Interest subvention up to 2%", "Priority sector lending"],
    documents: ["Udyam Registration Certificate", "Business PAN", "Bank Statements (6 months)"],
    status: "Eligible",
    appliesTo: (p) => p.size !== "Large",
  },
  {
    id: "food-processing-subsidy",
    name: "Food Processing Industry Subsidy",
    matchLevel: "Strong Match",
    why: "Your project profile is a food-processing manufacturing unit, the core target sector for this scheme.",
    eligibility: ["Food-processing manufacturing activity", "New setup or expansion", "Valid FSSAI application in progress"],
    benefits: ["Capital subsidy up to 35% of eligible plant & machinery cost", "Grading & standardisation support"],
    documents: ["Project Report (DPR)", "FSSAI Application Acknowledgement", "Land/Building Documents"],
    status: "Eligible",
    appliesTo: (p) => p.businessTypeId === "food",
  },
  {
    id: "state-industrial-incentive",
    name: "State Industrial Investment Incentive",
    matchLevel: "Strong Match",
    why: "New and expanding industrial units in your selected state qualify for capital and tax incentives under the state industrial policy.",
    eligibility: ["Industrial unit (manufacturing)", "Located within notified industrial area", "New Setup or Expansion"],
    benefits: ["Stamp duty exemption", "SGST reimbursement for 5–7 years", "Power tariff subsidy"],
    documents: ["Land Allotment Letter", "Project Report (DPR)", "Business Registration Certificate"],
    status: "Eligible",
    appliesTo: (p) => isIndustry(p) && p.projectType !== "Renewal",
  },
  {
    id: "startup-innovation",
    name: "Startup & Innovation Support Programme",
    matchLevel: "Possible Match",
    why: "Small, newly-established businesses may qualify if recognised under the state/national startup framework.",
    eligibility: ["Entity age under 10 years", "Innovative product/process element", "DPIIT recognition (optional)"],
    benefits: ["Seed funding support", "Tax holiday (subject to recognition)", "Fast-tracked approvals"],
    documents: ["Certificate of Incorporation", "Business Plan", "DPIIT Recognition (if available)"],
    status: "Not Applied",
    appliesTo: (p) => p.projectType === "New Setup" && p.size === "Small",
  },
  {
    id: "womens-retail-support",
    name: "Retail Trade Digitisation Support",
    matchLevel: "Possible Match",
    why: "Small retail shops adopting digital billing and inventory systems can claim a one-time digitisation grant.",
    eligibility: ["Registered retail shop", "Shop & Establishment Registration in place"],
    benefits: ["One-time digitisation grant up to ₹25,000", "GST e-invoicing onboarding support"],
    documents: ["Shop & Establishment Certificate", "GST Certificate"],
    status: "Not Applied",
    appliesTo: (p) => !isIndustry(p) && p.size === "Small",
  },
  {
    id: "cluster-development",
    name: "Industrial Cluster Development Scheme",
    matchLevel: "Possible Match",
    why: "Medium and large manufacturing units located in notified clusters can access shared infrastructure funding.",
    eligibility: ["Located in a notified industrial cluster", "Medium or Large business size"],
    benefits: ["Shared effluent treatment plant access", "Common testing facility access", "Infrastructure cost-sharing"],
    documents: ["Land Documents", "Cluster Membership Proof"],
    status: "Not Applied",
    appliesTo: (p) => isIndustry(p) && p.size !== "Small",
  },
];

export function getMatchedSchemes(profile: ProjectProfile): SchemeDef[] {
  return schemes.filter((s) => s.appliesTo(profile));
}
