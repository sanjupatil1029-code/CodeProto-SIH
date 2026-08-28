import { useNavigate } from "react-router-dom";
import { Award, CheckCircle2, FileText, Gift, ListChecks } from "lucide-react";
import AppShell from "../components/AppShell";
import { useApp } from "../context/AppContext";
import { getMatchedSchemes } from "../data/schemes";

const MATCH_STYLES: Record<string, string> = {
  "Strong Match": "bg-success-light text-success",
  "Possible Match": "bg-warn-light text-warn",
  "Not Eligible": "bg-slate-100 text-slate-soft",
};

export default function SchemeMatcher() {
  const { profile } = useApp();
  const navigate = useNavigate();

  if (!profile) {
    return (
      <AppShell>
        <div className="card p-10 text-center">
          <p className="text-sm text-slate-soft">Create a project profile to see matched government schemes.</p>
          <button onClick={() => navigate("/dashboard")} className="btn-primary mt-4">Go to Dashboard</button>
        </div>
      </AppShell>
    );
  }

  const matched = getMatchedSchemes(profile);

  return (
    <AppShell>
      <div className="flex items-center gap-2">
        <Award size={22} className="text-navy" />
        <h1 className="font-display text-3xl font-extrabold tracking-tight text-navy">Government Scheme Matcher</h1>
      </div>
      <p className="mt-1.5 max-w-2xl text-sm text-slate-soft">
        Matched using your industry, location, business size and project type. Sample/demo scheme data — verify current
        terms with the issuing department before applying.
      </p>

      <div className="mt-8 space-y-5">
        {matched.length === 0 ? (
          <div className="card p-10 text-center text-sm text-slate-soft">No schemes matched this profile yet.</div>
        ) : (
          matched.map((scheme) => (
            <div key={scheme.id} className="card p-6">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <h3 className="font-display text-lg font-bold text-ink">{scheme.name}</h3>
                <span className={`pill ${MATCH_STYLES[scheme.matchLevel]}`}>{scheme.matchLevel}</span>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-slate-soft">
                <span className="font-semibold text-ink">Why it matches: </span>{scheme.why}
              </p>

              <div className="mt-5 grid gap-5 sm:grid-cols-3">
                <div>
                  <h4 className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-slate-soft">
                    <ListChecks size={13} /> Eligibility
                  </h4>
                  <ul className="mt-2 space-y-1.5 text-sm text-ink">
                    {scheme.eligibility.map((e) => <li key={e}>• {e}</li>)}
                  </ul>
                </div>
                <div>
                  <h4 className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-slate-soft">
                    <Gift size={13} /> Benefits / Support
                  </h4>
                  <ul className="mt-2 space-y-1.5 text-sm text-ink">
                    {scheme.benefits.map((b) => <li key={b}>• {b}</li>)}
                  </ul>
                </div>
                <div>
                  <h4 className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-slate-soft">
                    <FileText size={13} /> Required Documents
                  </h4>
                  <ul className="mt-2 space-y-1.5 text-sm text-ink">
                    {scheme.documents.map((d) => <li key={d}>• {d}</li>)}
                  </ul>
                </div>
              </div>

              <div className="mt-5 flex items-center justify-between border-t border-navy/[0.06] pt-4">
                <span className="flex items-center gap-1.5 text-xs font-semibold text-slate-soft">
                  <CheckCircle2 size={13} /> Application status: {scheme.status}
                </span>
                <button className="btn-secondary !px-3 !py-1.5 text-xs">View Application Steps</button>
              </div>
            </div>
          ))
        )}
      </div>
    </AppShell>
  );
}
