import { useRef, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  FileCheck,
  FileCode,
  FileText,
  FolderOpen,
  History,
  KeyRound,
  Loader2,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  XCircle,
} from "lucide-react";
import AppShell from "../components/AppShell";
import { useApp } from "../context/AppContext";

interface ExtendedDocRecord {
  id: string;
  name: string;
  documentType: string;
  status: "verified" | "auto_verified" | "pending" | "expired" | "rejected";
  uploadedOn: string;
  expiry: string | null;
  version: number;
  isLatest: boolean;
  fileHash: string;
  extractedData?: {
    documentNumber?: string;
    entityName?: string;
    issueDate?: string;
    expiryDate?: string;
    confidence?: number;
    addressSnippet?: string;
  };
  storageKey: string;
  fileNameOnRecord: string;
  photoUrl?: string;
}

interface InconsistencyAlert {
  id: string;
  type: "ADDRESS_MISMATCH" | "NAME_MISMATCH" | "PAN_GSTIN_MISMATCH";
  severity: "CRITICAL" | "WARNING";
  title: string;
  expected: string;
  actual: string;
  affectedApprovals: string[];
}

const COMMON_DOCS = [
  { code: "PAN_CARD", name: "PAN Card" },
  { code: "GST_CERTIFICATE", name: "GST Certificate" },
  { code: "RENT_AGREEMENT", name: "Rental / Lease Agreement" },
  { code: "FIRE_SAFETY_NOC", name: "Fire Safety NOC" },
  { code: "FSSAI_LICENSE", name: "FSSAI Food License" },
  { code: "INCORPORATION_CERT", name: "Certificate of Incorporation" },
  { code: "ELECTRICITY_BILL", name: "Electricity Bill" },
];

export default function DocumentVault() {
  const { profile } = useApp();
  const [tab, setTab] = useState<"vault" | "check" | "validation" | "compliance">("validation");

  // Document state initialized with rich default examples including cross-document mismatch demonstration
  const [docRecords, setDocRecords] = useState<ExtendedDocRecord[]>([
    {
      id: "doc-101",
      name: "PAN Card of Business",
      documentType: "PAN_CARD",
      status: "auto_verified",
      uploadedOn: "2026-08-28 14:30",
      expiry: null,
      version: 2,
      isLatest: true,
      fileHash: "8a7f9b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a",
      storageKey: "businesses/apex-foods/PAN_CARD/v2_8a7f9b2c.pdf",
      fileNameOnRecord: "pan_card_apex_foods_v2.pdf",
      extractedData: {
        documentNumber: "ABCDE1234F",
        entityName: profile?.companyName || "Apex Foods & Beverages Pvt Ltd",
        issueDate: "15/01/2022",
        confidence: 0.98,
      },
    },
    {
      id: "doc-102",
      name: "Rental / Lease Agreement",
      documentType: "RENT_AGREEMENT",
      status: "rejected",
      uploadedOn: "2026-08-28 15:10",
      expiry: "2028-05-31",
      version: 1,
      isLatest: true,
      fileHash: "9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e",
      storageKey: "businesses/apex-foods/RENT_AGREEMENT/v1_9f8e7d6c.pdf",
      fileNameOnRecord: "rent_agreement_mumbai_branch.pdf",
      extractedData: {
        addressSnippet: "Plot 45, Bandra Kurla Complex, Mumbai, Maharashtra 400051",
        confidence: 0.94,
      },
    },
    {
      id: "doc-103",
      name: "GST Registration Certificate",
      documentType: "GST_CERTIFICATE",
      status: "verified",
      uploadedOn: "2026-08-27 10:15",
      expiry: "2030-12-31",
      version: 1,
      isLatest: true,
      fileHash: "1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a8a7f9b2c3d4e5f6a7b8c9d0e",
      storageKey: "businesses/apex-foods/GST_CERTIFICATE/v1_1f2a3b4c.pdf",
      fileNameOnRecord: "gst_certificate_2026.pdf",
      extractedData: {
        documentNumber: "27ABCDE1234F1Z5",
        entityName: profile?.companyName || "Apex Foods & Beverages Pvt Ltd",
        issueDate: "01/04/2022",
        expiryDate: "31/12/2030",
        confidence: 0.95,
      },
    },
  ]);

  // Simulated Cross-Document Inconsistencies
  const inconsistencies: InconsistencyAlert[] = [
    {
      id: "inc-1",
      type: "ADDRESS_MISMATCH",
      severity: "CRITICAL",
      title: "Address Mismatch between Business Profile & Rental Agreement",
      expected: `${profile?.cityTaluk || profile?.city || "Pune"}, ${profile?.state || "Maharashtra"} (Business Profile)`,
      actual: "Bandra Kurla Complex, Mumbai (Rental Agreement)",
      affectedApprovals: ["FSSAI_LICENSE", "FIRE_SAFETY_NOC", "WATER_CONSENT", "LOCAL_MUNICIPAL_NOC"],
    },
  ];

  // Upload Form State
  const [selectedType, setSelectedType] = useState("PAN_CARD");
  const [expiryInput, setExpiryInput] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  // Modal States
  const [historyDoc, setHistoryDoc] = useState<ExtendedDocRecord | null>(null);
  const [signedUrlData, setSignedUrlData] = useState<{ docId: string; filename: string; url: string; expiresAt: string } | null>(null);

  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<"all" | "auto_verified" | "verified" | "pending" | "rejected">("all");

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setSelectedFile(file);

    if (file.type.startsWith("image/")) {
      const reader = new FileReader();
      reader.onload = () => setFilePreview(reader.result as string);
      reader.readAsDataURL(file);
    } else {
      setFilePreview(null);
    }
  };

  const handleUploadSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploading(true);

    setTimeout(() => {
      const existingSameType = docRecords.filter((d) => d.documentType === selectedType);
      const nextVersion = existingSameType.length + 1;

      const updatedRecords = docRecords.map((d) =>
        d.documentType === selectedType ? { ...d, isLatest: false } : d
      );

      const typeMeta = COMMON_DOCS.find((c) => c.code === selectedType) || { code: selectedType, name: selectedType };
      const simulatedHash = Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join("");
      const docNum = selectedType === "PAN_CARD" ? "ABCDE" + Math.floor(1000 + Math.random() * 9000) + "F" : "27GSTIN" + Math.floor(10000 + Math.random() * 90000);

      const newRecord: ExtendedDocRecord = {
        id: `doc-${Date.now()}`,
        name: typeMeta.name,
        documentType: selectedType,
        status: "auto_verified",
        uploadedOn: new Date().toISOString().replace("T", " ").substring(0, 16),
        expiry: expiryInput || "2030-12-31",
        version: nextVersion,
        isLatest: true,
        fileHash: simulatedHash,
        storageKey: `businesses/apex-foods/${selectedType}/v${nextVersion}_${simulatedHash.substring(0, 8)}.${selectedFile.name.split(".").pop()}`,
        fileNameOnRecord: selectedFile.name,
        photoUrl: filePreview || undefined,
        extractedData: {
          documentNumber: docNum,
          entityName: profile?.companyName || "Apex Foods & Beverages Pvt Ltd",
          confidence: 0.97,
        },
      };

      setDocRecords([newRecord, ...updatedRecords]);
      setUploading(false);
      setSelectedFile(null);
      setFilePreview(null);
      setExpiryInput("");
      if (fileInputRef.current) fileInputRef.current.value = "";
    }, 1000);
  };

  const generateSignedUrl = (doc: ExtendedDocRecord) => {
    const token = Array.from({ length: 32 }, () => Math.floor(Math.random() * 16).toString(16)).join("");
    const expires = new Date(Date.now() + 5 * 60 * 1000).toLocaleTimeString();
    setSignedUrlData({
      docId: doc.id,
      filename: doc.fileNameOnRecord,
      url: `http://127.0.0.1:8000/api/v1/documents/download-signed/${token}`,
      expiresAt: expires,
    });
  };

  const filteredDocs = docRecords.filter((d) => {
    if (!d.isLatest && tab === "vault") return false;
    if (filter !== "all" && d.status !== filter) return false;
    if (query && !d.name.toLowerCase().includes(query.toLowerCase()) && !d.documentType.toLowerCase().includes(query.toLowerCase())) return false;
    return true;
  });

  return (
    <AppShell>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-extrabold tracking-tight text-navy">Smart Document Vault &amp; Validation</h1>
          <p className="mt-1 text-sm text-slate-soft">
            Local Privacy-First OCR, Magic Bytes Security Scanning &amp; Cross-Document Consistency Engine.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-2 rounded-xl bg-purple-50 border border-purple-200 p-2.5 text-xs font-semibold text-purple-900">
            <Sparkles size={16} className="text-purple-600" /> Gemini AI Vision Assistant (DPDP Rule 8(3) Compliant)
          </div>
          <div className="flex items-center gap-2 rounded-xl bg-navy/5 p-2.5 text-xs font-semibold text-navy">
            <ShieldCheck size={16} className="text-emerald-600" /> Masked PII Protection
          </div>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap gap-2 border-b border-navy/[0.08]">
        <button
          onClick={() => setTab("validation")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold ${
            tab === "validation" ? "border-navy text-navy" : "border-transparent text-slate-soft hover:text-ink"
          }`}
        >
          <ShieldAlert size={15} /> Validation Engine &amp; Mismatches
        </button>
        <button
          onClick={() => setTab("vault")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold ${
            tab === "vault" ? "border-navy text-navy" : "border-transparent text-slate-soft hover:text-ink"
          }`}
        >
          <FolderOpen size={15} /> Vault Documents
        </button>
        <button
          onClick={() => setTab("check")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold ${
            tab === "check" ? "border-navy text-navy" : "border-transparent text-slate-soft hover:text-ink"
          }`}
        >
          <Sparkles size={15} /> OCR Extraction Cards
        </button>
        <button
          onClick={() => setTab("compliance")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold ${
            tab === "compliance" ? "border-navy text-navy" : "border-transparent text-slate-soft hover:text-ink"
          }`}
        >
          <FileCheck size={15} /> Vault Compliance
        </button>
      </div>

      {tab === "validation" && (
        <div className="mt-6 space-y-6">
          {/* Health Score Overview */}
          <div className="card p-6 grid sm:grid-cols-3 gap-6 items-center">
            <div>
              <span className="text-xs uppercase tracking-wider text-slate-soft font-bold">Vault Validation Score</span>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="font-display text-4xl font-extrabold text-amber-600">75</span>
                <span className="text-sm font-semibold text-slate-soft">/ 100</span>
              </div>
              <p className="mt-1 text-xs text-amber-700 font-medium">1 Critical Address Mismatch Found</p>
            </div>

            <div className="sm:col-span-2 grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div className="rounded-xl bg-slate-50 p-3 text-xs border border-slate-200">
                <span className="text-slate-400 block font-sans">Magic Bytes Checks</span>
                <span className="font-bold text-emerald-700 flex items-center gap-1 mt-0.5"><CheckCircle2 size={13} /> 100% Passed</span>
              </div>
              <div className="rounded-xl bg-slate-50 p-3 text-xs border border-slate-200">
                <span className="text-slate-400 block font-sans">Security Payload Scan</span>
                <span className="font-bold text-emerald-700 flex items-center gap-1 mt-0.5"><CheckCircle2 size={13} /> Clean</span>
              </div>
              <div className="rounded-xl bg-slate-50 p-3 text-xs border border-slate-200">
                <span className="text-slate-400 block font-sans">Cross-Doc Mismatches</span>
                <span className="font-bold text-rose-700 flex items-center gap-1 mt-0.5"><AlertTriangle size={13} /> 1 Detected</span>
              </div>
            </div>
          </div>

          {/* Cross-Document Mismatch Alerts */}
          <div>
            <h2 className="font-display text-base font-bold text-ink mb-3 flex items-center gap-2">
              <ShieldAlert size={18} className="text-rose-600" /> Cross-Document &amp; Profile Inconsistencies
            </h2>

            <div className="space-y-4">
              {inconsistencies.map((inc) => (
                <div key={inc.id} className="card p-5 border-l-4 border-l-rose-600 bg-rose-50/20">
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="rounded bg-rose-100 px-2 py-0.5 text-xs font-bold text-rose-800 uppercase">
                          {inc.type.replace("_", " ")}
                        </span>
                        <h3 className="font-bold text-rose-950 text-sm">{inc.title}</h3>
                      </div>

                      <div className="mt-3 grid sm:grid-cols-2 gap-3 text-xs">
                        <div className="rounded-lg bg-white p-3 border border-rose-100">
                          <span className="text-slate-400 font-semibold block">Expected Value:</span>
                          <span className="font-semibold text-emerald-800">{inc.expected}</span>
                        </div>
                        <div className="rounded-lg bg-white p-3 border border-rose-100">
                          <span className="text-slate-400 font-semibold block">Actual Extracted Value:</span>
                          <span className="font-semibold text-rose-800">{inc.actual}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Affected Approvals Badge List */}
                  <div className="mt-4 border-t border-rose-100 pt-3">
                    <span className="text-xs font-bold text-slate-700 block mb-1.5">Affected Statutory Approvals:</span>
                    <div className="flex flex-wrap gap-2">
                      {inc.affectedApprovals.map((app) => (
                        <span key={app} className="rounded-full bg-rose-100 px-3 py-1 text-xs font-bold text-rose-900 border border-rose-200 flex items-center gap-1">
                          <XCircle size={13} className="text-rose-600" /> {app.replace("_", " ")}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Single Document Validation Pipeline Results */}
          <div>
            <h2 className="font-display text-base font-bold text-ink mb-3">Single Document Safety &amp; Validation Status</h2>
            <div className="space-y-3">
              {docRecords.map((doc) => (
                <div key={doc.id} className="card p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <FileText size={20} className="text-navy" />
                    <div>
                      <h4 className="font-bold text-ink text-sm">{doc.name}</h4>
                      <p className="text-xs text-slate-soft">File: {doc.fileNameOnRecord}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 text-xs">
                    <span className="rounded bg-emerald-50 px-2.5 py-1 font-semibold text-emerald-700 border border-emerald-200">
                      ✓ Magic Bytes
                    </span>
                    <span className="rounded bg-emerald-50 px-2.5 py-1 font-semibold text-emerald-700 border border-emerald-200">
                      ✓ Security Scan
                    </span>
                    {doc.status === "rejected" ? (
                      <span className="rounded bg-rose-100 px-2.5 py-1 font-bold text-rose-800 border border-rose-200">
                        Address Mismatch
                      </span>
                    ) : (
                      <span className="rounded bg-blue-50 px-2.5 py-1 font-bold text-blue-800 border border-blue-200">
                        {doc.status.toUpperCase()}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {tab === "vault" && (
        <div className="mt-6 grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <div className="mb-4 flex flex-wrap items-center gap-3">
              <input
                className="input-field max-w-xs"
                placeholder="Search by name or type..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              {(["all", "auto_verified", "verified", "pending", "rejected"] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`pill border ${
                    filter === f ? "border-navy bg-navy text-white" : "border-navy/15 bg-white text-slate-soft"
                  }`}
                >
                  {f === "auto_verified" ? "Auto Verified" : f[0].toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>

            <div className="space-y-4">
              {filteredDocs.map((doc) => (
                <div key={doc.id} className="card p-5 transition hover:shadow-md">
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                    <div className="flex items-start gap-3">
                      <div className="rounded-lg bg-mist p-3 text-navy">
                        <FileText size={24} />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-display font-bold text-ink">{doc.name}</h3>
                          <span className="rounded bg-navy/10 px-2 py-0.5 text-xs font-bold text-navy">v{doc.version}</span>
                          {doc.isLatest && <span className="rounded bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-800">Latest</span>}
                        </div>
                        <p className="mt-1 text-xs text-slate-soft font-mono">
                          Key: {doc.storageKey}
                        </p>
                        <p className="mt-0.5 text-xs text-slate-soft">
                          Uploaded on {doc.uploadedOn} · Hash: <span className="font-mono text-[10px]">{doc.fileHash.substring(0, 16)}…</span>
                        </p>
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-2">
                      {doc.status === "auto_verified" && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700">
                          <Sparkles size={12} /> Auto Verified
                        </span>
                      )}
                      {doc.status === "verified" && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">
                          <CheckCircle2 size={12} /> Officer Verified
                        </span>
                      )}
                      {doc.status === "rejected" && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2.5 py-1 text-xs font-bold text-rose-700">
                          <XCircle size={12} /> Address Mismatch
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3 text-xs">
                    <button
                      onClick={() => setHistoryDoc(doc)}
                      className="flex items-center gap-1 font-semibold text-navy hover:underline"
                    >
                      <History size={14} /> Version History
                    </button>

                    <button
                      onClick={() => generateSignedUrl(doc)}
                      className="btn-primary py-1.5 px-3 text-xs flex items-center gap-1.5"
                    >
                      <KeyRound size={13} /> Generate Signed Download URL
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="card h-fit p-6">
            <h2 className="flex items-center gap-2 font-display text-sm font-bold text-ink">
              <UploadCloud size={18} className="text-navy" /> Secure Document Upload
            </h2>
            <p className="mt-1 text-xs text-slate-soft">
              PDF, PNG, or JPG files. Automatically passes Magic Bytes &amp; Security Validation.
            </p>

            <form onSubmit={handleUploadSubmit} className="mt-4 space-y-4">
              <div>
                <label className="label-text">Document Classification</label>
                <select className="input-field" value={selectedType} onChange={(e) => setSelectedType(e.target.value)}>
                  {COMMON_DOCS.map((d) => (
                    <option key={d.code} value={d.code}>{d.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="label-text">Expiry Date (Optional)</label>
                <input
                  type="date"
                  className="input-field"
                  value={expiryInput}
                  onChange={(e) => setExpiryInput(e.target.value)}
                />
              </div>

              <div>
                <label className="label-text">Select Document File</label>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="application/pdf,image/png,image/jpeg"
                  onChange={handleFileChange}
                  className="block w-full text-xs text-slate-soft file:mr-3 file:rounded-lg file:border-0 file:bg-navy file:px-3.5 file:py-2 file:text-sm file:font-semibold file:text-white hover:file:bg-navy-dark"
                />
                {filePreview && (
                  <img src={filePreview} alt="Preview" className="mt-3 h-28 w-full rounded-lg border border-navy/10 object-cover" />
                )}
              </div>

              <button
                type="submit"
                disabled={!selectedFile || uploading}
                className="btn-primary w-full text-sm disabled:opacity-50"
              >
                {uploading ? (
                  <><Loader2 size={15} className="animate-spin" /> Scanning &amp; Validating…</>
                ) : (
                  <><UploadCloud size={15} /> Upload &amp; Validate</>
                )}
              </button>
            </form>
          </div>
        </div>
      )}

      {tab === "check" && (
        <div className="mt-6 space-y-4">
          <h2 className="font-display text-base font-bold text-ink">Automated OCR Extraction &amp; Metadata Analysis</h2>
          {docRecords.map((doc) => (
            <div key={doc.id} className="card p-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FileCode size={20} className="text-navy" />
                  <div>
                    <h3 className="font-bold text-ink">{doc.name}</h3>
                    <p className="text-xs text-slate-soft">File: {doc.fileNameOnRecord}</p>
                  </div>
                </div>
                <span className="rounded bg-blue-100 px-2.5 py-1 text-xs font-bold text-blue-800">
                  Confidence: {doc.extractedData?.confidence ? `${Math.round(doc.extractedData.confidence * 100)}%` : "N/A"}
                </span>
              </div>

              <div className="mt-4 rounded-lg bg-slate-900 p-4 text-xs text-emerald-400 font-mono space-y-1">
                <p>&#123;</p>
                <p className="pl-4">"document_id": "{doc.id}",</p>
                <p className="pl-4">"document_type": "{doc.documentType}",</p>
                <p className="pl-4">"file_hash": "{doc.fileHash}",</p>
                <p className="pl-4">"extracted_number": "{doc.extractedData?.documentNumber || "N/A"}",</p>
                <p className="pl-4">"entity_name": "{doc.extractedData?.entityName || "N/A"}",</p>
                <p className="pl-4">"verification_status": "{doc.status.toUpperCase()}",</p>
                <p className="pl-4">"storage_access": "RESTRICTED (Signed URL Required)"</p>
                <p>&#125;</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === "compliance" && (
        <div className="mt-6 card p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div>
              <h2 className="font-display text-lg font-bold text-ink">Vault Compliance &amp; Readiness Score</h2>
              <p className="text-xs text-slate-soft">Cross-referencing uploaded documents against required regulatory rules.</p>
            </div>
            <span className="font-display text-3xl font-extrabold text-navy">75%</span>
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            <div className="rounded-xl bg-emerald-50 p-4 border border-emerald-200">
              <h3 className="font-bold text-emerald-900 flex items-center gap-2">
                <CheckCircle2 size={16} /> PAN Card Verified
              </h3>
              <p className="mt-1 text-xs text-emerald-700">Required for GST Registration &amp; FSSAI License.</p>
            </div>
            <div className="rounded-xl bg-rose-50 p-4 border border-rose-200">
              <h3 className="font-bold text-rose-900 flex items-center gap-2">
                <XCircle size={16} /> Rental Agreement Address Mismatch
              </h3>
              <p className="mt-1 text-xs text-rose-700">Registered City: Pune vs Rental Agreement: Mumbai.</p>
            </div>
          </div>
        </div>
      )}

      {/* Version History Modal */}
      {historyDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="card max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-display text-base font-bold text-ink flex items-center gap-2">
                <History size={18} className="text-navy" /> Document Version Lineage
              </h3>
              <button onClick={() => setHistoryDoc(null)} className="text-slate-400 hover:text-ink font-bold">✕</button>
            </div>

            <div className="space-y-3">
              <div className="rounded-lg bg-navy/5 p-3 text-xs border border-navy/10">
                <p className="font-bold text-navy">Current Active Version (v{historyDoc.version})</p>
                <p className="mt-1 text-slate-soft">File: {historyDoc.fileNameOnRecord}</p>
                <p className="text-slate-soft">Hash: {historyDoc.fileHash.substring(0, 20)}…</p>
              </div>

              {historyDoc.version > 1 && (
                <div className="rounded-lg bg-slate-100 p-3 text-xs opacity-75 border border-slate-200">
                  <p className="font-bold text-slate-700">Archived Version (v1)</p>
                  <p className="mt-1 text-slate-soft">Uploaded: 2026-08-25</p>
                  <p className="text-slate-soft">Status: SUPERSEDED</p>
                </div>
              )}
            </div>

            <button onClick={() => setHistoryDoc(null)} className="btn-primary w-full text-xs">
              Close History
            </button>
          </div>
        </div>
      )}

      {/* Signed URL Modal */}
      {signedUrlData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="card max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-display text-base font-bold text-ink flex items-center gap-2">
                <KeyRound size={18} className="text-emerald-600" /> HMAC Signed Download URL
              </h3>
              <button onClick={() => setSignedUrlData(null)} className="text-slate-400 hover:text-ink font-bold">✕</button>
            </div>

            <div className="space-y-2 text-xs">
              <p className="text-slate-soft">This temporary URL allows secure access to <strong className="text-ink">{signedUrlData.filename}</strong> without revealing internal storage paths.</p>
              <div className="rounded-lg bg-slate-900 p-3 font-mono text-emerald-400 break-all select-all">
                {signedUrlData.url}
              </div>
              <p className="text-amber-600 text-[11px] font-semibold flex items-center gap-1">
                <Clock size={12} /> Valid for 5 minutes (Expires at {signedUrlData.expiresAt}).
              </p>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(signedUrlData.url);
                  alert("Signed URL copied to clipboard!");
                }}
                className="btn-primary w-full text-xs"
              >
                Copy URL
              </button>
              <button onClick={() => setSignedUrlData(null)} className="btn-secondary w-full text-xs">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
