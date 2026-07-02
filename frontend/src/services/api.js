const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
const AUTH_BASE_URL = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL.replace('/api', '/auth')
  : 'http://localhost:8000/auth';

const authHeaders = () => {
  const token = localStorage.getItem('token');
  
  let aiModel = '';
  let googleApiKey = '';
  let groqApiKey = '';
  
  try {
    const settings = JSON.parse(localStorage.getItem('tg_settings') || '{}');
    aiModel = settings.aiModel || '';
    googleApiKey = settings.googleApiKey || '';
    groqApiKey = settings.groqApiKey || '';
    
    if (aiModel.includes('llama3-')) {
      aiModel = aiModel.includes('70b') ? 'llama-3.3-70b-versatile' : 'llama-3.1-8b-instant';
    }
  } catch (e) {}
  
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (aiModel) headers['X-AI-Model'] = aiModel;
  if (googleApiKey) headers['X-Google-API-Key'] = googleApiKey;
  if (groqApiKey) headers['X-Groq-API-Key'] = groqApiKey;
  
  return headers;
};

/**
 * Global response handler — auto-logout on 401, throw on errors.
 */
const handleResponse = async (r) => {
  if (r.status === 401) {
    localStorage.removeItem('token');
    window.location.href = '/';
    throw new Error('Session expired. Please login again.');
  }
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: `HTTP ${r.status}` }));
    throw new Error(err.detail || `Request failed (${r.status})`);
  }
  return r.json();
};

export const apiService = {

  // ── Authentication ──────────────────────────────────────────────────────
  async login(username, password) {
    const r = await fetch(`${AUTH_BASE_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    return handleResponse(r);
  },

  async register(username, email, password, role = 'qa') {
    const r = await fetch(`${AUTH_BASE_URL}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password, role }),
    });
    return handleResponse(r);
  },

  async forgotPassword(email) {
    const r = await fetch(`${AUTH_BASE_URL}/forgot-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    return handleResponse(r);
  },

  // ── Users (Admin Only) ──────────────────────────────────────────────────
  async getUsers() {
    const r = await fetch(`${API_BASE_URL}/users`, { headers: authHeaders() });
    return handleResponse(r);
  },


  async createUser(data) {
    const r = await fetch(`${API_BASE_URL}/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(data),
    });
    return handleResponse(r);
  },

  async updateUser(id, data) {
    const r = await fetch(`${API_BASE_URL}/users/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(data),
    });
    return handleResponse(r);
  },

  async deleteUser(id) {
    const r = await fetch(`${API_BASE_URL}/users/${id}`, {
      method: 'DELETE',
      headers: authHeaders(),
    });
    return handleResponse(r);
  },

  // ── Projects ────────────────────────────────────────────────────────────
  async getProjects() {
    const r = await fetch(`${API_BASE_URL}/projects`, { headers: authHeaders() });
    return handleResponse(r);
  },

  async createProject(name, description) {
    const r = await fetch(`${API_BASE_URL}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ name, description }),
    });
    return handleResponse(r);
  },

  async createGithubProject(data) {
    const r = await fetch(`${API_BASE_URL}/projects/github/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(data),
    });
    return handleResponse(r);
  },


  async getDashboardProjects() {
    const r = await fetch(`${API_BASE_URL}/dashboard/projects`, { headers: authHeaders() });
    return handleResponse(r);
  },

  // ── Requirements ────────────────────────────────────────────────────────
  async getRequirements() {
    const r = await fetch(`${API_BASE_URL}/requirements`, { headers: authHeaders() });
    return handleResponse(r);
  },

  async uploadRequirement(data) {
    const params = new URLSearchParams({
      title: data.title,
      content: data.content,
      type: data.type,
      project_id: data.project_id || 1,
    });
    const r = await fetch(`${API_BASE_URL}/requirements/upload?${params}`, {
      method: 'POST',
      headers: authHeaders(),
    });
    return handleResponse(r);
  },

  async updateRequirement(id, data) {
    const r = await fetch(`${API_BASE_URL}/requirements/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(data),
    });
    return handleResponse(r);
  },

  async deleteRequirement(id) {
    const r = await fetch(`${API_BASE_URL}/requirements/${id}`, {
      method: 'DELETE',
      headers: authHeaders(),
    });
    return handleResponse(r);
  },

  // ── Jira Ingestion ───────────────────────────────────────────────────────
  async ingestJira(jiraUrl, projectId = 1) {
    const r = await fetch(`${API_BASE_URL}/ingest/jira`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ jira_url: jiraUrl, project_id: projectId }),
    });
    return handleResponse(r);
  },

  // ── AI Analysis ─────────────────────────────────────────────────────────
  async analyzeRequirement(id) {
    const r = await fetch(`${API_BASE_URL}/analyze/${id}`, {
      method: 'POST',
      headers: authHeaders(),
    });
    return handleResponse(r);
  },

  // ── Scenarios & Scripts ─────────────────────────────────────────────────
  async getScenarios(requirementId) {
    const validId = (requirementId && typeof requirementId !== 'object') ? requirementId : null;
    const url = validId
      ? `${API_BASE_URL}/scenarios?requirement_id=${validId}`
      : `${API_BASE_URL}/scenarios`;
    const r = await fetch(url, { headers: authHeaders() });
    return handleResponse(r);
  },

  async updateScenario(id, data) {
    const r = await fetch(`${API_BASE_URL}/scenarios/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(data),
    });
    return handleResponse(r);
  },

  async generateScenarioCode(id) {
    const r = await fetch(`${API_BASE_URL}/scenarios/${id}/generate-code`, {
      method: 'POST',
      headers: authHeaders(),
    });
    return handleResponse(r);
  },

  async pushToGithub(id) {
    const r = await fetch(`${API_BASE_URL}/scenarios/${id}/push-github`, {
      method: 'POST',
      headers: authHeaders(),
    });
    return handleResponse(r);
  },

  async getScript(scenarioId) {
    const r = await fetch(`${API_BASE_URL}/scripts/${scenarioId}`, { headers: authHeaders() });
    return handleResponse(r);
  },

  // ── Executions ──────────────────────────────────────────────────────────
  async executeTest(scriptId) {
    const r = await fetch(`${API_BASE_URL}/execute/${scriptId}`, {
      method: 'POST',
      headers: authHeaders(),
    });
    return handleResponse(r);
  },

  async getExecutions() {
    const r = await fetch(`${API_BASE_URL}/executions`, { headers: authHeaders() });
    return handleResponse(r);
  },

  // ── Traceability ────────────────────────────────────────────────────────
  async getTraceability() {
    const r = await fetch(`${API_BASE_URL}/traceability`, { headers: authHeaders() });
    return handleResponse(r);
  },

  // ── Dashboard ───────────────────────────────────────────────────────────
  async getDashboardStats() {
    const r = await fetch(`${API_BASE_URL}/dashboard/stats`, { headers: authHeaders() });
    return handleResponse(r);
  },

  async getActivityFeed() {
    const r = await fetch(`${API_BASE_URL}/dashboard/activity`, { headers: authHeaders() });
    return handleResponse(r);
  },

  // ── Reports & CI ────────────────────────────────────────────────────────
  async exportReport(projectId) {
    const r = await fetch(`${API_BASE_URL}/reports/export/${projectId || 1}`, { headers: authHeaders() });
    if (r.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/';
      throw new Error('Session expired. Please login again.');
    }
    if (!r.ok) throw new Error(`Export failed (${r.status})`);
    
    const blob = await r.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `SmartTestAccelerator_Report_${projectId || 1}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  },

  async exportGitlabCI() {
    window.open(`${API_BASE_URL}/ci/gitlab`, '_blank');
  },

  // ── GitLab Project Push ─────────────────────────────────────────────────
  async pushToGitLab(scenarioId, projectName, namespace) {
    const r = await fetch(`${API_BASE_URL}/gitlab/push`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({
        scenario_id: scenarioId,
        project_name: projectName || undefined,
        gitlab_namespace: namespace || undefined,
      }),
    });
    return handleResponse(r);
  },

  // ── AI Review (Valider/Review workflow) ──────────────────────────────────
  async reviewScenario(content, prompt) {
    const r = await fetch(`${API_BASE_URL}/ai/review-scenario`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ content, prompt, type: 'gherkin' }),
    });
    return handleResponse(r);
  },

  async reviewCode(content, prompt) {
    const r = await fetch(`${API_BASE_URL}/ai/review-code`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ content, prompt, type: 'code' }),
    });
    return handleResponse(r);
  },

  // ── PDF Upload ──────────────────────────────────────────────────────────
  async uploadPdf(file) {
    const formData = new FormData();
    formData.append('file', file);
    const r = await fetch(`${API_BASE_URL}/ingest/upload-pdf`, {
      method: 'POST',
      headers: authHeaders(),
      body: formData,
    });
    return handleResponse(r);
  },
};
