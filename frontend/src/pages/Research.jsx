import React, { useState, useEffect, useCallback } from 'react';
import ChatHistory from '../components/ChatHistory';
import ChatInterface from '../components/ChatInterface';
import { api } from '../services/api';
import { useWorkspace } from '../context/WorkspaceContext';

const Research = () => {
  const { activeWorkspace } = useWorkspace();
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);

  // Reload sessions whenever the active workspace changes
  const loadSessions = useCallback(async () => {
    if (!activeWorkspace?.id) {
      setSessions([]);
      return;
    }
    setIsLoadingSessions(true);
    try {
      const data = await api.getSessions(activeWorkspace.id);
      setSessions(data.sessions || []);
    } catch (err) {
      console.error('Failed to load chat sessions:', err);
    } finally {
      setIsLoadingSessions(false);
    }
  }, [activeWorkspace?.id]);

  // Wipe session state immediately on workspace switch
  useEffect(() => {
    setCurrentSessionId(null);
    setSessions([]);
  }, [activeWorkspace?.id]);

  // Then fetch sessions for the new workspace
  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  const handleNewSession = () => {
    setCurrentSessionId(null);
  };

  const handleSelectSession = (id) => {
    setCurrentSessionId(id);
  };

  const handleDeleteSession = async (id) => {
    try {
      await api.deleteSession(id);
      if (currentSessionId === id) setCurrentSessionId(null);
      loadSessions();
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  };

  // Called by ChatInterface when a new session is auto-created on first message
  const handleSessionCreated = (id) => {
    setCurrentSessionId(id);
    loadSessions();   // ← refresh list so the new session appears immediately
  };

  return (
    <div style={{ height: 'calc(100vh - 80px)', display: 'flex', padding: '0 24px 24px 24px' }}>
      <div className="glass-panel" style={{ display: 'flex', width: '100%', height: '100%', overflow: 'hidden', padding: 0 }}>

        <ChatHistory
          sessions={sessions}
          currentSessionId={currentSessionId}
          onSelect={handleSelectSession}
          onNew={handleNewSession}
          onDelete={handleDeleteSession}
          isLoading={isLoadingSessions}
        />

        <ChatInterface
          sessionId={currentSessionId}
          onNewSessionCreated={handleSessionCreated}
        />

      </div>
    </div>
  );
};

export default Research;
