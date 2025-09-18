import { useState, useEffect, type ReactNode } from "react";
import { AuthContext, type AuthContextType } from "./AuthContext";

interface Props { children: ReactNode; }

export const AuthProvider: React.FC<Props> = ({ children }) => {
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const saved = localStorage.getItem("token");
    if (saved) setToken(saved);
  }, []);

  const login: AuthContextType["login"] = (newToken) => {
    setToken(newToken);
    localStorage.setItem("token", newToken);
  };

  const logout: AuthContextType["logout"] = () => {
    setToken(null);
    localStorage.removeItem("token");
  };

  return (
    <AuthContext.Provider value={{ token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
