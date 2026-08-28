import PublicNavbar from "../components/PublicNavbar";
import { Layers, Network, ShieldCheck, Sparkles } from "lucide-react";

const PILLARS = [
  {
    icon: Layers,
    title: "Approval Intelligence",
    desc: "A version-controlled rule engine — not a chatbot guessing — decides which approvals apply to your business profile, with the reasoning shown alongside every result.",
  },
  {
    icon: Network,
    title: "Document Intelligence",
    desc: "Upload a document once and reuse it across every application that needs it. AI-assisted checks flag missing fields, expiry and name mismatches before you submit.",
  },
  {
    icon: Sparkles,
    title: "Workflow Orchestration",
    desc: "Approvals that can run in parallel are shown side-by-side; approvals with real dependencies are sequenced automatically.",
  },
  {
    icon: ShieldCheck,
    title: "Compliance Monitoring",
    desc: "SLA timers, inspection scheduling, smart alerts and renewal tracking keep both entrepreneurs and departments ahead of deadlines.",
  },
];

export default function About() {
  return (
    <div className="min-h-screen bg-mist">
      <PublicNavbar />
      <section className="mx-auto max-w-4xl px-6 py-16">
        <span className="pill bg-white text-indigo border border-indigo/15 shadow-card">About NIRVAAN</span>
        <h1 className="mt-4 font-display text-4xl font-extrabold tracking-tight text-navy">
          From project profile to approval readiness — one guided, verified, trackable journey.
        </h1>
        <p className="mt-4 max-w-2xl text-sm leading-relaxed text-slate-soft">
          NIRVAAN acts as a coordination layer between entrepreneurs and the departments they need
          approvals from — reducing incomplete applications, repeated document verification,
          approval delays, and missed renewals. This build is a hackathon prototype: statutory
          decisions always sit with authorised officials, and AI is used only to explain, extract
          and assist — never to decide.
        </p>

        <div className="mt-10 grid gap-5 sm:grid-cols-2">
          {PILLARS.map((p) => (
            <div key={p.title} className="card p-6">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo/10 text-indigo">
                <p.icon size={20} />
              </div>
              <h3 className="mt-4 font-display text-base font-bold text-ink">{p.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-slate-soft">{p.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
