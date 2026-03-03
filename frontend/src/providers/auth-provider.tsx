"use client";

import { SessionProvider } from "next-auth/react";
import { useSession, signIn, signOut } from "next-auth/react";
import type { UserProfile } from "@/lib/api";

interface AuthContextType {
  user: UserProfile | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (
    email: string,
    password: string,
    fullName: string
  ) => Promise<void>;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider>
      <AuthProviderInternal>{children}</AuthProviderInternal>
    </SessionProvider>
  );
}

function AuthProviderInternal({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession();
  
  const isLoading = status === "loading";
  const isAuthenticated = status === "authenticated";
  const user = session?.user ? {
    id: (session.user as Record<string, unknown>).id as string || "",
    email: session.user.email || "",
    full_name: session.user.name || "",
    is_active: true,
    created_at: "",
  } : null;

  const login = async (email: string, password: string) => {
    const result = await signIn("credentials", {
      email,
      password,
      redirect: false,
    });
    if (result?.error) {
      throw new Error("Invalid email or password");
    }
  };

  const logout = () => {
    signOut({ callbackUrl: "/login" });
  };

  const register = async (email: string, password: string, fullName: string) => {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Registration failed");
    }
    await login(email, password);
  };

  return (
    <AuthContextInternal.Provider
      value={{
        user,
        isLoading,
        isAuthenticated,
        login,
        logout,
        register,
      }}
    >
      {children}
    </AuthContextInternal.Provider>
  );
}

import { createContext, useContext } from "react";

const AuthContextInternal = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContextInternal);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
