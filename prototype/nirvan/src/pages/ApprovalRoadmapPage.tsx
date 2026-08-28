import { useNavigate } from "react-router-dom";
import AppShell from "../components/AppShell";
import RoadmapFlowchart from "../components/RoadmapFlowchart";
import { useApp } from "../context/AppContext";
import { getRoadmapLevels } from "../data/approvals";

export default function ApprovalRoadmapPage() {
  const { profile, approvalRuntimes } = useApp();
  const navigate = useNavigate();

  if (!profile) {
    return (
      <AppShell>
        <div className="card p-10 text-center">
          <p className="text-sm text-slate-soft">Create a project profile first to generate your roadmap.</p>
          <button onClick={() => navigate("/dashboard")} className="btn-primary mt-4">
            Go to Dashboard
          </button>
        </div>
      </AppShell>
    );
  }

  const levels = getRoadmapLevels(profile);
  const total = levels.flat().length;
  const approved = levels.flat().filter((a) => approvalRuntimes[a.id]?.status === "approved").length;

  return (
    <AppShell>
      <h1 className="font-display text-3xl font-extrabold tracking-tight text-navy">Your Approval Roadmap</h1>
      <p className="mt-1.5 text-sm text-slate-soft">
        Your requirements, organised into a clear step-by-step journey.
      </p>

      <div className="mt-5 flex flex-wrap items-center gap-4">
        <div className="pill bg-white border border-navy/10 text-ink">
          {approved} of {total} approvals complete
        </div>
        <div className="flex items-center gap-4 text-xs font-semibold text-slate-soft">
          <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-success" /> Completed</span>
          <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-saffron" /> Current</span>
          <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-slate-300" /> Pending</span>
          <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-danger" /> Action Required</span>
        </div>
      </div>

      <div className="card mt-6 p-5 sm:p-6">
        <RoadmapFlowchart levels={levels} runtimes={approvalRuntimes} />
      </div>
      <p className="mt-3 text-xs text-slate-soft">
        Tap any step to see what's needed and view its details. A green tick means your documents for that step are verified.
      </p>
    </AppShell>
  );
}
