import type { DocumentRecord, ProjectProfile, ApprovalRuntime } from "../types";
import { getApplicableApprovals } from "./approvals";

export interface DocumentExpiryAlertItem {
  id: string;
  docName: string;
  docType: string;
  expiryDate: string;
  daysRemaining: number;
  status: "CRITICAL_EXPIRED" | "RENEWAL_DUE" | "UP_TO_DATE";
  usedForApprovals: string[];
}

export interface ScheduledInspectionAlertItem {
  id: string;
  approvalId: string;
  approvalName: string;
  authority: string;
  inspectionDate: string;
  inspectorName: string;
  inspectionType: "PHYSICAL_SITE_VISIT" | "DIGITAL_CALIBRATION_AUDIT";
  siteChecklist: string[];
  status: "SCHEDULED" | "CONFIRMED";
}

export interface EscalationAlertItem {
  id: string;
  approvalId: string;
  approvalName: string;
  authority: string;
  slaDays: number;
  elapsedDays: number;
  escalationLevel: number;
  escalationTicketId: string;
  assignedOfficer: string;
  status: "ESCALATED_LEVEL_1" | "ESCALATED_LEVEL_2" | "SLA_BREACHED";
}

export function generateDocumentExpiryAlerts(documents: DocumentRecord[], profile: ProjectProfile | null): DocumentExpiryAlertItem[] {
  const alerts: DocumentExpiryAlertItem[] = [];

  // 1. Evaluate uploaded documents from Document Vault
  documents.forEach((d) => {
    if (d.expiry) {
      const expDate = new Date(d.expiry);
      const today = new Date();
      const diffTime = expDate.getTime() - today.getTime();
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

      let status: "CRITICAL_EXPIRED" | "RENEWAL_DUE" | "UP_TO_DATE" = "UP_TO_DATE";
      if (diffDays <= 15) status = "CRITICAL_EXPIRED";
      else if (diffDays <= 45) status = "RENEWAL_DUE";

      alerts.push({
        id: `exp-${d.id}`,
        docName: d.name,
        docType: d.name.toUpperCase().replace(/\s+/g, "_"),
        expiryDate: d.expiry,
        daysRemaining: diffDays,
        status,
        usedForApprovals: d.usedFor || ["biz-reg"],
      });
    }
  });

  // 2. If no uploaded document with expiry exists, provide sector-accurate defaults
  if (alerts.length === 0) {
    const isJewellery = profile?.businessTypeId === "jewelry";
    if (isJewellery) {
      alerts.push(
        {
          id: "exp-demo-1",
          docName: "Rent / Lease Agreement (Shop Premises)",
          docType: "RENT_AGREEMENT",
          expiryDate: "2026-09-15",
          daysRemaining: 17,
          status: "RENEWAL_DUE",
          usedForApprovals: ["Shop & Establishment", "Trade Licence"],
        },
        {
          id: "exp-demo-2",
          docName: "Legal Metrology Stamping Certificate",
          docType: "WEIGHTS_MEASURES_CERT",
          expiryDate: "2026-09-05",
          daysRemaining: 7,
          status: "CRITICAL_EXPIRED",
          usedForApprovals: ["Legal Metrology Licence"],
        }
      );
    } else {
      alerts.push(
        {
          id: "exp-demo-3",
          docName: "Fire Safety NOC Certificate",
          docType: "FIRE_SAFETY_NOC",
          expiryDate: "2026-09-02",
          daysRemaining: 4,
          status: "CRITICAL_EXPIRED",
          usedForApprovals: ["Fire NOC", "Factory Licence"],
        },
        {
          id: "exp-demo-4",
          docName: "Water Quality Test Report",
          docType: "WATER_TEST_REPORT",
          expiryDate: "2026-09-12",
          daysRemaining: 14,
          status: "RENEWAL_DUE",
          usedForApprovals: ["FSSAI License"],
        }
      );
    }
  }

  return alerts;
}

export function generateScheduledInspections(
  profile: ProjectProfile | null,
  _runtimes?: Record<string, ApprovalRuntime>
): ScheduledInspectionAlertItem[] {
  if (!profile) return [];
  const applicable = getApplicableApprovals(profile);
  const inspections: ScheduledInspectionAlertItem[] = [];

  const inspectable = applicable.filter((a) => a.inspectionRequired);

  const stateStr = profile.state || "State";
  const distStr = profile.district || profile.cityTaluk || "District";

  inspectable.forEach((a, idx) => {
    const isJewellery = profile.businessTypeId === "jewelry";

    let inspDate = "2026-09-05";
    if (idx === 1) inspDate = "2026-09-08";
    if (idx === 2) inspDate = "2026-09-14";

    let inspector = `Senior Licensing Inspector (${distStr} Circle)`;
    if (a.id.includes("hallmarking") || a.id.includes("jewelry-9")) {
      inspector = `BIS Assaying & Hallmarking Audit Team (${stateStr})`;
    } else if (a.id.includes("fire")) {
      inspector = `Divisional Fire Officer (${distStr} Fire Station)`;
    } else if (a.id.includes("metrology") || a.id.includes("jewelry-10")) {
      inspector = `Legal Metrology Inspector of Weights & Measures`;
    }

    const checklist = isJewellery
      ? ["Calibrated Electronic Scale", "BIS HUID Laser Marking Machine", "Shop Board Photo", "Rent Agreement"]
      : ["Fire Extinguishers List", "Effluent Treatment Layout", "Building Sanction Plan", "Safety Signages"];

    inspections.push({
      id: `insp-${a.id}`,
      approvalId: a.id,
      approvalName: a.name,
      authority: a.authority,
      inspectionDate: inspDate,
      inspectorName: inspector,
      inspectionType: isJewellery ? "DIGITAL_CALIBRATION_AUDIT" : "PHYSICAL_SITE_VISIT",
      siteChecklist: checklist,
      status: idx === 0 ? "CONFIRMED" : "SCHEDULED",
    });
  });

  return inspections;
}

export function generateEscalations(
  profile: ProjectProfile | null,
  runtimes: Record<string, ApprovalRuntime>
): EscalationAlertItem[] {
  if (!profile) return [];
  const applicable = getApplicableApprovals(profile);
  const escalations: EscalationAlertItem[] = [];

  applicable.forEach((a) => {
    const runtime = runtimes[a.id];
    const elapsed = runtime?.progressDays || (a.id.includes("trade") || a.id.includes("fire") ? a.slaDays + 8 : 0);

    if (elapsed > a.slaDays) {
      escalations.push({
        id: `esc-${a.id}`,
        approvalId: a.id,
        approvalName: a.name,
        authority: a.authority,
        slaDays: a.slaDays,
        elapsedDays: elapsed,
        escalationLevel: 2,
        escalationTicketId: `ESC-2026-${Math.floor(1000 + Math.random() * 9000)}`,
        assignedOfficer: `Joint Director of Statutory Grievance Redressal (${profile.state})`,
        status: "SLA_BREACHED",
      });
    }
  });

  // Provide fallback default escalation if no runtime has breached yet
  if (escalations.length === 0) {
    const isJewellery = profile.businessTypeId === "jewelry";
    if (isJewellery) {
      escalations.push({
        id: "esc-demo-jewel",
        approvalId: "trade-license",
        approvalName: "Municipal Trade Licence Clearance",
        authority: `${profile.district || "Municipal"} Corporation Trade Dept`,
        slaDays: 15,
        elapsedDays: 22,
        escalationLevel: 2,
        escalationTicketId: "ESC-2026-8812",
        assignedOfficer: `Assistant Municipal Commissioner (${profile.district || "Pune"})`,
        status: "SLA_BREACHED",
      });
    } else {
      escalations.push({
        id: "esc-demo-ind",
        approvalId: "fire-noc",
        approvalName: "Fire Safety NOC Clearance",
        authority: `${profile.state || "State"} Fire & Emergency Services`,
        slaDays: 15,
        elapsedDays: 24,
        escalationLevel: 2,
        escalationTicketId: "ESC-2026-9041",
        assignedOfficer: "Senior Regional Fire Inspector",
        status: "SLA_BREACHED",
      });
    }
  }

  return escalations;
}
