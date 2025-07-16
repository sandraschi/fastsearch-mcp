import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

// Dynamic API base URL detection for different access methods
const getApiBaseUrl = () => {
  if (process.env.NODE_ENV === 'production') {
    return ''; // Use relative URLs in production (proxy handles it)
  }
  
  // Check if accessing via different hostnames/IPs
  const hostname = window.location.hostname;
  const protocol = window.location.protocol;
  
  // Tailscale hostname access
  if (hostname === 'goliath') {
    return `${protocol}//goliath:4700`;
  }
  
  // Tailscale IP access
  if (hostname === '100.118.171.110') {
    return `${protocol}//100.118.171.110:4700`;
  }
  
  // Public IP access
  if (hostname === '213.47.34.131') {
    return `${protocol}//213.47.34.131:4700`;
  }
  
  // Default to localhost for local development
  return process.env.REACT_APP_API_URL || 'http://localhost:4700';
};

const API_BASE_URL = getApiBaseUrl();

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  // Check if user is authenticated on app load
  useEffect(() => {
    const checkAuth = async () => {
      if (token) {
        try {
          const response = await axios.get(`${API_BASE_URL}/api/v1/enhanced-auth/me`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          // /me endpoint returns user data directly, not nested in a user field
          setUser(response.data);
        } catch (error) {
          console.error('Auth check failed:', error);
          // Clear invalid token
          logout();
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, [token]);

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/v1/enhanced-auth/login`, {
        email,
        password
      });

      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(userData);
      
      return { success: true, user: userData };
    } catch (error) {
      console.error('Login failed:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      };
    }
  };

  const register = async (userData) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/v1/enhanced-auth/register`, userData);
      
      const { access_token, user: newUser } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(newUser);
      
      return { success: true, user: newUser };
    } catch (error) {
      console.error('Registration failed:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Registration failed' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const updateUser = (userData) => {
    setUser(userData);
  };

  const isAuthenticated = () => {
    return !!token && !!user;
  };

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    updateUser,
    isAuthenticated
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}; 