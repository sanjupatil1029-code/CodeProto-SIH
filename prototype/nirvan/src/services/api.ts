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

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: "Network response was not ok" }));
    throw new Error(errorData.detail || `Request failed with status ${response.status}`);
  }

  return response.json();
}

// ----------------------------------------------------
// 1. AUTH API
// ----------------------------------------------------
export async function registerUser(email: string, password: string, fullName: string) {
  return request<{ user: any; tokens: { access_token: string } }>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
}

export async function loginUser(email: string, password: string) {
  return request<{ user: any; tokens: { access_token: string } }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
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
  return request<any>("/businesses/create", {
    method: "POST",
    body: JSON.stringify(payload),
  });
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
    body: JSON.stringify({ document_id: documentId, mock_extracted_data: extractionData }),
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
