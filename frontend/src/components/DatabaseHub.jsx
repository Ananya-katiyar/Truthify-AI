import { useState, useEffect } from "react";
import {
  getDatabaseOverview,
  listVerifiedFacts,
  addVerifiedFact,
  deleteVerifiedFact,
  listTrustedSources,
  addTrustedSource,
  deleteTrustedSource,
} from "../api/client.js";

export default function DatabaseHub({ onDatabaseChanged }) {
  const [subTab, setSubTab] = useState("facts");
  const [overview, setOverview] = useState(null);
  const [facts, setFacts] = useState([]);
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Filters for facts
  const [searchQuery, setSearchQuery] = useState("");
  const [topicFilter, setTopicFilter] = useState("");
  const [verdictFilter, setVerdictFilter] = useState("");

  // Modal / Form state for adding fact
  const [showFactModal, setShowFactModal] = useState(false);
  const [newFact, setNewFact] = useState({
    claim: "",
    verdict: "debunked_as_false",
    explanation: "",
    source_name: "",
    source_url: "",
    topic: "general",
    trust_score: 0.95,
  });

  // Form state for adding trusted source
  const [showSourceModal, setShowSourceModal] = useState(false);
  const [newSource, setNewSource] = useState({
    domain: "",
    name: "",
    category: "fact_checker",
    trust_score: 0.95,
  });

  useEffect(() => {
    loadOverview();
    if (subTab === "facts") {
      loadFacts();
    } else if (subTab === "sources") {
      loadSources();
    }
  }, [subTab, topicFilter, verdictFilter]);

  async function loadOverview() {
    try {
      const data = await getDatabaseOverview();
      setOverview(data);
    } catch (err) {
      console.warn("Could not load overview:", err);
    }
  }

  async function loadFacts() {
    setLoading(true);
    setError(null);
    try {
      const data = await listVerifiedFacts(
        topicFilter || null,
        verdictFilter || null,
        searchQuery || null
      );
      setFacts(data);
    } catch (err) {
      setError("Failed to load verified facts from database.");
    } finally {
      setLoading(false);
    }
  }

  async function loadSources() {
    setLoading(true);
    setError(null);
    try {
      const data = await listTrustedSources();
      setSources(data);
    } catch (err) {
      setError("Failed to load trusted internet sources.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch(e) {
    e.preventDefault();
    loadFacts();
  }

  async function handleCreateFact(e) {
    e.preventDefault();
    if (!newFact.claim.trim() || !newFact.source_name.trim()) return;
    try {
      await addVerifiedFact(newFact);
      setShowFactModal(false);
      setNewFact({
        claim: "",
        verdict: "debunked_as_false",
        explanation: "",
        source_name: "",
        source_url: "",
        topic: "general",
        trust_score: 0.95,
      });
      loadFacts();
      loadOverview();
      onDatabaseChanged?.();
    } catch (err) {
      alert(err.message || "Failed to add fact");
    }
  }

  async function handleDeleteFact(factId) {
    if (!confirm("Are you sure you want to delete this verified fact from the database?")) return;
    try {
      await deleteVerifiedFact(factId);
      loadFacts();
      loadOverview();
      onDatabaseChanged?.();
    } catch (err) {
      alert(err.message || "Failed to delete fact");
    }
  }

  async function handleCreateSource(e) {
    e.preventDefault();
    if (!newSource.domain.trim() || !newSource.name.trim()) return;
    try {
      await addTrustedSource(newSource);
      setShowSourceModal(false);
      setNewSource({ domain: "", name: "", category: "fact_checker", trust_score: 0.95 });
      loadSources();
      loadOverview();
      onDatabaseChanged?.();
    } catch (err) {
      alert(err.message || "Failed to register source");
    }
  }

  async function handleDeleteSource(domain) {
    if (!confirm(`Remove ${domain} from the trusted internet sources directory?`)) return;
    try {
      await deleteTrustedSource(domain);
      loadSources();
      loadOverview();
      onDatabaseChanged?.();
    } catch (err) {
      alert(err.message || "Failed to remove source");
    }
  }

  const getVerdictBadge = (verdict) => {
    switch (verdict) {
      case "debunked_as_false":
      case "refuted":
        return <span className="badge badge-high">Debunked / False</span>;
      case "confirmed_true":
      case "supported":
        return <span className="badge badge-low">Verified True</span>;
      case "disputed_or_misleading":
        return <span className="badge badge-med">Disputed / Misleading</span>;
      default:
        return <span className="badge badge-neutral">Context Documented</span>;
    }
  };

  return (
    <div className="database-hub">
      {/* Overview Cards */}
      <div className="stats-grid" style={{ marginBottom: "24px" }}>
        <div className="stat-card">
          <div className="stat-label">Stored Verified Facts</div>
          <div className="stat-value" style={{ color: "#38bdf8" }}>
            {overview?.total_verified_facts ?? facts.length}
          </div>
          <div className="stat-subtext">Dynamic Knowledge Base</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Trusted Internet Sources</div>
          <div className="stat-value" style={{ color: "#818cf8" }}>
            {overview?.total_trusted_sources ?? sources.length}
          </div>
          <div className="stat-subtext">Verified Fact-Checkers & Authorities</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total Analyzed Submissions</div>
          <div className="stat-value stat-total">
            {overview?.total_analyses ?? 0}
          </div>
          <div className="stat-subtext">Archived in Database</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Storage Engine</div>
          <div className="stat-value" style={{ fontSize: "1.2rem", color: "#34d399", paddingTop: "8px" }}>
            {overview?.storage_mode === "persistent_json_store" ? "Persistent Store" : "MongoDB"}
          </div>
          <div className="stat-subtext">Live Auto-Sync Active</div>
        </div>
      </div>

      {/* Sub Header & Sub Tabs */}
      <div className="panel-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <h2 className="panel-title">Knowledge & Database Hub</h2>
          <p className="panel-description">
            Explore, expand, and manage verified intelligence. Live internet findings are auto-ingested to expand the database with every query.
          </p>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          <button
            type="button"
            className={`btn ${subTab === "facts" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setSubTab("facts")}
          >
            Verified Facts ({overview?.total_verified_facts ?? facts.length})
          </button>
          <button
            type="button"
            className={`btn ${subTab === "sources" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setSubTab("sources")}
          >
            Trusted Sources ({overview?.total_trusted_sources ?? sources.length})
          </button>
        </div>
      </div>

      {error && <div className="alert-box alert-error">{error}</div>}

      {/* SUBTAB 1: VERIFIED FACTS */}
      {subTab === "facts" && (
        <div>
          {/* Action Bar & Filters */}
          <div className="glass-panel" style={{ padding: "16px", marginBottom: "20px" }}>
            <form onSubmit={handleSearch} style={{ display: "flex", gap: "12px", flexWrap: "wrap", alignItems: "center" }}>
              <div style={{ flex: "1 1 240px" }}>
                <input
                  type="text"
                  className="input-field"
                  placeholder="Search claims, sources, or explanations..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{ width: "100%", padding: "10px 14px" }}
                />
              </div>
              <div style={{ minWidth: "140px" }}>
                <select
                  className="select-field"
                  value={topicFilter}
                  onChange={(e) => setTopicFilter(e.target.value)}
                  style={{ width: "100%", padding: "10px" }}
                >
                  <option value="">All Topics</option>
                  <option value="health">Health & Medicine</option>
                  <option value="elections">Elections & Politics</option>
                  <option value="technology">Technology & 5G</option>
                  <option value="environment">Environment & Climate</option>
                  <option value="science">Science</option>
                  <option value="general">General</option>
                </select>
              </div>
              <div style={{ minWidth: "150px" }}>
                <select
                  className="select-field"
                  value={verdictFilter}
                  onChange={(e) => setVerdictFilter(e.target.value)}
                  style={{ width: "100%", padding: "10px" }}
                >
                  <option value="">All Verdicts</option>
                  <option value="debunked_as_false">Debunked / False</option>
                  <option value="confirmed_true">Verified True</option>
                  <option value="disputed_or_misleading">Disputed</option>
                </select>
              </div>
              <button type="submit" className="btn btn-secondary">
                Search
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => setShowFactModal(true)}
                style={{ marginLeft: "auto" }}
              >
                + Add Verified Fact
              </button>
            </form>
          </div>

          {/* Facts List */}
          {loading ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <span>Loading verified facts...</span>
            </div>
          ) : facts.length === 0 ? (
            <div className="empty-state">
              <p>No verified facts match the current search filters.</p>
              <button
                type="button"
                className="btn btn-primary"
                style={{ marginTop: "12px" }}
                onClick={() => setShowFactModal(true)}
              >
                Add the First Fact to this Topic
              </button>
            </div>
          ) : (
            <div className="facts-grid" style={{ display: "grid", gap: "16px" }}>
              {facts.map((fact) => (
                <div key={fact.fact_id} className="glass-panel fact-card" style={{ padding: "20px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "12px", marginBottom: "12px" }}>
                    <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
                      {getVerdictBadge(fact.verdict)}
                      <span className="source-pill" style={{ textTransform: "capitalize" }}>
                        Topic: {fact.topic || "General"}
                      </span>
                      {fact.auto_ingested ? (
                        <span style={{ fontSize: "0.7rem", padding: "2px 8px", background: "rgba(56,189,248,0.15)", color: "#38bdf8", borderRadius: "9999px", border: "1px solid rgba(56,189,248,0.3)" }}>
                          ⚡ Auto-Learned from Internet Search
                        </span>
                      ) : (
                        <span style={{ fontSize: "0.7rem", padding: "2px 8px", background: "rgba(168,85,247,0.15)", color: "#c084fc", borderRadius: "9999px", border: "1px solid rgba(168,85,247,0.3)" }}>
                          Curated Entry
                        </span>
                      )}
                    </div>
                    <button
                      type="button"
                      className="btn-icon-danger"
                      onClick={() => handleDeleteFact(fact.fact_id)}
                      title="Delete fact from database"
                      style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: "1.1rem" }}
                    >
                      &times;
                    </button>
                  </div>

                  <h3 style={{ fontSize: "1.05rem", fontWeight: "600", color: "var(--text-primary)", marginBottom: "8px" }}>
                    "{fact.claim}"
                  </h3>

                  <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)", lineHeight: "1.5", marginBottom: "14px" }}>
                    {fact.explanation}
                  </p>

                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px", borderTop: "1px solid var(--border-subtle)", paddingTop: "12px", fontSize: "0.8rem", color: "var(--text-muted)" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <span>Source: <strong>{fact.source_name}</strong></span>
                      {fact.source_url && (
                        <a
                          href={fact.source_url}
                          target="_blank"
                          rel="noreferrer"
                          style={{ color: "#818cf8", textDecoration: "underline", display: "inline-flex", alignItems: "center", gap: "4px" }}
                        >
                          View External Reference &rarr;
                        </a>
                      )}
                    </div>
                    <div>
                      Trust Score: <strong>{Math.round((fact.trust_score || 0.9) * 100)}%</strong>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* SUBTAB 2: TRUSTED SOURCES */}
      {subTab === "sources" && (
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
              These high-authority domains are prioritized during real-time web verification to cross-check claims.
            </p>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => setShowSourceModal(true)}
            >
              + Register Trusted Domain
            </button>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "16px" }}>
            {sources.map((src) => (
              <div key={src.domain} className="glass-panel" style={{ padding: "18px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
                  <span style={{ fontSize: "0.75rem", padding: "2px 8px", background: "rgba(99,102,241,0.15)", color: "#a5b4fc", borderRadius: "4px", textTransform: "capitalize" }}>
                    {src.category.replace("_", " ")}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleDeleteSource(src.domain)}
                    style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: "1.1rem" }}
                    title="Remove source"
                  >
                    &times;
                  </button>
                </div>
                <h4 style={{ fontSize: "1rem", fontWeight: "600", color: "var(--text-primary)", marginBottom: "4px" }}>
                  {src.name}
                </h4>
                <div style={{ fontSize: "0.85rem", color: "#38bdf8", marginBottom: "12px", fontFamily: "var(--font-mono)" }}>
                  {src.domain}
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  <span>Reputation Score:</span>
                  <strong style={{ color: "#34d399" }}>{Math.round((src.trust_score || 0.95) * 100)}%</strong>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* MODAL: ADD VERIFIED FACT */}
      {showFactModal && (
        <div className="modal-backdrop" onClick={() => setShowFactModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="panel-header" style={{ marginBottom: "16px" }}>
              <h3 className="panel-title">Add Verified Fact to Database</h3>
              <p className="panel-description">
                Directly expand the truth repository with authoritative factual statements.
              </p>
            </div>
            <form onSubmit={handleCreateFact}>
              <div className="form-group">
                <label className="form-label">Claim or Statement</label>
                <textarea
                  className="text-area"
                  rows={2}
                  required
                  placeholder="e.g. Earth's average temperature has risen by 1.1 degrees Celsius since pre-industrial times"
                  value={newFact.claim}
                  onChange={(e) => setNewFact({ ...newFact, claim: e.target.value })}
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "12px" }}>
                <div className="form-group">
                  <label className="form-label">Verdict</label>
                  <select
                    className="select-field"
                    value={newFact.verdict}
                    onChange={(e) => setNewFact({ ...newFact, verdict: e.target.value })}
                  >
                    <option value="debunked_as_false">Debunked / False (Misinformation)</option>
                    <option value="confirmed_true">Confirmed True (Factual)</option>
                    <option value="disputed_or_misleading">Disputed / Misleading</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Topic</label>
                  <select
                    className="select-field"
                    value={newFact.topic}
                    onChange={(e) => setNewFact({ ...newFact, topic: e.target.value })}
                  >
                    <option value="health">Health & Medicine</option>
                    <option value="elections">Elections & Politics</option>
                    <option value="technology">Technology & 5G</option>
                    <option value="environment">Environment & Climate</option>
                    <option value="science">Science</option>
                    <option value="general">General</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Detailed Explanation & Scientific Proof</label>
                <textarea
                  className="text-area"
                  rows={3}
                  required
                  placeholder="Explain why this claim is true or false, citing findings or consensus..."
                  value={newFact.explanation}
                  onChange={(e) => setNewFact({ ...newFact, explanation: e.target.value })}
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "16px" }}>
                <div className="form-group">
                  <label className="form-label">Source Authority Name</label>
                  <input
                    type="text"
                    className="input-field"
                    required
                    placeholder="e.g. World Health Organization (WHO)"
                    value={newFact.source_name}
                    onChange={(e) => setNewFact({ ...newFact, source_name: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Source URL / Direct Link</label>
                  <input
                    type="url"
                    className="input-field"
                    placeholder="https://www.who.int/..."
                    value={newFact.source_url}
                    onChange={(e) => setNewFact({ ...newFact, source_url: e.target.value })}
                  />
                </div>
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowFactModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Save Fact to Database
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: ADD TRUSTED SOURCE */}
      {showSourceModal && (
        <div className="modal-backdrop" onClick={() => setShowSourceModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="panel-header" style={{ marginBottom: "16px" }}>
              <h3 className="panel-title">Register Trusted Domain</h3>
              <p className="panel-description">
                Add an authoritative domain that Truthify-AI will prioritize during live internet fact-checking.
              </p>
            </div>
            <form onSubmit={handleCreateSource}>
              <div className="form-group">
                <label className="form-label">Domain Name</label>
                <input
                  type="text"
                  className="input-field"
                  required
                  placeholder="e.g. bbc.com or nih.gov"
                  value={newSource.domain}
                  onChange={(e) => setNewSource({ ...newSource, domain: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Organization Name</label>
                <input
                  type="text"
                  className="input-field"
                  required
                  placeholder="e.g. BBC News & Reality Check"
                  value={newSource.name}
                  onChange={(e) => setNewSource({ ...newSource, name: e.target.value })}
                />
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "16px" }}>
                <div className="form-group">
                  <label className="form-label">Category</label>
                  <select
                    className="select-field"
                    value={newSource.category}
                    onChange={(e) => setNewSource({ ...newSource, category: e.target.value })}
                  >
                    <option value="fact_checker">Fact Checker</option>
                    <option value="health_authority">Health Authority</option>
                    <option value="news_agency">News Agency / Wire</option>
                    <option value="scientific_authority">Scientific Body</option>
                    <option value="encyclopedia">Encyclopedia</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Reputation Score (0.80 - 1.00)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.70"
                    max="1.00"
                    className="input-field"
                    value={newSource.trust_score}
                    onChange={(e) => setNewSource({ ...newSource, trust_score: parseFloat(e.target.value) || 0.95 })}
                  />
                </div>
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowSourceModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Register Source
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
