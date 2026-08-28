import { useNavigate } from "react-router-dom";
import { ChevronRight, RotateCcw } from "lucide-react";
import AppShell from "../components/AppShell";
import StatusBadge from "../components/StatusBadge";
import Timeline from "../components/Timeline";
import { useApp } from "../context/AppContext";
import { getApplicableApprovals } from "../data/approvals";
import type { ApprovalStatus } from "../types";

const NEXT_STATUS: Partial<Record<ApprovalStatus, ApprovalStatus>> = {
  not_started: "documents_required",
  documents_required: "ready",
  ready: "submitted",
  submitted: "under_review",
  under_review: "approved",
  query_raised: "under_review",
  inspection_scheduled: "approved",
};

export default function ApplicationTracker() {
  const { profile, approvalRuntimes, setApprovalStatus } = useApp();
  const navigate = useNavigate();

  if (!profile) {
    return (
      <AppShell>
        <div className="card p-10 text-center">
          <p className="text-sm text-slate-soft">Create a project profile to see your applications.</p>
          <button onClick={() => navigate("/dashboard")} className="btn-primary mt-4">Go to Dashboard</button>
        </div>
      </AppShell>
    );
  }

  const applicable = getApplicableApprovals(profile);

  return (
    <AppShell>
      <h1 className="font-display text-3xl font-extrabold tracking-tight text-navy">Application &amp; Workflow Tracker</h1>
      <p className="mt-1.5 text-sm text-slate-soft">Live status across every approval in your roadmap.</p>

      <div className="mt-8 space-y-5">
        {applicable.map((approval) => {
          const runtime = approvalRuntimes[approval.id];
          const status = runtime?.status || "not_started";
          const next = NEXT_STATUS[status];
          return (
            <div key={approval.id} className="card p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <button
                    onClick={() => navigate(`/roadmap/${approval.id}`)}
                    className="font-display text-base font-bold text-ink hover:text-navy hover:underline"
                  >
                    {approval.name}
                  </button>
                  <p className="text-xs text-slate-soft">{approval.authority}</p>
                </div>
                <StatusBadge status={status} size="md" />
              </div>

              <div className="mt-5">
                <Timeline status={status} />
              </div>

              <div className="mt-4 flex items-center justify-between">
                <p className="text-xs text-slate-soft">
                  SLA: {approval.slaDays} days {runtime?.progressDays ? `· ${runtime.progressDays} days elapsed` : ""}
                </p>
                <div className="flex gap-2">
                  {status !== "approved" && status !== "not_started" && (
                    <button
                      onClick={() => setApprovalStatus(approval.id, "not_started")}
                      className="flex items-center gap-1 text-xs font-semibold text-slate-soft hover:text-danger"
                    >
                      <RotateCcw size={12} /> Reset
                    </button>
                  )}
                  {next && (
                    <button
                      onClick={() => setApprovalStatus(approval.id, next)}
                      className="btn-secondary !px-3 !py-1.5 text-xs"
                    >
                      Advance <ChevronRight size={13} />
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </AppShell>
  );
}
