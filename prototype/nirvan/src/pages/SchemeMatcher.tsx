import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Award,
  History,
  Sparkles,
  Gift,
  Layers,
  Building2,
  ListChecks,
  CheckCircle2,
  FileCheck,
  ExternalLink,
} from "lucide-react";
import AppShell from "../components/AppShell";
import { useApp } from "../context/AppContext";

interface SchemeMatchRecord {
  id: string;
  code: string;
  name: string;
  department: string;
  category: "CAPITAL_SUBSIDY" | "INTEREST_SUBVENTION" | "INFRASTRUCTURE_GRANT";
  matchStatus: "MATCHED" | "CONDITIONAL" | "INELIGIBLE";
  estimatedBenefit: number;
  benefitSummary: string;
  reasons: string[];
  documents: string[];
  portalUrl: string;
}

interface RuleVersionRecord {
  ruleCode: string;
  name: string;
  version: string;
  status: "ACTIVE" | "SUPERSEDED";
  isLatest: boolean;
  effectiveFrom: string;
  effectiveTo?: string;
  slaDays: number;
  changeSummary: string;
}

export default function SchemeMatcher() {
  const { profile } = useApp();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<"schemes" | "regulatory_versions">("schemes");

  const [schemes] = useState<SchemeMatchRecord[]>([
    {
      id: "sch-1",
      code: "PMKSY_INFRASTRUCTURE_GRANT",
      name: "Pradhan Mantri Kisan SAMPADA Yojana (PMKSY) Infrastructure Grant",
      department: "Ministry of Food Processing Industries (MoFPI)",
      category: "INFRASTRUCTURE_GRANT",
      matchStatus: "MATCHED",
      estimatedBenefit: 5000000.0,
      benefitSummary: "35% to 50% Capital Grant up to ₹50 Lakhs for creation of cold chain & food processing clusters.",
      reasons: [
        "Sector 'FOOD_PROCESSING' qualifies under MoFPI central mandate.",
        "State 'Maharashtra' qualifies under national scheme jurisdiction.",
        "Project Investment ₹3.50 Crores meets minimum threshold of ₹2.00 Crores.",
      ],
      documents: ["PAN_CARD", "GST_IN", "RENT_AGREEMENT", "CHARTERED_ACCOUNTANT_CERTIFICATE", "DETAILED_PROJECT_REPORT"],
      portalUrl: "https://mofpi.gov.in/pmksy",
    },
    {
      id: "sch-2",
      code: "MAHA_PSI_CAPITAL_INCENTIVE",
      name: "Maharashtra Package Scheme of Incentives (PSI 2026) - Food Processing",
      department: "Industries Department, Government of Maharashtra / MAITRI",
      category: "INTEREST_SUBVENTION",
      matchStatus: "MATCHED",
      estimatedBenefit: 2500000.0,
      benefitSummary: "5% Interest Subvention for 5 years + Electricity Duty Exemption for MIDC/Industrial area units.",
      reasons: [
        "Located in MAHARASHTRA state industrial zone.",
        "MIDC Bhosari industrial plot premises qualifies for regional incentive bonus.",
      ],
      documents: ["PAN_CARD", "RENT_AGREEMENT", "ELECTRICITY_BILL", "MAITRI_REGISTRATION_CERT"],
      portalUrl: "https://maitri.mahaonline.gov.in",
    },
    {
      id: "sch-3",
      code: "MSME_INTEREST_SUBVENTION",
      name: "Central MSME Credit & Interest Subvention Scheme",
      department: "Ministry of Micro, Small & Medium Enterprises (MSME)",
      category: "INTEREST_SUBVENTION",
      matchStatus: "MATCHED",
      estimatedBenefit: 500000.0,
      benefitSummary: "2% Interest Subvention on fresh or incremental working capital loans up to ₹1 Crore.",
      reasons: ["MSME turnover within ₹5.00 Crore ceiling.", "Registered Private Limited entity."],
      documents: ["PAN_CARD", "UDYAM_REGISTRATION", "BANK_LOAN_SANCTION"],
      portalUrl: "https://udyamregistration.gov.in",
    },
  ]);

  const [ruleVersions] = useState<RuleVersionRecord[]>([
    {
      ruleCode: "FSSAI_LICENSE",
      name: "FSSAI Food Business License",
      version: "2.0",
      status: "ACTIVE",
      isLatest: true,
      effectiveFrom: "2026-08-28",
      slaDays: 15,
      changeSummary: "Updated via Official Gazette Notification 2026: Fast-Track SLA reduced from 30d to 15d; added mandatory Water Quality Test Report.",
    },
    {
      ruleCode: "FSSAI_LICENSE",
      name: "FSSAI Food Business License",
      version: "1.0",
      status: "SUPERSEDED",
      isLatest: false,
      effectiveFrom: "2025-01-01",
      effectiveTo: "2026-08-28",
      slaDays: 30,
      changeSummary: "Initial statutory baseline rule definition.",
    },
    {
      ruleCode: "FIRE_NOC",
      name: "Fire Safety NOC (Maharashtra Fire Services)",
      version: "1.0",
      status: "ACTIVE",
      isLatest: true,
      effectiveFrom: "2025-01-01",
      slaDays: 15,
      changeSummary: "Active Maharashtra Fire Prevention & Life Safety Act rule version.",
    },
  ]);

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

  const totalBenefit = schemes.reduce((acc, s) => acc + s.estimatedBenefit, 0);

  return (
    <AppShell>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Award size={24} className="text-navy" />
            <h1 className="font-display text-3xl font-extrabold tracking-tight text-navy">
              Scheme Matcher &amp; Regulatory Engine
            </h1>
          </div>
          <p className="mt-1 text-sm text-slate-soft">
            Government scheme eligibility matching (Module 14) &amp; Immutable rule versioning (Module 15).
          </p>
        </div>

        <div className="flex items-center gap-2 rounded-xl bg-navy/5 p-2.5 text-xs font-semibold text-navy">
          <Layers size={16} className="text-indigo-600" /> Explainable AI &amp; Immutable Audit
        </div>
      </div>

      <div className="mt-6 flex gap-2 border-b border-navy/[0.08]">
        <button
          onClick={() => setActiveTab("schemes")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold ${
            activeTab === "schemes" ? "border-navy text-navy" : "border-transparent text-slate-soft hover:text-ink"
          }`}
        >
          <Gift size={16} /> Module 14: Scheme Matcher
        </button>
        <button
          onClick={() => setActiveTab("regulatory_versions")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold ${
            activeTab === "regulatory_versions" ? "border-navy text-navy" : "border-transparent text-slate-soft hover:text-ink"
          }`}
        >
          <History size={16} /> Module 15: Rule Version Audit Trail
        </button>
      </div>

      {activeTab === "schemes" && (
        <div className="mt-6 space-y-6">
          <div className="card p-6 border-l-4 border-l-emerald-500 bg-gradient-to-r from-emerald-50/50 to-white flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <span className="text-xs font-bold uppercase tracking-wide text-emerald-800 flex items-center gap-1.5">
                <Sparkles size={16} className="text-emerald-600" /> Total Estimated Subsidy Benefit Matched
              </span>
              <p className="text-3xl font-extrabold text-navy mt-1">
                ₹{(totalBenefit / 100000).toFixed(2)} Lakhs
              </p>
              <p className="text-xs text-slate-soft mt-0.5">
                {schemes.length} Government Schemes matched for {profile.companyName} ({profile.sector || profile.businessTypeId}).
              </p>
            </div>
            <button className="btn-primary !bg-emerald-600 hover:!bg-emerald-700 text-xs">
              Apply via Single Window Gateway
            </button>
          </div>

          <div className="space-y-4">
            {schemes.map((s) => (
              <div key={s.id} className="card p-6 space-y-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-display text-lg font-bold text-ink">{s.name}</h3>
                      <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-bold text-emerald-800 border border-emerald-200">
                        {s.matchStatus}
                      </span>
                    </div>
                    <p className="text-xs text-slate-soft mt-1 flex items-center gap-1">
                      <Building2 size={13} /> {s.department}
                    </p>
                  </div>

                  <div className="text-right">
                    <span className="text-xs text-slate-soft block">Estimated Benefit</span>
                    <span className="font-display text-lg font-extrabold text-navy">
                      ₹{(s.estimatedBenefit / 100000).toFixed(2)} Lakhs
                    </span>
                  </div>
                </div>

                <p className="text-xs leading-relaxed text-slate-700 bg-slate-50 p-3 rounded-lg border border-slate-100">
                  <strong>Benefit Summary:</strong> {s.benefitSummary}
                </p>

                <div className="grid gap-4 sm:grid-cols-2 text-xs">
                  <div>
                    <h4 className="font-bold text-slate-soft uppercase tracking-wide flex items-center gap-1 mb-1.5">
                      <ListChecks size={14} className="text-navy" /> Why Your Profile Qualifies:
                    </h4>
                    <ul className="space-y-1 text-slate-700">
                      {s.reasons.map((r, i) => (
                        <li key={i} className="flex items-start gap-1.5">
                          <CheckCircle2 size={13} className="text-emerald-600 flex-shrink-0 mt-0.5" />
                          <span>{r}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <h4 className="font-bold text-slate-soft uppercase tracking-wide flex items-center gap-1 mb-1.5">
                      <FileCheck size={14} className="text-navy" /> Scheme Document Checklist:
                    </h4>
                    <div className="flex flex-wrap gap-1.5">
                      {s.documents.map((d) => (
                        <span key={d} className="rounded bg-slate-100 px-2 py-0.5 text-[11px] font-mono text-slate-700 border border-slate-200">
                          {d}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between border-t border-slate-100 pt-3 text-xs">
                  <span className="text-slate-soft">Official Government Portal</span>
                  <a
                    href={s.portalUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="btn-secondary !px-3 !py-1.5 text-xs flex items-center gap-1"
                  >
                    Visit Portal <ExternalLink size={13} />
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "regulatory_versions" && (
        <div className="mt-6 space-y-6">
          <div className="card p-6">
            <h2 className="font-display text-base font-bold text-ink flex items-center gap-2">
              <History size={18} className="text-navy" /> Immutable Rule Version Audit Trail (Module 15)
            </h2>
            <p className="text-xs text-slate-soft mt-1">
              Government rules are versioned and append-only. Old rule versions remain permanently stored for audit compliance.
            </p>
          </div>

          <div className="space-y-4">
            {ruleVersions.map((v, i) => (
              <div
                key={i}
                className={`card p-5 space-y-3 ${
                  v.isLatest ? "border-l-4 border-l-navy bg-indigo-50/20" : "opacity-75 bg-slate-50"
                }`}
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-navy text-base">{v.name}</h3>
                      <span
                        className={`rounded-full px-2.5 py-0.5 text-xs font-bold ${
                          v.isLatest
                            ? "bg-indigo-100 text-indigo-800 border border-indigo-200"
                            : "bg-slate-200 text-slate-700"
                        }`}
                      >
                        Version {v.version} {v.isLatest ? "(ACTIVE LATEST)" : "(SUPERSEDED)"}
                      </span>
                    </div>
                    <p className="text-xs text-slate-soft mt-0.5 font-mono">Code: {v.ruleCode}</p>
                  </div>

                  <span className="text-xs font-semibold text-slate-soft">
                    SLA Window: <strong className="text-ink">{v.slaDays} Days</strong>
                  </span>
                </div>

                <p className="text-xs text-slate-700 bg-white p-3 rounded-lg border border-slate-200">
                  <strong>Version Log:</strong> {v.changeSummary}
                </p>

                <div className="flex items-center justify-between text-xs text-slate-soft border-t border-slate-100 pt-2">
                  <span>Effective From: {v.effectiveFrom}</span>
                  {v.effectiveTo && <span>Superseded Date: {v.effectiveTo}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </AppShell>
  );
}
