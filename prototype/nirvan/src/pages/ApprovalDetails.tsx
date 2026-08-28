import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  CalendarClock, FileCheck, Landmark, Link2, RefreshCw, ScrollText, ShieldAlert,
  ClipboardCheck, Camera, CheckCircle2, AlertTriangle, Loader2, ChevronDown, FolderCheck,
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

  // Find the latest vault record for a given required document name (most recent upload wins).
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

  // Once every required document is verified (fresh upload or auto-fetched from the vault), tick the roadmap step.
  useEffect(() => {
    if (approval && allVerified && !runtime?.documentsReady) {
      markDocumentsReady(approval.id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

    // Simulated AI check — for now, any clear photo of a document is accepted.
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

  const handleMarkReady = () => {
    if (!allVerified) return;
    markDocumentsReady(approval.id);
  };

  const handleSubmit = () => {
    if (!allVerified) return;
    setApprovalStatus(approval.id, "submitted");
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
          <div className="mt-2"><StatusBadge status={status} size="md" /></div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={handleMarkReady}
            disabled={!allVerified}
            className="btn-secondary text-sm disabled:cursor-not-allowed disabled:opacity-40"
          >
            <FileCheck size={15} /> Mark as Ready
          </button>
          <button
            onClick={handleSubmit}
            disabled={!allVerified}
            className="btn-primary text-sm disabled:cursor-not-allowed disabled:opacity-40"
          >
            <ClipboardCheck size={15} /> Submit Application
          </button>
        </div>
      </div>
      {!allVerified && (
        <p className="mt-2 text-xs font-medium text-slate-soft">
          Upload and verify all required documents below to unlock Mark as Ready &amp; Submit.
        </p>
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
            <h2 className="flex items-center gap-2 font-display text-sm font-bold uppercase tracking-wide text-slate-soft">
              <ShieldAlert size={15} /> Applicability
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-ink">{approval.applicability}</p>
          </div>

          <div className="card p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="flex items-center gap-2 font-display text-sm font-bold uppercase tracking-wide text-slate-soft">
                <FileCheck size={15} /> Required Documents
              </h2>
              <div className="flex items-center gap-3">
                <span className="text-xs font-semibold text-slate-soft">
                  {verifiedCount} of {requiredDocs.length} verified
                </span>
                {requiredDocs.length > 0 && (
                  <button
                    onClick={() => setShowRemainingOnly((v) => !v)}
                    className="pill border border-navy/15 bg-white text-slate-soft hover:text-navy"
                  >
                    {showRemainingOnly ? "Show All" : "Show Remaining Only"}
                  </button>
                )}
              </div>
            </div>

            <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-mist">
              <div
                className="h-full rounded-full bg-gradient-to-r from-navy to-indigo transition-all"
                style={{ width: requiredDocs.length ? `${(verifiedCount / requiredDocs.length) * 100}%` : "0%" }}
              />
            </div>

            {visibleDocs.length === 0 ? (
              <p className="mt-4 text-sm text-slate-soft">All required documents are verified. 🎉</p>
            ) : (
              <ul className="mt-4 space-y-3">
                {visibleDocs.map((docName) => {
                  const st = docStatus(docName);
                  const vaultDoc = vaultDocFor(docName);
                  const row = rows[docName];
                  const isOpen = expandedDoc === docName;

                  return (
                    <li key={docName} className="rounded-lg border border-navy/[0.08] bg-mist/40 p-3.5">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center gap-2.5">
                          {st === "verified" && <CheckCircle2 size={16} className="flex-shrink-0 text-success" />}
                          {st === "flagged" && <AlertTriangle size={16} className="flex-shrink-0 text-warn" />}
                          {st === "missing" && <span className="h-1.5 w-1.5 flex-shrink-0 rounded-full bg-slate-300" />}
                          <span className="text-sm font-semibold text-ink">{docName}</span>
                          {st === "verified" && vaultDoc && (
                            <span className="pill bg-lavender text-[10px] text-indigo">
                              <FolderCheck size={10} /> From Document Vault
                            </span>
                          )}
                        </div>

                        {st !== "verified" && (
                          <button
                            onClick={() => (isOpen ? setExpandedDoc(null) : openUpload(docName))}
                            className="flex items-center gap-1 text-xs font-semibold text-navy hover:underline"
                          >
                            <Camera size={13} />
                            {st === "flagged" ? "Upload Again" : "Upload"}
                            <ChevronDown size={13} className={`transition-transform ${isOpen ? "rotate-180" : ""}`} />
                          </button>
                        )}
                      </div>

                      {st === "flagged" && vaultDoc?.flags.map((flag) => (
                        <p key={flag} className="mt-1.5 flex items-center gap-1.5 pl-6 text-xs font-medium text-warn">
                          <AlertTriangle size={12} /> {flag}
                        </p>
                      ))}

                      {isOpen && row && (
                        <div className="mt-3 space-y-3 rounded-lg bg-white p-3.5">
                          <div>
                            <label className="label-text">Photo of Document</label>
                            <input
                              ref={fileInputRef}
                              type="file"
                              accept="image/*"
                              capture="environment"
                              onChange={(e) => handlePhotoChange(docName, e)}
                              className="block w-full text-xs text-slate-soft file:mr-3 file:rounded-lg file:border-0 file:bg-navy file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-white hover:file:bg-navy-dark"
                            />
                            {row.photo && (
                              <img src={row.photo} alt={docName} className="mt-2 h-24 w-full rounded-lg border border-navy/10 object-cover" />
                            )}
                          </div>
                          <button
                            onClick={() => validateAndSave(docName)}
                            disabled={!row.photo || row.validating}
                            className="btn-primary w-full text-xs disabled:opacity-50"
                          >
                            {row.validating ? (
                              <><Loader2 size={13} className="animate-spin" /> AI is checking your document…</>
                            ) : (
                              <><CheckCircle2 size={13} /> Validate &amp; Save</>
                            )}
                          </button>
                        </div>
                      )}
                    </li>
                  );
                })}
              </ul>
            )}
          </div>

          {dependsOnNames.length > 0 && (
            <div className="card p-6">
              <h2 className="flex items-center gap-2 font-display text-sm font-bold uppercase tracking-wide text-slate-soft">
                <Link2 size={15} /> Dependencies
              </h2>
              <ul className="mt-3 space-y-2">
                {dependsOnNames.map((name) => (
                  <li key={name} className="flex items-center gap-2.5 rounded-lg bg-lavender/40 px-3.5 py-2.5 text-sm font-medium text-navy">
                    {name}
                  </li>
                ))}
              </ul>
            </div>
          )}
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
          <div className="card p-5">
            <h3 className="text-xs font-bold uppercase tracking-wide text-slate-soft">Inspection Required?</h3>
            <p className="mt-1.5 text-sm font-semibold text-ink">{approval.inspectionRequired ? "Yes" : "No"}</p>
          </div>
          <div className="card p-5">
            <h3 className="flex items-center gap-2 text-xs font-bold uppercase tracking-wide text-slate-soft">
              <RefreshCw size={14} /> Renewal Requirement
            </h3>
            <p className="mt-1.5 text-sm font-semibold text-ink">{approval.renewal}</p>
          </div>
          <div className="card p-5">
            <h3 className="text-xs font-bold uppercase tracking-wide text-slate-soft">Official Source</h3>
            <p className="mt-1.5 text-sm font-semibold text-ink">{approval.source}</p>
          </div>
          <div className="card p-5">
            <h3 className="text-xs font-bold uppercase tracking-wide text-slate-soft">Rule Version / Effective Date</h3>
            <p className="mt-1.5 text-sm font-semibold text-ink">{approval.ruleVersion} · {approval.effectiveDate}</p>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
