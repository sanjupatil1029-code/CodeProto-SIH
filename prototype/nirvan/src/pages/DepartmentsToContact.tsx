import { useNavigate } from "react-router-dom";
import { Landmark, ArrowRight } from "lucide-react";
import AppShell from "../components/AppShell";
import { useApp } from "../context/AppContext";
import { getApplicableApprovals } from "../data/approvals";
import type { ApprovalDef } from "../types";

export default function DepartmentsToContact() {
  const { profile } = useApp();
  const navigate = useNavigate();

  if (!profile) {
    return (
      <AppShell>
        <div className="card p-10 text-center">
          <p className="text-sm text-slate-soft">Create a project profile first to see which departments you'll need to contact.</p>
          <button onClick={() => navigate("/dashboard")} className="btn-primary mt-4">
            Go to Dashboard
          </button>
        </div>
      </AppShell>
    );
  }

  const applicable = getApplicableApprovals(profile);

  // Group approvals by their responsible department (authority)
  const groups = new Map<string, ApprovalDef[]>();
  applicable.forEach((a) => {
    const list = groups.get(a.authority) || [];
    list.push(a);
    groups.set(a.authority, list);
  });

  return (
    <AppShell>
      <div className="flex items-center gap-2">
        <Landmark size={22} className="text-navy" />
        <h1 className="font-display text-3xl font-extrabold tracking-tight text-navy">Departments to Contact</h1>
      </div>
      <p className="mt-1.5 text-sm text-slate-soft">
        Based on your project, here are the government departments you'll need to reach out to and why.
      </p>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {Array.from(groups.entries()).map(([authority, items]) => (
          <div key={authority} className="card p-5">
            <div className="flex items-start gap-3">
              <span className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-lavender text-indigo">
                <Landmark size={18} />
              </span>
              <div className="min-w-0">
                <h2 className="font-display text-sm font-bold leading-snug text-ink">{authority}</h2>
                <p className="mt-0.5 text-xs text-slate-soft">
                  {items.length} approval{items.length > 1 ? "s" : ""} handled here
                </p>
              </div>
            </div>

            <ul className="mt-4 space-y-2.5">
              {items.map((a) => (
                <li key={a.id} className="rounded-lg bg-mist px-3.5 py-2.5">
                  <button
                    onClick={() => navigate(`/roadmap/${a.id}`)}
                    className="text-left text-sm font-semibold text-ink hover:text-navy"
                  >
                    {a.name}
                  </button>
                  <p className="mt-0.5 text-xs text-slate-soft">{a.applicability}</p>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="mt-6 flex items-center gap-2 text-xs text-slate-soft">
        <ArrowRight size={13} />
        Tap any approval above to see full details and required documents.
      </div>
    </AppShell>
  );
}
