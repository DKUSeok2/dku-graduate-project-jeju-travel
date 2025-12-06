/**
 * Authentication Context
 */
import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User } from '../api/auth';
import { safeLocalStorage } from '../utils/storage';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
  updateUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 앱 시작 시 로컬스토리지에서 사용자 정보 로드
  useEffect(() => {
    const token = safeLocalStorage.getItem('access_token');
    const savedUser = safeLocalStorage.getItem('user');

    if (token && savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (error) {
        console.error('Failed to parse user data:', error);
        safeLocalStorage.removeItem('access_token');
        safeLocalStorage.removeItem('user');
      }
    }

    setIsLoading(false);
  }, []);

  const login = (token: string, userData: User) => {
    safeLocalStorage.setItem('access_token', token);
    safeLocalStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
  };

  const logout = () => {
    safeLocalStorage.removeItem('access_token');
    safeLocalStorage.removeItem('user');
    setUser(null);
  };

  const updateUser = (userData: User) => {
    safeLocalStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        updateUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

