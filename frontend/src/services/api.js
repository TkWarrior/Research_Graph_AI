import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // Document Upload
  uploadDocument: async (file, onUploadProgress) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post('/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress
    });
    return response.data;
  },

  // Q&A / Ask
  askQuestion: async (question, documentId = null, sessionId = null) => {
    const response = await apiClient.post('/ask/', {
      question,
      document_id: documentId,
      session_id: sessionId
    });
    return response.data;
  },

  // Research Query
  runResearchQuery: async (query) => {
    const response = await apiClient.post('/query/', { query });
    return response.data;
  },

  // Graph
  getGraph: async (limit = 500) => {
    const response = await apiClient.get(`/graph/?limit=${limit}`);
    return response.data;
  },
  
  getSubgraph: async (nodeName, depth = 2) => {
    const response = await apiClient.get(`/graph/subgraph/${encodeURIComponent(nodeName)}?depth=${depth}`);
    return response.data;
  },
  
  getGraphStats: async () => {
    const response = await apiClient.get('/graph/stats');
    return response.data;
  },

  // Graph Snapshots
  getSnapshots: async (documentId) => {
    const response = await apiClient.get(`/graph/snapshots/${documentId}`);
    return response.data;
  },
  
  getLatestSnapshot: async (documentId) => {
    const response = await apiClient.get(`/graph/snapshots/${documentId}/latest`);
    return response.data;
  },

  // Insights
  getInsights: async () => {
    const response = await apiClient.get('/insights/');
    return response.data;
  },

  // Chat Sessions
  getSessions: async (skip = 0, limit = 50) => {
    const response = await apiClient.get(`/sessions/?skip=${skip}&limit=${limit}`);
    return response.data;
  },
  
  getSession: async (sessionId) => {
    const response = await apiClient.get(`/sessions/${sessionId}`);
    return response.data;
  },
  
  createSession: async (title = null, documentId = null) => {
    const response = await apiClient.post('/sessions/', { title, document_id: documentId });
    return response.data;
  },
  
  renameSession: async (sessionId, title) => {
    const response = await apiClient.patch(`/sessions/${sessionId}`, { title });
    return response.data;
  },
  
  deleteSession: async (sessionId) => {
    const response = await apiClient.delete(`/sessions/${sessionId}`);
    return response.data;
  }
};
