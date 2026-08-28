import { AlertOctagon, AlertTriangle, Bell, CalendarClock, CheckCheck } from "lucide-react";
import AppShell from "../components/AppShell";
import { useApp } from "../context/AppContext";
import { approvals } from "../data/approvals";
import type { AlertSeverity } from "../types";

const SEVERITY_META: Record<AlertSeverity, { label: string; className: string; icon: React.ComponentType<{ size?: number; className?: string }> }> = {
  critical: { label: "SLA Risk", className: "border-danger/30 bg-danger-light", icon: AlertOctagon },
  high: { label: "Query Raised", className: "border-warn/30 bg-warn-light", icon: AlertTriangle },
  medium: { label: "Inspection / Renewal", className: "border-indigo/20 bg-lavender/50", icon: CalendarClock },
};

export default function SmartAlerts() {
  const { alerts, markAlertRead } = useApp();
  const unread = alerts.filter((a) => !a.read);
  const read = alerts.filter((a) => a.read);

  const renderAlert = (alert: (typeof alerts)[number]) => {
    const meta = SEVERITY_META[alert.severity];
    const Icon = meta.icon;
    const approvalName = alert.approvalId ? approvals.find((a) => a.id === alert.approvalId)?.name : null;
    return (
      <div key={alert.id} className={`card border p-5 ${meta.className} ${alert.read ? "opacity-60" : ""}`}>
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <Icon size={18} className="mt-0.5 flex-shrink-0 text-ink" />
            <div>
              <p className="text-sm font-bold text-ink">{alert.title}</p>
              <p className="mt-0.5 text-sm text-ink/80">{alert.message}</p>
              <div className="mt-2 flex items-center gap-3 text-xs text-slate-soft">
                <span>{alert.date}</span>
                {approvalName && <span className="pill bg-white/70 text-ink">{approvalName}</span>}
                {alert.actionRequired && <span className="pill bg-danger text-white">Action Required</span>}
              </div>
            </div>
          </div>
          {!alert.read && (
            <button
              onClick={() => markAlertRead(alert.id)}
              className="flex items-center gap-1 whitespace-nowrap rounded-lg bg-white px-2.5 py-1.5 text-xs font-semibold text-navy shadow-card hover:bg-lavender"
            >
              <CheckCheck size={13} /> Mark read
            </button>
          )}
        </div>
      </div>
    );
  };

  return (
    <AppShell>
      <div className="flex items-center gap-2">
        <Bell size={22} className="text-navy" />
        <h1 className="font-display text-3xl font-extrabold tracking-tight text-navy">Smart Alerts</h1>
      </div>
      <p className="mt-1.5 text-sm text-slate-soft">SLA risks, queries, inspections and renewals — all in one place.</p>

      <div className="mt-8 space-y-4">
        <h2 className="text-xs font-bold uppercase tracking-wide text-slate-soft">Unread ({unread.length})</h2>
        {unread.length === 0 ? (
          <p className="text-sm text-slate-soft">You're all caught up.</p>
        ) : (
          unread.map(renderAlert)
        )}
      </div>

      {read.length > 0 && (
        <div className="mt-8 space-y-4">
          <h2 className="text-xs font-bold uppercase tracking-wide text-slate-soft">Read</h2>
          {read.map(renderAlert)}
        </div>
      )}
    </AppShell>
  );
}
