import React, { useState, useRef } from 'react';
import { UploadCloud, File, CheckCircle, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

const UploadZone = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, uploading, processing, success, error
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  
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
    
    setStatus('uploading');
    setProgress(0);
    
    try {
      const response = await api.uploadDocument(file, (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setProgress(percentCompleted);
        
        if (percentCompleted === 100) {
          setStatus('processing');
        }
      });
      
      setStatus('success');
      if (onUploadSuccess) onUploadSuccess(response);
      
    } catch (err) {
      console.error(err);
      setStatus('error');
      setError(err.response?.data?.detail || "An error occurred during upload");
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '32px', maxWidth: '600px', margin: '0 auto', textAlign: 'center' }}>
      <h2 style={{ marginBottom: '8px', fontWeight: 600 }}>Ingest Knowledge</h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '24px', fontSize: '0.9rem' }}>
        Upload a PDF or DOCX document to extract entities and build the knowledge graph.
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

      {status === 'uploading' || status === 'processing' ? (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.85rem' }}>
            <span style={{ color: 'var(--text-secondary)' }}>
              {status === 'uploading' ? 'Uploading...' : 'Processing document with LLM... (This may take a minute)'}
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
