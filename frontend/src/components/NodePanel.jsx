import React from 'react';
import { X, ExternalLink, Hash, Info } from 'lucide-react';

const NodePanel = ({ node, onClose, onExplore }) => {
  if (!node) return null;

  return (
    <div className="glass-panel" style={{
      position: 'absolute',
      right: '24px',
      top: '24px',
      width: '320px',
      maxHeight: 'calc(100vh - 120px)',
      overflowY: 'auto',
      zIndex: 10,
      padding: '0'
    }}>
      <div style={{ 
        padding: '16px', 
        borderBottom: '1px solid var(--glass-border)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 600, margin: 0 }}>Node Details</h3>
        <button onClick={onClose} className="btn-icon">
          <X size={20} />
        </button>
      </div>

      <div style={{ padding: '20px 16px' }}>
        <div style={{ marginBottom: '20px' }}>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '1px', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
            <Hash size={14} /> {node.type || 'Entity'}
          </p>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>{node.name}</h2>
        </div>

        <div style={{ marginBottom: '24px' }}>
          <h4 style={{ fontSize: '0.9rem', color: 'var(--accent-color)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Info size={16} /> Description
          </h4>
          <p style={{ fontSize: '0.95rem', lineHeight: 1.5, color: '#e0e0e0' }}>
            {node.description || 'No description available for this entity.'}
          </p>
        </div>

        <button 
          className="btn-primary" 
          style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
          onClick={() => onExplore(node.name)}
        >
          <ExternalLink size={16} /> Explore Neighborhood
        </button>
      </div>
    </div>
  );
};

export default NodePanel;
