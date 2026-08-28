import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ExternalLink,
  ChevronRight,
  RotateCcw,
  CheckCircle2,
  Clock,
  Globe,
  Layers,
  Sparkles,
  ShieldCheck,
  Send,
  Building2,
} from "lucide-react";
import AppShell from "../components/AppShell";
import StatusBadge from "../components/StatusBadge";
import Timeline from "../components/Timeline";
import { useApp } from "../context/AppContext";
import { getApplicableApprovals } from "../data/approvals";

interface ExtendedWorkflowRecord {
  id: string;
  approvalId: string;
  name: string;
  authority: string;
  status: "not_started" | "ready" | "ready_for_submission" | "official_portal_handoff" | "submitted" | "in_progress" | "approved";
  externalSystem: string;
  externalRef: string | null;
  integrationMode: "PUBLIC_API" | "AUTHORISED_API" | "PORTAL_HANDOFF" | "MOCK";
  officialPortalUrl: string;
  slaDays: number;
  stageHistory: { status: string; timestamp: string; notes: string }[];
}

export default function ApplicationTracker() {
  const { profile } = useApp();
  const navigate = useNavigate();
  const [tab, setTab] = useState<"tracker" | "adapters">("tracker");

  const [workflows, setWorkflows] = useState<ExtendedWorkflowRecord[]>([
    {
      id: "wf-101",
      approvalId: "gst-reg",
      name: "GST Registration Certificate",
      authority: "Department of Revenue, Ministry of Finance",
      status: "approved",
      externalSystem: "GST Portal (CBIC)",
      externalRef: "AA2708261997Z1",
      integrationMode: "PUBLIC_API",
      officialPortalUrl: "https://services.gst.gov.in",
      slaDays: 7,
      stageHistory: [
        { status: "NOT_STARTED", timestamp: "2026-08-28 10:00", notes: "Roadmap entry created." },
        { status: "SUBMITTED", timestamp: "2026-08-28 10:15", notes: "Application submitted via GST G2B API. ARN: AA2708261997Z1" },
        { status: "APPROVED", timestamp: "2026-08-28 11:30", notes: "GSTIN generated and verified." },
      ],
    },
    {
      id: "wf-102",
      approvalId: "fssai-lic",
      name: "FSSAI Food Business License",
      authority: "Food Safety and Standards Authority of India (FSSAI)",
      status: "official_portal_handoff",
      externalSystem: "FoSCoS (FSSAI)",
      externalRef: "FSSAI61798674",
      integrationMode: "PORTAL_HANDOFF",
      officialPortalUrl: "https://foscos.fssai.gov.in",
      slaDays: 30,
      stageHistory: [
        { status: "NOT_STARTED", timestamp: "2026-08-28 10:00", notes: "Roadmap entry created." },
        { status: "READY_FOR_SUBMISSION", timestamp: "2026-08-28 14:00", notes: "Documents verified by Vault Engine." },
        { status: "OFFICIAL_PORTAL_HANDOFF", timestamp: "2026-08-28 14:30", notes: "Prefilled handoff package generated for FoSCoS portal." },
      ],
    },
    {
      id: "wf-103",
      approvalId: "fire-noc",
      name: "Fire Safety NOC",
      authority: "Maharashtra Fire Services Bureau / MAITRI",
      status: "in_progress",
      externalSystem: "MAITRI Single Window (Maharashtra Govt)",
      externalRef: "MAI-MH-2026-88412",
      integrationMode: "PORTAL_HANDOFF",
      officialPortalUrl: "https://maitri.mahaonline.gov.in",
      slaDays: 15,
      stageHistory: [
        { status: "NOT_STARTED", timestamp: "2026-08-28 10:00", notes: "Roadmap entry created." },
        { status: "SUBMITTED", timestamp: "2026-08-28 12:00", notes: "Routed via MAITRI Maharashtra Single Window portal." },
      ],
    },
  ]);

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

  const handleHandoffTrigger = (wfId: string, portalUrl: string) => {
    setWorkflows(
      workflows.map((w) =>
        w.id === wfId
          ? {
              ...w,
              status: "official_portal_handoff",
              stageHistory: [
                ...w.stageHistory,
                {
                  status: "OFFICIAL_PORTAL_HANDOFF",
                  timestamp: new Date().toISOString().replace("T", " ").substring(0, 16),
                  notes: `Initiated Official Portal Handoff to ${portalUrl}`,
                },
              ],
            }
          : w
      )
    );
    window.open(portalUrl, "_blank");
  };

  return (
    <AppShell>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-extrabold tracking-tight text-navy">Application &amp; Workflow Tracker</h1>
          <p className="mt-1 text-sm text-slate-soft">
            Internal Workflow Engine &amp; Government Adapter Integration Layer (Modules 8 &amp; 9).
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-xl bg-navy/5 p-2.5 text-xs font-semibold text-navy">
          <Layers size={16} className="text-indigo-600" /> Adapter Decoupled Architecture
        </div>
      </div>

      <div className="mt-6 flex gap-2 border-b border-navy/[0.08]">
        <button
          onClick={() => setTab("tracker")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold ${
            tab === "tracker" ? "border-navy text-navy" : "border-transparent text-slate-soft hover:text-ink"
          }`}
        >
          <Send size={15} /> Active Workflow Tracker
        </button>
        <button
          onClick={() => setTab("adapters")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold ${
            tab === "adapters" ? "border-navy text-navy" : "border-transparent text-slate-soft hover:text-ink"
          }`}
        >
          <Globe size={15} /> Government Adapters Registry
        </button>
      </div>

      {tab === "tracker" && (
        <div className="mt-6 space-y-6">
          {workflows.map((wf) => (
            <div key={wf.id} className="card p-6 space-y-5">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => navigate(`/roadmap/${wf.approvalId}`)}
                      className="font-display text-lg font-bold text-ink hover:text-navy hover:underline"
                    >
                      {wf.name}
                    </button>
                    <span className="rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-bold text-indigo-800 border border-indigo-200">
                      {wf.integrationMode}
                    </span>
                  </div>
                  <p className="text-xs text-slate-soft mt-1">{wf.authority}</p>
                </div>

                <div className="flex flex-col items-end gap-1">
                  <span className="text-xs font-bold text-navy">Target System: {wf.externalSystem}</span>
                  {wf.externalRef && (
                    <span className="rounded bg-slate-100 px-2 py-0.5 text-xs font-mono text-slate-700">
                      Ref: {wf.externalRef}
                    </span>
                  )}
                </div>
              </div>

              {/* Official Portal Handoff Alert Card */}
              {wf.status === "official_portal_handoff" && (
                <div className="rounded-xl bg-amber-50 p-4 border border-amber-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
                  <div>
                    <span className="font-bold text-amber-900 flex items-center gap-1.5 text-sm">
                      <Sparkles size={16} className="text-amber-600" /> Official Portal Handoff Ready
                    </span>
                    <p className="mt-0.5 text-amber-800">
                      NIRVAAN has prepared your prefilled application payload for {wf.externalSystem}.
                    </p>
                  </div>

                  <button
                    onClick={() => handleHandoffTrigger(wf.id, wf.officialPortalUrl)}
                    className="btn-primary !bg-amber-600 hover:!bg-amber-700 !py-2 !px-4 text-xs flex items-center gap-1.5 whitespace-nowrap"
                  >
                    Open {wf.externalSystem} <ExternalLink size={14} />
                  </button>
                </div>
              )}

              <div className="pt-2">
                <Timeline status={wf.status === "official_portal_handoff" ? "submitted" : (wf.status as any)} />
              </div>

              {/* Stage History Log */}
              <div className="rounded-lg bg-slate-50 p-3 text-xs text-slate-700 border border-slate-200 space-y-1">
                <span className="text-slate-400 font-semibold block mb-1">Stage Tracking History:</span>
                {wf.stageHistory.map((h, i) => (
                  <div key={i} className="flex items-center gap-2 font-mono">
                    <span className="text-slate-400">[{h.timestamp}]</span>
                    <span className="font-bold text-navy">{h.status}:</span>
                    <span className="text-slate-600 truncate">{h.notes}</span>
                  </div>
                ))}
              </div>

              <div className="flex items-center justify-between border-t border-slate-100 pt-3 text-xs">
                <span className="text-slate-soft">SLA Deadline: {wf.slaDays} Days</span>
                <div className="flex gap-2">
                  <a
                    href={wf.officialPortalUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="btn-secondary !px-3 !py-1.5 text-xs flex items-center gap-1"
                  >
                    <Globe size={13} /> Official Portal
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === "adapters" && (
        <div className="mt-6 space-y-4">
          <h2 className="font-display text-base font-bold text-ink">Registered Government Integration Adapters (Module 9)</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            <div className="card p-5 space-y-2">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-ink flex items-center gap-2">
                  <Building2 size={18} className="text-navy" /> FoSCoS (FSSAI) Adapter
                </h3>
                <span className="rounded bg-amber-100 px-2 py-0.5 text-xs font-bold text-amber-800">PORTAL_HANDOFF</span>
              </div>
              <p className="text-xs text-slate-soft">Food Safety Authority G2B portal handoff redirect integration.</p>
              <p className="text-xs font-mono text-navy">URL: https://foscos.fssai.gov.in</p>
            </div>

            <div className="card p-5 space-y-2">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-ink flex items-center gap-2">
                  <Building2 size={18} className="text-navy" /> GST System Adapter
                </h3>
                <span className="rounded bg-blue-100 px-2 py-0.5 text-xs font-bold text-blue-800">PUBLIC_API</span>
              </div>
              <p className="text-xs text-slate-soft">Goods &amp; Services Tax G2B API submission and ARN tracking.</p>
              <p className="text-xs font-mono text-navy">URL: https://services.gst.gov.in</p>
            </div>

            <div className="card p-5 space-y-2">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-ink flex items-center gap-2">
                  <Building2 size={18} className="text-navy" /> MAITRI Maharashtra Adapter
                </h3>
                <span className="rounded bg-amber-100 px-2 py-0.5 text-xs font-bold text-amber-800">PORTAL_HANDOFF</span>
              </div>
              <p className="text-xs text-slate-soft">Maharashtra Single Window portal routing Fire NOC &amp; Pollution Consent.</p>
              <p className="text-xs font-mono text-navy">URL: https://maitri.mahaonline.gov.in</p>
            </div>

            <div className="card p-5 space-y-2">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-ink flex items-center gap-2">
                  <Building2 size={18} className="text-navy" /> NSWS National Adapter
                </h3>
                <span className="rounded bg-emerald-100 px-2 py-0.5 text-xs font-bold text-emerald-800">AUTHORISED_API</span>
              </div>
              <p className="text-xs text-slate-soft">National Single Window System central government API integration.</p>
              <p className="text-xs font-mono text-navy">URL: https://nsws.gov.in</p>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
