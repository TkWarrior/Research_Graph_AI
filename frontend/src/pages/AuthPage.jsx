/**
 * Premium Auth Page — Sign In & Sign Up with animated glassmorphism design.
 */

import React, { useState } from 'react';
import { Brain, Mail, Lock, User, Eye, EyeOff, Loader2, Sparkles } from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

const AuthPage = () => {
  const { login } = useAuth();
  const [mode, setMode] = useState('signin'); // 'signin' | 'signup'
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({ full_name: '', email: '', password: '' });

  const handleChange = (e) =>
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      let result;
      if (mode === 'signup') {
        result = await api.signup(form.full_name, form.email, form.password);
      } else {
        result = await api.signin(form.email, form.password);
      }
      login(result); // stores token, sets user in context
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const switchMode = () => {
    setMode(m => m === 'signin' ? 'signup' : 'signin');
    setError('');
    setForm({ full_name: '', email: '', password: '' });
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0d0d1a 0%, #111127 50%, #0a0a1f 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Animated Background Orbs */}
      <div style={{
        position: 'absolute', width: '500px', height: '500px',
        background: 'radial-gradient(circle, rgba(110,69,226,0.15) 0%, transparent 70%)',
        top: '-100px', left: '-100px', borderRadius: '50%',
        animation: 'float 8s ease-in-out infinite',
      }} />
      <div style={{
        position: 'absolute', width: '400px', height: '400px',
        background: 'radial-gradient(circle, rgba(78,205,196,0.12) 0%, transparent 70%)',
        bottom: '-80px', right: '-80px', borderRadius: '50%',
        animation: 'float 10s ease-in-out infinite reverse',
      }} />
      <div style={{
        position: 'absolute', width: '300px', height: '300px',
        background: 'radial-gradient(circle, rgba(255,107,107,0.08) 0%, transparent 70%)',
        top: '40%', right: '20%', borderRadius: '50%',
        animation: 'float 12s ease-in-out infinite',
      }} />

      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px) scale(1); }
          50% { transform: translateY(-20px) scale(1.05); }
        }
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(20px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes shimmer {
          0% { background-position: -200% center; }
          100% { background-position: 200% center; }
        }
        .auth-input {
          width: 100%;
          padding: 12px 16px 12px 44px;
          background: rgba(255,255,255,0.04);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 12px;
          color: #fff;
          font-size: 0.9rem;
          outline: none;
          transition: all 0.2s ease;
          box-sizing: border-box;
          font-family: 'Inter', sans-serif;
        }
        .auth-input:focus {
          border-color: rgba(110,69,226,0.6);
          background: rgba(255,255,255,0.07);
          box-shadow: 0 0 0 3px rgba(110,69,226,0.15);
        }
        .auth-input::placeholder { color: rgba(255,255,255,0.3); }
        .auth-btn {
          width: 100%;
          padding: 13px;
          border: none;
          border-radius: 12px;
          background: linear-gradient(135deg, #6e45e2, #4ECDC4);
          color: #fff;
          font-size: 0.95rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          font-family: 'Inter', sans-serif;
          letter-spacing: 0.3px;
        }
        .auth-btn:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 8px 25px rgba(110,69,226,0.4);
        }
        .auth-btn:disabled { opacity: 0.7; cursor: not-allowed; }
        .switch-link {
          background: none;
          border: none;
          color: #88d3ce;
          cursor: pointer;
          font-size: 0.85rem;
          text-decoration: underline;
          font-family: 'Inter', sans-serif;
          padding: 0;
          transition: color 0.2s;
        }
        .switch-link:hover { color: #4ECDC4; }
      `}</style>

      {/* Card */}
      <div style={{
        width: '100%',
        maxWidth: '420px',
        background: 'rgba(255,255,255,0.04)',
        backdropFilter: 'blur(24px)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: '24px',
        padding: '40px',
        animation: 'fadeSlideIn 0.5s ease',
        position: 'relative',
        zIndex: 1,
        boxShadow: '0 25px 50px rgba(0,0,0,0.5)',
      }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{
            width: '60px', height: '60px',
            background: 'linear-gradient(135deg, #6e45e2, #4ECDC4)',
            borderRadius: '16px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 16px',
            boxShadow: '0 8px 24px rgba(110,69,226,0.4)',
          }}>
            <Brain size={28} color="#fff" />
          </div>
          <h1 style={{
            margin: '0 0 6px',
            fontSize: '1.6rem',
            fontWeight: 700,
            background: 'linear-gradient(135deg, #fff, #88d3ce)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            fontFamily: 'Inter, sans-serif',
          }}>
            {mode === 'signin' ? 'Welcome back' : 'Create account'}
          </h1>
          <p style={{ margin: 0, color: 'rgba(255,255,255,0.4)', fontSize: '0.85rem', fontFamily: 'Inter, sans-serif' }}>
            {mode === 'signin' ? 'Sign in to your research workspace' : 'Start your AI research journey'}
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Full Name — signup only */}
          {mode === 'signup' && (
            <div style={{ position: 'relative' }}>
              <User size={16} color="rgba(255,255,255,0.3)" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }} />
              <input
                id="auth-fullname"
                className="auth-input"
                type="text"
                name="full_name"
                placeholder="Full name"
                value={form.full_name}
                onChange={handleChange}
                required
                autoComplete="name"
              />
            </div>
          )}

          {/* Email */}
          <div style={{ position: 'relative' }}>
            <Mail size={16} color="rgba(255,255,255,0.3)" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }} />
            <input
              id="auth-email"
              className="auth-input"
              type="email"
              name="email"
              placeholder="Email address"
              value={form.email}
              onChange={handleChange}
              required
              autoComplete="email"
            />
          </div>

          {/* Password */}
          <div style={{ position: 'relative' }}>
            <Lock size={16} color="rgba(255,255,255,0.3)" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }} />
            <input
              id="auth-password"
              className="auth-input"
              type={showPassword ? 'text' : 'password'}
              name="password"
              placeholder={mode === 'signup' ? 'Password (min 8 chars)' : 'Password'}
              value={form.password}
              onChange={handleChange}
              required
              minLength={mode === 'signup' ? 8 : undefined}
              autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
              style={{ paddingRight: '44px' }}
            />
            <button
              type="button"
              onClick={() => setShowPassword(s => !s)}
              style={{
                position: 'absolute', right: '14px', top: '50%',
                transform: 'translateY(-50%)',
                background: 'none', border: 'none', cursor: 'pointer',
                color: 'rgba(255,255,255,0.3)', padding: 0,
              }}
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>

          {/* Error */}
          {error && (
            <div style={{
              padding: '10px 14px',
              background: 'rgba(255,107,107,0.1)',
              border: '1px solid rgba(255,107,107,0.3)',
              borderRadius: '8px',
              color: '#FF6B6B',
              fontSize: '0.82rem',
              fontFamily: 'Inter, sans-serif',
            }}>
              {error}
            </div>
          )}

          {/* Submit */}
          <button id="auth-submit-btn" type="submit" className="auth-btn" disabled={loading} style={{ marginTop: '4px' }}>
            {loading
              ? <><Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> {mode === 'signin' ? 'Signing in...' : 'Creating account...'}</>
              : <><Sparkles size={16} /> {mode === 'signin' ? 'Sign In' : 'Create Account'}</>
            }
          </button>
        </form>

        {/* Divider */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: '24px 0 20px', color: 'rgba(255,255,255,0.2)', fontSize: '0.75rem', fontFamily: 'Inter, sans-serif' }}>
          <div style={{ flex: 1, height: '1px', background: 'rgba(255,255,255,0.08)' }} />
          OR
          <div style={{ flex: 1, height: '1px', background: 'rgba(255,255,255,0.08)' }} />
        </div>

        {/* Switch mode */}
        <div style={{ textAlign: 'center', color: 'rgba(255,255,255,0.4)', fontSize: '0.85rem', fontFamily: 'Inter, sans-serif' }}>
          {mode === 'signin' ? "Don't have an account? " : 'Already have an account? '}
          <button className="switch-link" type="button" onClick={switchMode}>
            {mode === 'signin' ? 'Sign up free' : 'Sign in'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
