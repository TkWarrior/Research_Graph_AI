import React, { useState } from 'react';
import UploadZone from '../components/UploadZone';
import { Database, Zap, GitCommit } from 'lucide-react';
import { api } from '../services/api';

const Dashboard = () => {
  const [stats, setStats] = useState(null);

  const fetchStats = async () => {
    try {
      const data = await api.getGraph(10); // just getting graph data to count nodes
      setStats({
        entities: data.nodes ? data.nodes.length : 0,
        relationships: data.edges ? data.edges.length : 0
      });
    } catch (err) {
      console.error(err);
    }
  };

  React.useEffect(() => {
    fetchStats();
  }, []);

  const handleUploadSuccess = () => {
    // When upload finishes, it queues a background task. 
    // We can show a pending message or refetch stats after a delay.
    setTimeout(fetchStats, 5000);
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ textAlign: 'center', margin: '40px 0 60px 0' }}>
        <h1 style={{ fontSize: '3rem', fontWeight: 700, marginBottom: '16px' }}>
          Autonomous <span className="gradient-text">Research</span> System
        </h1>
        <p style={{ fontSize: '1.2rem', color: 'var(--text-secondary)', maxWidth: '600px', margin: '0 auto' }}>
          Upload documents to automatically extract knowledge graphs and perform deep semantic research using LangGraph and Neo4j.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px', alignItems: 'start' }}>
        <UploadZone onUploadSuccess={handleUploadSuccess} />
        
        <div className="glass-panel" style={{ padding: '32px' }}>
          <h2 style={{ marginBottom: '24px', fontWeight: 600 }}>System Status</h2>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div className="glass-panel" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '16px', background: 'rgba(0,0,0,0.2)' }}>
              <div style={{ background: 'rgba(110, 69, 226, 0.2)', padding: '12px', borderRadius: '12px', color: '#88d3ce' }}>
                <Database size={24} />
              </div>
              <div>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Vector Store (ChromaDB)</p>
                <p style={{ fontSize: '1.2rem', fontWeight: 600 }}>Online</p>
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '16px', background: 'rgba(0,0,0,0.2)' }}>
              <div style={{ background: 'rgba(78, 205, 196, 0.2)', padding: '12px', borderRadius: '12px', color: '#4ECDC4' }}>
                <GitCommit size={24} />
              </div>
              <div>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Knowledge Graph (Neo4j)</p>
                <p style={{ fontSize: '1.2rem', fontWeight: 600 }}>
                  {stats ? `${stats.entities} Entities / ${stats.relationships} Edges` : 'Online'}
                </p>
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '16px', background: 'rgba(0,0,0,0.2)' }}>
              <div style={{ background: 'rgba(255, 107, 107, 0.2)', padding: '12px', borderRadius: '12px', color: '#FF6B6B' }}>
                <Zap size={24} />
              </div>
              <div>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>LLM Extraction</p>
                <p style={{ fontSize: '1.2rem', fontWeight: 600 }}>Groq (llama3-70b-8192)</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
