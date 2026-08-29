import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertOctagon,
  AlertTriangle,
  Bell,
  CalendarClock,
  ShieldCheck,
  Info,
  CheckCheck,
  FileText,
  Clock,
  Calendar,
  User,
  ShieldAlert,
  ArrowRight,
  Sparkles,
  CheckCircle2,
} from "lucide-react";
import AppShell from "../components/AppShell";
import { useApp } from "../context/AppContext";
import {
  generateDocumentExpiryAlerts,
  generateScheduledInspections,
  generateEscalations,
} from "../data/alertGenerator";

interface NotificationFeedItem {
  id: string;
  eventType: string;
  severity: "INFO" | "WARNING" | "CRITICAL" | "SUCCESS";
  title: string;
  message: string;
  isRead: boolean;
  createdAt: string;
}

export default function SmartAlerts() {
  const { profile, documents, approvalRuntimes } = useApp();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<
    "notifications" | "doc_expirations" | "inspections" | "escalations"
  >("notifications");

  // Dynamic alert computations
  const documentExpirations = generateDocumentExpiryAlerts(documents, profile);
  const scheduledInspections = generateScheduledInspections(profile, approvalRuntimes);
  const SLAEscalations = generateEscalations(profile, approvalRuntimes);

  const [notifications, setNotifications] = useState<NotificationFeedItem[]>([
    {
      id: "n-1",
      eventType: "SLA_BREACHED",
      severity: "CRITICAL",
      title: `SLA Escalation Ticket: ${profile?.companyName || "Enterprise"} Application`,
      message: `Statutory turnaround SLA window exceeded. Automatic Level-2 Grievance Escalation ticket created for ${profile?.state || "State"} Authority review.`,
      isRead: false,
      createdAt: "2026-08-28 17:45",
    },
    {
      id: "n-2",
      eventType: "REGULATION_UPDATED",
      severity: "WARNING",
      title: `Statutory Gazette Update: Rules Updated for ${profile?.businessTypeId.toUpperCase() || "Business"} Sector`,
      message: `Official Gazette 2026 update applied: Fast-Track SLA window enabled. Document checklists updated in system.`,
      isRead: false,
      createdAt: "2026-08-28 16:30",
    },
    {
      id: "n-3",
      eventType: "DOCUMENT_EXPIRING",
      severity: "WARNING",
      title: "Document Expiration Warning: Premises Agreement",
      message: "Uploaded Rent/Lease Agreement expires in less than 30 days. Please upload updated lease deed in Document Vault.",
      isRead: true,
      createdAt: "2026-08-28 12:15",
    },
  ]);

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
              Smart Alerts &amp; Monitoring Central
            </h1>
          </div>
          <p className="mt-1 text-sm text-slate-soft">
            Real-time Expirations, Scheduled Government Inspections &amp; SLA Escalations.
          </p>
        </div>

        <div className="flex items-center gap-2 rounded-xl bg-navy/5 p-2.5 text-xs font-semibold text-navy">
          <ShieldCheck size={16} className="text-indigo-600" /> Statutory SLA &amp; Expiry Monitor Active
        </div>
      </div>

      {/* Enterprise Context Banner */}
      {profile && (
        <div className="mt-6 card p-4 bg-gradient-to-r from-navy/5 via-indigo-50/40 to-white flex flex-wrap items-center justify-between gap-4 border-l-4 border-l-navy">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-900 flex items-center gap-1">
              <Sparkles size={13} className="text-indigo-600" /> Active Monitoring Scope
            </span>
            <p className="font-display font-bold text-navy text-base mt-0.5">
              {profile.companyName} <span className="text-xs text-slate-soft font-normal">({profile.businessTypeId.toUpperCase()})</span>
            </p>
            <p className="text-xs text-slate-soft">
              Location: <strong>{profile.cityTaluk || profile.district}, {profile.state}</strong>
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <span className="rounded-lg bg-rose-50 px-3 py-1.5 font-bold text-rose-800 border border-rose-200">
              {documentExpirations.filter((d) => d.status !== "UP_TO_DATE").length} Doc Expirations
            </span>
            <span className="rounded-lg bg-amber-50 px-3 py-1.5 font-bold text-amber-800 border border-amber-200">
              {scheduledInspections.length} Inspections
            </span>
            <span className="rounded-lg bg-indigo-50 px-3 py-1.5 font-bold text-indigo-800 border border-indigo-200">
              {SLAEscalations.length} SLA Escalations
            </span>
          </div>
        </div>
      )}

      {/* Navigation Sub-Tabs */}
      <div className="mt-6 flex gap-2 border-b border-navy/[0.08] overflow-x-auto">
        <button
          onClick={() => setActiveTab("notifications")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold whitespace-nowrap ${
            activeTab === "notifications" ? "border-navy text-navy" : "border-transparent text-slate-soft hover:text-ink"
          }`}
        >
          <Bell size={16} /> Notification Feed
          {unreadCount > 0 && (
            <span className="rounded-full bg-rose-500 px-2 py-0.5 text-[11px] font-extrabold text-white">
              {unreadCount}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab("doc_expirations")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold whitespace-nowrap ${
            activeTab === "doc_expirations" ? "border-navy text-navy" : "border-transparent text-slate-soft hover:text-ink"
          }`}
        >
          <CalendarClock size={16} /> Document Expirations ({documentExpirations.length})
        </button>

        <button
          onClick={() => setActiveTab("inspections")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold whitespace-nowrap ${
            activeTab === "inspections" ? "border-navy text-navy" : "border-transparent text-slate-soft hover:text-ink"
          }`}
        >
          <Calendar size={16} /> Scheduled Inspections ({scheduledInspections.length})
        </button>

        <button
          onClick={() => setActiveTab("escalations")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold whitespace-nowrap ${
            activeTab === "escalations" ? "border-navy text-navy" : "border-transparent text-slate-soft hover:text-ink"
          }`}
        >
          <ShieldAlert size={16} /> Escalations &amp; SLA Risks ({SLAEscalations.length})
        </button>
      </div>

      {/* TAB 1: Notifications Feed */}
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

      {/* TAB 2: Document Expirations */}
      {activeTab === "doc_expirations" && (
        <div className="mt-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="font-display text-base font-bold text-ink flex items-center gap-2">
                <CalendarClock size={18} className="text-rose-600" /> Uploaded Document Expirations &amp; Validity Tracking
              </h2>
              <p className="text-xs text-slate-soft mt-0.5">
                Automatically monitors expiry dates across your uploaded vault documents (GST, Lease Deeds, Fire NOCs, Trade Licenses).
              </p>
            </div>

            <button onClick={() => navigate("/vault")} className="btn-primary py-2 px-4 text-xs flex items-center gap-1.5">
              <FileText size={14} /> Open Document Vault
            </button>
          </div>

          <div className="space-y-4">
            {documentExpirations.map((doc) => {
              const isCritical = doc.status === "CRITICAL_EXPIRED";
              const isDue = doc.status === "RENEWAL_DUE";

              return (
                <div
                  key={doc.id}
                  className={`card p-5 border-l-4 ${
                    isCritical
                      ? "border-l-rose-600 bg-rose-50/15"
                      : isDue
                      ? "border-l-amber-500 bg-amber-50/15"
                      : "border-l-emerald-500"
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex items-start gap-3">
                      <div className={`p-3 rounded-xl ${isCritical ? "bg-rose-100 text-rose-700" : "bg-amber-100 text-amber-800"}`}>
                        <CalendarClock size={22} />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-bold text-navy text-base">{doc.docName}</h3>
                          <span className="rounded bg-slate-100 px-2 py-0.5 text-xs font-mono text-slate-700 border border-slate-200">
                            {doc.docType}
                          </span>
                        </div>

                        <div className="mt-1 flex flex-wrap items-center gap-4 text-xs text-slate-soft">
                          <span className="flex items-center gap-1 font-semibold text-slate-700">
                            <Clock size={13} /> Expiry Date: <strong className="text-navy font-mono">{doc.expiryDate}</strong>
                          </span>
                          <span className="flex items-center gap-1 font-semibold text-slate-700">
                            Days Remaining:{" "}
                            <strong className={doc.daysRemaining <= 10 ? "text-rose-700 font-extrabold" : "text-amber-700 font-extrabold"}>
                              {doc.daysRemaining} Days
                            </strong>
                          </span>
                        </div>

                        <p className="mt-2 text-xs text-slate-600">
                          Required for approvals:{" "}
                          <span className="font-semibold text-navy">
                            {doc.usedForApprovals.join(", ")}
                          </span>
                        </p>
                      </div>
                    </div>

                    <div className="flex flex-col sm:items-end gap-2">
                      <span
                        className={`rounded-full px-3 py-1 text-xs font-extrabold border ${
                          isCritical
                            ? "bg-rose-100 text-rose-900 border-rose-300"
                            : isDue
                            ? "bg-amber-100 text-amber-900 border-amber-300"
                            : "bg-emerald-100 text-emerald-900 border-emerald-300"
                        }`}
                      >
                        {isCritical ? "CRITICAL (Immediate Renewal Required)" : isDue ? "RENEWAL DUE" : "VALID & ACTIVE"}
                      </span>

                      <button
                        onClick={() => navigate("/vault")}
                        className="btn-secondary !py-1.5 !px-3 text-xs flex items-center gap-1"
                      >
                        Upload Renewed Copy <ArrowRight size={13} />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 3: Scheduled Inspections */}
      {activeTab === "inspections" && (
        <div className="mt-6 space-y-6">
          <div>
            <h2 className="font-display text-base font-bold text-ink flex items-center gap-2">
              <Calendar size={18} className="text-indigo-600" /> Scheduled Government Site Inspections
            </h2>
            <p className="text-xs text-slate-soft mt-0.5">
              Tracks upcoming physical and digital site audits scheduled by licensing authorities.
            </p>
          </div>

          <div className="space-y-4">
            {scheduledInspections.map((insp) => (
              <div key={insp.id} className="card p-5 space-y-4 border-l-4 border-l-indigo-600 bg-indigo-50/10">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-navy text-base">{insp.approvalName} Inspection</h3>
                      <span className="rounded bg-indigo-100 px-2.5 py-0.5 text-xs font-bold text-indigo-900 border border-indigo-200">
                        {insp.inspectionType.replace("_", " ")}
                      </span>
                    </div>

                    <p className="text-xs text-slate-soft mt-0.5">
                      Issuing Authority: <strong>{insp.authority}</strong>
                    </p>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="rounded-xl bg-white p-3 border border-slate-200 text-right">
                      <span className="text-[11px] text-slate-soft block uppercase font-bold">Inspection Date</span>
                      <span className="font-display text-base font-extrabold text-indigo-950 flex items-center gap-1">
                        <Calendar size={15} className="text-indigo-600" /> {insp.inspectionDate}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="grid sm:grid-cols-2 gap-4 text-xs bg-white p-4 rounded-xl border border-slate-200">
                  <div>
                    <span className="text-slate-soft font-bold block mb-1 flex items-center gap-1">
                      <User size={13} className="text-navy" /> Assigned Inspection Officer:
                    </span>
                    <span className="font-bold text-navy">{insp.inspectorName}</span>
                  </div>

                  <div>
                    <span className="text-slate-soft font-bold block mb-1 flex items-center gap-1">
                      <CheckCircle2 size={13} className="text-emerald-600" /> Site Readiness Document Checklist:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {insp.siteChecklist.map((c) => (
                        <span key={c} className="rounded bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-slate-700 border border-slate-200">
                          ✓ {c}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 4: Escalations & SLA Risks */}
      {activeTab === "escalations" && (
        <div className="mt-6 space-y-6">
          <div>
            <h2 className="font-display text-base font-bold text-ink flex items-center gap-2">
              <ShieldAlert size={18} className="text-rose-600" /> SLA Breach &amp; Statutory Grievance Escalation Control
            </h2>
            <p className="text-xs text-slate-soft mt-0.5">
              Monitors applications exceeding statutory SLA turnaround deadlines. Trigger official escalation tickets directly to Senior Department Directors.
            </p>
          </div>

          <div className="space-y-4">
            {SLAEscalations.map((esc) => (
              <div key={esc.id} className="card p-5 border-l-4 border-l-rose-600 bg-rose-50/20 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-navy text-base">{esc.approvalName}</h3>
                      <span className="rounded bg-rose-100 px-2.5 py-0.5 text-xs font-extrabold text-rose-900 border border-rose-300">
                        SLA BREACHED ({esc.elapsedDays} of {esc.slaDays} Days)
                      </span>
                    </div>

                    <p className="text-xs text-slate-soft mt-0.5">
                      Authority: <strong>{esc.authority}</strong> · Escalation Ticket: <strong className="font-mono text-rose-800">{esc.escalationTicketId}</strong>
                    </p>
                  </div>

                  <button
                    onClick={() => navigate("/grievances")}
                    className="btn-accent py-2 px-4 text-xs flex items-center gap-1.5"
                  >
                    <ShieldAlert size={14} /> Escalate to Appellate Authority
                  </button>
                </div>

                <div className="bg-white p-3.5 rounded-xl border border-rose-200 text-xs flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <span className="text-slate-soft font-bold block">Assigned Appellate Redressal Officer:</span>
                    <span className="font-bold text-rose-950">{esc.assignedOfficer}</span>
                  </div>

                  <span className="rounded bg-rose-100 px-3 py-1 font-bold text-rose-900">
                    Escalation Status: Level-{esc.escalationLevel} Statutory Review Active
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
