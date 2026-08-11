import { create } from 'zustand';

import { api, setAuthToken } from '@/lib/api';
import { loadStoredAuth, saveStoredAuth, clearStoredAuth } from '@/lib/storage';
import type { User } from '@/lib/types';

type AuthState = {
  user: User | null;
  token: string | null;
  hydrated: boolean;
  hydrate: () => Promise<void>;
  login: (account: string, password: string) => Promise<void>;
  register: (username: string, password: string, email?: string) => Promise<void>;
  logout: () => Promise<void>;
  setUser: (user: User) => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  hydrated: false,

  hydrate: async () => {
    const stored = await loadStoredAuth();
    if (stored) {
      setAuthToken(stored.access_token);
      set({ user: stored.user, token: stored.access_token, hydrated: true });
    } else {
      set({ hydrated: true });
    }
  },

  login: async (account, password) => {
    const resp = await api.post<{ access_token: string; user: User }>(
      '/auth/login',
      { account, password },
    );
    setAuthToken(resp.access_token);
    await saveStoredAuth({ access_token: resp.access_token, user: resp.user });
    set({ user: resp.user, token: resp.access_token });
  },

  register: async (username, password, email) => {
    const resp = await api.post<{ access_token: string; user: User }>(
      '/auth/register',
      { username, password, email: email || null },
    );
    setAuthToken(resp.access_token);
    await saveStoredAuth({ access_token: resp.access_token, user: resp.user });
    set({ user: resp.user, token: resp.access_token });
  },

  logout: async () => {
    setAuthToken(null);
    await clearStoredAuth();
    set({ user: null, token: null });
  },

  setUser: (user) => set({ user }),
}));
