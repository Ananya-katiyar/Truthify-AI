import { useState, useEffect } from "react";
import SubmitContent from "./components/SubmitContent.jsx";
import Dashboard from "./components/Dashboard.jsx";
import AlertsPanel from "./components/AlertsPanel.jsx";
import DatabaseHub from "./components/DatabaseHub.jsx";
import { getStats } from "./api/client.js";

export default function App() {
  const [activeTab, setActiveTab] = useState("studio");
  const [refreshKey, setRefreshKey] = useState(0);
  const [stats, setStats] = useState({
    total_analyzed: 0,
    high_risk: 0,
    medium_risk: 0,
    low_risk: 0,
    pending_review: 0,
  });

  useEffect(() => {
    fetchStats();
  }, [refreshKey]);

  async function fetchStats() {
    try {
      const data = await getStats();
      if (data) setStats(data);
    } catch {
      // Backend may be starting or offline
    }
  }

  const handleRefresh = () => {
    setRefreshKey((k) => k + 1);
  };

  return (
    <div className="app-container">
      {/* Header Navigation */}
      <header className="navbar">
        <div className="brand-group">
          <div className="brand-icon">T</div>
          <div>
            <div className="brand-title">
              Truthify-AI
              <span style={{ fontSize: "0.65rem", padding: "2px 6px", background: "rgba(99,102,241,0.2)", color: "#818cf8", borderRadius: "4px", border: "1px solid rgba(99,102,241,0.3)" }}>
                MULTIMODAL & LIVE INTERNET
              </span>
            </div>
            <div className="brand-subtitle">
              Automated Misinformation Detection, Live Internet Fact-Checking & Knowledge Hub
            </div>
          </div>
        </div>

        <nav className="nav-tabs">
          <button
            type="button"
            className={`tab-btn ${activeTab === "studio" ? "active" : ""}`}
            onClick={() => setActiveTab("studio")}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 20h9M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
            </svg>
            Detection Studio
          </button>
          <button
            type="button"
            className={`tab-btn ${activeTab === "database" ? "active" : ""}`}
            onClick={() => setActiveTab("database")}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <ellipse cx="12" cy="5" rx="9" ry="3" />
              <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
              <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
            </svg>
            Database & Sources
          </button>
          <button
            type="button"
            className={`tab-btn ${activeTab === "dashboard" ? "active" : ""}`}
            onClick={() => setActiveTab("dashboard")}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="7" height="9" />
              <rect x="14" y="3" width="7" height="5" />
              <rect x="14" y="12" width="7" height="9" />
              <rect x="3" y="16" width="7" height="5" />
            </svg>
            Feed & Ledger
          </button>
          <button
            type="button"
            className={`tab-btn ${activeTab === "alerts" ? "active" : ""}`}
            onClick={() => setActiveTab("alerts")}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              <line x1="12" y1="9" x2="12" y2="13" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
            Alerts
            {stats.pending_review > 0 && (
              <span className="badge-count">{stats.pending_review}</span>
            )}
          </button>
        </nav>
      </header>

      {/* Overview Stat Cards */}
      <section className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Evaluated</div>
          <div className="stat-value stat-total">{stats.total_analyzed}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">High Risk Flagged</div>
          <div className="stat-value stat-high">{stats.high_risk}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Medium Risk</div>
          <div className="stat-value stat-med">{stats.medium_risk}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Verified Low Risk</div>
          <div className="stat-value stat-low">{stats.low_risk}</div>
        </div>
      </section>

      {/* Main Viewport Panels */}
      <main>
        {activeTab === "studio" && (
          <>
            <SubmitContent onAnalyzed={handleRefresh} onFactAdded={handleRefresh} />
            <div style={{ marginTop: "32px" }}>
              <Dashboard refreshKey={refreshKey} />
            </div>
          </>
        )}

        {activeTab === "database" && (
          <DatabaseHub onDatabaseChanged={handleRefresh} />
        )}

        {activeTab === "dashboard" && (
          <Dashboard refreshKey={refreshKey} />
        )}

        {activeTab === "alerts" && (
          <AlertsPanel refreshKey={refreshKey} onAlertResolved={handleRefresh} />
        )}
      </main>

      {/* System Footer */}
      <footer style={{ marginTop: "48px", paddingTop: "24px", borderTop: "1px solid var(--border-subtle)", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px", fontSize: "0.8rem", color: "var(--text-muted)" }}>
        <div>
          Truthify-AI: Multimodal (Images/Videos/PDFs) • Live Internet Verification (Reuters, WHO, CDC, Wikipedia) • Self-Expanding Knowledge DB
        </div>
        <div style={{ display: "flex", gap: "16px" }}>
          <span>Backend: Port 8000</span>
          <span>AI Microservice: Port 8001</span>
          <span>Frontend: Port 5173</span>
        </div>
      </footer>
    </div>
  );
}
