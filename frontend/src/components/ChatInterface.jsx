import React, { useState, useEffect, useRef } from 'react';
import { Send, User, Bot, AlertTriangle, Layers } from 'lucide-react';
import { api } from '../services/api';
import { useWorkspace } from '../context/WorkspaceContext';

const ChatInterface = ({ sessionId, onNewSessionCreated }) => {
  const { activeWorkspace } = useWorkspace();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [currentSession, setCurrentSession] = useState(sessionId);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    setCurrentSession(sessionId);
  }, [sessionId]);

  useEffect(() => {
    if (sessionId) {
      loadSession(sessionId);
    } else {
      setMessages([]);
      setCurrentSession(null);
    }
  }, [sessionId]);

  const loadSession = async (id) => {
    try {
      const data = await api.getSession(id);
      setMessages(data.messages || []);
      setCurrentSession(id);
    } catch (err) {
      console.error("Failed to load session:", err);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const query = input.trim();
    setInput("");
    
    // Add optimistic user message
    const tempUserMsg = { id: Date.now().toString(), role: 'user', content: query };
    setMessages(prev => [...prev, tempUserMsg]);
    setIsLoading(true);

    try {
      const res = await api.askQuestion(query, activeWorkspace?.id, currentSession);
      
      // If a new session was created on the backend, update our state
      if (!currentSession && res.session_id) {
        setCurrentSession(res.session_id);
        if (onNewSessionCreated) onNewSessionCreated(res.session_id);
      }
      
      // Add assistant response
      const tempAsstMsg = { 
        id: (Date.now()+1).toString(), 
        role: 'assistant', 
        content: res.answer,
        sources: res.sources,
        graph_context: res.graph_context
      };
      setMessages(prev => [...prev, tempAsstMsg]);
      
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { 
        id: Date.now().toString(), 
        role: 'system', 
        content: `Error: ${err.response?.data?.detail || "Failed to get an answer."}` 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', flex: 1, background: 'rgba(10, 10, 26, 0.4)' }}>
      {/* Chat Messages Area */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
        {messages.length === 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-secondary)' }}>
            <Bot size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
            <h3 style={{ fontSize: '1.2rem', marginBottom: '8px', color: 'white' }}>How can I help you research?</h3>
            <p style={{ maxWidth: '400px', textAlign: 'center', fontSize: '0.9rem' }}>
              Ask any question about your uploaded documents. I'll use both semantic search and the knowledge graph to find the answer.
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '800px', margin: '0 auto' }}>
            {messages.map((msg, idx) => (
              <div key={msg.id || idx} style={{ display: 'flex', gap: '16px' }}>
                <div style={{ 
                  width: '36px', height: '36px', borderRadius: '50%', flexShrink: 0,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  background: msg.role === 'user' ? 'rgba(255,255,255,0.1)' : msg.role === 'system' ? '#FF6B6B' : 'var(--accent-gradient)'
                }}>
                  {msg.role === 'user' ? <User size={18} /> : msg.role === 'system' ? <AlertTriangle size={18} color="white" /> : <Bot size={18} color="white" />}
                </div>
                
                <div style={{ flex: 1, paddingTop: '6px' }}>
                  <div style={{ fontWeight: 600, marginBottom: '8px', fontSize: '0.9rem', color: msg.role === 'user' ? 'var(--text-secondary)' : 'var(--accent-color)' }}>
                    {msg.role === 'user' ? 'You' : msg.role === 'system' ? 'System Error' : 'Research Agent'}
                  </div>
                  
                  {/* Message Content */}
                  <div style={{ lineHeight: 1.6, fontSize: '0.95rem', whiteSpace: 'pre-wrap' }}>
                    {msg.content}
                  </div>
                  
                  {/* Sources & Context (if any) */}
                  {(msg.sources?.length > 0 || msg.graph_context?.length > 0) && (
                    <div style={{ marginTop: '16px', padding: '12px', background: 'rgba(0,0,0,0.3)', borderRadius: '8px', border: '1px solid var(--glass-border)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: 'var(--text-secondary)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
                        <Layers size={14} /> Sources Utilized
                      </div>
                      <div style={{ display: 'flex', gap: '12px', fontSize: '0.85rem' }}>
                        {msg.sources?.length > 0 && <span>• {msg.sources.length} Text Chunks</span>}
                        {msg.graph_context?.length > 0 && <span>• {msg.graph_context.length} Graph Sub-networks</span>}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div style={{ display: 'flex', gap: '16px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '50%', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--accent-gradient)' }}>
                  <Bot size={18} color="white" />
                </div>
                <div style={{ paddingTop: '6px', color: 'var(--text-secondary)' }}>
                  <div className="typing-indicator">
                    <span></span><span></span><span></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div style={{ padding: '20px', borderTop: '1px solid var(--glass-border)' }}>
        <form onSubmit={handleSubmit} style={{ maxWidth: '800px', margin: '0 auto', position: 'relative' }}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about the documents..."
            disabled={isLoading}
            style={{
              width: '100%',
              padding: '16px 56px 16px 20px',
              borderRadius: '12px',
              border: '1px solid var(--glass-border)',
              background: 'rgba(255,255,255,0.05)',
              color: 'white',
              fontSize: '1rem',
              outline: 'none',
              transition: 'border 0.2s',
            }}
            onFocus={(e) => e.target.style.borderColor = 'var(--accent-color)'}
            onBlur={(e) => e.target.style.borderColor = 'var(--glass-border)'}
          />
          <button 
            type="submit" 
            disabled={!input.trim() || isLoading}
            style={{
              position: 'absolute',
              right: '12px',
              top: '50%',
              transform: 'translateY(-50%)',
              background: input.trim() && !isLoading ? 'var(--accent-gradient)' : 'rgba(255,255,255,0.1)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              width: '36px',
              height: '36px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: input.trim() && !isLoading ? 'pointer' : 'not-allowed',
              transition: 'all 0.2s'
            }}
          >
            <Send size={16} />
          </button>
        </form>
      </div>
      <style>{`
        .typing-indicator span {
          display: inline-block;
          width: 6px;
          height: 6px;
          background-color: var(--accent-color);
          border-radius: 50%;
          margin-right: 4px;
          animation: bounce 1.4s infinite ease-in-out both;
        }
        .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
        .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0); }
          40% { transform: scale(1); }
        }
      `}</style>
    </div>
  );
};

export default ChatInterface;
