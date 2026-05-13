import React from 'react';
import { NavLink } from 'react-router-dom';
import { Database, Network, Search, Upload } from 'lucide-react';
import '../styles/index.css';

const Header = () => {
  return (
    <header className="glass-panel" style={{
      margin: '16px',
      padding: '16px 24px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      zIndex: 100
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{
          background: 'var(--accent-gradient)',
          padding: '8px',
          borderRadius: '8px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <Database size={20} color="white" />
        </div>
        <h1 style={{ fontSize: '1.25rem', fontWeight: 600, margin: 0 }}>
          Research<span className="gradient-text">Graph</span>
        </h1>
      </div>

      <nav style={{ display: 'flex', gap: '8px' }}>
        <NavLink 
          to="/" 
          style={({isActive}) => ({
            textDecoration: 'none',
            color: isActive ? 'white' : 'var(--text-secondary)',
            padding: '8px 16px',
            borderRadius: '6px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: isActive ? 'rgba(255,255,255,0.1)' : 'transparent',
            transition: 'all 0.2s'
          })}
        >
          <Upload size={18} /> Dashboard
        </NavLink>
        
        <NavLink 
          to="/graph" 
          style={({isActive}) => ({
            textDecoration: 'none',
            color: isActive ? 'white' : 'var(--text-secondary)',
            padding: '8px 16px',
            borderRadius: '6px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: isActive ? 'rgba(255,255,255,0.1)' : 'transparent',
            transition: 'all 0.2s'
          })}
        >
          <Network size={18} /> Graph Explorer
        </NavLink>
        
        <NavLink 
          to="/research" 
          style={({isActive}) => ({
            textDecoration: 'none',
            color: isActive ? 'white' : 'var(--text-secondary)',
            padding: '8px 16px',
            borderRadius: '6px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: isActive ? 'rgba(255,255,255,0.1)' : 'transparent',
            transition: 'all 0.2s'
          })}
        >
          <Search size={18} /> Q&A Research
        </NavLink>
      </nav>
    </header>
  );
};

export default Header;
