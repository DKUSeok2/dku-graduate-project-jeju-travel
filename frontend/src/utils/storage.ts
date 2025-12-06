/**
 * 안전한 localStorage/sessionStorage 접근 헬퍼
 * 개인정보 보호 모드나 저장소가 차단된 환경에서도 에러 없이 작동
 */

export const safeLocalStorage = {
  getItem: (key: string): string | null => {
    try {
      return localStorage.getItem(key);
    } catch (error) {
      // 개인정보 보호 모드 등에서 접근 불가
      return null;
    }
  },

  setItem: (key: string, value: string): boolean => {
    try {
      localStorage.setItem(key, value);
      return true;
    } catch (error) {
      // 개인정보 보호 모드 등에서 접근 불가
      return false;
    }
  },

  removeItem: (key: string): void => {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      // 개인정보 보호 모드 등에서 접근 불가
      // 무시
    }
  },

  clear: (): void => {
    try {
      localStorage.clear();
    } catch (error) {
      // 무시
    }
  }
};

export const safeSessionStorage = {
  getItem: (key: string): string | null => {
    try {
      return sessionStorage.getItem(key);
    } catch (error) {
      return null;
    }
  },

  setItem: (key: string, value: string): boolean => {
    try {
      sessionStorage.setItem(key, value);
      return true;
    } catch (error) {
      return false;
    }
  },

  removeItem: (key: string): void => {
    try {
      sessionStorage.removeItem(key);
    } catch (error) {
      // 무시
    }
  }
};

