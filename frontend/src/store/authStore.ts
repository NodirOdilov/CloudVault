import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import apiClient from '../api/client';

interface User {
  id: string;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  full_name: string;
  avatar: string;
  storage_quota: {
    quota_bytes: number;
    used_bytes: number;
    usage_percentage: number;
    available_bytes: number;
  } | null;
  storage_used_display: string;
  storage_quota_display: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    email: string;
    username: string;
    password: string;
    password_confirm: string;
    first_name?: string;
    last_name?: string;
  }) => Promise<void>;
  logout: () => Promise<void>;
  fetchProfile: () => Promise<void>;
  updateProfile: (data: Partial<User>) => Promise<void>;
  changePassword: (
    oldPassword: string,
    newPassword: string,
    newPasswordConfirm: string
  ) => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      (set) => ({
        user: null,
        isAuthenticated: !!localStorage.getItem('access_token'),
        isLoading: false,
        error: null,

        login: async (email, password) => {
          set({ isLoading: true, error: null });
          try {
            const response = await apiClient.post('/auth/login/', {
              email,
              password,
            });
            const { user, tokens } = response.data;
            localStorage.setItem('access_token', tokens.access);
            localStorage.setItem('refresh_token', tokens.refresh);
            set({ user, isAuthenticated: true, isLoading: false });
          } catch (err: any) {
            const message =
              err.response?.data?.message ||
              err.response?.data?.detail ||
              'Login failed. Please check your credentials.';
            set({ error: message, isLoading: false });
            throw new Error(message);
          }
        },

        register: async (data) => {
          set({ isLoading: true, error: null });
          try {
            const response = await apiClient.post('/auth/register/', data);
            const { user, tokens } = response.data;
            localStorage.setItem('access_token', tokens.access);
            localStorage.setItem('refresh_token', tokens.refresh);
            set({ user, isAuthenticated: true, isLoading: false });
          } catch (err: any) {
            const message =
              err.response?.data?.message || 'Registration failed.';
            set({ error: message, isLoading: false });
            throw new Error(message);
          }
        },

        logout: async () => {
          try {
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
              await apiClient.post('/auth/logout/', {
                refresh: refreshToken,
              });
            }
          } catch {
            // Silently handle logout errors
          } finally {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            set({
              user: null,
              isAuthenticated: false,
              error: null,
            });
          }
        },

        fetchProfile: async () => {
          set({ isLoading: true });
          try {
            const response = await apiClient.get('/auth/profile/');
            set({ user: response.data, isLoading: false });
          } catch (err: any) {
            set({ isLoading: false });
            if (err.response?.status === 401) {
              localStorage.removeItem('access_token');
              localStorage.removeItem('refresh_token');
              set({ isAuthenticated: false, user: null });
            }
          }
        },

        updateProfile: async (data) => {
          set({ isLoading: true, error: null });
          try {
            const response = await apiClient.patch('/auth/profile/', data);
            set({ user: response.data, isLoading: false });
          } catch (err: any) {
            set({
              error: err.response?.data?.message || 'Failed to update profile.',
              isLoading: false,
            });
          }
        },

        changePassword: async (oldPassword, newPassword, newPasswordConfirm) => {
          set({ isLoading: true, error: null });
          try {
            await apiClient.post('/auth/change-password/', {
              old_password: oldPassword,
              new_password: newPassword,
              new_password_confirm: newPasswordConfirm,
            });
            set({ isLoading: false });
          } catch (err: any) {
            const message =
              err.response?.data?.message || 'Failed to change password.';
            set({ error: message, isLoading: false });
            throw new Error(message);
          }
        },

        clearError: () => set({ error: null }),
      }),
      {
        name: 'auth-storage',
        partialize: (state) => ({
          isAuthenticated: state.isAuthenticated,
        }),
      }
    ),
    { name: 'auth-store' }
  )
);
