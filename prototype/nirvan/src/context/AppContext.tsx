import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import type {
  ProjectProfile,
  ApprovalRuntime,
  ApprovalStatus,
  DocumentRecord,
  AlertRecord,
} from "../types";
import { getApplicableApprovals } from "../data/approvals";

interface User {
  name: string;
  email: string;
}

interface AppState {
  user: User | null;
  login: (email: string, name?: string) => void;
  logout: () => void;

  category: "shop" | "industry" | null;
  setCategory: (c: "shop" | "industry" | null) => void;

  profile: ProjectProfile | null;
  setProfile: (p: ProjectProfile) => void;

  approvalRuntimes: Record<string, ApprovalRuntime>;
  setApprovalStatus: (approvalId: string, status: ApprovalStatus) => void;
  markDocumentsReady: (approvalId: string) => void;

  documents: DocumentRecord[];
  addDocument: (doc: DocumentRecord) => void;

  alerts: AlertRecord[];
  markAlertRead: (id: string) => void;

  resetProject: () => void;
}

const AppCtx = createContext<AppState | null>(null);

const STORAGE_KEY = "NIRVAAN_state_v1";

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function seedAlerts(): AlertRecord[] {
  return [
    {
      id: "a1",
      severity: "critical",
      title: "SLA Risk",
      message: "Pollution Consent has been under review for 28 of 30 SLA days. Escalation recommended.",
      date: "2026-08-25",
      read: false,
      actionRequired: true,
      approvalId: "pollution-consent",
    },
    {
      id: "a2",
      severity: "high",
      title: "Query Raised",
      message: "Fire Department has requested a revised fire-fighting equipment list.",
      date: "2026-08-24",
      read: false,
      actionRequired: true,
      approvalId: "fire-noc",
    },
    {
      id: "a3",
      severity: "medium",
      title: "Inspection Scheduled",
      message: "Factory Licence inspection scheduled for 02 Sep 2026, 11:00 AM.",
      date: "2026-08-22",
      read: false,
      actionRequired: false,
      approvalId: "factory-licence",
    },
    {
      id: "a4",
      severity: "medium",
      title: "Renewal Due",
      message: "Trade Licence expires in 30 days. Start renewal to avoid a compliance gap.",
      date: "2026-08-20",
      read: true,
      actionRequired: true,
      approvalId: "trade-license",
    },
  ];
}

export function AppProvider({ children }: { children: React.ReactNode }) {
  const persisted = loadState();

  const [user, setUser] = useState<User | null>(persisted?.user ?? null);
  const [category, setCategory] = useState<"shop" | "industry" | null>(persisted?.category ?? null);
  const [profile, setProfileState] = useState<ProjectProfile | null>(persisted?.profile ?? null);
  const [approvalRuntimes, setApprovalRuntimes] = useState<Record<string, ApprovalRuntime>>(
    persisted?.approvalRuntimes ?? {}
  );
  const [documents, setDocuments] = useState<DocumentRecord[]>(persisted?.documents ?? []);
  const [alerts, setAlerts] = useState<AlertRecord[]>(persisted?.alerts ?? seedAlerts());

  useEffect(() => {
    try {
      // Photos are kept in memory only — base64 images are too large for localStorage
      // and were throwing a silent quota error that crashed the whole app.
      const lightDocuments = documents.map(({ photoUrl, ...rest }) => rest);
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ user, category, profile, approvalRuntimes, documents: lightDocuments, alerts })
      );
    } catch (err) {
      console.warn("Could not persist app state to localStorage:", err);
    }
  }, [user, category, profile, approvalRuntimes, documents, alerts]);

  const login = (email: string, name?: string) => {
    setUser({ email, name: name || email.split("@")[0] });
  };
  const logout = () => setUser(null);

  const setProfile = (p: ProjectProfile) => {
    setProfileState(p);
    const applicable = getApplicableApprovals(p);
    const runtimes: Record<string, ApprovalRuntime> = {};
    applicable.forEach((a, idx) => {
      let status: ApprovalStatus = "not_started";
      if (idx === 0) status = "under_review";
      if (idx === 1) status = "documents_required";
      runtimes[a.id] = {
        approvalId: a.id,
        status,
        progressDays: idx === 0 ? 12 : 0,
        documentsReady: false,
      };
    });
    setApprovalRuntimes(runtimes);
    // seed a couple of vault documents relevant to biz-reg
    setDocuments([
      {
        id: "d1",
        name: "PAN Card",
        status: "verified",
        uploadedOn: "2026-08-18",
        expiry: null,
        usedFor: ["biz-reg", "gst-reg"],
        fileNameOnRecord: p.companyName,
        flags: [],
      },
      {
        id: "d2",
        name: "GST Certificate",
        status: "verified",
        uploadedOn: "2026-08-20",
        expiry: null,
        usedFor: ["gst-reg"],
        fileNameOnRecord: p.companyName,
        flags: [],
      },
    ]);
  };

  const setApprovalStatus = (approvalId: string, status: ApprovalStatus) => {
    setApprovalRuntimes((prev) => ({
      ...prev,
      [approvalId]: {
        ...(prev[approvalId] || { approvalId, progressDays: 0, documentsReady: false }),
        status,
      },
    }));
  };

  const markDocumentsReady = (approvalId: string) => {
    setApprovalRuntimes((prev) => ({
      ...prev,
      [approvalId]: {
        ...(prev[approvalId] || { approvalId, progressDays: 0, status: "not_started" }),
        documentsReady: true,
        status: prev[approvalId]?.status === "not_started" ? "ready" : prev[approvalId]?.status || "ready",
      },
    }));
  };

  const addDocument = (doc: DocumentRecord) => {
    setDocuments((prev) => [doc, ...prev]);
  };

  const markAlertRead = (id: string) => {
    setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, read: true } : a)));
  };

  const resetProject = () => {
    setCategory(null);
    setProfileState(null);
    setApprovalRuntimes({});
    setDocuments([]);
  };

  const value = useMemo(
    () => ({
      user,
      login,
      logout,
      category,
      setCategory,
      profile,
      setProfile,
      approvalRuntimes,
      setApprovalStatus,
      markDocumentsReady,
      documents,
      addDocument,
      alerts,
      markAlertRead,
      resetProject,
    }),
    [user, category, profile, approvalRuntimes, documents, alerts]
  );

  return <AppCtx.Provider value={value}>{children}</AppCtx.Provider>;
}

export function useApp() {
  const ctx = useContext(AppCtx);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}
