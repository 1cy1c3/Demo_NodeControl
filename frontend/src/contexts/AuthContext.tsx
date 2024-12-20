import React, {
  createContext,
  useState,
  useContext,
  useEffect,
  ReactNode,
} from "react";

interface AuthContextType {
  userId: number | null;
  userName: string | null;
  isAuthenticated: boolean;
  login: (id: number, name: string) => void;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(
  undefined
);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [userId, setUserId] = useState<number | null>(null);
  const [userName, setUserName] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);

  useEffect(() => {
    const storedUserId = localStorage.getItem("userId");
    const storedUserName = localStorage.getItem("userName");
    if (storedUserId && storedUserName) {
      const parsedUserId = parseInt(storedUserId, 10);
      setUserId(parsedUserId);
      setUserName(storedUserName);
      setIsAuthenticated(true);
    }
  }, []);

  const login = (id: number, name: string) => {
    setUserId(id);
    setUserName(name);
    setIsAuthenticated(true);
    localStorage.setItem("userId", id.toString());
    localStorage.setItem("userName", name);
  };

  const logout = () => {
    setUserId(null);
    setUserName(null);
    setIsAuthenticated(false);
    localStorage.removeItem("userId");
    localStorage.removeItem("userName");
  };

  const value = {
    userId,
    userName,
    isAuthenticated,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
