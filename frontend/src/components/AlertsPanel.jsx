import { useEffect, useState } from "react";
import { getAlerts, markReviewed } from "../api/client.js";

/*
Member 5 (Frontend Engineer) owns this file.
Alerts panel: high-risk content awaiting human review (human-in-the-loop step).
*/

export default function AlertsPanel({ refreshKey }) {
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    getAlerts().then(setAlerts).catch(console.error);
  }, [refreshKey]);

  async function handleReview(contentId) {
    await markReviewed(contentId, "Reviewed via dashboard");
    setAlerts((prev) => prev.filter((a) => a.content_id !== contentId));
  }

  return (
    <div style={{ marginBottom: 32 }}>
      <h2>High-Risk Alerts ({alerts.length})</h2>
      {alerts.length === 0 && <p>No pending alerts.</p>}
      {alerts.map((a) => (
        <div key={a.content_id} style={{ padding: 12, border: "1px solid #f8bbd0", marginBottom: 8, borderRadius: 6 }}>
          <p>{a.input_text.slice(0, 150)}</p>
          <button onClick={() => handleReview(a.content_id)}>Mark Reviewed</button>
        </div>
      ))}
    </div>
  );
}
