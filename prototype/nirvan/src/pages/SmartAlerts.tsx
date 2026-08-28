import { useState } from "react";
import {
  AlertOctagon,
  AlertTriangle,
  Bell,
  CalendarClock,
  TrendingDown,
  ShieldCheck,
  Info,
  FileSpreadsheet,
  CheckCheck,
  UserCheck,
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

interface NotificationFeedItem {
  id: string;
  eventType: string;
  severity: "INFO" | "WARNING" | "CRITICAL" | "SUCCESS";
  title: string;
  message: string;
  isRead: boolean;
  createdAt: string;
}

interface AuditLogRecord {
  id: string;
  actorRole: string;
  action: string;
  resourceType: string;
  resourceId: string;
  timestamp: string;
  oldValue: Record<string, any>;
  newValue: Record<string, any>;
}

export default function SmartAlerts() {
  const [activeTab, setActiveTab] = useState<"notifications" | "renewals" | "sla_bottlenecks" | "audit_logs">("notifications");

  const [notifications, setNotifications] = useState<NotificationFeedItem[]>([
    {
      id: "n-1",
      eventType: "SLA_BREACHED",
      severity: "CRITICAL",
      title: "SLA Breached: Fire Safety NOC Application",
      message: "Fire NOC processing window has exceeded the statutory 15-day SLA deadline. Automatic grievance escalation ticket raised.",
      isRead: false,
      createdAt: "2026-08-28 17:45",
    },
    {
      id: "n-2",
      eventType: "REGULATION_UPDATED",
      severity: "WARNING",
      title: "Gazette Update: FSSAI Rule Version 2.0 Deployed",
      message: "FSSAI License processing window reduced to 15 days under Gazette Notification 2026. Added mandatory Water Quality Test Report requirement.",
      isRead: false,
      createdAt: "2026-08-28 16:30",
    },
    {
      id: "n-3",
      eventType: "DOCUMENT_INVALID",
      severity: "WARNING",
      title: "Document Cross-Mismatch Detected",
      message: "Rental Agreement address 'Mumbai' mismatches Business Profile location 'Pune'. Affected approvals: FSSAI License, MPCB Consent.",
      isRead: true,
      createdAt: "2026-08-28 12:15",
    },
  ]);

  const [auditLogs] = useState<AuditLogRecord[]>([
    {
      id: "aud-901",
      actorRole: "ADMIN",
      action: "RULE_VERSION_APPROVED",
      resourceType: "ApprovalRule",
      resourceId: "FSSAI_LICENSE",
      timestamp: "2026-08-28 18:36",
      oldValue: { rule_version: "1.0", sla_days: 30, is_latest: true },
      newValue: { rule_version: "2.0", sla_days: 15, is_latest: true, added_docs: ["WATER_TEST_REPORT"] },
    },
    {
      id: "aud-902",
      actorRole: "ENTREPRENEUR",
      action: "GRIEVANCE_ESCALATED",
      resourceType: "Grievance",
      resourceId: "grv-901",
      timestamp: "2026-08-28 17:45",
      oldValue: { status: "OPEN", escalation_level: 1 },
      newValue: { status: "ESCALATED", escalation_level: 2, assigned: "Senior Regional Inspector" },
    },
    {
      id: "aud-903",
      actorRole: "SYSTEM",
      action: "DOCUMENT_VALIDATED",
      resourceType: "Document",
      resourceId: "d-9912",
      timestamp: "2026-08-28 14:10",
      oldValue: { status: "UNVERIFIED" },
      newValue: { status: "FLAGGED", flags: ["ADDRESS_MISMATCH_PUNE_VS_MUMBAI"] },
    },
  ]);

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
  ];

  const markRead = (id: string) => {
    setNotifications(notifications.map((n) => (n.id === id ? { ...n, isRead: true } : n)));
  };

  const markAllRead = () => {
    setNotifications(notifications.map((n) => ({ ...n, isRead: true })));
  };

  const unreadCount = notifications.filter((n) => !n.isRead).length;

  return (
    <AppShell>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Bell size={24} className="text-navy" />
            <h1 className="font-display text-3xl font-extrabold tracking-tight text-navy">
              Smart Alerts &amp; Notifications
            </h1>
          </div>
          <p className="mt-1 text-sm text-slate-soft">
            Event-based notifications (Module 16) &amp; Immutable append-only audit trail (Module 17).
          </p>
        </div>

        <div className="flex items-center gap-2 rounded-xl bg-navy/5 p-2.5 text-xs font-semibold text-navy">
          <ShieldCheck size={16} className="text-indigo-600" /> Event-Driven Notification Engine
        </div>
      </div>

      <div className="mt-6 flex gap-2 border-b border-navy/[0.08] overflow-x-auto">
        <button
          onClick={() => setActiveTab("notifications")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold whitespace-nowrap ${
            activeTab === "notifications" ? "border-navy text-navy" : "border-transparent text-slate-soft hover:text-ink"
          }`}
        >
          <Bell size={16} /> Module 16: In-App Feed
          {unreadCount > 0 && (
            <span className="rounded-full bg-rose-500 px-2 py-0.5 text-[11px] font-extrabold text-white">
              {unreadCount}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab("renewals")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold whitespace-nowrap ${
            activeTab === "renewals" ? "border-navy text-navy" : "border-transparent text-slate-soft hover:text-ink"
          }`}
        >
          <CalendarClock size={16} /> Module 10: Renewals
        </button>
        <button
          onClick={() => setActiveTab("sla_bottlenecks")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold whitespace-nowrap ${
            activeTab === "sla_bottlenecks" ? "border-navy text-navy" : "border-transparent text-slate-soft hover:text-ink"
          }`}
        >
          <TrendingDown size={16} /> Module 11: SLA Analytics
        </button>
        <button
          onClick={() => setActiveTab("audit_logs")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold whitespace-nowrap ${
            activeTab === "audit_logs" ? "border-navy text-navy" : "border-transparent text-slate-soft hover:text-ink"
          }`}
        >
          <FileSpreadsheet size={16} /> Module 17: Append-Only Audit Trail
        </button>
      </div>

      {activeTab === "notifications" && (
        <div className="mt-6 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-base font-bold text-ink flex items-center gap-2">
              Event-Driven Notifications Feed ({unreadCount} Unread)
            </h2>
            {unreadCount > 0 && (
              <button
                onClick={markAllRead}
                className="btn-secondary !px-3 !py-1.5 text-xs flex items-center gap-1"
              >
                <CheckCheck size={14} /> Mark All as Read
              </button>
            )}
          </div>

          <div className="space-y-4">
            {notifications.map((n) => (
              <div
                key={n.id}
                className={`card p-5 space-y-3 ${
                  !n.isRead ? "border-l-4 border-l-rose-500 bg-rose-50/20" : "opacity-80"
                }`}
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    {n.severity === "CRITICAL" && <AlertOctagon size={18} className="text-rose-600" />}
                    {n.severity === "WARNING" && <AlertTriangle size={18} className="text-amber-600" />}
                    {n.severity === "INFO" && <Info size={18} className="text-indigo-600" />}
                    <h3 className="font-bold text-navy text-sm">{n.title}</h3>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-soft font-mono">{n.createdAt}</span>
                    {!n.isRead && (
                      <button
                        onClick={() => markRead(n.id)}
                        className="rounded bg-navy/10 px-2 py-0.5 text-xs font-semibold text-navy hover:bg-navy/20"
                      >
                        Mark Read
                      </button>
                    )}
                  </div>
                </div>

                <p className="text-xs leading-relaxed text-slate-700 bg-white p-3 rounded-lg border border-slate-200">
                  {n.message}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "audit_logs" && (
        <div className="mt-6 space-y-6">
          <div className="card p-6">
            <h2 className="font-display text-base font-bold text-ink flex items-center gap-2">
              <FileSpreadsheet size={18} className="text-navy" /> Module 17: Administrative Append-Only Audit Trail
            </h2>
            <p className="text-xs text-slate-soft mt-1">
              Statutory action records are strictly append-only and cannot be altered or deleted. Every state change captures exact old vs new JSON values.
            </p>
          </div>

          <div className="space-y-4">
            {auditLogs.map((log) => (
              <div key={log.id} className="card p-5 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-navy px-2 py-0.5 text-[11px] font-bold text-white font-mono">
                      {log.action}
                    </span>
                    <span className="text-xs text-slate-soft font-mono">
                      {log.resourceType}:{log.resourceId}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 text-xs text-slate-soft">
                    <span className="flex items-center gap-1">
                      <UserCheck size={13} /> Role: <strong className="text-ink">{log.actorRole}</strong>
                    </span>
                    <span className="font-mono">{log.timestamp}</span>
                  </div>
                </div>

                <div className="grid sm:grid-cols-2 gap-3 text-xs">
                  <div className="bg-rose-50/50 p-3 rounded-lg border border-rose-100 font-mono">
                    <span className="font-bold text-rose-800 block mb-1">Old State Value (Before):</span>
                    <pre className="text-[11px] whitespace-pre-wrap">{JSON.stringify(log.oldValue, null, 2)}</pre>
                  </div>
                  <div className="bg-emerald-50/50 p-3 rounded-lg border border-emerald-100 font-mono">
                    <span className="font-bold text-emerald-800 block mb-1">New State Value (After):</span>
                    <pre className="text-[11px] whitespace-pre-wrap">{JSON.stringify(log.newValue, null, 2)}</pre>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "renewals" && (
        <div className="mt-6 space-y-6">
          <div className="space-y-4">
            <h2 className="font-display text-base font-bold text-ink">Upcoming Expiration &amp; Renewal Reminders</h2>
            {renewals.map((r) => (
              <div key={r.approvalId} className="card p-5 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h3 className="font-bold text-ink text-base">{r.name}</h3>
                    <p className="text-xs text-slate-soft">{r.authority}</p>
                  </div>

                  <span className="rounded-full bg-rose-100 px-3 py-1 text-xs font-bold text-rose-800 border border-rose-200">
                    Critical ({r.daysRemaining} days left)
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "sla_bottlenecks" && (
        <div className="mt-6 space-y-6">
          <div className="space-y-4">
            <h2 className="font-display text-base font-bold text-ink">Active Application SLA Velocity</h2>
            {slaItems.map((item) => (
              <div key={item.approvalId} className="card p-5 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h3 className="font-bold text-ink text-base">{item.name}</h3>
                    <p className="text-xs text-slate-soft">{item.authority}</p>
                  </div>
                  <span className="rounded-full bg-rose-100 px-3 py-1 text-xs font-extrabold text-rose-900 border border-rose-300">
                    SLA Breached ({item.elapsedDays} / {item.slaDays} Days)
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </AppShell>
  );
}
