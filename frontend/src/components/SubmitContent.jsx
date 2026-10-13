import { useState, useRef } from "react";
import { submitContent, submitContentWithMedia, submitFeedback, addVerifiedFact } from "../api/client.js";

const PRESET_EXAMPLES = [
  {
    label: "Fake Health Claim",
    source: "social_media",
    text: "URGENT WARNING! Doctors secretly confirm vaccines cause autism and inject microchips to track citizens. Share immediately before this gets deleted!",
  },
  {
    label: "Legitimate Science",
    source: "news_article",
    text: "According to NASA and NOAA researchers, global temperatures have risen approximately 1.1 degrees Celsius since pre-industrial times, driving Arctic sea ice decline.",
  },
  {
    label: "5G Conspiracy",
    source: "social_media",
    text: "The new 5G cellular towers are weaponized radiation emitters designed to alter DNA and cause biological diseases across metropolitan centers.",
  },
  {
    label: "Election Integrity",
    source: "news_article",
    text: "The Election Commission verified that electronic voting machines undergo rigorous physical audits, mock polling, and secure hash verification prior to ballot counting.",
  },
];

export default function SubmitContent({ onAnalyzed, onFactAdded }) {
  const [text, setText] = useState("");
  const [sourceType, setSourceType] = useState("social_media");
  const [selectedFile, setSelectedFile] = useState(null);
  const [filePreview, setFilePreview] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [processingStep, setProcessingStep] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [feedbackSuccess, setFeedbackSuccess] = useState(false);
  const [saveFactSuccess, setSaveFactSuccess] = useState(false);

  const fileInputRef = useRef(null);

  const handleFileSelect = (file) => {
    if (!file) return;
    setSelectedFile(file);
    setError(null);

    // Create preview
    if (file.type.startsWith("image/")) {
      const reader = new FileReader();
      reader.onload = (e) => setFilePreview({ type: "image", url: e.target.result, name: file.name, size: file.size });
      reader.readAsDataURL(file);
    } else if (file.type.startsWith("video/")) {
      const url = URL.createObjectURL(file);
      setFilePreview({ type: "video", url, name: file.name, size: file.size });
    } else if (file.type === "application/pdf" || file.name.endsWith(".pdf")) {
      setFilePreview({ type: "pdf", name: file.name, size: file.size });
    } else {
      setFilePreview({ type: "file", name: file.name, size: file.size });
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setFilePreview(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  async function handleSubmit(e) {
    e.preventDefault();
    if (!text.trim() && !selectedFile) {
      setError("Please enter text or upload an Image, Video, or PDF to analyze.");
      return;
    }

    setLoading(true);
    setError(null);
    setFeedbackSuccess(false);
    setSaveFactSuccess(false);

    try {
      let data;
      if (selectedFile) {
        setProcessingStep("Extracting media content (OCR / Keyframe Analysis / PDF text)...");
        data = await submitContentWithMedia(selectedFile, text, sourceType);
      } else {
        setProcessingStep("Searching live trusted internet sources & verifying claims...");
        data = await submitContent(text, sourceType);
      }
      setResult(data);
      onAnalyzed?.(data);
    } catch (err) {
      setError(err.message || "Could not analyze content.");
    } finally {
      setLoading(false);
      setProcessingStep("");
    }
  }

  async function handleFeedback(newRisk) {
    if (!result?.content_id) return;
    try {
      await submitFeedback(result.content_id, newRisk, "Corrected via Quick Feedback");
      setFeedbackSuccess(true);
      setResult((prev) => ({ ...prev, risk_level: newRisk }));
      onAnalyzed?.();
    } catch (err) {
      console.error(err);
    }
  }

  async function handleSaveAsFact(claimItem) {
    try {
      await addVerifiedFact({
        claim: claimItem.claim,
        verdict: claimItem.verdict || "debunked_as_false",
        explanation: claimItem.explanation || "Verified via Truthify-AI live internet search.",
        source_name: claimItem.source || "Live Internet Fact-Check",
        source_url: claimItem.top_url || "",
        topic: "general",
        trust_score: claimItem.top_similarity || 0.95,
      });
      setSaveFactSuccess(true);
      onFactAdded?.();
      setTimeout(() => setSaveFactSuccess(false), 3500);
    } catch (err) {
      alert(err.message || "Failed to save fact to database.");
    }
  }

  const getMeterColor = (score) => {
    if (score >= 60) return "var(--risk-high)";
    if (score >= 30) return "var(--risk-med)";
    return "var(--risk-low)";
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return "0 KB";
    if (bytes > 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + " MB";
    return Math.round(bytes / 1024) + " KB";
  };

  return (
    <div className="glass-panel">
      <div className="panel-header">
        <h2 className="panel-title">Multimodal Misinformation Studio</h2>
        <p className="panel-description">
          Analyze text, images, videos, and PDFs against live trusted internet sources (Reuters, WHO, CDC, Wikipedia) without hardcoded facts.
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Multimodal Drag-and-Drop Area */}
        <div className="form-group">
          <label className="form-label" style={{ display: "flex", justifyContent: "space-between" }}>
            <span>Upload Media (Images, Videos, or PDFs)</span>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              Supports JPG, PNG, WEBP, MP4, MOV, WEBM, PDF
            </span>
          </label>

          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => handleFileSelect(e.target.files[0])}
            accept="image/*,video/*,application/pdf,.pdf"
            style={{ display: "none" }}
          />

          {!filePreview ? (
            <div
              className={`dropzone ${isDragging ? "dropzone-active" : ""}`}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onClick={() => fileInputRef.current?.click()}
              style={{
                border: "2px dashed var(--border-active)",
                borderRadius: "var(--radius-md)",
                padding: "24px 16px",
                textAlign: "center",
                cursor: "pointer",
                background: "rgba(13, 18, 29, 0.6)",
                transition: "all 0.2s ease",
              }}
            >
              <div style={{ display: "flex", justifyContent: "center", gap: "14px", marginBottom: "8px", opacity: 0.8 }}>
                <span title="Images" style={{ fontSize: "1.4rem" }}>🖼️</span>
                <span title="Videos" style={{ fontSize: "1.4rem" }}>🎥</span>
                <span title="PDF Documents" style={{ fontSize: "1.4rem" }}>📄</span>
              </div>
              <div style={{ color: "var(--text-primary)", fontWeight: "500", fontSize: "0.95rem" }}>
                Drag & drop Image, Video, or PDF here, or <span style={{ color: "var(--accent-primary)", textDecoration: "underline" }}>browse file</span>
              </div>
              <div style={{ color: "var(--text-muted)", fontSize: "0.8rem", marginTop: "4px" }}>
                Automatic OCR extraction, keyframe banner scanning, and PDF text parsing
              </div>
            </div>
          ) : (
            <div
              className="media-preview-card"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "16px",
                padding: "12px 16px",
                background: "rgba(99, 102, 241, 0.08)",
                border: "1px solid rgba(99, 102, 241, 0.3)",
                borderRadius: "var(--radius-md)",
                position: "relative",
              }}
            >
              {filePreview.type === "image" && (
                <img
                  src={filePreview.url}
                  alt="Upload preview"
                  style={{ width: "64px", height: "64px", objectFit: "cover", borderRadius: "8px" }}
                />
              )}
              {filePreview.type === "video" && (
                <video
                  src={filePreview.url}
                  style={{ width: "96px", height: "64px", objectFit: "cover", borderRadius: "8px" }}
                  muted
                />
              )}
              {filePreview.type === "pdf" && (
                <div style={{ width: "54px", height: "64px", background: "rgba(239, 68, 68, 0.15)", color: "#f87171", display: "flex", alignItems: "center", justifyContent: "center", borderRadius: "8px", fontSize: "1.6rem" }}>
                  📄
                </div>
              )}

              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "0.75rem", padding: "2px 6px", background: "rgba(99, 102, 241, 0.25)", color: "#c7d2fe", borderRadius: "4px", textTransform: "uppercase", fontWeight: "600" }}>
                    {filePreview.type}
                  </span>
                  <span style={{ fontWeight: "600", fontSize: "0.9rem", color: "var(--text-primary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {filePreview.name}
                  </span>
                </div>
                <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "4px" }}>
                  File size: {formatFileSize(filePreview.size)} • Ready for automated multimodal extraction
                </div>
              </div>

              <button
                type="button"
                onClick={handleRemoveFile}
                className="btn-secondary"
                style={{ padding: "6px 12px", fontSize: "0.8rem" }}
              >
                Remove
              </button>
            </div>
          )}
        </div>

        {/* Text Input / Caption Area */}
        <div className="form-group">
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
            <label className="form-label">
              {selectedFile ? "Accompanying Caption / Context / Headline (Optional)" : "Input Text / Article / Claim"}
            </label>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              {text.length} characters
            </span>
          </div>
          <textarea
            className="text-area"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={selectedFile ? "Add any context, headline, or claim about this uploaded file..." : "Paste headline, article excerpt, social media post, or specific claim to verify against live internet sources..."}
            rows={4}
          />

          {!selectedFile && (
            <div className="preset-pills">
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", alignSelf: "center" }}>
                Quick test examples:
              </span>
              {PRESET_EXAMPLES.map((ex, idx) => (
                <button
                  key={idx}
                  type="button"
                  className="preset-pill"
                  onClick={() => {
                    setText(ex.text);
                    setSourceType(ex.source);
                  }}
                >
                  {ex.label}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="form-row">
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <label className="form-label" style={{ margin: 0 }}>Content Source:</label>
            <select
              className="select-input"
              value={sourceType}
              onChange={(e) => setSourceType(e.target.value)}
            >
              <option value="social_media">Social Media Post</option>
              <option value="news_article">News Article</option>
              <option value="user_submitted">Direct User Claim</option>
              <option value="document">Official Document / PDF</option>
              <option value="broadcast">Video Broadcast / TV</option>
            </select>
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={loading || (!text.trim() && !selectedFile)}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                <span>Verifying Live Internet...</span>
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <span>Analyze Content</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Loading Steps Indicator */}
      {loading && processingStep && (
        <div style={{ marginTop: "16px", padding: "12px 16px", background: "rgba(99, 102, 241, 0.12)", border: "1px solid rgba(99, 102, 241, 0.3)", borderRadius: "var(--radius-sm)", color: "#a5b4fc", fontSize: "0.85rem", display: "flex", alignItems: "center", gap: "10px" }}>
          <span className="spinner"></span>
          <span>{processingStep}</span>
        </div>
      )}

      {error && (
        <div style={{ marginTop: "16px", padding: "12px 16px", background: "rgba(244, 63, 94, 0.1)", border: "1px solid var(--risk-high-border)", borderRadius: "var(--radius-sm)", color: "var(--risk-high)", fontSize: "0.875rem" }}>
          ⚠️ <strong>Error:</strong> {error}
        </div>
      )}

      {saveFactSuccess && (
        <div style={{ marginTop: "16px", padding: "12px 16px", background: "rgba(16, 185, 129, 0.15)", border: "1px solid rgba(16, 185, 129, 0.3)", borderRadius: "var(--radius-sm)", color: "#34d399", fontSize: "0.875rem" }}>
          ✓ Verified fact successfully added to the expanded database!
        </div>
      )}

      {/* ANALYSIS RESULT DISPLAY */}
      {result && (
        <div className="result-box" style={{ marginTop: "24px" }}>
          <div className="result-header">
            <div>
              <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                ASSESSMENT VERDICT
              </span>
              <div className={`risk-badge ${result.risk_level}`}>
                <span>{result.risk_level} Risk</span>
                <span>•</span>
                <span>{result.risk_score} / 100</span>
              </div>
            </div>

            <div className="risk-meter">
              <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>Risk Score:</span>
              <div className="meter-track">
                <div
                  className="meter-fill"
                  style={{
                    width: `${result.risk_score}%`,
                    backgroundColor: getMeterColor(result.risk_score),
                  }}
                />
              </div>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.85rem", fontWeight: "600" }}>
                {result.risk_score}%
              </span>
            </div>

            {result.processing_time_seconds > 0 && (
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                Latency: {result.processing_time_seconds}s
              </span>
            )}
          </div>

          {/* Multimodal Extraction Details if media provided */}
          {result.media_type && result.media_type !== "text" && (
            <div style={{ marginTop: "16px", padding: "14px 18px", background: "rgba(255, 255, 255, 0.03)", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
                <span style={{ fontSize: "0.75rem", padding: "2px 8px", background: "rgba(56, 189, 248, 0.2)", color: "#38bdf8", borderRadius: "4px", fontWeight: "600", textTransform: "uppercase" }}>
                  {result.media_type} Analyzed
                </span>
                <span style={{ fontSize: "0.85rem", fontWeight: "600", color: "var(--text-primary)" }}>
                  {result.media_filename || "Media File"}
                </span>
              </div>

              {result.thumbnail_b64 && (
                <div style={{ marginBottom: "10px" }}>
                  <img
                    src={result.thumbnail_b64}
                    alt="Analyzed media preview"
                    style={{ maxWidth: "200px", maxHeight: "140px", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}
                  />
                </div>
              )}

              {result.media_metadata && Object.keys(result.media_metadata).length > 0 && (
                <div style={{ display: "flex", gap: "16px", flexWrap: "wrap", fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "8px" }}>
                  {result.media_metadata.pages && <span>Pages: <strong>{result.media_metadata.pages}</strong></span>}
                  {result.media_metadata.duration_seconds && <span>Duration: <strong>{result.media_metadata.duration_seconds}s</strong></span>}
                  {result.media_metadata.dimensions && <span>Dimensions: <strong>{result.media_metadata.dimensions}</strong></span>}
                  {result.media_metadata.resolution && <span>Resolution: <strong>{result.media_metadata.resolution}</strong></span>}
                  {result.media_metadata.camera_model && <span>Device: <strong>{result.media_metadata.camera_model}</strong></span>}
                </div>
              )}

              <div style={{ fontSize: "0.825rem", color: "var(--text-secondary)", background: "rgba(0,0,0,0.25)", padding: "8px 12px", borderRadius: "6px", fontFamily: "var(--font-mono)", maxHeight: "100px", overflowY: "auto" }}>
                <strong>Extracted Text / OCR:</strong><br />
                {result.input_text || "No text overlays detected."}
              </div>
            </div>
          )}

          {result.summary && (
            <div className="result-summary" style={{ marginTop: "16px" }}>
              <strong style={{ color: "var(--text-primary)", display: "block", marginBottom: "4px" }}>
                AI Executive Summary
              </strong>
              {result.summary}
            </div>
          )}

          {/* Linguistic Content Analysis Badges */}
          <div className="meta-grid" style={{ marginTop: "16px" }}>
            <div className="meta-card">
              <div className="meta-title">Intent Detection</div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span className="badge-tag">
                  {result.content_analysis?.intent?.top_label || "N/A"}
                </span>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                  {result.content_analysis?.intent?.confidence ? `${Math.round(result.content_analysis.intent.confidence * 100)}% conf.` : ""}
                </span>
              </div>
            </div>

            <div className="meta-card">
              <div className="meta-title">Tone & Framing</div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span className="badge-tag">
                  {result.content_analysis?.tone?.top_label || "N/A"}
                </span>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                  {result.content_analysis?.tone?.confidence ? `${Math.round(result.content_analysis.tone.confidence * 100)}% conf.` : ""}
                </span>
              </div>
            </div>

            <div className="meta-card">
              <div className="meta-title">Content Categorization</div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span className="badge-tag">
                  {result.content_analysis?.content_type?.top_label || "N/A"}
                </span>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                  {result.content_analysis?.content_type?.confidence ? `${Math.round(result.content_analysis.content_type.confidence * 100)}% conf.` : ""}
                </span>
              </div>
            </div>
          </div>

          {/* LIVE INTERNET FACT-CHECKING SECTION */}
          <div style={{ marginTop: "24px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", flexWrap: "wrap", gap: "8px" }}>
              <h4 style={{ fontSize: "0.95rem", fontWeight: "600", color: "var(--text-primary)", display: "flex", alignItems: "center", gap: "8px" }}>
                <span>🌐 LIVE INTERNET FACT VERIFICATION</span>
                <span style={{ fontSize: "0.75rem", padding: "2px 8px", background: "rgba(16, 185, 129, 0.15)", color: "#34d399", borderRadius: "9999px", border: "1px solid rgba(16, 185, 129, 0.3)" }}>
                  Real-time Trusted Sources
                </span>
              </h4>
              <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                {result.extracted_claims?.length || 0} claims examined
              </span>
            </div>

            {(!result.fact_check || result.fact_check.length === 0) ? (
              <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                No checkable factual claims extracted from this submission.
              </p>
            ) : (
              result.fact_check.map((fc, idx) => (
                <div key={idx} className="claim-card" style={{ marginBottom: "16px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px", flexWrap: "wrap", gap: "8px" }}>
                    <span
                      className={`claim-verdict ${
                        fc.verdict === "confirmed_true" || fc.verdict === "supported_or_related"
                          ? "verdict-supported"
                          : fc.verdict === "debunked_as_false"
                          ? "verdict-none"
                          : "verdict-weak"
                      }`}
                      style={{ fontSize: "0.8rem", fontWeight: "600", padding: "3px 10px" }}
                    >
                      {fc.verdict === "confirmed_true" || fc.verdict === "supported_or_related"
                        ? "✓ Verified by Trusted Sources"
                        : fc.verdict === "debunked_as_false"
                        ? "✗ Refuted / Debunked as False"
                        : fc.verdict === "disputed_or_misleading"
                        ? "⚠ Disputed / Missing Context"
                        : "ℹ️ Unverified in Trusted Records"}
                    </span>

                    <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                      {fc.source && (
                        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                          Primary: <strong style={{ color: "var(--text-primary)" }}>{fc.source}</strong>
                        </span>
                      )}
                      <button
                        type="button"
                        onClick={() => handleSaveAsFact(fc)}
                        className="btn-secondary"
                        style={{ padding: "3px 8px", fontSize: "0.75rem", display: "inline-flex", alignItems: "center", gap: "4px" }}
                        title="Persist this finding into the verified facts database"
                      >
                        + Save to DB
                      </button>
                    </div>
                  </div>

                  <p style={{ fontSize: "0.95rem", color: "var(--text-primary)", fontWeight: "600", marginBottom: "8px" }}>
                    "{fc.claim}"
                  </p>

                  {fc.explanation && (
                    <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "10px", lineHeight: "1.5" }}>
                      {fc.explanation}
                    </p>
                  )}

                  {/* List of Live Internet Evidence Links */}
                  {fc.evidence && fc.evidence.length > 0 && (
                    <div style={{ marginTop: "10px", paddingTop: "10px", borderTop: "1px solid rgba(255,255,255,0.06)" }}>
                      <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block", marginBottom: "6px" }}>
                        Corroborating Internet Sources & Reporting:
                      </span>
                      <div style={{ display: "grid", gap: "8px" }}>
                        {fc.evidence.map((ev, evIdx) => (
                          <div
                            key={evIdx}
                            style={{
                              padding: "8px 12px",
                              background: "rgba(255,255,255,0.02)",
                              borderRadius: "6px",
                              border: "1px solid rgba(255,255,255,0.05)",
                              fontSize: "0.825rem",
                            }}
                          >
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px", flexWrap: "wrap", gap: "6px" }}>
                              <span style={{ fontWeight: "600", color: "#818cf8" }}>
                                {ev.source_name || ev.domain}
                              </span>
                              {ev.url && (
                                <a
                                  href={ev.url}
                                  target="_blank"
                                  rel="noreferrer"
                                  style={{ color: "#38bdf8", textDecoration: "underline", fontSize: "0.75rem" }}
                                >
                                  View Source Link ↗
                                </a>
                              )}
                            </div>
                            <div style={{ color: "var(--text-secondary)", lineHeight: "1.4" }}>
                              "{ev.snippet}"
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          {/* Reasoning & Risk Factors */}
          <div style={{ marginTop: "24px" }}>
            <h4 style={{ fontSize: "0.9rem", fontWeight: "600", marginBottom: "10px", color: "var(--text-secondary)" }}>
              REASONING & RISK SIGNALS
            </h4>
            <ul style={{ paddingLeft: "20px", fontSize: "0.875rem", color: "var(--text-secondary)", lineHeight: 1.7 }}>
              {result.explanation?.map((exp, idx) => (
                <li key={idx}>{exp}</li>
              ))}
            </ul>
          </div>

          {/* Human Feedback */}
          <div style={{ marginTop: "24px", paddingTop: "16px", borderTop: "1px solid var(--border-subtle)", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
            <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
              Human-In-The-Loop Validation:
            </span>
            <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => handleFeedback("low")}
                disabled={feedbackSuccess}
              >
                Mark Low
              </button>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => handleFeedback("medium")}
                disabled={feedbackSuccess}
              >
                Mark Medium
              </button>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => handleFeedback("high")}
                disabled={feedbackSuccess}
              >
                Mark High
              </button>
              {feedbackSuccess && (
                <span style={{ fontSize: "0.8rem", color: "var(--risk-low)", marginLeft: "8px" }}>
                  ✓ Feedback logged!
                </span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
