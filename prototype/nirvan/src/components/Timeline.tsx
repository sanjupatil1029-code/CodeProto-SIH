import { Check } from "lucide-react";
import type { ApprovalStatus } from "../types";

const STEPS: { key: ApprovalStatus; label: string }[] = [
  { key: "documents_required", label: "Documents Ready" },
  { key: "submitted", label: "Submitted" },
  { key: "under_review", label: "Under Review" },
  { key: "inspection_scheduled", label: "Inspection" },
  { key: "approved", label: "Approval" },
];

const ORDER: ApprovalStatus[] = [
  "not_started",
  "documents_required",
  "ready",
  "submitted",
  "under_review",
  "query_raised",
  "inspection_scheduled",
  "approved",
  "renewal_due",
];

export default function Timeline({ status }: { status: ApprovalStatus }) {
  const currentIdx = ORDER.indexOf(status === "ready" ? "documents_required" : status === "query_raised" ? "under_review" : status);

  return (
    <div className="flex items-center">
      {STEPS.map((step, i) => {
        const stepIdx = ORDER.indexOf(step.key);
        const done = currentIdx > stepIdx || status === "approved";
        const current = ORDER[currentIdx] === step.key || (status === "query_raised" && step.key === "under_review") || (status === "ready" && step.key === "documents_required");
        return (
          <div key={step.key} className="flex flex-1 items-center last:flex-none">
            <div className="flex flex-col items-center gap-1.5">
              <div
                className={`flex h-7 w-7 items-center justify-center rounded-full border-2 text-xs font-bold ${
                  done
                    ? "border-success bg-success text-white"
                    : current
                    ? "border-saffron bg-saffron/10 text-saffron-dark"
                    : "border-navy/15 bg-white text-slate-soft"
                }`}
              >
                {done ? <Check size={13} /> : i + 1}
              </div>
              <span className={`w-20 text-center text-[11px] font-semibold ${done || current ? "text-ink" : "text-slate-soft"}`}>
                {step.label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div className={`mx-1 h-0.5 flex-1 ${done ? "bg-success" : "bg-navy/10"}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
