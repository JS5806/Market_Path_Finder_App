/**
 * 인증 상태 관리 (Zustand)
 * 역할(role) 기반: admin, manager, customer
 */
import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { userAPI } from '../services/api';

export type UserRole = 'admin' | 'manager' | 'customer';

interface User {
  user_id: string;
  email: string;
  user_name: string;
  role: UserRole;
  age_group?: string;
  preferred_categories?: string[];
  preferred_store_id?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;

  login: (email: string, password: string) => Promise<boolean>;
  register: (email: string, password: string, userName: string) => Promise<boolean>;
  logout: () => Promise<void>;
  loadToken: () => Promise<void>;
  fetchProfile: () => Promise<void>;
  clearError: () => void;
}

/**
 * 이메일 도메인으로 역할 판별 (프론트엔드 보조용)
 * 실제 역할은 서버 응답(JWT/프로필)에서 결정
 */
export function getRoleFromEmail(email: string): UserRole {
  const domain = email.split('@')[1]?.toLowerCase() || '';
  if (domain === 'admin.smartmart.com') return 'admin';
  if (domain === 'manager.smartmart.com') return 'manager';
  return 'customer';
}

export function getRoleLabel(role: UserRole): string {
  switch (role) {
    case 'admin': return '프로그램 관리자';
    case 'manager': return '마트 관리자';
    case 'customer': return '일반 사용자';
    default: return '사용자';
  }
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const res = await userAPI.login({ email, password });
      const { access_token, user_id, user_name, role } = res.data.data;
      await AsyncStorage.setItem('access_token', access_token);
      set({
        token: access_token,
        user: { user_id, email, user_name, role: role || getRoleFromEmail(email) },
        isLoading: false,
      });
      return true;
    } catch (e: any) {
      const msg = e.response?.data?.detail || '로그인에 실패했습니다';
      set({ error: msg, isLoading: false });
      return false;
    }
  },

  register: async (email, password, userName) => {
    set({ isLoading: true, error: null });
    try {
      await userAPI.register({ email, password, user_name: userName });
      set({ isLoading: false });
      return true;
    } catch (e: any) {
      const msg = e.response?.data?.detail || '회원가입에 실패했습니다';
      set({ error: msg, isLoading: false });
      return false;
    }
  },

  logout: async () => {
    await AsyncStorage.removeItem('access_token');
    set({ user: null, token: null });
  },

  loadToken: async () => {
    const token = await AsyncStorage.getItem('access_token');
    if (token) {
      set({ token });
      await get().fetchProfile();
    }
  },

  fetchProfile: async () => {
    try {
      const res = await userAPI.getProfile();
      const data = res.data.data;
      set({
        user: {
          ...data,
          role: data.role || getRoleFromEmail(data.email || ''),
        },
      });
    } catch {
      set({ user: null, token: null });
      await AsyncStorage.removeItem('access_token');
    }
  },

  clearError: () => set({ error: null }),
}));
