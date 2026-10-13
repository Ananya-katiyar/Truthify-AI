/*
Truthify-AI Client API
Points to FastAPI Backend at http://localhost:8000
*/

const BASE_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

export async function submitContent(text, sourceType = "user_submitted") {
  const res = await fetch(`${BASE_URL}/content/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, source_type: sourceType }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to submit content for analysis");
  }
  return res.json();
}

export async function submitContentWithMedia(file, text = "", sourceType = "user_submitted") {
  const formData = new FormData();
  formData.append("file", file);
  if (text) formData.append("text", text);
  formData.append("source_type", sourceType);

  const res = await fetch(`${BASE_URL}/content/submit-media`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to analyze uploaded media");
  }
  return res.json();
}

export async function listContent(riskLevel = null, limit = 50) {
  const params = new URLSearchParams();
  if (riskLevel) params.append("risk_level", riskLevel);
  if (limit) params.append("limit", limit.toString());

  const url = `${BASE_URL}/content/?${params.toString()}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch analyzed content list");
  return res.json();
}

export async function getStats() {
  const res = await fetch(`${BASE_URL}/content/stats`);
  if (!res.ok) throw new Error("Failed to fetch system stats");
  return res.json();
}

export async function getAlerts(limit = 20) {
  const res = await fetch(`${BASE_URL}/alerts/?limit=${limit}`);
  if (!res.ok) throw new Error("Failed to fetch high-risk alerts");
  return res.json();
}

export async function markReviewed(contentId, notes = "") {
  const res = await fetch(`${BASE_URL}/alerts/${contentId}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ notes }),
  });
  if (!res.ok) throw new Error("Failed to mark alert as reviewed");
  return res.json();
}

export async function submitFeedback(contentId, correctRiskLevel, notes = "") {
  const res = await fetch(`${BASE_URL}/content/${contentId}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      correct_risk_level: correctRiskLevel,
      notes,
    }),
  });
  if (!res.ok) throw new Error("Failed to submit feedback");
  return res.json();
}

// --- Expanded Database Operations ---

export async function getDatabaseOverview() {
  const res = await fetch(`${BASE_URL}/database/overview`);
  if (!res.ok) throw new Error("Failed to fetch database overview");
  return res.json();
}

export async function listVerifiedFacts(topic = null, verdict = null, search = null, limit = 50) {
  const params = new URLSearchParams();
  if (topic) params.append("topic", topic);
  if (verdict) params.append("verdict", verdict);
  if (search) params.append("search", search);
  if (limit) params.append("limit", limit.toString());

  const res = await fetch(`${BASE_URL}/database/facts?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch verified facts");
  return res.json();
}

export async function addVerifiedFact(factData) {
  const res = await fetch(`${BASE_URL}/database/facts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(factData),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to add verified fact to database");
  }
  return res.json();
}

export async function deleteVerifiedFact(factId) {
  const res = await fetch(`${BASE_URL}/database/facts/${factId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete verified fact");
  return res.json();
}

export async function listTrustedSources() {
  const res = await fetch(`${BASE_URL}/database/sources`);
  if (!res.ok) throw new Error("Failed to fetch trusted sources directory");
  return res.json();
}

export async function addTrustedSource(sourceData) {
  const res = await fetch(`${BASE_URL}/database/sources`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(sourceData),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to register trusted source");
  }
  return res.json();
}

export async function deleteTrustedSource(domain) {
  const res = await fetch(`${BASE_URL}/database/sources/${encodeURIComponent(domain)}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to remove trusted source");
  return res.json();
}
