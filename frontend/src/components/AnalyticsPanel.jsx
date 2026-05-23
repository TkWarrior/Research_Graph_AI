import React, { useState } from 'react';
import { BarChart3, TrendingUp, Circle, Zap, Network, Layers, Brain, Lightbulb, Search } from 'lucide-react';
import { api } from '../services/api';
import { useWorkspace } from '../context/WorkspaceContext';

const AnalyticsPanel = ({ analytics, onClose }) => {
  const { activeWorkspace } = useWorkspace();
  const [aiResult, setAiResult] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiLabel, setAiLabel] = useState('');

  if (!analytics) return null;

  const { centrality = [], communities = {}, gaps = [], stats = {} } = analytics;
  const clusters = communities.clusters || [];

  const handleAiAction = async (action, label) => {
    setAiLoading(true);
    setAiLabel(label);
    setAiResult(null);
    if (!activeWorkspace?.id) {
      setAiResult("Please select a workspace first.");
      setAiLoading(false);
      return;
    }

    try {
      let result;
      if (action === 'insights') {
        result = await api.getInsights(activeWorkspace.id);
        setAiResult(result.insights?.[0] || 'No insights generated.');
      } else if (action === 'bridge') {
        result = await api.getBridgeQuestions(activeWorkspace.id, 0);
        setAiResult(result.questions || 'No bridge questions generated.');
      } else if (action === 'blindspots') {
        result = await api.getBlindSpots(activeWorkspace.id);
        setAiResult(result.blind_spots || 'No blind spots identified.');
      }
    } catch (err) {
      setAiResult(`Error: ${err.message}`);
    } finally {
      setAiLoading(false);
    }
  };

  return (
    <div className="glass-panel" style={{
      position: 'absolute',
      left: '24px',
      top: '80px',
      width: '300px',
      maxHeight: 'calc(100vh - 140px)',
      overflowY: 'auto',
      zIndex: 10,
      padding: '0',
    }}>
      {/* Header */}
      <div style={{ 
        padding: '16px', 
        borderBottom: '1px solid var(--glass-border)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <BarChart3 size={18} color="var(--accent-color)" /> Network Analytics
        </h3>
      </div>

      {/* Network Stats */}
      <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--glass-border)' }}>
        <h4 style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--text-secondary)', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Network size={14} /> Network Health
        </h4>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          <StatBox label="Nodes" value={stats.node_count || 0} />
          <StatBox label="Edges" value={stats.edge_count || 0} />
          <StatBox label="Density" value={(stats.density || 0).toFixed(3)} />
          <StatBox label="Avg Degree" value={stats.avg_degree || 0} />
          <StatBox label="Clustering" value={(stats.avg_clustering || 0).toFixed(3)} />
          <StatBox label="Components" value={stats.connected_components || 0} />
        </div>
      </div>

      {/* Topic Clusters */}
      <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--glass-border)' }}>
        <h4 style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--text-secondary)', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Layers size={14} /> Topic Clusters ({clusters.length})
        </h4>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
          Modularity: <span style={{ color: '#4ECDC4', fontWeight: 600 }}>{(communities.modularity || 0).toFixed(3)}</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {clusters.slice(0, 8).map((cluster) => (
            <div key={cluster.id} style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              padding: '6px 10px',
              background: 'rgba(255,255,255,0.03)',
              borderRadius: '6px',
              borderLeft: `3px solid ${cluster.color}`,
            }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '0.8rem', fontWeight: 600, color: cluster.color }}>
                  Cluster {cluster.id + 1}
                </div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                  {cluster.members?.slice(0, 3).join(', ')}{cluster.members?.length > 3 ? '...' : ''}
                </div>
              </div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                {cluster.size} nodes
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Top Bridge Nodes (Centrality) */}
      <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--glass-border)' }}>
        <h4 style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--text-secondary)', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <TrendingUp size={14} /> Top Bridge Nodes
        </h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {centrality.slice(0, 8).map((item, i) => (
            <div key={item.name} style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              padding: '5px 8px',
              borderRadius: '4px',
              background: i === 0 ? 'rgba(255, 215, 0, 0.08)' : 'transparent',
            }}>
              <span style={{ 
                fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-secondary)', 
                width: '18px', textAlign: 'right' 
              }}>
                {i + 1}
              </span>
              <span style={{ flex: 1, fontSize: '0.8rem', fontWeight: i < 3 ? 600 : 400 }}>
                {item.name}
              </span>
              <div style={{
                height: '4px',
                width: `${Math.max(item.centrality * 200, 8)}px`,
                background: `linear-gradient(90deg, var(--accent-color), ${i === 0 ? '#FFD700' : '#4D96FF'})`,
                borderRadius: '2px',
              }} />
            </div>
          ))}
        </div>
      </div>

      {/* Structural Gaps */}
      {gaps.length > 0 && (
        <div style={{ padding: '14px 16px' }}>
          <h4 style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--text-secondary)', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Zap size={14} /> Structural Gaps
          </h4>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
            Disconnected cluster pairs — potential research opportunities
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {gaps.slice(0, 4).map((gap, i) => (
              <div key={i} style={{
                padding: '8px 10px',
                background: gap.gap_strength === 'strong' 
                  ? 'rgba(255, 107, 107, 0.08)' 
                  : 'rgba(255, 159, 28, 0.06)',
                borderRadius: '6px',
                border: `1px solid ${gap.gap_strength === 'strong' ? 'rgba(255,107,107,0.2)' : 'rgba(255,159,28,0.15)'}`,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                  <Circle size={8} fill={gap.cluster_a.color} stroke="none" />
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>↔</span>
                  <Circle size={8} fill={gap.cluster_b.color} stroke="none" />
                  <span style={{ 
                    fontSize: '0.65rem', 
                    color: gap.gap_strength === 'strong' ? '#FF6B6B' : '#FF9F1C',
                    fontWeight: 600,
                    marginLeft: 'auto',
                  }}>
                    {gap.gap_strength === 'strong' ? 'NO CONNECTION' : `${gap.inter_edges} edges`}
                  </span>
                </div>
                <div style={{ fontSize: '0.7rem', color: '#ccc' }}>
                  {gap.cluster_a.top_nodes.join(', ')} ↔ {gap.cluster_b.top_nodes.join(', ')}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI-Powered Actions */}
      <div style={{ padding: '14px 16px', borderTop: '1px solid var(--glass-border)' }}>
        <h4 style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--text-secondary)', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Brain size={14} /> AI Analysis
        </h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <button
            onClick={() => handleAiAction('insights', 'Structural Insights')}
            disabled={aiLoading}
            style={{
              padding: '8px 12px', display: 'flex', alignItems: 'center', gap: '8px',
              background: 'rgba(77, 150, 255, 0.1)', border: '1px solid rgba(77, 150, 255, 0.2)',
              borderRadius: '6px', cursor: 'pointer', color: '#fff', fontSize: '0.8rem',
              opacity: aiLoading ? 0.6 : 1, transition: 'all 0.2s ease',
            }}
          >
            <Lightbulb size={14} color="#FFE66D" /> Get AI Insights
          </button>
          <button
            onClick={() => handleAiAction('bridge', 'Bridge Questions')}
            disabled={aiLoading || gaps.length === 0}
            style={{
              padding: '8px 12px', display: 'flex', alignItems: 'center', gap: '8px',
              background: 'rgba(78, 205, 196, 0.1)', border: '1px solid rgba(78, 205, 196, 0.2)',
              borderRadius: '6px', cursor: 'pointer', color: '#fff', fontSize: '0.8rem',
              opacity: (aiLoading || gaps.length === 0) ? 0.6 : 1, transition: 'all 0.2s ease',
            }}
          >
            <Zap size={14} color="#4ECDC4" /> Bridge Gaps
          </button>
          <button
            onClick={() => handleAiAction('blindspots', 'Blind Spots')}
            disabled={aiLoading}
            style={{
              padding: '8px 12px', display: 'flex', alignItems: 'center', gap: '8px',
              background: 'rgba(255, 107, 107, 0.1)', border: '1px solid rgba(255, 107, 107, 0.2)',
              borderRadius: '6px', cursor: 'pointer', color: '#fff', fontSize: '0.8rem',
              opacity: aiLoading ? 0.6 : 1, transition: 'all 0.2s ease',
            }}
          >
            <Search size={14} color="#FF6B6B" /> Find Blind Spots
          </button>
        </div>

        {/* AI Result Display */}
        {(aiLoading || aiResult) && (
          <div style={{
            marginTop: '12px', padding: '12px',
            background: 'rgba(0,0,0,0.3)', borderRadius: '8px',
            border: '1px solid rgba(255,255,255,0.05)',
            maxHeight: '300px', overflowY: 'auto',
          }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--accent-color)', fontWeight: 600, marginBottom: '8px' }}>
              {aiLabel}
            </div>
            {aiLoading ? (
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontStyle: 'italic' }}>
                Analyzing graph structure with AI...
              </div>
            ) : (
              <div style={{ fontSize: '0.8rem', lineHeight: 1.6, color: '#e0e0e0', whiteSpace: 'pre-wrap' }}>
                {aiResult}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Small stat box component
const StatBox = ({ label, value }) => (
  <div style={{
    padding: '8px',
    background: 'rgba(255,255,255,0.03)',
    borderRadius: '6px',
    textAlign: 'center',
  }}>
    <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff' }}>{value}</div>
    <div style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', marginTop: '2px' }}>{label}</div>
  </div>
);

export default AnalyticsPanel;
