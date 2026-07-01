"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import api, { setToken, clearToken } from "@/lib/api";
import type { User, LoginRequest, RegisterRequest, TokenResponse } from "@/types";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(() => {
    if (typeof window === "undefined") return true;
    return Boolean(localStorage.getItem("access_token"));
  });

  const fetchUser = useCallback(async () => {
    try {
      const res = await api.get<User>("/users/me");
      setUser(res.data);
      localStorage.setItem("user", JSON.stringify(res.data));
    } catch {
      clearToken();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      void Promise.resolve().then(fetchUser);
    }
  }, [fetchUser]);

  const login = async (data: LoginRequest) => {
    queryClient.clear();
    const res = await api.post<TokenResponse>("/auth/login", {
      email: data.email,
      password: data.password,
    });
    setToken(res.data.access_token);
    await fetchUser();
  };

  const register = async (data: RegisterRequest) => {
    queryClient.clear();
    const res = await api.post<TokenResponse>("/auth/register", data);
    setToken(res.data.access_token);
    await fetchUser();
  };

  const logout = () => {
    queryClient.clear();
    clearToken();
    setUser(null);
    window.location.href = "/login";
  };

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, logout, isAuthenticated: !!user }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
