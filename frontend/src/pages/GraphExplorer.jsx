import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw, LayoutTemplate, BarChart3 } from 'lucide-react';
import KnowledgeGraph from '../components/KnowledgeGraph';
import NodePanel from '../components/NodePanel';
import AnalyticsPanel from '../components/AnalyticsPanel';
import ClusterFilter from '../components/ClusterFilter';
import { api } from '../services/api';
import { useWorkspace } from '../context/WorkspaceContext';

const GraphExplorer = () => {
  const { activeWorkspace } = useWorkspace();
  const [graphData, setGraphData] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState(null);
  const [error, setError] = useState(null);
  const [showAnalytics, setShowAnalytics] = useState(true);
  const [hiddenClusters, setHiddenClusters] = useState(new Set());

  const fetchGraphWithAnalytics = useCallback(async () => {
    if (!activeWorkspace) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.getGraphWithAnalytics(1000, activeWorkspace.id);
      setGraphData({ nodes: data.nodes, edges: data.edges });
      const fullAnalytics = await api.getFullAnalysis(1000, activeWorkspace.id);
      setAnalytics(fullAnalytics);
    } catch (err) {
      console.error('Failed to fetch graph:', err);
      setError('Failed to connect to Knowledge Graph. Have you uploaded any documents yet?');
    } finally {
      setLoading(false);
    }
  }, [activeWorkspace]);

  // ── Step 1: Immediately wipe stale data when workspace changes ────
  // This runs SYNCHRONOUSLY before the async fetch so the user never
  // sees a previous workspace's graph bleeding into the new one.
  useEffect(() => {
    setGraphData(null);
    setAnalytics(null);
    setSelectedNode(null);
    setHiddenClusters(new Set());
    setError(null);
  }, [activeWorkspace?.id]);

  // ── Step 2: Fetch new workspace graph data ────────────────────────
  useEffect(() => {
    fetchGraphWithAnalytics();
  }, [fetchGraphWithAnalytics]);

  const handleNodeClick = (node) => {
    setSelectedNode(node);
  };

  const handleExploreNeighborhood = async (nodeName) => {
    if (!activeWorkspace) return;
    setLoading(true);
    try {
      const data = await api.getSubgraph(nodeName, 2, activeWorkspace.id);
      setGraphData(data);
    } catch (err) {
      console.error('Failed to fetch subgraph:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClusterToggle = (clusterId) => {
    setHiddenClusters(prev => {
      const next = new Set(prev);
      if (next.has(clusterId)) next.delete(clusterId);
      else next.add(clusterId);
      return next;
    });
  };

  const clusters = analytics?.communities?.clusters || [];

  return (
    <div style={{ position: 'relative', width: '100%', height: 'calc(100vh - 80px)' }}>
      {/* Top Controls Overlay */}
      <div className="glass-panel" style={{
        position: 'absolute',
        left: showAnalytics ? '340px' : '24px',
        top: '24px', zIndex: 10, padding: '10px 12px',
        display: 'flex', gap: '8px', alignItems: 'center',
        transition: 'left 0.3s ease', flexWrap: 'wrap',
      }}>
        {/* Active Workspace Badge */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: '6px',
          padding: '6px 12px', background: 'rgba(136,211,206,0.1)',
          border: '1px solid rgba(136,211,206,0.25)', borderRadius: '6px',
          fontSize: '0.82rem', color: '#88d3ce',
        }}>
          {activeWorkspace?.name ?? 'No workspace'}
        </div>

        <button onClick={() => fetchGraphWithAnalytics()} className="btn-primary"
          style={{ padding: '7px 14px', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}>
          <RefreshCw size={14} /> Reset
        </button>
        <button onClick={() => setShowAnalytics(!showAnalytics)}
          style={{ padding: '7px 14px', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem',
            background: showAnalytics ? 'rgba(77, 150, 255, 0.15)' : 'rgba(255,255,255,0.05)',
            border: `1px solid ${showAnalytics ? 'rgba(77, 150, 255, 0.3)' : 'rgba(255,255,255,0.1)'}`,
            borderRadius: '8px', cursor: 'pointer', color: '#fff', transition: 'all 0.2s ease' }}>
          <BarChart3 size={14} /> Analytics
        </button>
        <div style={{ padding: '7px 14px', background: 'rgba(0,0,0,0.3)', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}>
          <LayoutTemplate size={14} color="var(--accent-color)" />
          {graphData?.nodes?.length || 0} Nodes
        </div>
      </div>

      {/* Analytics Panel (Left Sidebar) */}
      {showAnalytics && !loading && analytics && (
        <AnalyticsPanel 
          analytics={analytics} 
          onClose={() => setShowAnalytics(false)}
        />
      )}

      {/* Cluster Filter (Bottom Right) */}
      {!loading && clusters.length >= 2 && (
        <ClusterFilter 
          clusters={clusters}
          hiddenClusters={hiddenClusters}
          onToggle={handleClusterToggle}
        />
      )}

      {/* Main Graph */}
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
          <div className="spinner" style={{ width: '40px', height: '40px', border: '3px solid rgba(255,255,255,0.1)', borderTop: '3px solid var(--accent-color)', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
          <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
        </div>
      ) : error ? (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', color: '#FF6B6B' }}>
          {error}
        </div>
      ) : (
        <KnowledgeGraph 
          graphData={graphData} 
          onNodeClick={handleNodeClick}
          hiddenClusters={hiddenClusters}
        />
      )}

      {/* Node Detail Panel (Right) */}
      {selectedNode && (
        <NodePanel 
          node={selectedNode} 
          onClose={() => setSelectedNode(null)} 
          onExplore={handleExploreNeighborhood}
        />
      )}
    </div>
  );
};

export default GraphExplorer;
