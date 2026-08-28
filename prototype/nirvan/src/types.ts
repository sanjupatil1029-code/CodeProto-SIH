export type BusinessCategory = "shop" | "industry";

export interface BusinessTypeDef {
  id: string;
  category: BusinessCategory;
  name: string;
  description: string;
  icon: string; // lucide icon name
}

export type BusinessSize = "Small" | "Medium" | "Large";
export type ProjectType = "New Setup" | "Expansion" | "Renewal";

export interface ProjectProfile {
  id?: string;
  companyName: string;
  businessTypeId: string;
  sector?: string;
  state: string;
  district: string;
  cityTaluk: string;
  city?: string;
  location?: string;
  size: BusinessSize;
  projectType: ProjectType;
  employees: number;
  investmentAmount?: number;
  expectedTurnover?: number;
  premisesType?: string;
  activity: string;
}

export type ApprovalStatus =
  | "not_started"
  | "documents_required"
  | "ready"
  | "submitted"
  | "under_review"
  | "query_raised"
  | "inspection_scheduled"
  | "approved"
  | "renewal_due";

export interface ApprovalDef {
  id: string;
  name: string;
  why: string;
  applicability: string;
  documents: string[];
  authority: string;
  dependsOn: string[]; // ids of approvals this depends on
  inspectionRequired: boolean;
  slaDays: number;
  renewal: string;
  source: string;
  ruleVersion: string;
  effectiveDate: string;
  appliesTo: (p: ProjectProfile) => boolean;
}

export interface ApprovalRuntime {
  approvalId: string;
  status: ApprovalStatus;
  progressDays: number;
  documentsReady: boolean;
}

export type DocStatus = "verified" | "pending" | "expired" | "missing";

export interface DocumentRecord {
  id: string;
  name: string;
  status: DocStatus;
  uploadedOn: string | null;
  expiry: string | null;
  usedFor: string[]; // approval ids
  fileNameOnRecord: string; // simulated extracted "name on document"
  flags: string[];
  photoUrl?: string | null; // preview of the uploaded photo, if any
}

export type AlertSeverity = "critical" | "high" | "medium";

export interface AlertRecord {
  id: string;
  severity: AlertSeverity;
  title: string;
  message: string;
  date: string;
  read: boolean;
  actionRequired: boolean;
  approvalId?: string;
}

export interface SchemeDef {
  id: string;
  name: string;
  matchLevel: "Strong Match" | "Possible Match" | "Not Eligible";
  why: string;
  eligibility: string[];
  benefits: string[];
  documents: string[];
  status: "Not Applied" | "Eligible" | "Applied";
  appliesTo: (p: ProjectProfile) => boolean;
}

