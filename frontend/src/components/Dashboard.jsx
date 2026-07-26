import { useEffect, useState } from "react";
import { listContent } from "../api/client.js";

/*
Member 5 (Frontend Engineer) owns this file.
Monitoring dashboard: table of analyzed content with filters.
*/

export default function Dashboard({ refreshKey }) {
  const [items, setItems] = useState([]);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    listContent(filter || null).then(setItems).catch(console.error);
  }, [filter, refreshKey]);

  return (
    <div style={{ marginBottom: 32 }}>
      <h2>Monitoring Dashboard</h2>
      <label>
        Filter by risk:{" "}
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="">All</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
      </label>

      <table style={{ width: "100%", marginTop: 12, borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>Content</th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>Risk</th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>Score</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.content_id}>
              <td style={{ maxWidth: 400 }}>{item.input_text.slice(0, 100)}</td>
              <td>{item.risk_level}</td>
              <td>{item.risk_score}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
