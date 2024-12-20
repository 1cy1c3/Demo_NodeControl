import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login, register } from "../services/auth";
import { useAuth } from "../contexts/AuthContext";

const AuthPage: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [username, setUsername] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { login: authLogin } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (isLogin) {
        const response = await login(email, password);
        console.log(response);
        authLogin(response.user_id, response.user_name);
        navigate("/dashboard");
      } else {
        const response = await register(username, email, password);
        console.log(response);
        setIsLogin(true);
        setError("Registration successful! Please verify your e-mail address.");
      }
    } catch (err: any) {
      console.error("Auth error:", err);
      if (err.response) {
        console.error("Response data:", err.response.data);
        console.error("Response status:", err.response.status);
        console.error("Response headers:", err.response.headers);
      } else if (err.request) {
        console.error("No response received:", err.request);
      } else {
        console.error("Error message:", err.message);
      }
      setError(
        isLogin
          ? "Login failed. Please check your credentials."
          : "Registration failed. Please try again."
      );
    }
  };

  return (
    <div className="container mt-5">
      <div className="row justify-content-center">
        <div className="col-md-6">
          <div className="card bg-light dark:bg-dark">
            <div className="card-body">
              <h2 className="card-title text-center mb-4">
                {isLogin ? "Login" : "Register"}
              </h2>
              <form onSubmit={handleSubmit}>
                {!isLogin && (
                  <div className="mb-3">
                    <label htmlFor="username" className="form-label">
                      Username
                    </label>
                    <input
                      type="text"
                      className="form-control bg-light dark:bg-dark"
                      id="username"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      required
                    />
                  </div>
                )}
                <div className="mb-3">
                  <label htmlFor="email" className="form-label">
                    Email
                  </label>
                  <input
                    type="email"
                    className="form-control bg-light dark:bg-dark"
                    id="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
                <div className="mb-3">
                  <label htmlFor="password" className="form-label">
                    Password
                  </label>
                  <input
                    type="password"
                    className="form-control bg-light dark:bg-dark"
                    id="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>
                <button type="submit" className="btn btn-secondary w-100">
                  {isLogin ? "Login" : "Register"}
                </button>
              </form>
              {error && <p className="text-danger mt-3">{error}</p>}
              <p className="mt-3 text-center">
                {isLogin
                  ? "Don't have an account?"
                  : "Already have an account?"}
                <button
                  className="btn btn-link"
                  onClick={() => setIsLogin(!isLogin)}
                >
                  {isLogin ? "Register" : "Login"}
                </button>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
