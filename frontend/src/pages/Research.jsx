import React, { useState, useEffect } from 'react';
import ChatHistory from '../components/ChatHistory';
import ChatInterface from '../components/ChatInterface';
import { api } from '../services/api';

const Research = () => {
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const data = await api.getSessions();
      setSessions(data.sessions || []);
    } catch (err) {
      console.error("Failed to load chat sessions:", err);
    }
  };

  const handleNewSession = () => {
    setCurrentSessionId(null);
  };

  const handleSelectSession = (id) => {
    setCurrentSessionId(id);
  };

  const handleDeleteSession = async (id) => {
    try {
      await api.deleteSession(id);
      if (currentSessionId === id) {
        setCurrentSessionId(null);
      }
      loadSessions();
    } catch (err) {
      console.error("Failed to delete session:", err);
    }
  };

  const handleSessionCreated = (id) => {
    setCurrentSessionId(id);
    loadSessions(); // Refresh list to show new session
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
