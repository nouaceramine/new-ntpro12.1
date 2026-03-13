import { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);
  const [features, setFeatures] = useState(null);
  const [limits, setLimits] = useState(null);
  
  // Set axios default header
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token]);
  
  // Check token on mount
  useEffect(() => {
    const verifyToken = async () => {
      if (!token) {
        setLoading(false);
        return;
      }
      
      try {
        const response = await axios.get(`${API}/auth/me`);
        // Merge with localStorage data to get user_type
        const storedUser = JSON.parse(localStorage.getItem('user') || '{}');
        const userData = {
          ...response.data,
          user_type: response.data.user_type || storedUser.user_type
        };
        setUser(userData);
        // Set features and limits from response
        setFeatures(response.data.features || null);
        setLimits(response.data.limits || null);
      } catch (error) {
        console.error('Token verification failed:', error);
        logout();
      } finally {
        setLoading(false);
      }
    };
    
    verifyToken();
  }, [token]);
  
  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/unified-login`, { email, password });
    const { access_token, user: userData, user_type, redirect_to } = response.data;
    
    localStorage.setItem('token', access_token);
    localStorage.setItem('user_type', user_type || 'admin');
    localStorage.setItem('redirect_to', redirect_to || '/');
    setToken(access_token);
    setUser(userData);
    // Set features and limits from login response
    setFeatures(userData.features || null);
    setLimits(userData.limits || null);
    
    return { ...userData, user_type, redirect_to };
  };
  
  const register = async (email, password, name, role = 'user') => {
    const response = await axios.post(`${API}/auth/register`, { 
      email, 
      password, 
      name,
      role 
    });
    const { access_token, user: userData } = response.data;
    
    localStorage.setItem('token', access_token);
    setToken(access_token);
    setUser(userData);
    
    return userData;
  };
  
  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setFeatures(null);
    setLimits(null);
  };
  
  // Check if a feature is enabled
  const isFeatureEnabled = (categoryKey, subFeatureKey = null) => {
    // Super admin has all features
    if (user?.role === 'super_admin') return true;
    // If no features set, allow all (default behavior)
    if (!features) return true;
    
    const category = features[categoryKey];
    if (!category) return true; // Feature not defined = enabled by default
    
    // Check if category is disabled
    if (category.enabled === false) return false;
    
    // If checking sub-feature
    if (subFeatureKey && category.subFeatures) {
      return category.subFeatures[subFeatureKey] !== false;
    }
    
    return true;
  };
  
  // Admin includes both 'admin' and 'super_admin' roles
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';
  const isSuperAdmin = user?.role === 'super_admin';
  const isTenant = user?.user_type === 'tenant' || user?.role === 'tenant_admin';
  const isAgent = user?.user_type === 'agent' || user?.role === 'agent';
  
  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    isAdmin,
    isSuperAdmin,
    isTenant,
    isAgent,
    isAuthenticated: !!user,
    features,
    limits,
    isFeatureEnabled
  };
  
  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
