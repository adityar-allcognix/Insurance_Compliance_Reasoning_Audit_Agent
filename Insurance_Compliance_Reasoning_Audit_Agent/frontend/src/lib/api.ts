const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
  }

  return response;
}

export const api = {
  login: (username: string, password: string) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    return fetch(`${API_BASE_URL}/token`, {
      method: 'POST',
      body: formData,
    });
  },
  getRules: () => fetchWithAuth('/rules/'),
  createRule: (rule: any) => fetchWithAuth('/rules/', {
    method: 'POST',
    body: JSON.stringify(rule),
  }),
  getWorkflows: () => fetchWithAuth('/workflows/'),
  createWorkflow: (workflow: any) => fetchWithAuth('/workflows/', {
    method: 'POST',
    body: JSON.stringify(workflow),
  }),
  auditWorkflow: (workflowId: string) => fetchWithAuth(`/workflows/${workflowId}/audit`, {
    method: 'POST',
  }),
  getAllDecisions: () => fetchWithAuth('/decisions/'),
  getDecisions: (workflowId: string) => fetchWithAuth(`/decisions/${workflowId}`),
  replayDecision: (workflowId: string, decisionId: number) => fetchWithAuth(`/workflows/${workflowId}/replay/${decisionId}`, {
    method: 'POST',
  }),
  getDashboardStats: () => fetchWithAuth('/dashboard/stats'),
  getSystemMetrics: () => fetchWithAuth('/dashboard/metrics'),
  getHealth: () => fetch('/health'), // Public endpoint
  getStructuredRules: (ruleId: string) => fetchWithAuth(`/rules/${ruleId}/structured`),
};
