/**
 * Workspace React Context
 *
 * Provides the active workspace to the entire component tree so that
 * workspace_id never needs to be passed as a prop through every layer.
 *
 * Usage:
 *   const { activeWorkspace, setActiveWorkspace, workspaces, refreshWorkspaces } = useWorkspace();
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

const WorkspaceContext = createContext(null);

export const WorkspaceProvider = ({ children }) => {
  const [workspaces, setWorkspaces] = useState([]);
  const [activeWorkspace, setActiveWorkspaceState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refreshWorkspaces = useCallback(async () => {
    try {
      const data = await api.getWorkspaces();
      setWorkspaces(data.workspaces || []);

      // Re-validate active workspace still exists after a refresh
      setActiveWorkspaceState(prev => {
        if (!prev) return prev;
        const stillExists = (data.workspaces || []).find(w => w.id === prev.id);
        return stillExists || (data.workspaces?.[0] ?? null);
      });
    } catch (err) {
      console.error('Failed to fetch workspaces:', err);
      setError('Could not load workspaces.');
    } finally {
      setLoading(false);
    }
  }, []);

  // Load workspaces on mount
  useEffect(() => {
    refreshWorkspaces();
  }, [refreshWorkspaces]);

  // Persist active workspace ID to localStorage so it survives page refresh
  useEffect(() => {
    if (activeWorkspace) {
      localStorage.setItem('activeWorkspaceId', activeWorkspace.id);
    }
  }, [activeWorkspace]);

  // Restore persisted selection after workspaces load
  useEffect(() => {
    if (workspaces.length === 0) return;

    const saved = localStorage.getItem('activeWorkspaceId');
    if (saved) {
      const found = workspaces.find(w => w.id === saved);
      if (found) {
        setActiveWorkspaceState(found);
        return;
      }
    }
    // Default to first workspace if nothing saved or saved ws was deleted
    setActiveWorkspaceState(workspaces[0]);
  }, [workspaces]);

  const setActiveWorkspace = useCallback((workspace) => {
    setActiveWorkspaceState(workspace);
  }, []);

  const createWorkspace = useCallback(async (name, description = '') => {
    const created = await api.createWorkspace({ name, description });
    await refreshWorkspaces();
    setActiveWorkspaceState(created);
    return created;
  }, [refreshWorkspaces]);

  const deleteWorkspace = useCallback(async (workspaceId) => {
    await api.deleteWorkspace(workspaceId);
    await refreshWorkspaces();
    // If we deleted the active one, fall through to the useEffect above which picks workspaces[0]
    setActiveWorkspaceState(prev => prev?.id === workspaceId ? null : prev);
  }, [refreshWorkspaces]);

  const renameWorkspace = useCallback(async (workspaceId, name) => {
    const updated = await api.updateWorkspace(workspaceId, { name });
    await refreshWorkspaces();
    // If we renamed the active one, update the active reference too
    setActiveWorkspaceState(prev => prev?.id === workspaceId ? updated : prev);
    return updated;
  }, [refreshWorkspaces]);

  return (
    <WorkspaceContext.Provider value={{
      workspaces,
      activeWorkspace,
      setActiveWorkspace,
      createWorkspace,
      deleteWorkspace,
      renameWorkspace,
      refreshWorkspaces,
      loading,
      error,
    }}>
      {children}
    </WorkspaceContext.Provider>
  );
};

export const useWorkspace = () => {
  const ctx = useContext(WorkspaceContext);
  if (!ctx) throw new Error('useWorkspace must be used inside <WorkspaceProvider>');
  return ctx;
};
