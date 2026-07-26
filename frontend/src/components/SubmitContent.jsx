import { useState } from "react";
import { submitContent } from "../api/client.js";

/*
Member 5 (Frontend Engineer) owns this file.
Submission form + inline result display (risk score, explanation, evidence).
*/

const riskColors = { low: "#2e7d32", medium: "#f9a825", high: "#c62828" };

export default function SubmitContent({ onAnalyzed }) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await submitContent(text);
      setResult(data);
      onAnalyzed?.(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ marginBottom: 32 }}>
      <h2>Submit Content for Analysis</h2>
      <form onSubmit={handleSubmit}>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste a social media post, article, or claim to analyze..."
          rows={5}
          style={{ width: "100%", padding: 8, fontFamily: "inherit" }}
        />
        <button type="submit" disabled={loading} style={{ marginTop: 8 }}>
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </form>

      {error && <p style={{ color: "red" }}>Error: {error}</p>}

      {result && (
        <div style={{ marginTop: 16, padding: 16, border: "1px solid #ddd", borderRadius: 8 }}>
          <h3>
            Risk Level:{" "}
            <span style={{ color: riskColors[result.risk_level] }}>
              {result.risk_level.toUpperCase()} ({result.risk_score}/100)
            </span>
          </h3>
          <p><strong>Extracted claims:</strong> {result.extracted_claims.join(" | ") || "None found"}</p>
          <p><strong>Why flagged:</strong></p>
          <ul>
            {result.explanation.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
