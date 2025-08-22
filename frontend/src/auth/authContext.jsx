// src/auth/AuthContext.jsx
import { createContext, useContext, useEffect, useState } from "react";
import { me } from "@/api/auth";

const AuthCtx = createContext({
  user: null,
  loading: true,
  refresh: async () => {},
});

export function useAuth() {
  return useContext(AuthCtx);
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    try {
      const u = await me();
      setUser(u);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  return (
    <AuthCtx.Provider value={{ user, loading, refresh }}>
      {children}
    </AuthCtx.Provider>
  );
}
