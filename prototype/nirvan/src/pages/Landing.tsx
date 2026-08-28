import { useNavigate } from "react-router-dom";
import { ArrowRight, Building2, FileCheck2, ListChecks, Route as RouteIcon, ShieldCheck } from "lucide-react";
import PublicNavbar from "../components/PublicNavbar";

const JOURNEY = [
  { label: "Business Profile", icon: Building2, desc: "Tell us what you're building & where" },
  { label: "Approval Discovery", icon: ListChecks, desc: "See exactly what's required, and why" },
  { label: "Document Readiness", icon: FileCheck2, desc: "Upload once, reuse everywhere" },
  { label: "Compliance Tracking", icon: ShieldCheck, desc: "Track approvals, renewals & alerts" },
];

export default function Landing() {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen bg-mist">
      <PublicNavbar />

      <section className="relative overflow-hidden bg-hero-grid [background-size:22px_22px]">
        <div className="absolute inset-x-0 top-0 h-[520px] bg-gradient-to-b from-lavender/60 via-mist to-mist" />
        <div className="relative mx-auto max-w-5xl px-6 pb-20 pt-20 text-center">
         
          <h1 className="font-display text-5xl font-extrabold tracking-tight text-navy sm:text-6xl">
            NIRVAAN
          </h1>
          <p className="mt-3 text-xl font-semibold text-indigo">
            Industrial Approval &amp; Compliance Orchestrator
          </p>
          <p className="mx-auto mt-6 max-w-2xl text-base leading-relaxed text-slate-soft">
            Your guided digital journey for discovering approvals ,  documents and
            navigating industrial compliance — one connected platform instead of a dozen scattered portals.
          </p>
          <div className="mt-9 flex items-center justify-center gap-3">
            <button onClick={() => navigate("/signup")} className="btn-accent">
              Get Started <ArrowRight size={16} />
            </button>
            <button onClick={() => navigate("/about")} className="btn-secondary">
              Explore Platform
            </button>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-24">
        <div className="mb-10 flex items-center gap-2">
          <RouteIcon size={18} className="text-saffron" />
          <h2 className="font-display text-sm font-bold uppercase tracking-wider text-slate-soft">
            Your guided journey
          </h2>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {JOURNEY.map((step, i) => (
            <div key={step.label} className="card relative p-6">
              <span className="font-mono text-xs font-semibold text-indigo/50">
                {String(i + 1).padStart(2, "0")}
              </span>
              <div className="mt-3 flex h-11 w-11 items-center justify-center rounded-xl bg-navy/[0.06] text-navy">
                <step.icon size={20} />
              </div>
              <h3 className="mt-4 font-display text-base font-bold text-ink">{step.label}</h3>
              <p className="mt-1 text-sm text-slate-soft">{step.desc}</p>
              {i < JOURNEY.length - 1 && (
                <ArrowRight
                  size={18}
                  className="absolute -right-3 top-1/2 hidden -translate-y-1/2 text-navy/20 lg:block"
                />
              )}
            </div>
          ))}
        </div>
      </section>

      <section className="border-t border-navy/[0.06] bg-white py-16">
        <div className="mx-auto grid max-w-6xl gap-8 px-6 sm:grid-cols-3">
          <div>
            <h3 className="font-display text-lg font-bold text-navy">What is NIRVAAN?</h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-soft">
              A unified platform for industrial approvals and compliance — replacing scattered
              portals, repeated document uploads, and guesswork with one explainable roadmap.
            </p>
          </div>
          <div>
            <h3 className="font-display text-lg font-bold text-navy">Who uses it?</h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-soft">
              Entrepreneurs setting up shops and industries, and government department
              officers reviewing, inspecting and approving applications.
            </p>
          </div>
          <div>
            <h3 className="font-display text-lg font-bold text-navy">What makes it intelligent?</h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-soft">
              Personalised approval discovery, document reuse, dependency-aware workflows,
              proactive alerts and government scheme matching — grounded in rules, not guesses.
            </p>
          </div>
        </div>
      </section>

      <footer className="border-t border-navy/[0.06] py-8 text-center text-xs text-slate-soft">
        NIRVAAN —  All data shown is simulated for demonstration.
      </footer>
    </div>
  );
}
