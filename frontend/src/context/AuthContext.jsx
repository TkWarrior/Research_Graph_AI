/**
 * Auth Context — stores the JWT token and current user globally.
 *
 * Usage:
 *   const { user, token, login, logout, isAuthenticated } = useAuth();
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser]   = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('authToken'));
  const [loading, setLoading] = useState(true);

  // On mount — validate stored token and restore user
  useEffect(() => {
    const stored = localStorage.getItem('authToken');
    if (!stored) { setLoading(false); return; }

    api.getMe(stored)
      .then(u => setUser(u))
      .catch(() => {
        localStorage.removeItem('authToken');
        setToken(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(({ access_token, user: u }) => {
    localStorage.setItem('authToken', access_token);
    setToken(access_token);
    setUser(u);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('activeWorkspaceId');
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated: !!token, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
};
