/*
Member 5 (Frontend Engineer) owns this file.
Thin wrapper around the backend API. Points at http://localhost:8000 by default.
*/

const BASE_URL = "http://localhost:8000";

export async function submitContent(text, sourceType = "user_submitted") {
  const res = await fetch(`${BASE_URL}/content/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, source_type: sourceType }),
  });
  if (!res.ok) throw new Error("Failed to submit content");
  return res.json();
}

export async function listContent(riskLevel = null) {
  const url = riskLevel ? `${BASE_URL}/content/?risk_level=${riskLevel}` : `${BASE_URL}/content/`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch content");
  return res.json();
}

export async function getAlerts() {
  const res = await fetch(`${BASE_URL}/alerts/`);
  if (!res.ok) throw new Error("Failed to fetch alerts");
  return res.json();
}

export async function markReviewed(contentId, notes) {
  const res = await fetch(`${BASE_URL}/alerts/${contentId}/review?notes=${encodeURIComponent(notes || "")}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to mark reviewed");
  return res.json();
}
