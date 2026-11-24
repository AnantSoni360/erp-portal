import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi } from '../api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState({
    username: 'admin',
    full_name: 'MMTPL Store Administrator',
    role: 'admin',
    is_active: true
  });
  const [demoUsers, setDemoUsers] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Attempt auto-login or fetch demo users
    const initAuth = async () => {
      try {
        const res = await authApi.login('admin', 'admin123');
        if (res.data?.access_token) {
          localStorage.setItem('mmtpl_token', res.data.access_token);
          setUser(res.data.user);
        }
      } catch (err) {
        console.warn('Auto login failed, using default admin role', err);
      }

      try {
        const demoRes = await authApi.getDemoUsers();
        setDemoUsers(demoRes.data || []);
      } catch (e) {
        // Fallback demo users
        setDemoUsers([
          { username: 'admin', full_name: 'MMTPL Store Administrator', role: 'admin', description: 'Full system control' },
          { username: 'manager', full_name: 'Rajesh Kumar (Store Manager)', role: 'store_manager', description: 'Approve transactions, inventory control' },
          { username: 'employee', full_name: 'Suresh Sharma (Store Clerk)', role: 'store_employee', description: 'Record inward receipts, issues & returns' },
          { username: 'management', full_name: 'MMTPL Executive Viewer', role: 'management', description: 'Executive dashboard & reports' }
        ]);
      }
    };

    initAuth();
  }, []);

  const switchRole = async (username) => {
    setLoading(true);
    const pwdMap = {
      admin: 'admin123',
      manager: 'manager123',
      employee: 'employee123',
      management: 'view123'
    };
    try {
      const res = await authApi.login(username, pwdMap[username] || 'admin123');
      if (res.data?.access_token) {
        localStorage.setItem('mmtpl_token', res.data.access_token);
        setUser(res.data.user);
      }
    } catch (err) {
      console.error('Failed to switch role', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthContext.Provider value={{ user, demoUsers, switchRole, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
