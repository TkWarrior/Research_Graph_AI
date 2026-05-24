import React from 'react';
import { X, ExternalLink, Hash, Info, TrendingUp, Layers, Activity } from 'lucide-react';

const NodePanel = ({ node, onClose, onExplore }) => {
  if (!node) return null;

  const centrality = node.centrality || 0;
  const pagerank = node.pagerank || 0;
  const communityId = node.community;
  const communityColor = node.community_color || '#FFFFFF';
  const frequency = node.frequency || null;

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
        {/* Node Identity */}
        <div style={{ marginBottom: '20px' }}>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '1px', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
            <Hash size={14} /> {node.type || 'Entity'}
          </p>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>{node.name}</h2>
        </div>

        {/* Analytics Scores */}
        <div style={{ marginBottom: '20px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          {/* Centrality */}
          <div style={{
            padding: '10px',
            background: 'rgba(255,255,255,0.03)',
            borderRadius: '8px',
            textAlign: 'center',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px', marginBottom: '4px' }}>
              <TrendingUp size={12} color="var(--accent-color)" />
              <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Centrality</span>
            </div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>
              {(centrality * 100).toFixed(1)}%
            </div>
          </div>

          {/* PageRank */}
          <div style={{
            padding: '10px',
            background: 'rgba(255,255,255,0.03)',
            borderRadius: '8px',
            textAlign: 'center',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px', marginBottom: '4px' }}>
              <Activity size={12} color="#4ECDC4" />
              <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>PageRank</span>
            </div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>
              {(pagerank * 1000).toFixed(1)}
            </div>
          </div>

          {/* Community */}
          {communityId !== undefined && communityId !== null && (
            <div style={{
              padding: '10px',
              background: 'rgba(255,255,255,0.03)',
              borderRadius: '8px',
              textAlign: 'center',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px', marginBottom: '4px' }}>
                <Layers size={12} color={communityColor} />
                <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Cluster</span>
              </div>
              <div style={{ fontSize: '1.2rem', fontWeight: 700, color: communityColor }}>
                #{communityId + 1}
              </div>
            </div>
          )}

          {/* Frequency */}
          {frequency !== null && (
            <div style={{
              padding: '10px',
              background: 'rgba(255,255,255,0.03)',
              borderRadius: '8px',
              textAlign: 'center',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px', marginBottom: '4px' }}>
                <Hash size={12} color="#FFE66D" />
                <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Frequency</span>
              </div>
              <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>
                {frequency}
              </div>
            </div>
          )}
        </div>

        {/* Description */}
        {node.description && (
          <div style={{ marginBottom: '24px' }}>
            <h4 style={{ fontSize: '0.9rem', color: 'var(--accent-color)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Info size={16} /> Description
            </h4>
            <p style={{ fontSize: '0.95rem', lineHeight: 1.5, color: '#e0e0e0' }}>
              {node.description}
            </p>
          </div>
        )}

      </div>
    </div>
  );
};

export default NodePanel;
