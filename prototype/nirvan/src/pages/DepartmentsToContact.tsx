import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Landmark, ArrowRight, Building, Search, Sparkles, Clock } from "lucide-react";
import AppShell from "../components/AppShell";
import { useApp } from "../context/AppContext";
import { getApplicableApprovals } from "../data/approvals";
import type { ApprovalDef } from "../types";

export default function DepartmentsToContact() {
  const { profile, approvalRuntimes } = useApp();
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState("");

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

  // Helper to localize department names based on entrepreneur state & district
  const getLocalizedAuthorityName = (authority: string): string => {
    const stateStr = profile.state || "State";
    const distStr = profile.district || profile.cityTaluk || "Local";

    if (authority.toLowerCase().includes("municipal corporation")) {
      return `${distStr} Municipal Corporation / Local Civic Authority`;
    }
    if (authority.toLowerCase().includes("state labour")) {
      return `Department of Labour, Govt. of ${stateStr} (${distStr} Circle)`;
    }
    if (authority.toLowerCase().includes("pollution control")) {
      return `${stateStr} Pollution Control Board (Regional Office, ${distStr})`;
    }
    if (authority.toLowerCase().includes("fire")) {
      return `${stateStr} Fire & Emergency Services Department`;
    }
    if (authority.toLowerCase().includes("legal metrology")) {
      return `Department of Legal Metrology, Govt. of ${stateStr}`;
    }
    if (authority.toLowerCase().includes("bureau of indian standards") || authority.includes("BIS")) {
      return `Bureau of Indian Standards (BIS ${stateStr} Regional Hub)`;
    }
    if (authority.toLowerCase().includes("drugs control")) {
      return `State Drugs Control Department (${stateStr})`;
    }
    if (authority.toLowerCase().includes("industries department")) {
      return `Industries Department, Govt. of ${stateStr}`;
    }
    return authority;
  };

  const filteredGroups = Array.from(groups.entries()).filter(([authority, items]) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    const locAuth = getLocalizedAuthorityName(authority).toLowerCase();
    return (
      authority.toLowerCase().includes(term) ||
      locAuth.includes(term) ||
      items.some((i) => i.name.toLowerCase().includes(term) || i.why.toLowerCase().includes(term))
    );
  });

  return (
    <AppShell>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Landmark size={24} className="text-navy" />
            <h1 className="font-display text-3xl font-extrabold tracking-tight text-navy">Departments to Contact</h1>
          </div>
          <p className="mt-1 text-sm text-slate-soft">
            Tailored list of statutory government bodies &amp; authorities for <strong>{profile.companyName}</strong>.
          </p>
        </div>

        <div className="flex items-center gap-2 rounded-xl bg-navy/5 p-2.5 text-xs font-semibold text-navy">
          <Building size={16} className="text-indigo-600" /> {groups.size} Statutory Authorities Identified
        </div>
      </div>

      {/* Entrepreneur Project Summary Banner */}
      <div className="mt-6 card p-5 border-l-4 border-l-navy bg-gradient-to-r from-indigo-50/50 to-white flex flex-wrap items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wide text-indigo-900 flex items-center gap-1.5">
            <Sparkles size={15} className="text-indigo-600" /> Active Enterprise Profile
          </span>
          <p className="font-display text-lg font-bold text-navy mt-0.5">
            {profile.companyName} <span className="text-slate-soft text-sm font-normal">({profile.businessTypeId.toUpperCase()})</span>
          </p>
          <p className="text-xs text-slate-soft mt-0.5">
            Location: <strong>{profile.cityTaluk || profile.district}, {profile.state}</strong> · Employees: {profile.employees} · Scale: {profile.size}
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <div className="rounded-lg bg-white p-2.5 border border-slate-200 text-center">
            <span className="text-slate-soft block">Required Approvals</span>
            <span className="font-bold text-navy text-sm">{applicable.length}</span>
          </div>
          <div className="rounded-lg bg-white p-2.5 border border-slate-200 text-center">
            <span className="text-slate-soft block">Department Count</span>
            <span className="font-bold text-emerald-700 text-sm">{groups.size}</span>
          </div>
        </div>
      </div>

      {/* Search Input */}
      <div className="mt-6 flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            className="input-field pl-9"
            placeholder="Search department, authority name, or approval..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Departments Grid */}
      <div className="mt-6 grid gap-5 sm:grid-cols-2">
        {filteredGroups.map(([authority, items]) => {
          const localizedName = getLocalizedAuthorityName(authority);
          return (
            <div key={authority} className="card p-5 space-y-4 flex flex-col justify-between hover:shadow-md transition">
              <div>
                <div className="flex items-start gap-3">
                  <span className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-navy/10 text-navy font-bold">
                    <Landmark size={20} />
                  </span>
                  <div className="min-w-0 flex-1">
                    <h2 className="font-display text-base font-bold leading-snug text-navy">{localizedName}</h2>
                    <p className="text-xs text-slate-soft font-mono mt-0.5">
                      Statutory Authority: {authority}
                    </p>
                    <div className="mt-1.5 flex items-center gap-2">
                      <span className="rounded-full bg-indigo-50 px-2.5 py-0.5 text-[11px] font-bold text-indigo-800 border border-indigo-200">
                        {items.length} Approval{items.length > 1 ? "s" : ""} Handled Here
                      </span>
                    </div>
                  </div>
                </div>

                <ul className="mt-4 space-y-2.5">
                  {items.map((a) => {
                    const runtime = approvalRuntimes[a.id];
                    const statusStr = runtime?.status || "not_started";
                    const isApproved = statusStr === "approved";
                    const isReview = statusStr === "under_review" || statusStr === "ready";

                    return (
                      <li key={a.id} className="rounded-lg bg-slate-50 p-3.5 border border-slate-100 space-y-1.5">
                        <div className="flex items-center justify-between gap-2">
                          <button
                            onClick={() => navigate(`/roadmap/${a.id}`)}
                            className="text-left text-sm font-bold text-navy hover:underline flex items-center gap-1.5"
                          >
                            {a.name}
                          </button>
                          <span
                            className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase ${
                              isApproved
                                ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                                : isReview
                                ? "bg-blue-100 text-blue-800 border border-blue-200"
                                : "bg-slate-200 text-slate-700"
                            }`}
                          >
                            {statusStr.replace("_", " ")}
                          </span>
                        </div>

                        <p className="text-xs text-slate-600 leading-relaxed">{a.why}</p>

                        <div className="flex items-center justify-between text-[11px] text-slate-soft pt-1 border-t border-slate-200/60">
                          <span className="flex items-center gap-1 font-mono">
                            <Clock size={12} /> SLA Window: {a.slaDays} Days
                          </span>
                          <span className="font-medium text-navy hover:underline cursor-pointer" onClick={() => navigate(`/roadmap/${a.id}`)}>
                            View Documents &amp; Portal →
                          </span>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-soft">
                <span>Jurisdiction: {profile.state}</span>
                <span className="font-semibold text-navy">Single Window Gateway Enabled</span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-6 flex items-center gap-2 text-xs text-slate-soft">
        <ArrowRight size={13} />
        Tap any approval above to view required document checklists, statutory SLA windows, and official portal handoff URLs.
      </div>
    </AppShell>
  );
}

