import React, { createContext, useContext, useState, useEffect } from 'react';
import { safeLocalStorage } from '../utils/storage';

interface ThemeContextType {
  isDarkMode: boolean;
  toggleDarkMode: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isDarkMode, setIsDarkMode] = useState(() => {
    // 초기 상태 로드
    const saved = safeLocalStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : false;
  });

  // 초기 로드 시 HTML 클래스 적용
  useEffect(() => {
    const applyDarkMode = (isDark: boolean) => {
      const htmlElement = document.documentElement;
      
      if (isDark) {
        htmlElement.classList.add('dark');
      } else {
        htmlElement.classList.remove('dark');
      }
      
      console.log('🎨 다크모드 적용:', {
        isDark,
        classList: htmlElement.classList.toString(),
        hasClass: htmlElement.classList.contains('dark')
      });
    };

    applyDarkMode(isDarkMode);
    safeLocalStorage.setItem('darkMode', JSON.stringify(isDarkMode));
  }, [isDarkMode]);

  const toggleDarkMode = () => {
    console.log('🎛️ toggleDarkMode 호출, 현재 값:', isDarkMode);
    setIsDarkMode((prev: boolean) => {
      const newValue = !prev;
      console.log('🔄 새로운 값:', newValue);
      return newValue;
    });
  };

  return (
    <ThemeContext.Provider value={{ isDarkMode, toggleDarkMode }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

