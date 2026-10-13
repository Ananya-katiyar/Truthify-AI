import { useEffect, useState } from "react";
import { listContent } from "../api/client.js";

export default function Dashboard({ refreshKey }) {
  const [items, setItems] = useState([]);
  const [filter, setFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    fetchItems();
  }, [filter, refreshKey]);

  async function fetchItems() {
    setLoading(true);
    try {
      const data = await listContent(filter || null);
      setItems(data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  const filteredItems = items.filter((item) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.input_text.toLowerCase().includes(q) ||
      (item.summary && item.summary.toLowerCase().includes(q)) ||
      (item.risk_level && item.risk_level.toLowerCase().includes(q)) ||
      (item.media_type && item.media_type.toLowerCase().includes(q)) ||
      (item.media_filename && item.media_filename.toLowerCase().includes(q))
    );
  });

  const getMediaBadge = (mediaType) => {
    switch (mediaType) {
      case "image":
        return <span style={{ fontSize: "0.7rem", padding: "2px 6px", background: "rgba(56,189,248,0.15)", color: "#38bdf8", borderRadius: "4px" }}>🖼️ Image</span>;
      case "video":
        return <span style={{ fontSize: "0.7rem", padding: "2px 6px", background: "rgba(168,85,247,0.15)", color: "#c084fc", borderRadius: "4px" }}>🎥 Video</span>;
      case "pdf":
        return <span style={{ fontSize: "0.7rem", padding: "2px 6px", background: "rgba(239,68,68,0.15)", color: "#f87171", borderRadius: "4px" }}>📄 PDF</span>;
      default:
        return <span style={{ fontSize: "0.7rem", padding: "2px 6px", background: "rgba(148,163,184,0.15)", color: "#94a3b8", borderRadius: "4px" }}>📝 Text</span>;
    }
  };

  return (
    <div className="glass-panel">
      <div className="panel-header">
        <h2 className="panel-title">Monitoring & Ingestion Feed</h2>
        <p className="panel-description">
          Real-time ledger of all submitted posts, media files, evaluated risks, and live internet verification citations.
        </p>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px", marginBottom: "16px" }}>
        <div className="filter-bar" style={{ margin: 0 }}>
          <button
            type="button"
            className={`filter-btn ${filter === "" ? "active" : ""}`}
            onClick={() => setFilter("")}
          >
            All Analyses ({items.length})
          </button>
          <button
            type="button"
            className={`filter-btn ${filter === "high" ? "active" : ""}`}
            onClick={() => setFilter("high")}
          >
            High Risk
          </button>
          <button
            type="button"
            className={`filter-btn ${filter === "medium" ? "active" : ""}`}
            onClick={() => setFilter("medium")}
          >
            Medium Risk
          </button>
          <button
            type="button"
            className={`filter-btn ${filter === "low" ? "active" : ""}`}
            onClick={() => setFilter("low")}
          >
            Low Risk
          </button>
        </div>

        <div style={{ minWidth: "240px" }}>
          <input
            type="text"
            placeholder="Search feed contents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: "100%",
              background: "var(--bg-input)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-sm)",
              padding: "8px 12px",
              color: "var(--text-primary)",
              fontSize: "0.85rem",
              outline: "none",
            }}
          />
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: "center", padding: "40px 0" }}>
          <span className="spinner"></span>
          <p style={{ marginTop: "8px", fontSize: "0.85rem", color: "var(--text-muted)" }}>
            Loading analyses...
          </p>
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">🔍</div>
          <h3>No Analyzed Content Found</h3>
          <p style={{ marginTop: "4px", fontSize: "0.875rem" }}>
            Submit an article, image, video, or PDF document above to see real-time detection results in this dashboard.
          </p>
        </div>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table className="custom-table">
            <thead>
              <tr>
                <th style={{ width: "42%" }}>Submitted Content</th>
                <th>Format</th>
                <th>Risk Verdict</th>
                <th>Score</th>
                <th>Claims</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.map((item) => {
                const isExpanded = expandedId === item.content_id;
                return (
                  <tr key={item.content_id}>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                        {getMediaBadge(item.media_type)}
                        {item.media_filename && (
                          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                            {item.media_filename}
                          </span>
                        )}
                      </div>
                      <div style={{ fontWeight: "500", color: "var(--text-primary)", marginBottom: "4px" }}>
                        {isExpanded ? item.input_text : `${item.input_text.slice(0, 95)}...`}
                      </div>
                      {item.summary && (
                        <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                          {item.summary.slice(0, 80)}...
                        </div>
                      )}

                      {/* Expanded View */}
                      {isExpanded && (
                        <div style={{ marginTop: "12px", padding: "12px", background: "rgba(0,0,0,0.3)", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
                          {item.thumbnail_b64 && (
                            <div style={{ marginBottom: "10px" }}>
                              <img
                                src={item.thumbnail_b64}
                                alt="Media preview"
                                style={{ maxWidth: "160px", maxHeight: "100px", borderRadius: "6px" }}
                              />
                            </div>
                          )}
                          <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "8px" }}>
                            <strong>Summary:</strong> {item.summary}
                          </div>
                          {item.fact_check && item.fact_check.length > 0 && (
                            <div style={{ marginTop: "8px" }}>
                              <strong style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                                Internet Citations:
                              </strong>
                              {item.fact_check.map((fc, i) => (
                                <div key={i} style={{ fontSize: "0.75rem", marginBottom: "4px" }}>
                                  • <strong>{fc.claim}</strong> &rarr; <span style={{ color: fc.verdict === "confirmed_true" ? "#34d399" : fc.verdict === "debunked_as_false" ? "#f43f5e" : "#fbbf24" }}>{fc.verdict}</span> ({fc.source || "Web"})
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </td>
                    <td>
                      <span className="badge-tag" style={{ fontSize: "0.7rem" }}>
                        {item.source_type || "user_submitted"}
                      </span>
                    </td>
                    <td>
                      <span className={`risk-badge ${item.risk_level}`} style={{ fontSize: "0.75rem", padding: "3px 10px" }}>
                        {item.risk_level}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontFamily: "var(--font-mono)", fontWeight: "600" }}>
                        {item.risk_score}
                      </span>
                      <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>/100</span>
                    </td>
                    <td>
                      <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                        {item.extracted_claims ? `${item.extracted_claims.length} claims` : "0"}
                      </span>
                    </td>
                    <td>
                      <button
                        type="button"
                        className="btn-secondary"
                        style={{ fontSize: "0.75rem", padding: "4px 10px" }}
                        onClick={() => setExpandedId(isExpanded ? null : item.content_id)}
                      >
                        {isExpanded ? "Collapse" : "Inspect"}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
