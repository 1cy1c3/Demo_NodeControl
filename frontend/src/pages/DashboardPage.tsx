import React, { useState, useEffect, useRef } from "react";
import {
  ArrowLeft,
  Activity,
  Server,
  Globe,
  Clock,
  Plus,
  Square,
  Play,
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import {
  getUserProjects,
  getInstanceStatus,
  streamLogsDocker,
} from "../services/auth";
import { useTheme } from "../components/ThemeContext";
import { Link } from "react-router-dom";
import { DateFormatter } from "../components/DateFormatter";


interface VPS {
  id: number;
  project_id: number;
  instance_id: string;
  version: string;
  network: string;
  creation_date: string;
  last_modified_date: string;
  project_name: string;
  ip_address: string;
  public_key: string;
  private_key: string;
  status?: string;
}

const capitalizeFirstLetter = (word: string): string => {
  if (word.length === 0) return word;
  return word.charAt(0).toUpperCase() + word.slice(1);
};

const EmptyStateCard: React.FC = () => {
  const { isDarkMode } = useTheme();

  return (
    <div className="d-flex justify-content-center align-items-center h-100">
      <div
        className="card"
        style={{
          backgroundColor: isDarkMode ? "rgba(40, 40, 40, 1)" : "white",
          borderRadius: "12px",
          border: isDarkMode ? "1px solid #444" : "1px solid #ddd",
          width: "100%",
          maxWidth: "500px",
          padding: "2rem",
        }}
      >
        <div className="card-body text-center">
          <h2
            className={`card-title mb-4 ${
              isDarkMode ? "text-light" : "text-dark"
            }`}
          >
            No Projects Yet
          </h2>
          <p
            className={`card-text mb-4 ${
              isDarkMode ? "text-light" : "text-dark"
            }`}
            style={{ fontSize: "1.1rem" }}
          >
            You haven't set up any projects. Get started by creating your first
            project!
          </p>
          <Link to="/products" className="btn btn-primary btn-lg">
            <Plus size={24} className="me-2" />
            Set Up a Project Now
          </Link>
        </div>
      </div>
    </div>
  );
};

const DashboardPage: React.FC = () => {
  const [vpsList, setVpsList] = useState<VPS[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedVPS, setSelectedVPS] = useState<VPS | null>(null);
  const { userId, userName } = useAuth();
  const { isDarkMode } = useTheme();

  useEffect(() => {
    const fetchData = async () => {
      if (!userId) {
        setError("User not authenticated");
        console.log(error);
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        // Simulate loading delay
        await new Promise((resolve) => setTimeout(resolve, 2000));

        const vpsData = await getUserProjects(userId);
        const instanceIds = vpsData.data.map((vps: VPS) => vps.instance_id);
        const statusesResponse = await getInstanceStatus(instanceIds);
        const statusesData = statusesResponse.statuses;

        const vpsListWithStatus = vpsData.data.map((vps: VPS) => {
          const status =
            statusesData?.find(
              (status: { instanceId: string; status: string }) =>
                status.instanceId === vps.instance_id
            )?.status || "unknown";
          return { ...vps, status };
        });

        setVpsList(vpsListWithStatus);
      } catch (e) {
        setError("Failed to fetch VPS data. Please try again later.");
        console.error("Error fetching VPS data:", e);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [userId, userName, error]);

  const handleVPSClick = (vps: VPS) => {
    setSelectedVPS(vps);
  };

  const handleBack = () => {
    setSelectedVPS(null);
  };

  return (
    <div className="container-fluid p-3">
      <h1 className={`my-4 ${isDarkMode ? "text-light" : "text-dark"}`}>
        {userName
          ? `Welcome to your VPS Dashboard, ${userName}`
          : "Welcome to your VPS Dashboard"}
      </h1>
      <div className="row">
        <div
          className={`col-md-3 mb-4 ${selectedVPS ? "d-none d-md-block" : ""}`}
        >
          <div className="list-group">
            {loading ? (
              Array.from({ length: 3 }).map((_, index) => (
                <div
                  key={index}
                  className={`list-group-item list-group-item-action d-flex justify-content-between align-items-center ${
                    isDarkMode ? "text-light bg-dark" : "text-dark bg-light"
                  }`}
                >
                  <span className="placeholder-glow w-75">
                    <span className="placeholder col-12"></span>
                  </span>
                  <span className="placeholder-glow w-25">
                    <span className="placeholder col-12"></span>
                  </span>
                </div>
              ))
            ) : vpsList.length === 0 ? (
              <EmptyStateCard />
            ) : (
              vpsList.map((vps) => (
                <button
                  key={vps.id}
                  className={`list-group-item list-group-item-action d-flex justify-content-between align-items-center ${
                    isDarkMode
                      ? selectedVPS?.id === vps.id
                        ? "list-group-item-secondary text-dark"
                        : "text-light bg-dark"
                      : selectedVPS?.id === vps.id
                      ? "list-group-item-secondary text-light"
                      : "text-dark bg-light"
                  }`}
                  onClick={() => handleVPSClick(vps)}
                >
                  <span>
                    {vps.project_name} - {vps.instance_id}
                  </span>
                  <span
                    className={`badge ${
                      vps.status === "running"
                        ? "bg-success"
                        : vps.status === "stopped"
                        ? "bg-secondary"
                        : vps.status === "starting"
                        ? "bg-info"
                        : vps.status === "stopping"
                        ? "bg-warning"
                        : "bg-danger"
                    }`}
                  >
                    {vps.status}
                  </span>
                </button>
              ))
            )}
          </div>
        </div>
        <div className={`col-md-9 ${selectedVPS ? "col-12" : ""}`}>
          {selectedVPS ? (
            <VPSDetails vps={selectedVPS} onBack={handleBack} />
          ) : (
            <VPSOverview
              vpsList={vpsList}
              onVPSClick={handleVPSClick}
              loading={loading}
            />
          )}
        </div>
      </div>
    </div>
  );
};

const VPSOverview: React.FC<{
  vpsList: VPS[];
  onVPSClick: (vps: VPS) => void;
  loading: boolean;
}> = ({ vpsList, onVPSClick, loading }) => {
  const { isDarkMode } = useTheme();

  if (loading) {
    return (
      <div className="row">
        {Array.from({ length: 6 }).map((_, index) => (
          <div key={index} className="col-md-4 col-sm-6 mb-4">
            <div
              className="card h-100"
              style={{
                backgroundColor: isDarkMode ? "rgba(40, 40, 40, 1)" : "white",
                borderRadius: "8px",
                border: isDarkMode ? "1px solid white" : "1px solid black",
              }}
            >
              <div className="card-body">
                <h5
                  className={`card-title placeholder-glow ${
                    isDarkMode ? "text-light" : "text-dark"
                  }`}
                >
                  <span className="placeholder col-6"></span>
                </h5>
                <p
                  className={`card-text placeholder-glow ${
                    isDarkMode ? "text-light" : "text-dark"
                  }`}
                >
                  <span className="placeholder col-4"></span>
                </p>
                <p
                  className={`card-text placeholder-glow ${
                    isDarkMode ? "text-light" : "text-dark"
                  }`}
                >
                  <span className="placeholder col-8"></span>
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="row">
      {vpsList.map((vps) => (
        <div key={vps.id} className="col-md-4 col-sm-6 mb-4">
          <div
            className="card h-100 cursor-pointer"
            onClick={() => onVPSClick(vps)}
            style={{
              backgroundColor: isDarkMode ? "rgba(40, 40, 40, 1)" : "white",
              borderRadius: "8px",
              cursor: "pointer",
              border: isDarkMode ? "1px solid white" : "1px solid black",
            }}
          >
            <div className="card-body">
              <h5
                className={`card-title ${
                  isDarkMode ? "text-light" : "text-dark"
                }`}
              >
                {vps.project_name} - {vps.instance_id}
              </h5>
              <p
                className={`card-text ${
                  isDarkMode ? "text-light" : "text-dark"
                }`}
              >
                Status: {vps.status}
              </p>
              <p
                className={`card-text ${
                  isDarkMode ? "text-light" : "text-dark"
                }`}
              >
                IP: {vps.ip_address}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

const VPSDetails: React.FC<{ vps: VPS; onBack: () => void }> = ({
  vps,
  onBack,
}) => {
  const { isDarkMode } = useTheme();
  const [logs, setLogs] = useState<string[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const toggleStreaming = () => {
    if (!isStreaming && vps.ip_address) {
      setIsStreaming(true);
      abortControllerRef.current = new AbortController();
      streamLogsDocker(
        vps.ip_address,
        (log) => {
          setLogs((prevLogs) => [...prevLogs, log]);
        },
        abortControllerRef.current
      )
        .then(() => {
          console.log("Streaming completed");
          setIsStreaming(false);
        })
        .catch((error) => {
          if (error.name !== "AbortError") {
            console.error("Streaming error:", error);
          }
          setIsStreaming(false);
        });
    } else {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
      setIsStreaming(false);
    }
  };

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return (
    <div className="vps-details">
      <button
        className="btn btn-link mb-3 p-0 d-flex align-items-center"
        onClick={onBack}
        aria-label="Go back"
      >
        <ArrowLeft size={24} className="me-2" />
        <span>Back to Overview</span>
      </button>

      <h2 className="mb-4">
        {vps.project_name} - {vps.instance_id}
      </h2>

      <div className="row mb-4">
        <div className="col-md-6 mb-3">
          <div
            className="card h-100"
            style={{
              backgroundColor: isDarkMode ? "rgba(40, 40, 40, 1)" : "white",
              borderRadius: "8px",
              border: isDarkMode ? "1px solid white" : "1px solid black",
            }}
          >
            <div className="card-header">
              <h5
                className={`card-title mb-0 ${
                  isDarkMode ? "text-light" : "text-dark"
                }`}
              >
                <Server className="me-2" size={20} />
                Status
              </h5>
            </div>
            <div className="card-body">
              <h3
                className={`mb-0 ${
                  vps.status === "running"
                    ? "text-success"
                    : vps.status === "stopped"
                    ? "text-warning"
                    : "text-danger"
                }`}
              >
                {vps.status
                  ? vps.status.charAt(0).toUpperCase() + vps.status.slice(1)
                  : "Unknown"}
              </h3>
            </div>
          </div>
        </div>
        <div className="col-md-6 mb-3">
          <div
            className="card h-100"
            style={{
              backgroundColor: isDarkMode ? "rgba(40, 40, 40, 1)" : "white",
              borderRadius: "8px",
              border: isDarkMode ? "1px solid white" : "1px solid black",
            }}
          >
            <div className="card-header">
              <h5
                className={`card-title mb-0 ${
                  isDarkMode ? "text-light" : "text-dark"
                }`}
              >
                <Globe className="me-2" size={20} />
                IP Address
              </h5>
            </div>
            <div className="card-body">
              <h3
                className={`card-text mb-0 ${
                  isDarkMode ? "text-light" : "text-dark"
                }`}
              >
                {vps.ip_address}
              </h3>
            </div>
          </div>
        </div>
      </div>

      <div className="row">
        <div className="col-md-4 mb-3">
          <div
            className="card h-100"
            style={{
              backgroundColor: isDarkMode ? "rgba(40, 40, 40, 1)" : "white",
              borderRadius: "8px",
              border: isDarkMode ? "1px solid white" : "1px solid black",
            }}
          >
            <div className="card-header">
              <h5
                className={`card-title mb-0 ${
                  isDarkMode ? "text-light" : "text-dark"
                }`}
              >
                <Activity className="me-2" size={20} />
                Network
              </h5>
            </div>
            <div className="card-body">
              <h3
                className={`card-text mb-0 ${
                  isDarkMode ? "text-light" : "text-dark"
                }`}
              >
                {capitalizeFirstLetter(vps.network)}
              </h3>
            </div>
          </div>
        </div>
        <div className="col-md-4 mb-3">
          <div
            className="card h-100"
            style={{
              backgroundColor: isDarkMode ? "rgba(40, 40, 40, 1)" : "white",
              borderRadius: "8px",
              border: isDarkMode ? "1px solid white" : "1px solid black",
            }}
          >
            <div className="card-header">
              <h5
                className={`card-title mb-0 ${
                  isDarkMode ? "text-light" : "text-dark"
                }`}
              >
                <Clock className="me-2" size={20} />
                Running since
              </h5>
            </div>
            <div className="card-body">
              <h3
                className={`card-text mb-0 ${
                  isDarkMode ? "text-light" : "text-dark"
                }`}
              >
                <DateFormatter dateString={vps.creation_date} />
              </h3>
              {/* <p
                className={`card-text mb-0 ${
                  isDarkMode ? "text-light" : "text-dark"
                }`}
              >
                {vps.private_key}
              </p> */}
            </div>
          </div>
        </div>
        <div className="col-md-4 mb-3">
          <div
            className="card h-100"
            style={{
              backgroundColor: isDarkMode ? "rgba(40, 40, 40, 1)" : "white",
              borderRadius: "8px",
              border: isDarkMode ? "1px solid white" : "1px solid black",
            }}
          >
            <div className="card-header">
              <h5
                className={`card-title mb-0 ${
                  isDarkMode ? "text-light" : "text-dark"
                }`}
              >
                <Server className="me-2" size={20} />
                Version
              </h5>
            </div>
            <div className="card-body">
              <h3
                className={`card-text mb-0 ${
                  isDarkMode ? "text-light" : "text-dark"
                }`}
              >
                {vps.version}
              </h3>
            </div>
          </div>
        </div>
      </div>

      {/* Log streaming section */}
      <div className="row mt-4">
        <div className="col-12">
          <div
            className="card"
            style={{
              backgroundColor: isDarkMode ? "rgba(40, 40, 40, 1)" : "white",
              borderRadius: "8px",
              border: isDarkMode ? "1px solid white" : "1px solid black",
            }}
          >
            <div className="card-header d-flex justify-content-between align-items-center">
              <h5
                className={`card-title mb-0 ${
                  isDarkMode ? "text-light" : "text-dark"
                }`}
              >
                Log Stream
              </h5>
              <button
                className={`btn ${isStreaming ? "btn-danger" : "btn-success"}`}
                onClick={toggleStreaming}
              >
                {isStreaming ? <Square size={20} /> : <Play size={20} />}
                {isStreaming ? " Stop" : " Start"} Stream
              </button>
            </div>
            <div className="card-body">
              <div
                style={{
                  height: "300px",
                  overflowY: "auto",
                  backgroundColor: isDarkMode ? "#1a1a1a" : "#f8f9fa",
                  padding: "10px",
                  borderRadius: "4px",
                }}
              >
                {logs.map((log, index) => (
                  <div
                    key={index}
                    className={isDarkMode ? "text-light" : "text-dark"}
                  >
                    {log}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
