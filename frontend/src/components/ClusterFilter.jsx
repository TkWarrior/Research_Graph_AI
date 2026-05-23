import React from 'react';
import { Eye, EyeOff, Filter } from 'lucide-react';

const ClusterFilter = ({ clusters = [], hiddenClusters, onToggle }) => {
  if (!clusters || clusters.length < 2) return null;

  return (
    <div className="glass-panel" style={{
      position: 'absolute',
      right: '24px',
      bottom: '24px',
      zIndex: 10,
      padding: '12px 14px',
      minWidth: '180px',
    }}>
      <div style={{ 
        display: 'flex', alignItems: 'center', gap: '6px', 
        marginBottom: '10px', fontSize: '0.75rem', fontWeight: 600,
        textTransform: 'uppercase', letterSpacing: '0.5px',
        color: 'var(--text-secondary)',
      }}>
        <Filter size={13} /> Cluster Filter
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {clusters.map((cluster) => {
          const isHidden = hiddenClusters.has(cluster.id);
          return (
            <button
              key={cluster.id}
              onClick={() => onToggle(cluster.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '6px 8px',
                background: isHidden ? 'rgba(255,255,255,0.02)' : 'rgba(255,255,255,0.06)',
                border: 'none',
                borderRadius: '5px',
                cursor: 'pointer',
                color: isHidden ? 'rgba(255,255,255,0.3)' : '#fff',
                fontSize: '0.78rem',
                transition: 'all 0.2s ease',
                textAlign: 'left',
                opacity: isHidden ? 0.5 : 1,
              }}
            >
              <div style={{
                width: '10px', height: '10px', borderRadius: '50%',
                background: isHidden ? 'rgba(255,255,255,0.15)' : cluster.color,
                flexShrink: 0,
                transition: 'background 0.2s ease',
              }} />
              <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                Cluster {cluster.id + 1}
                <span style={{ color: 'var(--text-secondary)', marginLeft: '4px', fontSize: '0.7rem' }}>
                  ({cluster.size})
                </span>
              </span>
              {isHidden ? <EyeOff size={13} /> : <Eye size={13} />}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default ClusterFilter;
