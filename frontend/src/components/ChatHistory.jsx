import React from 'react';
import { MessageSquare, Plus, Trash2 } from 'lucide-react';

const ChatHistory = ({ sessions, currentSessionId, onSelect, onNew, onDelete, isLoading }) => {
  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '280px', flexShrink: 0, borderRadius: '16px 0 0 16px', borderRight: '1px solid var(--glass-border)' }}>
      <div style={{ padding: '20px', borderBottom: '1px solid var(--glass-border)' }}>
        <button 
          className="btn-primary" 
          onClick={onNew}
          style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
        >
          <Plus size={18} /> New Research Chat
        </button>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 12px' }}>
        <h4 style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '12px', paddingLeft: '8px' }}>
          Recent Sessions
        </h4>
        
        {isLoading ? (
          <div style={{ display: 'flex', justifyContent: 'center', marginTop: '40px' }}>
            <div className="spinner" style={{ width: '24px', height: '24px', border: '2px solid rgba(255,255,255,0.1)', borderTop: '2px solid var(--accent-color)', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
          </div>
        ) : sessions.length === 0 ? (
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', textAlign: 'center', marginTop: '20px' }}>No research chats here yet.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {sessions.map(session => (
              <div 
                key={session.id}
                onClick={() => onSelect(session.id)}
                style={{
                  padding: '12px',
                  borderRadius: '8px',
                  background: currentSessionId === session.id ? 'rgba(255,255,255,0.1)' : 'transparent',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  transition: 'background 0.2s',
                  border: currentSessionId === session.id ? '1px solid rgba(255,255,255,0.1)' : '1px solid transparent'
                }}
                onMouseEnter={(e) => {
                  if (currentSessionId !== session.id) e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
                }}
                onMouseLeave={(e) => {
                  if (currentSessionId !== session.id) e.currentTarget.style.background = 'transparent';
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', overflow: 'hidden' }}>
                  <MessageSquare size={16} color="var(--text-secondary)" />
                  <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontSize: '0.9rem' }}>
                    {session.title || "Untitled Chat"}
                  </span>
                </div>
                
                <button 
                  className="btn-icon" 
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(session.id);
                  }}
                  style={{ padding: '4px' }}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatHistory;
