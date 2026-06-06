const API_BASE = import.meta.env.VITE_API_URL || "";

let csrfToken = "";

export function setAccessToken(token: string) {
  localStorage.setItem("access_token", token);
}

export function clearAccessToken() {
  localStorage.removeItem("access_token");
}

export function getAccessToken() {
  return localStorage.getItem("access_token") || "";
}

let csrfInitPromise: Promise<void> | null = null;

async function refreshCsrfToken() {
  const res = await fetch(`${API_BASE}/auth/csrf`, { credentials: "include" });
  if (!res.ok) throw new Error("Failed to initialize CSRF");
  const data = await res.json();
  csrfToken = data.csrf_token;
}

function formatApiError(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (item && typeof item === "object" && "msg" in item) {
          const loc = "loc" in item && Array.isArray(item.loc) ? item.loc.join(".") : "";
          return loc ? `${loc}: ${item.msg}` : String(item.msg);
        }
        return JSON.stringify(item);
      })
      .join("; ");
  }
  if (detail && typeof detail === "object") return JSON.stringify(detail);
  return "Request failed";
}

export async function initCsrf() {
  csrfInitPromise ??= refreshCsrfToken().catch((e) => {
    csrfInitPromise = null;
    throw e;
  });
  await csrfInitPromise;
}

function buildHeaders(method: string, extra?: HeadersInit): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(extra as Record<string, string>),
  };
  const token = getAccessToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (csrfToken && method !== "GET" && method !== "HEAD") {
    headers["X-CSRF-Token"] = csrfToken;
  }
  return headers;
}

async function apiFetch(path: string, options: RequestInit = {}) {
  const method = options.method || "GET";
  const needsCsrf = method !== "GET" && method !== "HEAD";
  if (needsCsrf) {
    await refreshCsrfToken();
  }

  const doFetch = () =>
    fetch(`${API_BASE}${path}`, {
      ...options,
      headers: buildHeaders(method, options.headers),
      credentials: "include",
    });

  let res = await doFetch();

  if (needsCsrf && res.status === 403) {
    const err = await res.clone().json().catch(() => ({ detail: "" }));
    const detail = formatApiError(err.detail);
    if (detail.toLowerCase().includes("csrf")) {
      await refreshCsrfToken();
      res = await doFetch();
    }
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    if (res.status === 401 && !path.startsWith("/auth/")) {
      clearAccessToken();
    }
    throw new Error(formatApiError(err.detail));
  }
  if (res.status === 204) return null;
  return res.json();
}

function publicHeaders(sessionToken?: string): Record<string, string> {
  const headers: Record<string, string> = {};
  if (sessionToken) headers["X-Session-Token"] = sessionToken;
  return headers;
}

export const api = {
  initCsrf,
  loginInit: () => apiFetch("/auth/login/init") as Promise<{ authorization_url: string; state: string }>,
  getMe: () => apiFetch("/auth/me"),
  getSurveys: () => apiFetch("/surveys/"),
  createSurvey: (body: object) => apiFetch("/surveys/", { method: "POST", body: JSON.stringify(body) }),
  getSurvey: (id: string) => apiFetch(`/surveys/${id}`),
  updateSurvey: (id: string, body: object) =>
    apiFetch(`/surveys/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteSurvey: (id: string) => apiFetch(`/surveys/${id}`, { method: "DELETE" }),
  getQuestions: (surveyId: string) => apiFetch(`/surveys/${surveyId}/questions`),
  createQuestion: (surveyId: string, body: object) =>
    apiFetch(`/surveys/${surveyId}/questions`, { method: "POST", body: JSON.stringify(body) }),
  updateQuestion: (surveyId: string, questionId: string, body: object) =>
    apiFetch(`/surveys/${surveyId}/questions/${questionId}`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  deleteQuestion: (surveyId: string, questionId: string) =>
    apiFetch(`/surveys/${surveyId}/questions/${questionId}`, { method: "DELETE" }),
  createOption: (surveyId: string, questionId: string, body: object) =>
    apiFetch(`/surveys/${surveyId}/questions/${questionId}/options`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  deleteOption: (surveyId: string, questionId: string, optionId: string) =>
    apiFetch(`/surveys/${surveyId}/questions/${questionId}/options/${optionId}`, {
      method: "DELETE",
    }),
  updateOption: (surveyId: string, questionId: string, optionId: string, body: object) =>
    apiFetch(`/surveys/${surveyId}/questions/${questionId}/options/${optionId}`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  getSurveyResponses: (
    surveyId: string,
    params: { sortBy?: string; sortOrder?: string } = {},
  ) => {
    const qs = new URLSearchParams();
    if (params.sortBy) qs.set("sort_by", params.sortBy);
    if (params.sortOrder) qs.set("sort_order", params.sortOrder);
    const query = qs.toString();
    return apiFetch(`/surveys/${surveyId}/responses${query ? `?${query}` : ""}`);
  },
  uploadImage: async (surveyId: string, file: File) => {
    await refreshCsrfToken();
    const form = new FormData();
    form.append("file", file);
    const headers: Record<string, string> = {};
    const token = getAccessToken();
    if (token) headers.Authorization = `Bearer ${token}`;
    if (csrfToken) headers["X-CSRF-Token"] = csrfToken;
    const res = await fetch(`${API_BASE}/surveys/${surveyId}/images`, {
      method: "POST",
      headers,
      body: form,
      credentials: "include",
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(formatApiError(err.detail));
    }
    return res.json() as Promise<{ url: string }>;
  },
  createLink: (surveyId: string) =>
    apiFetch(`/surveys/${surveyId}/links`, { method: "POST", body: JSON.stringify({}) }),
  getLinks: (surveyId: string) => apiFetch(`/surveys/${surveyId}/links`),
  exportUrl: (surveyId: string) => `${API_BASE}/surveys/${surveyId}/export.xlsx`,
  publicSurvey: (token: string) => apiFetch(`/public/surveys/${token}`),
  startSession: (token: string) =>
    apiFetch(`/public/surveys/${token}/sessions`, { method: "POST" }) as Promise<{
      session_id: string;
      session_token: string;
    }>,
  getDraft: (sessionId: string, sessionToken: string) =>
    fetch(`${API_BASE}/public/sessions/${sessionId}/draft`, {
      headers: publicHeaders(sessionToken),
    }).then(async (res) => {
      if (!res.ok) throw new Error("Failed to load draft");
      return res.json();
    }),
  saveDraft: (sessionId: string, sessionToken: string, answers: object[]) =>
    fetch(`${API_BASE}/public/sessions/${sessionId}/draft`, {
      method: "PUT",
      headers: { ...publicHeaders(sessionToken), "Content-Type": "application/json" },
      body: JSON.stringify({ answers }),
    }).then(async (res) => {
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(formatApiError(err.detail));
      }
    }),
  submitSurvey: (sessionId: string, sessionToken: string, answers: object[]) =>
    fetch(`${API_BASE}/public/sessions/${sessionId}/submit`, {
      method: "POST",
      headers: { ...publicHeaders(sessionToken), "Content-Type": "application/json" },
      body: JSON.stringify({ answers }),
    }).then(async (res) => {
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(formatApiError(err.detail));
      }
    }),
  uploadAnswerImage: async (sessionId: string, sessionToken: string, questionId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_BASE}/public/sessions/${sessionId}/questions/${questionId}/image`, {
      method: "POST",
      headers: publicHeaders(sessionToken),
      body: form,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(formatApiError(err.detail));
    }
    return res.json() as Promise<{ url: string }>;
  },
};
