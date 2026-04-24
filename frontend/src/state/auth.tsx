import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { authApi } from "../api/cinelux";
import type { User } from "../types";

type Session = { token: string; refreshToken: string; userId: string; user: User | null };
type AuthContextValue = Session & {
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshProfile: () => Promise<void>;
  setUser: (user: User) => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);
const STORAGE_KEY = "cinelux.session";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session>(() => {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : { token: "", refreshToken: "", userId: "", user: null };
  });

  useEffect(() => {
    if (session.token) localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    else localStorage.removeItem(STORAGE_KEY);
  }, [session]);

  const refreshProfile = useCallback(async () => {
    if (!session.token || !session.userId) return;
    const user = await authApi.profile(session.userId, session.token);
    setSession((current) => ({ ...current, user }));
  }, [session.token, session.userId]);

  useEffect(() => {
    if (session.token && !session.user) void refreshProfile();
  }, [session.token, session.user, refreshProfile]);

  const login = useCallback(async (email: string, password: string) => {
    const response = await authApi.login(email, password);
    const user = await authApi.profile(response.userId, response.token);
    setSession({ ...response, user });
  }, []);

  const logout = useCallback(() => {
    setSession({ token: "", refreshToken: "", userId: "", user: null });
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      ...session,
      isAuthenticated: Boolean(session.token),
      login,
      logout,
      refreshProfile,
      setUser: (user) => setSession((current) => ({ ...current, user })),
    }),
    [session, login, logout, refreshProfile],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
