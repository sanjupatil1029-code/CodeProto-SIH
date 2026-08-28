import { useRef, useState } from "react";
import { AlertTriangle, Camera, CheckCircle2, FolderOpen, Loader2, Sparkles, UploadCloud } from "lucide-react";
import AppShell from "../components/AppShell";
import DocumentCard from "../components/DocumentCard";
import { useApp } from "../context/AppContext";
import { getAllApprovalDefs, getApplicableApprovals } from "../data/approvals";
import type { DocumentRecord } from "../types";

const COMMON_DOCS = [
  "PAN Card", "GST Certificate", "Aadhaar Card", "Fire Safety Layout", "Site Layout Plan",
  "Building Plan Approval", "Project Report (DPR)", "Water Test Report", "Employee List with Details",
];

export default function DocumentVault() {
  const { profile, documents, addDocument, markDocumentsReady } = useApp();
  const [tab, setTab] = useState<"vault" | "check">("vault");

  const docOptions = profile
    ? Array.from(new Set(getApplicableApprovals(profile).flatMap((a) => a.documents)))
    : COMMON_DOCS;

  // upload form
  const [docName, setDocName] = useState(docOptions[0]);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [validating, setValidating] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<"all" | "verified" | "pending" | "expired">("all");

  const filtered = documents.filter((d) => {
    if (filter !== "all" && d.status !== filter) return false;
    if (query && !d.name.toLowerCase().includes(query.toLowerCase())) return false;
    return true;
  });

  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => setPhotoPreview(reader.result as string);
    reader.readAsDataURL(file);
  };

  const runValidation = (e: React.FormEvent) => {
    e.preventDefault();
    if (!photoPreview) return;

    setValidating(true);
    // Simulated AI check — for now, any clear photo of a document is accepted.
    setTimeout(() => {
      const matchingApprovals = getAllApprovalDefs().filter((a) => a.documents.includes(docName));

      const doc: DocumentRecord = {
        id: `d-${Date.now()}`,
        name: docName,
        status: "verified",
        uploadedOn: "2026-08-28",
        expiry: null,
        usedFor: matchingApprovals.map((a) => a.id),
        fileNameOnRecord: profile?.companyName || "—",
        flags: [],
        photoUrl: photoPreview,
      };
      addDocument(doc);

      // Tick off this document on every matching roadmap step
      matchingApprovals.forEach((a) => markDocumentsReady(a.id));

      setValidating(false);
      setPhotoPreview(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }, 700);
  };

  const flaggedDocs = documents.filter((d) => d.flags.length > 0 || d.status !== "verified");
  const readiness = documents.length
    ? Math.round(((documents.length - flaggedDocs.length) / documents.length) * 100)
    : 0;

  return (
    <AppShell>
      <h1 className="font-display text-3xl font-extrabold tracking-tight text-navy">Document Vault</h1>
      <p className="mt-1.5 text-sm text-slate-soft">Upload a photo of your document once. Our AI checks it and reuses it across your applications.</p>

      <div className="mt-6 flex gap-2 border-b border-navy/[0.08]">
        <button
          onClick={() => setTab("vault")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold ${
            tab === "vault" ? "border-navy text-navy" : "border-transparent text-slate-soft hover:text-ink"
          }`}
        >
          <FolderOpen size={15} /> Document Vault
        </button>
        <button
          onClick={() => setTab("check")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold ${
            tab === "check" ? "border-navy text-navy" : "border-transparent text-slate-soft hover:text-ink"
          }`}
        >
          <Sparkles size={15} /> AI Document Check
        </button>
      </div>

      {tab === "vault" ? (
        <div className="mt-6 grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <div className="mb-4 flex flex-wrap items-center gap-3">
              <input
                className="input-field max-w-xs"
                placeholder="Search documents…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              {(["all", "verified", "pending", "expired"] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`pill border ${
                    filter === f ? "border-navy bg-navy text-white" : "border-navy/15 bg-white text-slate-soft"
                  }`}
                >
                  {f[0].toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>
            {filtered.length === 0 ? (
              <div className="card p-10 text-center text-sm text-slate-soft">No documents match this filter yet.</div>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2">
                {filtered.map((doc) => <DocumentCard key={doc.id} doc={doc} />)}
              </div>
            )}
          </div>

          <div className="card h-fit p-6">
            <h2 className="flex items-center gap-2 font-display text-sm font-bold text-ink">
              <Camera size={16} className="text-navy" /> Upload a Document Photo
            </h2>
            <p className="mt-1 text-xs text-slate-soft">Take a photo or choose a picture of your document. Simple as that.</p>

            <form onSubmit={runValidation} className="mt-4 space-y-4">
              <div>
                <label className="label-text">Document Type</label>
                <select className="input-field" value={docName} onChange={(e) => setDocName(e.target.value)}>
                  {docOptions.map((d) => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>

              <div>
                <label className="label-text">Photo of Document</label>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  capture="environment"
                  onChange={handlePhotoChange}
                  className="block w-full text-xs text-slate-soft file:mr-3 file:rounded-lg file:border-0 file:bg-navy file:px-3.5 file:py-2 file:text-sm file:font-semibold file:text-white hover:file:bg-navy-dark"
                />
                {photoPreview && (
                  <img src={photoPreview} alt="Document preview" className="mt-3 h-32 w-full rounded-lg border border-navy/10 object-cover" />
                )}
              </div>

              <button type="submit" disabled={!photoPreview || validating} className="btn-primary w-full text-sm disabled:opacity-50">
                {validating ? (
                  <><Loader2 size={15} className="animate-spin" /> AI is checking your document…</>
                ) : (
                  <><UploadCloud size={15} /> Upload &amp; Validate</>
                )}
              </button>
              {!photoPreview && <p className="text-center text-xs text-slate-soft">Add a photo above to enable upload.</p>}
            </form>
          </div>
        </div>
      ) : (
        <div className="mt-6 space-y-6">
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <h2 className="font-display text-base font-bold text-ink">Application Readiness Score</h2>
              <span className="font-display text-2xl font-extrabold text-navy">{readiness}%</span>
            </div>
            <div className="mt-3 h-2.5 w-full overflow-hidden rounded-full bg-mist">
              <div className="h-full rounded-full bg-gradient-to-r from-navy to-indigo" style={{ width: `${readiness}%` }} />
            </div>
            <p className="mt-3 text-xs text-slate-soft">
              AI assists with extraction and flagging only — it does not make statutory approval decisions. Final review always rests with the responsible department.
            </p>
          </div>

          <div>
            <h3 className="mb-3 font-display text-sm font-bold uppercase tracking-wide text-slate-soft">Document Checks</h3>
            {documents.length === 0 ? (
              <div className="card p-10 text-center text-sm text-slate-soft">Upload a document photo in the Vault tab to see AI checks here.</div>
            ) : (
              <div className="space-y-3">
                {documents.map((doc) => (
                  <div key={doc.id} className="card flex items-start gap-4 p-4">
                    {doc.photoUrl && (
                      <img src={doc.photoUrl} alt={doc.name} className="h-12 w-12 flex-shrink-0 rounded-lg border border-navy/10 object-cover" />
                    )}
                    <div>
                      <p className="font-semibold text-ink">{doc.name}</p>
                      <p className="text-xs text-slate-soft">Name read from photo: "{doc.fileNameOnRecord}"</p>
                      {doc.flags.length === 0 ? (
                        <p className="mt-1.5 flex items-center gap-1.5 text-sm font-medium text-success">
                          <CheckCircle2 size={14} /> Correct document type · required information present
                        </p>
                      ) : (
                        doc.flags.map((flag) => (
                          <p key={flag} className="mt-1.5 flex items-center gap-1.5 text-sm font-medium text-warn">
                            <AlertTriangle size={14} /> {flag}
                          </p>
                        ))
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </AppShell>
  );
}
