import React, { useState, useRef } from 'react';
import { UploadCloud, File, CheckCircle, AlertCircle, Zap, Brain, Layers } from 'lucide-react';
import { api } from '../services/api';
import { useWorkspace } from '../context/WorkspaceContext';

const UploadZone = ({ onUploadSuccess }) => {
  const { activeWorkspace } = useWorkspace();
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('idle');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [graphMode, setGraphMode] = useState('cooccurrence');
  
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true);
    } else if (e.type === 'dragleave') {
      setIsDragging(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFileSelection(e.target.files[0]);
    }
  };

  const handleFileSelection = (selectedFile) => {
    // Validate file type
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!validTypes.includes(selectedFile.type)) {
      setError("Please upload a PDF or DOCX file.");
      setStatus('error');
      return;
    }
    
    setFile(selectedFile);
    setError(null);
    setStatus('idle');
  };

  const handleUpload = async () => {
    if (!file) return;
    if (!activeWorkspace) {
      setError('Please select or create a workspace first.');
      setStatus('error');
      return;
    }
    setStatus('uploading');
    setProgress(0);
    try {
      const response = await api.uploadDocument(
        file,
        activeWorkspace.id,
        (progressEvent) => {
          const pct = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setProgress(pct);
          if (pct === 100) setStatus('processing');
        },
        graphMode
      );
      setStatus('success');
      if (onUploadSuccess) onUploadSuccess(response);
    } catch (err) {
      console.error(err);
      setStatus('error');
      setError(err.response?.data?.detail || 'An error occurred during upload');
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '32px', maxWidth: '600px', margin: '0 auto', textAlign: 'center' }}>
      <h2 style={{ marginBottom: '8px', fontWeight: 600 }}>Ingest Knowledge</h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '24px', fontSize: '0.9rem' }}>
        Upload a PDF or DOCX document to build the knowledge graph.
      </p>

      <div 
        onClick={() => status !== 'uploading' && status !== 'processing' && fileInputRef.current?.click()}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        style={{
          border: `2px dashed ${isDragging ? 'var(--accent-color)' : 'rgba(255,255,255,0.2)'}`,
          borderRadius: '12px',
          padding: '40px 20px',
          cursor: (status === 'uploading' || status === 'processing') ? 'not-allowed' : 'pointer',
          background: isDragging ? 'rgba(136, 211, 206, 0.05)' : 'rgba(0,0,0,0.2)',
          transition: 'all 0.2s ease',
          marginBottom: '24px'
        }}
      >
        <input 
          ref={fileInputRef}
          type="file" 
          accept=".pdf,.docx" 
          onChange={handleChange}
          style={{ display: 'none' }}
        />
        
        {!file ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
            <UploadCloud size={48} color={isDragging ? 'var(--accent-color)' : 'var(--text-secondary)'} />
            <div>
              <p style={{ fontWeight: 500, fontSize: '1.1rem' }}>Drag & drop your document here</p>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '4px' }}>
                or click to browse (PDF, DOCX up to 10MB)
              </p>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
            <File size={40} color="var(--accent-color)" />
            <div>
              <p style={{ fontWeight: 500 }}>{file.name}</p>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                {(file.size / (1024 * 1024)).toFixed(2)} MB
              </p>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div style={{ color: '#FF6B6B', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginBottom: '16px' }}>
          <AlertCircle size={16} /> {error}
        </div>
      )}

      {/* Graph Mode Selector */}
      {file && status === 'idle' && (
        <div style={{ marginBottom: '16px', textAlign: 'left' }}>
          <label style={{ 
            fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '1px', 
            color: 'var(--text-secondary)', marginBottom: '8px', display: 'block', fontWeight: 600 
          }}>
            Graph Construction Mode
          </label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {[
              { 
                value: 'cooccurrence', 
                label: 'Co-occurrence (Fast)', 
                icon: <Zap size={16} color="#4ECDC4" />,
                desc: 'NLP-based word co-occurrence network. Free, ~2 seconds.',
                color: '#4ECDC4',
              },
              { 
                value: 'llm', 
                label: 'LLM Semantic (Rich)', 
                icon: <Brain size={16} color="#A29BFE" />,
                desc: 'LLM extracts typed entities & named relationships. Uses API credits.',
                color: '#A29BFE',
              },
              { 
                value: 'both', 
                label: 'Hybrid (Both)', 
                icon: <Layers size={16} color="#FFE66D" />,
                desc: 'Runs both modes in parallel. Richest graph, uses API credits.',
                color: '#FFE66D',
              },
            ].map(mode => (
              <button
                key={mode.value}
                onClick={() => setGraphMode(mode.value)}
                style={{
                  display: 'flex', alignItems: 'center', gap: '10px',
                  padding: '10px 14px',
                  background: graphMode === mode.value 
                    ? `${mode.color}18`
                    : 'rgba(255,255,255,0.03)',
                  border: `1px solid ${graphMode === mode.value ? mode.color + '55' : 'rgba(255,255,255,0.08)'}`,
                  borderRadius: '8px',
                  cursor: 'pointer',
                  color: '#fff',
                  textAlign: 'left',
                  transition: 'all 0.2s ease',
                }}
              >
                {mode.icon}
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: graphMode === mode.value ? 600 : 400, color: graphMode === mode.value ? mode.color : '#fff' }}>
                    {mode.label}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                    {mode.desc}
                  </div>
                </div>
                {graphMode === mode.value && (
                  <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: mode.color, flexShrink: 0 }} />
                )}
              </button>
            ))}
          </div>
        </div>
      )}
      {status === 'uploading' || status === 'processing' ? (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.85rem' }}>
            <span style={{ color: 'var(--text-secondary)' }}>
              {status === 'uploading' 
                ? 'Uploading...' 
                : graphMode === 'cooccurrence' 
                  ? 'Building co-occurrence network...' 
                  : 'Processing document with LLM... (This may take a minute)'}
            </span>
            <span>{status === 'uploading' ? `${progress}%` : ''}</span>
          </div>
          <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{ 
              height: '100%', 
              background: 'var(--accent-gradient)',
              width: status === 'uploading' ? `${progress}%` : '100%',
              transition: 'width 0.3s ease',
              animation: status === 'processing' ? 'pulse 1.5s infinite alternate' : 'none'
            }} />
          </div>
          <style>{`
            @keyframes pulse {
              0% { opacity: 0.6; }
              100% { opacity: 1; }
            }
          `}</style>
        </div>
      ) : status === 'success' ? (
        <div style={{ color: '#4ECDC4', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
          <CheckCircle size={20} /> Processing Complete!
        </div>
      ) : (
        <button 
          className="btn-primary" 
          onClick={handleUpload}
          disabled={!file}
          style={{ width: '100%', opacity: !file ? 0.5 : 1 }}
        >
          Process Document
        </button>
      )}
    </div>
  );
};

export default UploadZone;
