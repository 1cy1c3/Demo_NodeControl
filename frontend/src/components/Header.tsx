import React, { useState, useEffect } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { Moon, Sun, Menu, LogOutIcon } from "lucide-react";
import { useTheme } from "./ThemeContext";

const Header: React.FC = () => {
  const { logout, isAuthenticated } = useAuth();
  const { isDarkMode, toggleDarkMode } = useTheme();
  const [isNavCollapsed, setIsNavCollapsed] = useState(true);

  const handleNavCollapse = () => setIsNavCollapsed(!isNavCollapsed);

  useEffect(() => {
    // Reset nav collapse state when authentication state changes
    setIsNavCollapsed(true);
  }, [isAuthenticated]);

  return (
    <header
      className={`bg-${isDarkMode ? "dark" : "light"} text-${
        isDarkMode ? "light" : "dark"
      }`}
    >
      <div className="container-fluid">
        <div className="d-flex justify-content-between align-items-center py-3">
          <NavLink className="text-decoration-none text-inherit fs-4" to="/">
            Node Control
          </NavLink>
          <button
            className="navbar-toggler d-lg-none"
            type="button"
            onClick={handleNavCollapse}
            aria-label="Toggle navigation"
          >
            <Menu className="w-6 h-6" />
          </button>
          <nav
            className={`${
              isNavCollapsed ? "d-none" : ""
            } d-lg-flex align-items-center`}
          >
            <NavLink className="nav-link px-3" to="/">
              Home
            </NavLink>
            {isAuthenticated && (
              <>
                <NavLink className="nav-link px-3" to="/products">
                  Products
                </NavLink>
                <NavLink className="nav-link px-3" to="/dashboard">
                  Dashboard
                </NavLink>
                <a
                  className="btn btn-link nav-link px-3"
                  onClick={logout}
                  aria-label="Logout"
                  href="/login"
                >
                  <LogOutIcon className="w-5 h-5" />
                </a>
              </>
            )}
            {!isAuthenticated && (
              <NavLink className="nav-link px-3" to="/login">
                Login
              </NavLink>
            )}
            <button
              className="btn btn-link nav-link px-3"
              onClick={toggleDarkMode}
              aria-label="Toggle dark mode"
            >
              {isDarkMode ? (
                <Sun className="w-5 h-5 text-yellow-400" />
              ) : (
                <Moon className="w-5 h-5 text-gray-700" />
              )}
            </button>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;
