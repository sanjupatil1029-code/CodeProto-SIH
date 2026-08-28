import { CheckCircle2, Clock3, AlertTriangle, XCircle } from "lucide-react";
import type { DocumentRecord } from "../types";
import { getAllApprovalDefs } from "../data/approvals";

const DOC_STATUS_META = {
  verified: { label: "Verified", className: "bg-success-light text-success", icon: CheckCircle2 },
  pending: { label: "Pending", className: "bg-warn-light text-warn", icon: Clock3 },
  expired: { label: "Expired", className: "bg-danger-light text-danger", icon: AlertTriangle },
  missing: { label: "Missing", className: "bg-slate-100 text-slate-soft", icon: XCircle },
};

export default function DocumentCard({ doc }: { doc: DocumentRecord }) {
  const meta = DOC_STATUS_META[doc.status];
  const Icon = meta.icon;
  const usedForNames = doc.usedFor
    .map((id) => getAllApprovalDefs().find((a) => a.id === id)?.name)
    .filter(Boolean);

  return (
    <div className="card p-5">
      <div className="flex items-start gap-3">
        {doc.photoUrl && (
          <img
            src={doc.photoUrl}
            alt={doc.name}
            className="h-14 w-14 flex-shrink-0 rounded-lg border border-navy/10 object-cover"
          />
        )}
        <div className="flex flex-1 items-start justify-between gap-3">
          <div>
            <h3 className="font-display text-sm font-bold text-ink">{doc.name}</h3>
            <p className="mt-0.5 text-xs text-slate-soft">
              {doc.uploadedOn ? `Uploaded: ${doc.uploadedOn}` : "Not yet uploaded"}
              {doc.expiry ? ` · Expires: ${doc.expiry}` : ""}
            </p>
          </div>
          <span className={`pill flex-shrink-0 ${meta.className}`}>
            <Icon size={12} /> {meta.label}
          </span>
        </div>
      </div>

      {usedForNames.length > 0 && (
        <div className="mt-3">
          <p className="text-xs font-semibold text-slate-soft">Used for:</p>
          <div className="mt-1.5 flex flex-wrap gap-1.5">
            {usedForNames.map((name) => (
              <span key={name} className="pill bg-lavender text-indigo">{name}</span>
            ))}
          </div>
        </div>
      )}

      {doc.flags.length > 0 && (
        <div className="mt-3 space-y-1.5">
          {doc.flags.map((flag) => (
            <p key={flag} className="flex items-center gap-1.5 text-xs font-medium text-warn">
              <AlertTriangle size={12} /> {flag}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
