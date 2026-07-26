import { useState } from "react";
import SubmitContent from "./components/SubmitContent.jsx";
import Dashboard from "./components/Dashboard.jsx";
import AlertsPanel from "./components/AlertsPanel.jsx";

export default function App() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: 24, fontFamily: "sans-serif" }}>
      <h1>Misinformation Detection & Risk Analysis</h1>
      <SubmitContent onAnalyzed={() => setRefreshKey((k) => k + 1)} />
      <AlertsPanel refreshKey={refreshKey} />
      <Dashboard refreshKey={refreshKey} />
    </div>
  );
}
