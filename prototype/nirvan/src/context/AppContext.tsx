import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import type {
  ProjectProfile,
  ApprovalRuntime,
  ApprovalStatus,
  DocumentRecord,
  AlertRecord,
  SchemeMatchRecord,
} from "../types";
import { getApplicableApprovals } from "../data/approvals";
import { evaluateSchemesWithGemini } from "../services/geminiSchemes";
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

  schemes: SchemeMatchRecord[];
  loadingSchemes: boolean;
  evaluateSchemes: (targetProfile?: ProjectProfile) => Promise<void>;

  resetProject: () => void;
  syncBackendState: () => Promise<void>;
}

const AppCtx = createContext<AppState | null>(null);

const CURRENT_USER_KEY = "NIRVAAN_current_user";

function getUserStorageKey(email?: string | null): string {
  if (!email) return "NIRVAAN_state_guest";
  return `NIRVAAN_state_${email.toLowerCase().trim()}`;
}

function loadSavedUser(): User | null {
  try {
    const raw = localStorage.getItem(CURRENT_USER_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function loadSavedStateForUser(user: User | null) {
  if (!user?.email) return null;
  try {
    const key = getUserStorageKey(user.email);
    const raw = localStorage.getItem(key);
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
  const initialUser = loadSavedUser();
  const initialSaved = loadSavedStateForUser(initialUser);

  const [user, setUser] = useState<User | null>(initialUser);
  const [category, setCategory] = useState<"shop" | "industry" | null>(initialSaved?.category ?? null);
  const [profile, setProfileState] = useState<ProjectProfile | null>(initialSaved?.profile ?? null);
  const [approvalRuntimes, setApprovalRuntimes] = useState<Record<string, ApprovalRuntime>>(
    initialSaved?.approvalRuntimes ?? {}
  );
  const [documents, setDocuments] = useState<DocumentRecord[]>(initialSaved?.documents ?? []);
  const [alerts, setAlerts] = useState<AlertRecord[]>(initialSaved?.alerts ?? seedAlerts());

  const [schemes, setSchemes] = useState<SchemeMatchRecord[]>(initialSaved?.schemes ?? []);
  const [loadingSchemes, setLoadingSchemes] = useState<boolean>(false);

  // Save active user and user progress whenever state updates
  useEffect(() => {
    try {
      if (user) {
        localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(user));
        const lightDocuments = documents.map(({ photoUrl, ...rest }) => rest);
        const storageKey = getUserStorageKey(user.email);
        localStorage.setItem(
          storageKey,
          JSON.stringify({ user, category, profile, approvalRuntimes, documents: lightDocuments, alerts, schemes })
        );
      } else {
        localStorage.removeItem(CURRENT_USER_KEY);
      }
    } catch (err) {
      console.warn("Could not persist user progress to localStorage:", err);
    }
  }, [user, category, profile, approvalRuntimes, documents, alerts, schemes]);

  // Sync state from backend when user has an active business profile
  const restoreBackendState = async (activeUser?: User | null) => {
    const currUser = activeUser || user;
    if (!currUser) return;

    try {
      const businesses = await api.getUserBusinesses();
      if (Array.isArray(businesses) && businesses.length > 0) {
        const biz = businesses[0];
        const restoredProfile: ProjectProfile = {
          id: biz.id,
          companyName: biz.name,
          businessTypeId: (biz.sector || "").toLowerCase(),
          sector: biz.sector,
          state: biz.state,
          district: biz.district,
          cityTaluk: biz.city || biz.district,
          size: biz.investment_amount > 50000000 ? "Large" : biz.investment_amount > 10000000 ? "Medium" : "Small",
          projectType: (biz.operational_stage as any) || "New Setup",
          employees: biz.employee_count,
          activity: biz.flexible_attributes?.activity || biz.sector,
          investmentAmount: biz.investment_amount,
          expectedTurnover: biz.expected_turnover,
          premisesType: biz.premises_type,
        };
        setProfileState(restoredProfile);

        const isShop = biz.sector.toLowerCase().includes("jewel") || biz.sector.toLowerCase().includes("shop");
        setCategory(isShop ? "shop" : "industry");

        // Restore roadmap
        let roadmap: any[] = [];
        try {
          roadmap = await api.getRoadmap(biz.id);
          if (!Array.isArray(roadmap) || roadmap.length === 0) {
            roadmap = await api.generateRoadmap(biz.id);
          }
        } catch {
          roadmap = await api.generateRoadmap(biz.id);
        }

        if (Array.isArray(roadmap) && roadmap.length > 0) {
          const runtimes: Record<string, ApprovalRuntime> = {};
          roadmap.forEach((r) => {
            const approvalId = r.rule_code || r.id;
            runtimes[approvalId] = {
              approvalId,
              status: (r.status.toLowerCase() as ApprovalStatus) || "not_started",
              progressDays: r.sla_elapsed_percent || 0,
              documentsReady: r.status === "READY" || r.status === "APPROVED",
            };
          });
          setApprovalRuntimes((prev) => ({ ...runtimes, ...prev }));
        }

        // Restore documents
        try {
          const bizDocs = await api.getBusinessDocuments(biz.id);
          if (Array.isArray(bizDocs) && bizDocs.length > 0) {
            const restoredDocs: DocumentRecord[] = bizDocs.map((d) => ({
              id: d.id,
              name: d.file_name || d.document_type,
              status: d.verification_status === "VERIFIED" ? "verified" : "pending",
              uploadedOn: d.uploaded_at ? d.uploaded_at.split("T")[0] : new Date().toISOString().split("T")[0],
              expiry: d.expiry_date || null,
              usedFor: ["biz-reg"],
              fileNameOnRecord: biz.name,
              flags: d.ai_flags || [],
            }));
            setDocuments((prev) => {
              const existingIds = new Set(prev.map((p) => p.id));
              const newDocs = restoredDocs.filter((rd) => !existingIds.has(rd.id));
              return [...newDocs, ...prev];
            });
          }
        } catch (err) {
          console.warn("Could not fetch business documents:", err);
        }
      }
    } catch (err) {
      console.warn("Could not restore state from backend:", err);
    }
  };

  // Sync from backend on initial mount if authenticated
  useEffect(() => {
    if (user && localStorage.getItem("NIRVAAN_token")) {
      restoreBackendState(user);
    }
  }, []);

  const login = async (email: string, name?: string, password?: string) => {
    let loggedUser: User;

    if (password) {
      const res = await api.loginUser(email, password);
      api.setToken(res.tokens.access_token);
      try {
        const me = await api.getCurrentUser();
        loggedUser = { id: me.id, email: me.email, name: me.full_name || res.user.full_name || name || email.split("@")[0] };
      } catch {
        loggedUser = { id: res.user.id, email: res.user.email, name: res.user.full_name || name || email.split("@")[0] };
      }
    } else {
      loggedUser = { email, name: name || email.split("@")[0] };
    }

    setUser(loggedUser);

    // 1. Restore local saved progress for this user
    const saved = loadSavedStateForUser(loggedUser);
    if (saved) {
      setCategory(saved.category ?? null);
      setProfileState(saved.profile ?? null);
      setApprovalRuntimes(saved.approvalRuntimes ?? {});
      setDocuments(saved.documents ?? []);
      setAlerts(saved.alerts ?? seedAlerts());
      if (saved.schemes) setSchemes(saved.schemes);
    } else {
      // Reset if no saved session for new local user
      setCategory(null);
      setProfileState(null);
      setApprovalRuntimes({});
      setDocuments([]);
      setAlerts(seedAlerts());
      setSchemes([]);
    }

    // 2. Restore backend progress if logged into backend server
    if (password || localStorage.getItem("NIRVAAN_token")) {
      await restoreBackendState(loggedUser);
    }
  };

  const register = async (email: string, password: string, name: string) => {
    await api.registerUser(email, password, name);
  };

  const logout = () => {
    api.removeToken();
    localStorage.removeItem(CURRENT_USER_KEY);
    setUser(null);
    setCategory(null);
    setProfileState(null);
    setApprovalRuntimes({});
    setDocuments([]);
    setAlerts(seedAlerts());
    setSchemes([]);
  };

  const syncBackendState = async () => {
    await restoreBackendState();
  };

  const evaluateSchemes = async (targetProfile?: ProjectProfile) => {
    const profToUse = targetProfile || profile;
    if (!profToUse) return;
    setLoadingSchemes(true);
    try {
      const evalSchemes = await evaluateSchemesWithGemini(profToUse);
      setSchemes(evalSchemes);
    } catch (err) {
      console.warn("Gemini scheme evaluation failed:", err);
    } finally {
      setLoadingSchemes(false);
    }
  };

  const setProfile = async (p: ProjectProfile) => {
    setProfileState(p);

    // Evaluate real schemes tailored to user profile input using Gemini AI API
    evaluateSchemes(p);

    // Attempt backend creation/sync
    try {
      const locStr = p.location || `${p.state},${p.district}`;
      const parts = locStr.split(",");
      const backendBiz = await api.createBusiness({
        name: p.companyName,
        sector: p.sector || (category === "shop" ? "JEWELLERY_SHOP" : "SUGAR_FACTORY"),
        state: parts[0] || p.state || "Maharashtra",
        district: parts[1] || p.district || "Pune",
        investment_amount: p.investmentAmount ?? 10000000,
        employee_count: p.employees,
        expected_turnover: p.expectedTurnover ?? 25000000,
        premises_type: p.premisesType || "MIDC_PLOT",
      });

      if (backendBiz?.id) {
        setProfileState({ ...p, id: backendBiz.id });
        const roadmap = await api.generateRoadmap(backendBiz.id);
        const runtimes: Record<string, ApprovalRuntime> = {};
        roadmap.forEach((r) => {
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
    setSchemes([]);
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
      schemes,
      loadingSchemes,
      evaluateSchemes,
      resetProject,
      syncBackendState,
    }),
    [user, category, profile, approvalRuntimes, documents, alerts, schemes, loadingSchemes]
  );

  return <AppCtx.Provider value={value}>{children}</AppCtx.Provider>;
}

export function useApp() {
  const ctx = useContext(AppCtx);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}

