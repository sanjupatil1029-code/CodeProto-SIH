const BASE_URL = "http://localhost:8000/api/v1";

function getToken(): string | null {
  return localStorage.getItem("NIRVAAN_token");
}

export function setToken(token: string) {
  localStorage.setItem("NIRVAAN_token", token);
}

export function removeToken() {
  localStorage.removeItem("NIRVAAN_token");
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });
  } catch {
    throw new Error("Unable to connect to NIRVAAN backend server. Please ensure the backend is running on http://localhost:8000.");
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: "Network error." }));
    let errorMsg = "Request failed";
    if (typeof errorData.detail === "string") {
      errorMsg = errorData.detail;
    } else if (Array.isArray(errorData.detail)) {
      errorMsg = errorData.detail.map((e: any) => e.msg || (typeof e === "string" ? e : JSON.stringify(e))).join("; ");
    } else if (errorData.detail) {
      errorMsg = typeof errorData.detail === "object" ? JSON.stringify(errorData.detail) : String(errorData.detail);
    }
    throw new Error(errorMsg);
  }

  return response.json();
}

// ----------------------------------------------------
// 1. AUTH API
// ----------------------------------------------------
export async function registerUser(email: string, password: string, fullName: string) {
  return request<{ id: string; email: string; full_name: string; role: string }>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
}

export async function loginUser(email: string, password: string) {
  const body = new URLSearchParams();
  body.append("username", email);
  body.append("password", password);

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: body.toString(),
    });
  } catch {
    throw new Error("Unable to connect to NIRVAAN backend server. Please ensure the backend is running on http://localhost:8000.");
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: "Invalid email or password" }));
    let errorMsg = "Incorrect email or password. If you don't have an account, please sign up.";
    if (typeof errorData.detail === "string") {
      errorMsg = errorData.detail;
    } else if (Array.isArray(errorData.detail)) {
      errorMsg = errorData.detail.map((e: any) => e.msg || (typeof e === "string" ? e : JSON.stringify(e))).join("; ");
    }
    throw new Error(errorMsg);
  }

  const data = await response.json();
  return {
    tokens: { access_token: data.access_token },
    user: { id: data.user_id, email, full_name: data.full_name || email.split("@")[0] },
  };
}

export async function getCurrentUser() {
  return request<{ id: string; email: string; full_name?: string; role: string }>("/auth/me");
}

// ----------------------------------------------------
// 2. BUSINESS API
// ----------------------------------------------------
export async function createBusiness(payload: {
  name: string;
  sector: string;
  sub_sector?: string;
  state: string;
  district: string;
  city?: string;
  investment_amount: number;
  employee_count: number;
  expected_turnover: number;
  operational_stage?: string;
  ownership_type?: string;
  premises_type?: string;
}) {
  return request<any>("/businesses/", {
    method: "POST",
    body: JSON.stringify({
      sub_sector: "GENERAL",
      city: payload.city || payload.district || "DEFAULT",
      operational_stage: "PLANNED",
      ownership_type: "PROPRIETORSHIP",
      premises_type: "RENTED",
      ...payload,
    }),
  });
}

export async function getUserBusinesses() {
  return request<any[]>("/businesses/");
}

export async function getBusiness(businessId: string) {
  return request<any>(`/businesses/${businessId}`);
}

// ----------------------------------------------------
// 3. WORKFLOWS & ROADMAP API
// ----------------------------------------------------
export async function generateRoadmap(businessId: string) {
  return request<any[]>(`/workflows/generate/${businessId}`, {
    method: "POST",
  });
}

export async function getRoadmap(businessId: string) {
  return request<any[]>(`/workflows/business/${businessId}`);
}

export async function updateApprovalStatus(approvalId: string, targetStatus: string) {
  return request<any>(`/workflows/approval/${approvalId}/status`, {
    method: "POST",
    body: JSON.stringify({ target_status: targetStatus }),
  });
}

export async function getPortalHandoff(approvalId: string) {
  return request<{ approval_id: string; official_portal_url: string; external_system: string }>(
    `/workflows/approval/${approvalId}/handoff`
  );
}

export async function submitApplication(approvalId: string, externalRefId?: string) {
  return request<any>(`/workflows/approval/${approvalId}/submit`, {
    method: "POST",
    body: JSON.stringify({ external_reference_id: externalRefId || `REF-${Date.now()}` }),
  });
}

// ----------------------------------------------------
// 4. DOCUMENTS & VALIDATION API
// ----------------------------------------------------
export async function uploadDocument(payload: {
  business_id: string;
  document_type: string;
  file_name: string;
  file_content_b64?: string;
  expiry_date?: string;
}) {
  return request<any>("/documents/upload", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function validateDocument(documentId: string, extractionData?: Record<string, any>) {
  return request<any>("/documents/validate", {
    method: "POST",
    body: JSON.stringify({ document_id: documentId, extracted_data: extractionData }),
  });
}

export async function validateDocumentWithAI(documentId: string) {
  return request<{ document: any; ai_report: any }>(`/documents/ai-validate/${documentId}`, {
    method: "POST",
  });
}

export async function getBusinessDocuments(businessId: string) {
  return request<any[]>(`/documents/business/${businessId}`);
}

// ----------------------------------------------------
// 5. SCHEME MATCHER API
// ----------------------------------------------------
export async function getMatchedSchemes(businessId: string) {
  return request<{
    business_id: string;
    total_schemes_evaluated: number;
    matched_count: number;
    conditional_count: number;
    total_potential_benefit: number;
    matches: any[];
  }>(`/schemes/business/${businessId}/matches`);
}

// ----------------------------------------------------
// 6. REGULATIONS & RULE VERSIONS API
// ----------------------------------------------------
export async function getPendingRegulatoryUpdates() {
  return request<any[]>("/regulations/updates/pending");
}

export async function getRuleHistory(ruleCode: string) {
  return request<{ rule_code: string; name: string; versions_count: number; versions: any[] }>(
    `/regulations/history/${ruleCode}`
  );
}

// ----------------------------------------------------
// 7. NOTIFICATIONS API
// ----------------------------------------------------
export async function getNotificationFeed(unreadOnly: boolean = false) {
  return request<{ total_count: number; unread_count: number; notifications: any[] }>(
    `/notifications/feed?unread_only=${unreadOnly}`
  );
}

export async function markNotificationRead(notificationId: string) {
  return request<any>(`/notifications/${notificationId}/read`, {
    method: "POST",
  });
}

// ----------------------------------------------------
// 8. AUDIT LOGS API
// ----------------------------------------------------
export async function getAuditLogs(resourceType?: string, resourceId?: string) {
  let url = "/admin/audit-logs";
  if (resourceType && resourceId) {
    url = `/admin/audit-logs/resource/${resourceType}/${resourceId}`;
  }
  return request<{ total_count: number; limit: number; offset: number; logs: any[] }>(url);
}
