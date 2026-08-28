import { useState } from "react";
import {
  AlertOctagon,
  AlertTriangle,
  Bell,
  CalendarClock,
  Clock,
  Gauge,
  TrendingDown,
  Building2,
  CalendarCheck2,
  RotateCcw,
} from "lucide-react";
import AppShell from "../components/AppShell";

interface RenewalAlertItem {
  approvalId: string;
  name: string;
  authority: string;
  expiryDate: string;
  daysRemaining: number;
  status: "UP_TO_DATE" | "RENEWAL_DUE" | "CRITICAL_RENEWAL" | "EXPIRED";
  reminderThreshold: number;
}

interface SLABottleneckItem {
  approvalId: string;
  name: string;
  authority: string;
  startedAt: string;
  slaDays: number;
  elapsedDays: number;
  elapsedPercent: number;
  slaStatus: "ON_TRACK" | "SLA_WARNING" | "SLA_BREACHED";
}

interface DepartmentMetrics {
  authority: string;
  inProgress: number;
  breached: number;
  avgDays: number;
  riskLevel: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
}

export default function SmartAlerts() {
  const [activeTab, setActiveTab] = useState<"alerts" | "renewals" | "sla_bottlenecks">("renewals");

  const renewals: RenewalAlertItem[] = [
    {
      approvalId: "fssai-lic",
      name: "FSSAI Food Business License",
      authority: "Food Safety and Standards Authority of India (FSSAI)",
      expiryDate: "2026-09-12",
      daysRemaining: 15,
      status: "RENEWAL_DUE",
      reminderThreshold: 15,
    },
    {
      approvalId: "fire-noc",
      name: "Fire Safety NOC",
      authority: "Maharashtra Fire Services Bureau",
      expiryDate: "2026-09-02",
      daysRemaining: 5,
      status: "CRITICAL_RENEWAL",
      reminderThreshold: 7,
    },
    {
      approvalId: "gst-cert",
      name: "GST Registration Certificate",
      authority: "Department of Revenue, Ministry of Finance",
      expiryDate: "2027-08-28",
      daysRemaining: 365,
      status: "UP_TO_DATE",
      reminderThreshold: 30,
    },
  ];

  const slaItems: SLABottleneckItem[] = [
    {
      approvalId: "water-consent",
      name: "Consent to Establish (Water Pollution Control)",
      authority: "Maharashtra Pollution Control Board (MPCB)",
      startedAt: "2026-08-03",
      slaDays: 30,
      elapsedDays: 25,
      elapsedPercent: 83.3,
      slaStatus: "SLA_WARNING",
    },
    {
      approvalId: "fire-noc",
      name: "Fire Safety NOC",
      authority: "Maharashtra Fire Services Bureau",
      startedAt: "2026-07-19",
      slaDays: 15,
      elapsedDays: 40,
      elapsedPercent: 266.7,
      slaStatus: "SLA_BREACHED",
    },
  ];

  const departments: DepartmentMetrics[] = [
    { authority: "Food Safety & Standards Authority (FSSAI)", inProgress: 1, breached: 0, avgDays: 14.2, riskLevel: "LOW" },
    { authority: "Maharashtra Fire Services Bureau", inProgress: 2, breached: 1, avgDays: 28.5, riskLevel: "MEDIUM" },
    { authority: "Maharashtra Pollution Control Board (MPCB)", inProgress: 1, breached: 0, avgDays: 18.0, riskLevel: "LOW" },
    { authority: "Department of Revenue (GST)", inProgress: 0, breached: 0, avgDays: 3.5, riskLevel: "LOW" },
  ];

  return (
    <AppShell>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Bell size={24} className="text-navy" />
            <h1 className="font-display text-3xl font-extrabold tracking-tight text-navy">
              Compliance &amp; SLA Engine
            </h1>
          </div>
          <p className="mt-1 text-sm text-slate-soft">
            Expiry renewal tracking (Module 10) &amp; SLA bottleneck analytics (Module 11).
          </p>
        </div>

        <div className="flex items-center gap-2 rounded-xl bg-navy/5 p-2 text-xs font-semibold text-navy">
          <Gauge size={16} className="text-indigo-600" /> Real-time Automated Engine
        </div>
      </div>

      <div className="mt-6 flex gap-2 border-b border-navy/[0.08]">
        <button
          onClick={() => setActiveTab("renewals")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold ${
            activeTab === "renewals" ? "border-navy text-navy" : "border-transparent text-slate-soft hover:text-ink"
          }`}
        >
          <CalendarClock size={16} /> Module 10: Renewal Engine
        </button>
        <button
          onClick={() => setActiveTab("sla_bottlenecks")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold ${
            activeTab === "sla_bottlenecks" ? "border-navy text-navy" : "border-transparent text-slate-soft hover:text-ink"
          }`}
        >
          <TrendingDown size={16} /> Module 11: SLA &amp; Bottlenecks
        </button>
      </div>

      {activeTab === "renewals" && (
        <div className="mt-6 space-y-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="card p-4 border-l-4 border-l-emerald-500">
              <span className="text-xs font-semibold text-slate-soft block">Up To Date</span>
              <span className="text-2xl font-extrabold text-navy">1</span>
            </div>
            <div className="card p-4 border-l-4 border-l-amber-500">
              <span className="text-xs font-semibold text-slate-soft block">Renewal Due (&lt;=30d)</span>
              <span className="text-2xl font-extrabold text-amber-600">1</span>
            </div>
            <div className="card p-4 border-l-4 border-l-rose-500">
              <span className="text-xs font-semibold text-slate-soft block">Critical (&lt;=7d)</span>
              <span className="text-2xl font-extrabold text-rose-600">1</span>
            </div>
            <div className="card p-4 border-l-4 border-l-slate-400">
              <span className="text-xs font-semibold text-slate-soft block">Expired</span>
              <span className="text-2xl font-extrabold text-slate-700">0</span>
            </div>
          </div>

          <div className="space-y-4">
            <h2 className="font-display text-base font-bold text-ink">Upcoming Expiration &amp; Renewal Reminders</h2>
            {renewals.map((r) => (
              <div key={r.approvalId} className="card p-5 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h3 className="font-bold text-ink text-base">{r.name}</h3>
                    <p className="text-xs text-slate-soft">{r.authority}</p>
                  </div>

                  <div className="flex items-center gap-2">
                    {r.status === "CRITICAL_RENEWAL" && (
                      <span className="rounded-full bg-rose-100 px-3 py-1 text-xs font-bold text-rose-800 border border-rose-200">
                        Critical ({r.daysRemaining} days left)
                      </span>
                    )}
                    {r.status === "RENEWAL_DUE" && (
                      <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-800 border border-amber-200">
                        Renewal Due ({r.daysRemaining} days left)
                      </span>
                    )}
                    {r.status === "UP_TO_DATE" && (
                      <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-800 border border-emerald-200">
                        Up To Date
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex flex-wrap items-center justify-between border-t border-slate-100 pt-3 text-xs">
                  <span className="text-slate-soft flex items-center gap-1.5">
                    <CalendarCheck2 size={14} className="text-navy" /> Expiry Date: <strong className="text-ink">{r.expiryDate}</strong>
                  </span>
                  <span className="text-slate-soft">
                    Reminder Threshold Triggered: <strong>{r.reminderThreshold} Days Threshold</strong>
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "sla_bottlenecks" && (
        <div className="mt-6 space-y-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="card p-4 border-l-4 border-l-indigo-500">
              <span className="text-xs font-semibold text-slate-soft block">Overall SLA Health</span>
              <span className="text-2xl font-extrabold text-indigo-700">50.0%</span>
            </div>
            <div className="card p-4 border-l-4 border-l-emerald-500">
              <span className="text-xs font-semibold text-slate-soft block">On Track (&lt;80%)</span>
              <span className="text-2xl font-extrabold text-emerald-600">0</span>
            </div>
            <div className="card p-4 border-l-4 border-l-amber-500">
              <span className="text-xs font-semibold text-slate-soft block">SLA Warning (&gt;=80%)</span>
              <span className="text-2xl font-extrabold text-amber-600">1</span>
            </div>
            <div className="card p-4 border-l-4 border-l-rose-500">
              <span className="text-xs font-semibold text-slate-soft block">SLA Breached (100%+)</span>
              <span className="text-2xl font-extrabold text-rose-600">1</span>
            </div>
          </div>

          {/* SLA Active Applications */}
          <div className="space-y-4">
            <h2 className="font-display text-base font-bold text-ink">Active Application SLA Velocity</h2>
            {slaItems.map((item) => (
              <div key={item.approvalId} className="card p-5 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h3 className="font-bold text-ink text-base">{item.name}</h3>
                    <p className="text-xs text-slate-soft">{item.authority}</p>
                  </div>
                  {item.slaStatus === "SLA_BREACHED" && (
                    <span className="rounded-full bg-rose-100 px-3 py-1 text-xs font-extrabold text-rose-900 border border-rose-300 flex items-center gap-1">
                      <AlertOctagon size={14} /> SLA Breached ({item.elapsedDays} / {item.slaDays} Days)
                    </span>
                  )}
                  {item.slaStatus === "SLA_WARNING" && (
                    <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-900 border border-amber-300 flex items-center gap-1">
                      <AlertTriangle size={14} /> SLA Warning ({item.elapsedPercent}%)
                    </span>
                  )}
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between text-xs font-semibold text-slate-soft">
                    <span>SLA Progress</span>
                    <span>{item.elapsedPercent}%</span>
                  </div>
                  <div className="w-full h-2.5 rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        item.slaStatus === "SLA_BREACHED"
                          ? "bg-rose-500"
                          : item.slaStatus === "SLA_WARNING"
                          ? "bg-amber-500"
                          : "bg-emerald-500"
                      }`}
                      style={{ width: `${Math.min(100, item.elapsedPercent)}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Department Bottleneck Analytics */}
          <div className="space-y-4">
            <h2 className="font-display text-base font-bold text-ink">Department &amp; Authority Bottleneck Risk Matrix</h2>
            <div className="grid sm:grid-cols-2 gap-4">
              {departments.map((d, i) => (
                <div key={i} className="card p-5 space-y-2">
                  <div className="flex items-center justify-between">
                    <h3 className="font-bold text-ink text-sm flex items-center gap-2">
                      <Building2 size={16} className="text-navy" /> {d.authority}
                    </h3>
                    <span
                      className={`rounded px-2 py-0.5 text-xs font-bold ${
                        d.riskLevel === "MEDIUM"
                          ? "bg-amber-100 text-amber-800"
                          : d.riskLevel === "CRITICAL" || d.riskLevel === "HIGH"
                          ? "bg-rose-100 text-rose-800"
                          : "bg-emerald-100 text-emerald-800"
                      }`}
                    >
                      {d.riskLevel} RISK
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 pt-2 text-xs text-slate-soft border-t border-slate-100">
                    <div>In Progress: <strong className="text-ink">{d.inProgress}</strong></div>
                    <div>Breached: <strong className="text-rose-600">{d.breached}</strong></div>
                    <div>Avg Days: <strong className="text-ink">{d.avgDays}d</strong></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
