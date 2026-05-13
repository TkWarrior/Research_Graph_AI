import React, { useState, useEffect } from 'react';
import { RefreshCw, LayoutTemplate } from 'lucide-react';
import KnowledgeGraph from '../components/KnowledgeGraph';
import NodePanel from '../components/NodePanel';
import { api } from '../services/api';

const GraphExplorer = () => {
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState(null);
  const [error, setError] = useState(null);

  const fetchFullGraph = async () => {
    setLoading(true);
    try {
      const data = await api.getGraph(500);
      setGraphData(data);
      setError(null);
    } catch (err) {
      console.error("Failed to fetch graph:", err);
      setError("Failed to connect to Knowledge Graph. Have you uploaded any documents yet?");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFullGraph();
  }, []);

  const handleNodeClick = (node) => {
    setSelectedNode(node);
  };

  const handleExploreNeighborhood = async (nodeName) => {
    setLoading(true);
    try {
      const data = await api.getSubgraph(nodeName, 2);
      setGraphData(data);
    } catch (err) {
      console.error("Failed to fetch subgraph:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ position: 'relative', width: '100%', height: 'calc(100vh - 80px)' }}>
      {/* Controls Overlay */}
      <div className="glass-panel" style={{ 
        position: 'absolute', 
        left: '24px', 
        top: '24px', 
        zIndex: 10,
        padding: '12px',
        display: 'flex',
        gap: '8px'
      }}>
        <button 
          onClick={fetchFullGraph}
          className="btn-primary" 
          style={{ padding: '8px 16px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem' }}
        >
          <RefreshCw size={16} /> Reset Graph
        </button>
        <div style={{ padding: '8px 16px', background: 'rgba(0,0,0,0.3)', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem' }}>
          <LayoutTemplate size={16} color="var(--accent-color)" /> 
          {graphData?.nodes?.length || 0} Nodes
        </div>
      </div>

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
        />
      )}

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
