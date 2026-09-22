import { createContext, useContext, useEffect, useState } from "react";
import { getCurrentUser, login as loginRequest, logout as logoutRequest } from "../api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      return;
    }

    getCurrentUser()
      .then((res) => setUser(res.data))
      .catch(() => localStorage.removeItem("access_token"))
      .finally(() => setLoading(false));
  }, []);

  async function login(credentials) {
    const { data } = await loginRequest(credentials);
    localStorage.setItem("access_token", data.access_token);
    const { data: me } = await getCurrentUser();
    setUser(me);
  }

  async function logout() {
    try {
      await logoutRequest();
    } catch {
      // token may already be expired/invalid server-side; clear local state regardless
    }
    localStorage.removeItem("access_token");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
