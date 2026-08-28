import { CheckCircle2, Clock3, AlertTriangle, CircleDashed, FileWarning, Search, RefreshCcw } from "lucide-react";
import type { ApprovalStatus } from "../types";

const STATUS_META: Record<
  ApprovalStatus,
  { label: string; className: string; icon: React.ComponentType<{ size?: number; className?: string }> }
> = {
  not_started: { label: "Not Started", className: "bg-slate-100 text-slate-soft", icon: CircleDashed },
  documents_required: { label: "Documents Required", className: "bg-warn-light text-warn", icon: FileWarning },
  ready: { label: "Ready", className: "bg-lavender text-indigo", icon: CheckCircle2 },
  submitted: { label: "Submitted", className: "bg-lavender text-indigo", icon: Clock3 },
  under_review: { label: "Under Review", className: "bg-saffron/15 text-saffron-dark", icon: Search },
  query_raised: { label: "Query Raised", className: "bg-danger-light text-danger", icon: AlertTriangle },
  inspection_scheduled: { label: "Inspection Scheduled", className: "bg-warn-light text-warn", icon: Clock3 },
  approved: { label: "Approved", className: "bg-success-light text-success", icon: CheckCircle2 },
  renewal_due: { label: "Renewal Due", className: "bg-warn-light text-warn", icon: RefreshCcw },
};

export default function StatusBadge({ status, size = "sm" }: { status: ApprovalStatus; size?: "sm" | "md" }) {
  const meta = STATUS_META[status];
  const Icon = meta.icon;
  return (
    <span className={`pill ${meta.className} ${size === "md" ? "text-sm px-3 py-1" : ""}`}>
      <Icon size={size === "md" ? 14 : 12} />
      {meta.label}
    </span>
  );
}

export { STATUS_META };
