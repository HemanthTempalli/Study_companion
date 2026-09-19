/** API client — centralized HTTP client for all backend calls */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Don't set Content-Type for FormData
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new ApiError(body.detail || 'Request failed', res.status);
  }

  if (res.status === 204) return {} as T;
  return res.json();
}

// ──────────── Auth ────────────
export const api = {
  auth: {
    register: (data: { email: string; password: string; full_name: string }) =>
      request<{ access_token: string; user: any }>('/api/auth/register', { method: 'POST', body: JSON.stringify(data) }),
    login: (data: { email: string; password: string }) =>
      request<{ access_token: string; user: any }>('/api/auth/login', { method: 'POST', body: JSON.stringify(data) }),
    me: () => request<any>('/api/auth/me'),
  },

  // ──────────── Spaces ────────────
  spaces: {
    list: () => request<any[]>('/api/spaces/'),
    get: (id: string) => request<any>(`/api/spaces/${id}`),
    create: (data: { name: string; description?: string; color?: string; icon?: string }) =>
      request<any>('/api/spaces/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: string, data: any) =>
      request<any>(`/api/spaces/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: string) =>
      request<void>(`/api/spaces/${id}`, { method: 'DELETE' }),
  },

  // ──────────── Projects ────────────
  projects: {
    list: (spaceId?: string) =>
      request<any[]>(`/api/projects/${spaceId ? `?space_id=${spaceId}` : ''}`),
    get: (id: string) => request<any>(`/api/projects/${id}`),
    dashboard: (id: string) => request<any>(`/api/projects/${id}/dashboard`),
    create: (data: { name: string; description?: string; learning_goal?: string; space_id: string }) =>
      request<any>('/api/projects/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: string, data: any) =>
      request<any>(`/api/projects/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: string) =>
      request<void>(`/api/projects/${id}`, { method: 'DELETE' }),
  },

  // ──────────── Materials ────────────
  materials: {
    list: (projectId: string) => request<any[]>(`/api/projects/${projectId}/materials/`),
    upload: (projectId: string, file: File) => {
      const form = new FormData();
      form.append('file', file);
      return request<any>(`/api/projects/${projectId}/materials/`, { method: 'POST', body: form });
    },
    delete: (projectId: string, materialId: string) =>
      request<void>(`/api/projects/${projectId}/materials/${materialId}`, { method: 'DELETE' }),
    retry: (projectId: string, materialId: string) =>
      request<any>(`/api/projects/${projectId}/materials/${materialId}/retry`, { method: 'POST' }),
  },

  // ──────────── Tutor ────────────
  tutor: {
    chat: (projectId: string, data: { message: string; conversation_id?: string }) =>
      request<any>(`/api/projects/${projectId}/tutor/chat`, { method: 'POST', body: JSON.stringify(data) }),
    conversations: (projectId: string) =>
      request<any[]>(`/api/projects/${projectId}/tutor/conversations`),
    messages: (projectId: string, conversationId: string) =>
      request<any[]>(`/api/projects/${projectId}/tutor/conversations/${conversationId}/messages`),
  },

  // ──────────── Quiz ────────────
  quiz: {
    generate: (projectId: string, data: { num_questions?: number; difficulty?: string }) =>
      request<any>(`/api/projects/${projectId}/quiz/generate`, { method: 'POST', body: JSON.stringify(data) }),
    submit: (projectId: string, quizId: string, answers: any[]) =>
      request<any>(`/api/projects/${projectId}/quiz/${quizId}/submit`, { method: 'POST', body: JSON.stringify(answers) }),
    history: (projectId: string) =>
      request<any[]>(`/api/projects/${projectId}/quiz/history`),
  },

  // ──────────── Mastery ────────────
  mastery: {
    get: (projectId: string) => request<any[]>(`/api/projects/${projectId}/mastery`),
    growth: (projectId: string) => request<any>(`/api/projects/${projectId}/growth`),
  },

  // ──────────── Recommendations ────────────
  recommendations: {
    list: (projectId: string) => request<any[]>(`/api/projects/${projectId}/recommendations/`),
    generate: (projectId: string) =>
      request<any>(`/api/projects/${projectId}/recommendations/generate`, { method: 'POST' }),
    dismiss: (projectId: string, recId: string) =>
      request<void>(`/api/projects/${projectId}/recommendations/${recId}/dismiss`, { method: 'POST' }),
  },

  // ──────────── Analytics ────────────
  analytics: {
    project: (projectId: string) => request<any>(`/api/projects/${projectId}/analytics`),
    global: () => request<any>('/api/admin/analytics'),
  },

  // ──────────── Admin ────────────
  admin: {
    users: () => request<any[]>('/api/admin/users'),
    userJourney: (userId: string) => request<any>(`/api/admin/users/${userId}/journey`),
    projects: (userId?: string) => request<any[]>(`/api/admin/projects${userId ? `?user_id=${userId}` : ''}`),
    health: () => request<any>('/api/admin/health'),
    aiLogs: (limit: number = 50, feature?: string, model?: string, status?: string) => {
      const params = new URLSearchParams({ limit: limit.toString() });
      if (feature) params.append('feature', feature);
      if (model) params.append('model', model);
      if (status) params.append('status', status);
      return request<any[]>(`/api/admin/ai-logs?${params.toString()}`);
    },
    evaluations: (limit: number = 50, feature?: string, passed?: boolean) => {
      const params = new URLSearchParams({ limit: limit.toString() });
      if (feature) params.append('feature', feature);
      if (passed !== undefined) params.append('passed', passed.toString());
      return request<any[]>(`/api/admin/evaluations?${params.toString()}`);
    },
    jobs: (status?: string, jobType?: string, limit: number = 50) => {
      const params = new URLSearchParams({ limit: limit.toString() });
      if (status) params.append('status', status);
      if (jobType) params.append('job_type', jobType);
      return request<any[]>(`/api/admin/jobs?${params.toString()}`);
    },
    makeAdmin: (userId: string) =>
      request<any>(`/api/admin/make-admin/${userId}`, { method: 'POST' }),
  },
};

export { ApiError };
export default api;
