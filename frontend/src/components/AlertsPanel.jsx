import { useEffect, useState } from "react";
import { getAlerts, markReviewed } from "../api/client.js";

export default function AlertsPanel({ refreshKey, onAlertResolved }) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeReviewId, setActiveReviewId] = useState(null);
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchAlerts();
  }, [refreshKey]);

  async function fetchAlerts() {
    setLoading(true);
    try {
      const data = await getAlerts();
      setAlerts(data || []);
    } catch (err) {
      console.error("Failed to fetch alerts:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleReviewSubmit(contentId) {
    setSubmitting(true);
    try {
      await markReviewed(contentId, notes || "Reviewed and validated by human operator");
      setAlerts((prev) => prev.filter((a) => a.content_id !== contentId));
      setActiveReviewId(null);
      setNotes("");
      onAlertResolved?.();
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="glass-panel" style={{ border: alerts.length > 0 ? "1px solid var(--risk-high-border)" : undefined }}>
      <div className="panel-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
            {alerts.length > 0 && <span className="alert-pulse"></span>}
            <h2 className="panel-title" style={{ margin: 0 }}>
              High-Risk Misinformation Alerts
            </h2>
            <span className="badge-count">{alerts.length}</span>
          </div>
          <p className="panel-description">
            Content flagged as High Risk (Score ≥ 60) requiring human-in-the-loop verification before dissemination.
          </p>
        </div>

        <button
          type="button"
          className="btn-secondary"
          onClick={fetchAlerts}
          disabled={loading}
          style={{ fontSize: "0.8rem" }}
        >
          {loading ? "Refreshing..." : "↻ Refresh Alerts"}
        </button>
      </div>

      {alerts.length === 0 ? (
        <div className="empty-state" style={{ padding: "36px 16px" }}>
          <div style={{ fontSize: "2rem", marginBottom: "8px" }}>🛡️</div>
          <h3 style={{ color: "var(--risk-low)", fontSize: "1.05rem" }}>System All-Clear</h3>
          <p style={{ fontSize: "0.85rem", marginTop: "4px", color: "var(--text-muted)" }}>
            No unresolved high-risk alerts currently pending review.
          </p>
        </div>
      ) : (
        <div>
          {alerts.map((alert) => {
            const isReviewing = activeReviewId === alert.content_id;
            return (
              <div key={alert.content_id} className="alert-card">
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px", flexWrap: "wrap" }}>
                    <span className="risk-badge high" style={{ fontSize: "0.75rem", padding: "2px 8px" }}>
                      Risk Score: {alert.risk_score}/100
                    </span>
                    <span className="badge-tag" style={{ fontSize: "0.7rem" }}>
                      {alert.source_type || "social_media"}
                    </span>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                      ID: {alert.content_id.slice(0, 8)}
                    </span>
                  </div>

                  <p style={{ fontSize: "0.95rem", color: "var(--text-primary)", fontWeight: "500", marginBottom: "10px", lineHeight: 1.5 }}>
                    "{alert.input_text}"
                  </p>

                  {alert.explanation && alert.explanation.length > 0 && (
                    <div style={{ background: "rgba(0,0,0,0.2)", padding: "10px 14px", borderRadius: "var(--radius-sm)", marginBottom: "12px" }}>
                      <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: "600", display: "block", marginBottom: "4px" }}>
                        Flagging Reasons:
                      </span>
                      <ul style={{ paddingLeft: "16px", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                        {alert.explanation.map((exp, i) => (
                          <li key={i}>{exp}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {isReviewing ? (
                    <div style={{ marginTop: "12px", background: "rgba(0,0,0,0.4)", padding: "14px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
                      <label className="form-label" style={{ fontSize: "0.8rem" }}>
                        Reviewer Notes & Action:
                      </label>
                      <input
                        type="text"
                        placeholder="e.g. Confirmed false medical claim, issued takedown or counter-notice"
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        style={{
                          width: "100%",
                          background: "var(--bg-input)",
                          border: "1px solid var(--border-subtle)",
                          borderRadius: "var(--radius-sm)",
                          padding: "8px 12px",
                          color: "var(--text-primary)",
                          fontSize: "0.85rem",
                          marginBottom: "10px",
                          outline: "none",
                        }}
                      />
                      <div style={{ display: "flex", gap: "8px" }}>
                        <button
                          type="button"
                          className="btn-primary"
                          style={{ padding: "8px 16px", fontSize: "0.8rem" }}
                          disabled={submitting}
                          onClick={() => handleReviewSubmit(alert.content_id)}
                        >
                          {submitting ? "Resolving..." : "Confirm Review & Resolve"}
                        </button>
                        <button
                          type="button"
                          className="btn-secondary"
                          style={{ fontSize: "0.8rem" }}
                          onClick={() => {
                            setActiveReviewId(null);
                            setNotes("");
                          }}
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      type="button"
                      className="btn-primary"
                      style={{
                        background: "var(--risk-high)",
                        padding: "8px 16px",
                        fontSize: "0.8rem",
                        boxShadow: "0 2px 10px rgba(244, 63, 94, 0.4)",
                      }}
                      onClick={() => setActiveReviewId(alert.content_id)}
                    >
                      Conduct Human Review
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
