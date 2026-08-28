import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import type {
  ProjectProfile,
  ApprovalRuntime,
  ApprovalStatus,
  DocumentRecord,
  AlertRecord,
} from "../types";
import { getApplicableApprovals } from "../data/approvals";
import * as api from "../services/api";

interface User {
  id?: string;
  name: string;
  email: string;
}

interface AppState {
  user: User | null;
  login: (email: string, name?: string, password?: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => void;

  category: "shop" | "industry" | null;
  setCategory: (c: "shop" | "industry" | null) => void;

  profile: ProjectProfile | null;
  setProfile: (p: ProjectProfile) => Promise<void>;

  approvalRuntimes: Record<string, ApprovalRuntime>;
  setApprovalStatus: (approvalId: string, status: ApprovalStatus) => Promise<void>;
  markDocumentsReady: (approvalId: string) => void;

  documents: DocumentRecord[];
  addDocument: (doc: DocumentRecord) => Promise<void>;

  alerts: AlertRecord[];
  markAlertRead: (id: string) => void;

  resetProject: () => void;
  syncBackendState: () => Promise<void>;
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
      const lightDocuments = documents.map(({ photoUrl, ...rest }) => rest);
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ user, category, profile, approvalRuntimes, documents: lightDocuments, alerts })
      );
    } catch (err) {
      console.warn("Could not persist app state to localStorage:", err);
    }
  }, [user, category, profile, approvalRuntimes, documents, alerts]);

  const login = async (email: string, name?: string, password?: string) => {
    try {
      if (password) {
        const res = await api.loginUser(email, password);
        api.setToken(res.tokens.access_token);
        setUser({ id: res.user.id, email: res.user.email, name: res.user.full_name || name || email.split("@")[0] });
        return;
      }
    } catch (err) {
      console.warn("Backend login error, falling back to local session:", err);
    }
    setUser({ email, name: name || email.split("@")[0] });
  };

  const register = async (email: string, password: string, name: string) => {
    try {
      const res = await api.registerUser(email, password, name);
      api.setToken(res.tokens.access_token);
      setUser({ id: res.user.id, email: res.user.email, name: res.user.full_name || name });
    } catch (err) {
      console.warn("Backend register error, falling back to local session:", err);
      setUser({ email, name });
    }
  };

  const logout = () => {
    api.removeToken();
    setUser(null);
  };

  const syncBackendState = async () => {
    if (!profile?.id) return;
    try {
      const roadmap = await api.getRoadmap(profile.id);
      if (Array.isArray(roadmap) && roadmap.length > 0) {
        const runtimes: Record<string, ApprovalRuntime> = {};
        roadmap.forEach((r) => {
          runtimes[r.rule_code || r.id] = {
            approvalId: r.rule_code || r.id,
            status: (r.status.toLowerCase() as ApprovalStatus) || "not_started",
            progressDays: r.sla_elapsed_percent || 0,
            documentsReady: r.status === "READY" || r.status === "APPROVED",
          };
        });
        setApprovalRuntimes(runtimes);
      }
    } catch (err) {
      console.warn("Failed to sync backend state:", err);
    }
  };

  const setProfile = async (p: ProjectProfile) => {
    setProfileState(p);
    
    // Attempt backend sync
    try {
      const backendBiz = await api.createBusiness({
        name: p.companyName,
        sector: p.sector || (category === "shop" ? "JEWELLERY_SHOP" : "SUGAR_FACTORY"),
        state: p.location.split(",")[0] || "Maharashtra",
        district: p.location.split(",")[1] || "Pune",
        investment_amount: p.investmentAmount,
        employee_count: p.employees,
        expected_turnover: p.expectedTurnover,
        premises_type: p.premisesType,
      });

      if (backendBiz?.id) {
        p.id = backendBiz.id;
        setProfileState({ ...p, id: backendBiz.id });
        const roadmap = await api.generateRoadmap(backendBiz.id);
        const runtimes: Record<string, ApprovalRuntime> = {};
        roadmap.forEach((r, idx) => {
          runtimes[r.rule_code || r.id] = {
            approvalId: r.rule_code || r.id,
            status: (r.status.toLowerCase() as ApprovalStatus) || "not_started",
            progressDays: 0,
            documentsReady: false,
          };
        });
        setApprovalRuntimes(runtimes);
        return;
      }
    } catch (err) {
      console.warn("Backend business creation fallback to local roadmap generator:", err);
    }

    // Local fallback
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
    ]);
  };

  const setApprovalStatus = async (approvalId: string, status: ApprovalStatus) => {
    setApprovalRuntimes((prev) => ({
      ...prev,
      [approvalId]: {
        ...(prev[approvalId] || { approvalId, progressDays: 0, documentsReady: false }),
        status,
      },
    }));

    try {
      await api.updateApprovalStatus(approvalId, status.toUpperCase());
    } catch (err) {
      console.warn("Failed to update status on backend:", err);
    }
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

  const addDocument = async (doc: DocumentRecord) => {
    setDocuments((prev) => [doc, ...prev]);

    if (profile?.id) {
      try {
        const uploaded = await api.uploadDocument({
          business_id: profile.id,
          document_type: doc.name.toUpperCase().replace(/\s+/g, "_"),
          file_name: doc.name,
        });
        if (uploaded?.id) {
          await api.validateDocument(uploaded.id, { company_name: profile.companyName });
        }
      } catch (err) {
        console.warn("Backend document upload fallback:", err);
      }
    }
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
      register,
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
      syncBackendState,
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
