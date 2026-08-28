import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  CalendarClock, FileCheck, Landmark, Link2, RefreshCw, ScrollText, ShieldAlert,
  ClipboardCheck, Camera, CheckCircle2, AlertTriangle, Loader2, ChevronDown, FolderCheck,
  ShieldCheck, AlertOctagon, HelpCircle, MessageSquarePlus, UserCheck, Flame, Send
} from "lucide-react";
import AppShell from "../components/AppShell";
import StatusBadge from "../components/StatusBadge";
import { useApp } from "../context/AppContext";
import { findApprovalById } from "../data/approvals";
import type { DocumentRecord } from "../types";

type RowState = { photo: string | null; validating: boolean };

export default function ApprovalDetails() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { profile, documents, addDocument, approvalRuntimes, markDocumentsReady, setApprovalStatus } = useApp();

  const approval = id ? findApprovalById(id) : undefined;

  const [expandedDoc, setExpandedDoc] = useState<string | null>(null);
  const [rows, setRows] = useState<Record<string, RowState>>({});
  const [showRemainingOnly, setShowRemainingOnly] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Module 12 Inspection State
  const [inspection, setInspection] = useState({
    scheduled: true,
    title: "On-Site Statutory Safety & Hygiene Inspection",
    officer: "Officer K. Sharma (State Inspector)",
    scheduledDate: "2026-09-02 11:00 AM",
    status: "SCHEDULED",
    location: "MIDC Bhosari, Industrial Area, Pune",
    findings: "Dual fire hydrants and 500L water capacity verified on site.",
    checklist: [
      { check: "Fire Extinguishers ISI Certified", passed: true },
      { check: "Emergency Exits Unobstructed", passed: true },
      { check: "Effluent Water Discharge Pre-treatment", passed: true },
    ]
  });

  // Module 13 Grievance State
  const [showGrievanceModal, setShowGrievanceModal] = useState(false);
  const [grievances, setGrievances] = useState([
    {
      id: "grv-901",
      title: "SLA Resolution Delay past 30-Day Window",
      category: "SLA_BREACH",
      priority: "HIGH",
      status: "ESCALATED",
      escalationLevel: 2,
      escalationTitle: "Level 2: Regional Senior Inspector",
      deadline: "2026-08-30 (Extended)",
      assignedOfficer: "Regional Nodal Officer M. Patil",
      history: [
        { level: 1, action: "Grievance Ticket Created & Level 1 Nodal Assigned", date: "2026-08-20" },
        { level: 2, action: "Automatic Multi-Tier Escalation: SLA Resolution Deadline Exceeded", date: "2026-08-28" }
      ]
    }
  ]);

  const [newGrvTitle, setNewGrvTitle] = useState("");
  const [newGrvDesc, setNewGrvDesc] = useState("");
  const [newGrvPriority, setNewGrvPriority] = useState<"LOW" | "MEDIUM" | "HIGH" | "CRITICAL">("HIGH");

  const vaultDocFor = (docName: string): DocumentRecord | undefined => documents.find((d) => d.name === docName);

  const docStatus = (docName: string): "verified" | "flagged" | "missing" => {
    const v = vaultDocFor(docName);
    if (!v) return "missing";
    return v.status === "verified" ? "verified" : "flagged";
  };

  const runtime = approval ? approvalRuntimes[approval.id] : undefined;
  const requiredDocs = approval?.documents || [];
  const verifiedCount = requiredDocs.filter((d) => docStatus(d) === "verified").length;
  const allVerified = requiredDocs.length === 0 || verifiedCount === requiredDocs.length;

  useEffect(() => {
    if (approval && allVerified && !runtime?.documentsReady) {
      markDocumentsReady(approval.id);
    }
  }, [allVerified, approval?.id, runtime?.documentsReady]);

  if (!approval) {
    return (
      <AppShell>
        <p className="text-sm text-slate-soft">Approval not found.</p>
      </AppShell>
    );
  }

  const status = runtime?.status || "not_started";
  const dependsOnNames = approval.dependsOn
    .map((depId) => findApprovalById(depId)?.name)
    .filter(Boolean);

  const openUpload = (docName: string) => {
    setRows((prev) => ({
      ...prev,
      [docName]: prev[docName] || { photo: null, validating: false },
    }));
    setExpandedDoc(docName);
  };

  const handlePhotoChange = (docName: string, e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      setRows((prev) => ({ ...prev, [docName]: { ...prev[docName], photo: reader.result as string } }));
    };
    reader.readAsDataURL(file);
  };

  const updateRow = (docName: string, patch: Partial<RowState>) => {
    setRows((prev) => ({ ...prev, [docName]: { ...prev[docName], ...patch } }));
  };

  const validateAndSave = (docName: string) => {
    const row = rows[docName];
    if (!row?.photo) return;
    updateRow(docName, { validating: true });

    setTimeout(() => {
      const doc: DocumentRecord = {
        id: `d-${Date.now()}`,
        name: docName,
        status: "verified",
        uploadedOn: "2026-08-28",
        expiry: null,
        usedFor: [approval.id],
        fileNameOnRecord: profile?.companyName || "—",
        flags: [],
        photoUrl: row.photo,
      };
      addDocument(doc);
      updateRow(docName, { validating: false, photo: null });
      setExpandedDoc(null);
    }, 700);
  };

  const handleCreateGrievance = () => {
    if (!newGrvTitle.trim()) return;
    const newGrv = {
      id: `grv-${Date.now()}`,
      title: newGrvTitle,
      category: "SLA_BREACH",
      priority: newGrvPriority,
      status: "OPEN",
      escalationLevel: 1,
      escalationTitle: "Level 1: Nodal Officer Assigned",
      deadline: new Date(Date.now() + 48 * 3600 * 1000).toISOString().substring(0, 10),
      assignedOfficer: "Assigned Nodal Officer",
      history: [
        { level: 1, action: "Grievance Ticket Created", date: new Date().toISOString().substring(0, 10) }
      ]
    };
    setGrievances([newGrv, ...grievances]);
    setNewGrvTitle("");
    setNewGrvDesc("");
    setShowGrievanceModal(false);
  };

  const visibleDocs = showRemainingOnly ? requiredDocs.filter((d) => docStatus(d) !== "verified") : requiredDocs;

  return (
    <AppShell>
      <button onClick={() => navigate("/roadmap")} className="text-sm font-semibold text-slate-soft hover:text-navy">
        ← Back to Roadmap
      </button>

      <div className="mt-3 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-extrabold tracking-tight text-navy sm:text-3xl">{approval.name}</h1>
          <div className="mt-2 flex items-center gap-3">
            <StatusBadge status={status} size="md" />
            <button
              onClick={() => setShowGrievanceModal(true)}
              className="pill bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100 flex items-center gap-1.5 text-xs font-bold"
            >
              <MessageSquarePlus size={13} /> Raise Grievance / SLA Ticket
            </button>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => markDocumentsReady(approval.id)}
            disabled={!allVerified}
            className="btn-secondary text-sm disabled:cursor-not-allowed disabled:opacity-40"
          >
            <FileCheck size={15} /> Mark as Ready
          </button>
          <button
            onClick={() => setApprovalStatus(approval.id, "submitted")}
            disabled={!allVerified}
            className="btn-primary text-sm disabled:cursor-not-allowed disabled:opacity-40"
          >
            <ClipboardCheck size={15} /> Submit Application
          </button>
        </div>
      </div>

      {/* Module 12: Inspection Management Card */}
      {approval.inspectionRequired && (
        <div className="mt-6 card p-6 border-l-4 border-l-amber-500 bg-amber-50/30 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <span className="text-xs font-bold text-amber-900 uppercase tracking-wide flex items-center gap-1.5">
                <Flame size={16} className="text-amber-600" /> Module 12: Statutory Inspection Scheduled
              </span>
              <h2 className="text-base font-extrabold text-navy mt-1">{inspection.title}</h2>
              <p className="text-xs text-slate-soft mt-0.5">Location: {inspection.location}</p>
            </div>
            <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-900 border border-amber-300">
              {inspection.status}
            </span>
          </div>

          <div className="grid sm:grid-cols-2 gap-3 text-xs bg-white p-3.5 rounded-xl border border-amber-200">
            <div><span className="text-slate-soft">Assigned Inspector:</span> <strong className="text-navy">{inspection.officer}</strong></div>
            <div><span className="text-slate-soft">Scheduled Date:</span> <strong className="text-navy">{inspection.scheduledDate}</strong></div>
          </div>

          <div className="space-y-2">
            <span className="text-xs font-bold text-navy block">Inspector Checklist &amp; Statutory Requirements:</span>
            <div className="grid sm:grid-cols-3 gap-2">
              {inspection.checklist.map((chk, idx) => (
                <div key={idx} className="flex items-center gap-2 text-xs bg-white p-2.5 rounded-lg border border-slate-200">
                  <CheckCircle2 size={15} className="text-emerald-600 flex-shrink-0" />
                  <span className="text-slate-700 font-medium">{chk.check}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Module 13: Active Grievances & Escalations */}
      {grievances.length > 0 && (
        <div className="mt-6 card p-6 border-l-4 border-l-rose-500 bg-rose-50/20 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-base font-extrabold text-navy flex items-center gap-2">
              <AlertOctagon size={18} className="text-rose-600" /> Module 13: Active Grievances &amp; Multi-Tier Escalations
            </h2>
            <span className="text-xs font-bold text-rose-800 bg-rose-100 px-2.5 py-0.5 rounded-full border border-rose-200">
              {grievances.length} Active Ticket(s)
            </span>
          </div>

          {grievances.map((g) => (
            <div key={g.id} className="bg-white p-4 rounded-xl border border-rose-200 space-y-3 text-xs">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-bold text-navy text-sm">{g.title}</span>
                <span className="rounded bg-rose-100 px-2 py-0.5 text-xs font-bold text-rose-900">
                  ESCALATION LEVEL {g.escalationLevel}: {g.escalationTitle}
                </span>
              </div>
              <div className="flex flex-wrap justify-between text-slate-soft border-t border-slate-100 pt-2">
                <span>Assigned: <strong className="text-navy">{g.assignedOfficer}</strong></span>
                <span>Resolution SLA Deadline: <strong className="text-rose-600">{g.deadline}</strong></span>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-8 grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <div className="card p-6">
            <h2 className="flex items-center gap-2 font-display text-sm font-bold uppercase tracking-wide text-slate-soft">
              <ScrollText size={15} /> Why is this required?
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-ink">{approval.why}</p>
          </div>

          <div className="card p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="flex items-center gap-2 font-display text-sm font-bold uppercase tracking-wide text-slate-soft">
                <FileCheck size={15} /> Required Documents
              </h2>
              <span className="text-xs font-semibold text-slate-soft">
                {verifiedCount} of {requiredDocs.length} verified
              </span>
            </div>

            <ul className="mt-4 space-y-3">
              {visibleDocs.map((docName) => {
                const st = docStatus(docName);
                return (
                  <li key={docName} className="rounded-lg border border-navy/[0.08] bg-mist/40 p-3.5 flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      {st === "verified" ? <CheckCircle2 size={16} className="text-success" /> : <AlertTriangle size={16} className="text-warn" />}
                      <span className="text-sm font-semibold text-ink">{docName}</span>
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        </div>

        <div className="space-y-5">
          <div className="card p-5">
            <h3 className="flex items-center gap-2 text-xs font-bold uppercase tracking-wide text-slate-soft">
              <Landmark size={14} /> Responsible Authority
            </h3>
            <p className="mt-1.5 text-sm font-semibold text-ink">{approval.authority}</p>
          </div>
          <div className="card p-5">
            <h3 className="flex items-center gap-2 text-xs font-bold uppercase tracking-wide text-slate-soft">
              <CalendarClock size={14} /> SLA / Timeline
            </h3>
            <p className="mt-1.5 text-sm font-semibold text-ink">{approval.slaDays} days</p>
          </div>
        </div>
      </div>

      {/* Module 13: Raise Grievance Modal */}
      {showGrievanceModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-navy/40 backdrop-blur-sm p-4">
          <div className="card w-full max-w-lg p-6 space-y-4 bg-white shadow-xl">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="font-display text-lg font-bold text-navy flex items-center gap-2">
                <MessageSquarePlus size={20} className="text-rose-600" /> Raise Grievance / SLA Ticket (Module 13)
              </h3>
              <button onClick={() => setShowGrievanceModal(false)} className="text-slate-soft hover:text-ink font-bold">✕</button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="label-text">Grievance Title</label>
                <input
                  type="text"
                  placeholder="e.g. SLA Resolution Delay past 30 days"
                  value={newGrvTitle}
                  onChange={(e) => setNewGrvTitle(e.target.value)}
                  className="input-field mt-1"
                />
              </div>

              <div>
                <label className="label-text">Priority Level</label>
                <select
                  value={newGrvPriority}
                  onChange={(e) => setNewGrvPriority(e.target.value as any)}
                  className="input-field mt-1"
                >
                  <option value="CRITICAL">CRITICAL (24 Hours SLA Resolution)</option>
                  <option value="HIGH">HIGH (48 Hours SLA Resolution)</option>
                  <option value="MEDIUM">MEDIUM (7 Days SLA Resolution)</option>
                  <option value="LOW">LOW (14 Days SLA Resolution)</option>
                </select>
              </div>

              <div>
                <label className="label-text">Detailed Description</label>
                <textarea
                  rows={3}
                  placeholder="Provide details regarding statutory delay or officer query..."
                  value={newGrvDesc}
                  onChange={(e) => setNewGrvDesc(e.target.value)}
                  className="input-field mt-1"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t">
              <button onClick={() => setShowGrievanceModal(false)} className="btn-secondary text-xs">Cancel</button>
              <button onClick={handleCreateGrievance} className="btn-primary !bg-rose-600 hover:!bg-rose-700 text-xs flex items-center gap-1">
                <Send size={13} /> Submit Grievance Ticket
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
