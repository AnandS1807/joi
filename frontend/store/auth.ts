import { create } from "zustand";
import { authApi } from "@/lib/api";

interface User {
  id: string;
  email: string;
  full_name?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;

  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, full_name?: string) => Promise<void>;
  logout: () => void;
  hydrate: () => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isLoading: false,
  error: null,

  hydrate: () => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem("access_token");
    const user = localStorage.getItem("user");
    if (token && user) {
      set({ token, user: JSON.parse(user) });
    }
  },

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const res = await authApi.login({ email, password });
      const { access_token } = res.data;
      localStorage.setItem("access_token", access_token);

      // Backend login response does not include profile, so keep existing user or a lightweight placeholder.
      const existing = localStorage.getItem("user");
      const user = existing
        ? (JSON.parse(existing) as User)
        : { id: "", email, full_name: email.split("@")[0] };
      localStorage.setItem("user", JSON.stringify(user));

      set({ token: access_token, user, isLoading: false });
    } catch (err: any) {
      set({ error: err.response?.data?.detail || "Login failed", isLoading: false });
      throw err;
    }
  },

  register: async (email, password, full_name) => {
    set({ isLoading: true, error: null });
    try {
      const res = await authApi.register({ email, password, full_name });
      localStorage.setItem("user", JSON.stringify(res.data));
      set({ user: res.data, isLoading: false });
    } catch (err: any) {
      set({ error: err.response?.data?.detail || "Registration failed", isLoading: false });
      throw err;
    }
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    set({ user: null, token: null });
    window.location.href = "/login";
  },

  clearError: () => set({ error: null }),
}));