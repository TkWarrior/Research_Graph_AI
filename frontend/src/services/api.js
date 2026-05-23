import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token automatically to every request
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const api = {
  // ── Auth ─────────────────────────────────────────────────────────
  signup: async (full_name, email, password) => {
    const res = await apiClient.post('/auth/signup', { full_name, email, password });
    return res.data;
  },
  signin: async (email, password) => {
    const res = await apiClient.post('/auth/signin', { email, password });
    return res.data;
  },
  getMe: async (token) => {
    const res = await apiClient.get('/auth/me', {
      headers: { Authorization: `Bearer ${token}` },
    });
    return res.data;
  },

  // ── Workspaces ────────────────────────────────────────────────────
  getWorkspaces: async (skip = 0, limit = 50) => {
    const res = await apiClient.get(`/workspaces/?skip=${skip}&limit=${limit}`);
    return res.data;
  },
  getWorkspace: async (workspaceId) => {
    const res = await apiClient.get(`/workspaces/${workspaceId}`);
    return res.data;
  },
  createWorkspace: async ({ name, description = '' }) => {
    const res = await apiClient.post('/workspaces/', { name, description });
    return res.data;
  },
  updateWorkspace: async (workspaceId, { name, description }) => {
    const res = await apiClient.patch(`/workspaces/${workspaceId}`, { name, description });
    return res.data;
  },
  deleteWorkspace: async (workspaceId) => {
    const res = await apiClient.delete(`/workspaces/${workspaceId}`);
    return res.data;
  },

  // ── Document Upload ───────────────────────────────────────────────
  uploadDocument: async (file, workspaceId, onUploadProgress, graphMode = 'cooccurrence') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('workspace_id', workspaceId);
    formData.append('graph_mode', graphMode);
    const res = await apiClient.post('/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress,
    });
    return res.data;
  },

  getDocuments: async (workspaceId = null) => {
    let url = '/upload/documents';
    if (workspaceId) url += `?workspace_id=${workspaceId}`;
    const res = await apiClient.get(url);
    return res.data;
  },

  // ── Q&A ──────────────────────────────────────────────────────────
  askQuestion: async (question, workspaceId, sessionId = null) => {
    const res = await apiClient.post('/ask/', {
      question,
      workspace_id: workspaceId,
      session_id: sessionId,
    });
    return res.data;
  },

  // ── Research Query ────────────────────────────────────────────────
  runResearchQuery: async (query, workspaceId) => {
    const res = await apiClient.post('/query/', { 
      query, 
      workspace_id: workspaceId 
    });
    return res.data;
  },

  // ── Graph (Neo4j) — all require workspace_id ──────────────────────
  getGraph: async (limit = 500, workspaceId) => {
    const res = await apiClient.get(`/graph/?limit=${limit}&workspace_id=${workspaceId}`);
    return res.data;
  },
  getSubgraph: async (nodeName, depth = 2, workspaceId) => {
    const res = await apiClient.get(
      `/graph/subgraph/${encodeURIComponent(nodeName)}?depth=${depth}&workspace_id=${workspaceId}`
    );
    return res.data;
  },
  getGraphStats: async (workspaceId) => {
    const res = await apiClient.get(`/graph/stats?workspace_id=${workspaceId}`);
    return res.data;
  },
  deleteDocumentGraph: async (documentId) => {
    const res = await apiClient.delete(`/graph/document/${documentId}`);
    return res.data;
  },

  // ── Graph Snapshots ───────────────────────────────────────────────
  getSnapshots: async (workspaceId) => {
    const res = await apiClient.get(`/graph/snapshots/${workspaceId}`);
    return res.data;
  },
  getLatestSnapshot: async (workspaceId) => {
    const res = await apiClient.get(`/graph/snapshots/${workspaceId}/latest`);
    return res.data;
  },

  // ── Insights ─────────────────────────────────────────────────────
  getInsights: async (workspaceId) => {
    const res = await apiClient.get(`/insights/?workspace_id=${workspaceId}`);
    return res.data;
  },
  getBridgeQuestions: async (workspaceId, gapIndex = 0) => {
    const res = await apiClient.get(`/insights/bridge?workspace_id=${workspaceId}&gap_index=${gapIndex}`);
    return res.data;
  },
  getBlindSpots: async (workspaceId) => {
    const res = await apiClient.get(`/insights/blind-spots?workspace_id=${workspaceId}`);
    return res.data;
  },

  // ── Chat Sessions ─────────────────────────────────────────────────
  getSessions: async (workspaceId = null, skip = 0, limit = 50) => {
    let url = `/sessions/?skip=${skip}&limit=${limit}`;
    if (workspaceId) url += `&workspace_id=${workspaceId}`;
    const res = await apiClient.get(url);
    return res.data;
  },
  getSession: async (sessionId) => {
    const res = await apiClient.get(`/sessions/${sessionId}`);
    return res.data;
  },
  createSession: async (workspaceId, title = null) => {
    const res = await apiClient.post('/sessions/', { workspace_id: workspaceId, title });
    return res.data;
  },
  renameSession: async (sessionId, title) => {
    const res = await apiClient.patch(`/sessions/${sessionId}`, { title });
    return res.data;
  },
  deleteSession: async (sessionId) => {
    const res = await apiClient.delete(`/sessions/${sessionId}`);
    return res.data;
  },

  // ── Analytics ────────────────────────────────────────────────────
  getFullAnalysis: async (limit = 1000, workspaceId) => {
    const res = await apiClient.get(`/analytics/full?limit=${limit}&workspace_id=${workspaceId}`);
    return res.data;
  },
  getCentrality: async (topN = 20, workspaceId) => {
    const res = await apiClient.get(`/analytics/centrality?top_n=${topN}&workspace_id=${workspaceId}`);
    return res.data;
  },
  getCommunities: async (workspaceId) => {
    const res = await apiClient.get(`/analytics/communities?workspace_id=${workspaceId}`);
    return res.data;
  },
  getStructuralGaps: async (maxGaps = 5, workspaceId) => {
    const res = await apiClient.get(`/analytics/gaps?max_gaps=${maxGaps}&workspace_id=${workspaceId}`);
    return res.data;
  },
  getNetworkStats: async (workspaceId) => {
    const res = await apiClient.get(`/analytics/stats?workspace_id=${workspaceId}`);
    return res.data;
  },
  getGraphWithAnalytics: async (limit = 1000, workspaceId) => {
    const res = await apiClient.get(`/analytics/graph-with-analytics?limit=${limit}&workspace_id=${workspaceId}`);
    return res.data;
  },

  // ── Direct Text Input ─────────────────────────────────────────────
  analyzeText: async (text, options = {}) => {
    const res = await apiClient.post('/text-input/', {
      text,
      window_size: options.windowSize || 5,
      min_weight: options.minWeight || 2,
      persist: options.persist || false,
    });
    return res.data;
  },
};
