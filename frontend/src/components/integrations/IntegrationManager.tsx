"use client";

import React, { useEffect, useState } from "react";

interface IntegrationConfig {
  enabled: boolean;
  [key: string]: any;
}

const INTEGRATION_TYPES = [
  { key: "webhooks", label: "Webhooks" },
  { key: "notifications", label: "Notifications (Slack/Teams/Gmail)" },
  { key: "cloud-storage", label: "Cloud Storage (S3/GCS/Azure)" },
  { key: "bi-tools", label: "BI Tools (Tableau/Power BI)" },
  { key: "data-catalogs", label: "Data Catalogs (Collibra/Alation)" },
  { key: "custom-api", label: "Custom API Connectors" },
];

const API_BASE = "/api/integrations";

export default function IntegrationManager() {
  const [configs, setConfigs] = useState<Record<string, IntegrationConfig>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAllConfigs();
  }, []);

  async function fetchAllConfigs() {
    setLoading(true);
    setError(null);
    try {
      const results: Record<string, IntegrationConfig> = {};
      for (const t of INTEGRATION_TYPES) {
        const res = await fetch(`${API_BASE}/${t.key}`);
        if (res.ok) {
          results[t.key] = await res.json();
        }
      }
      setConfigs(results);
    } catch (e) {
      setError("Failed to load integration configs");
    } finally {
      setLoading(false);
    }
  }

  async function toggleIntegration(key: string, enable: boolean) {
    setLoading(true);
    setError(null);
    try {
      await fetch(`${API_BASE}/${key}/${enable ? "enable" : "disable"}`, { method: "POST" });
      await fetchAllConfigs();
    } catch (e) {
      setError(`Failed to ${enable ? "enable" : "disable"} integration`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Integration Marketplace</h2>
      {error && <div className="text-red-500 mb-2">{error}</div>}
      {loading && <div>Loading...</div>}
      <div className="space-y-4">
        {INTEGRATION_TYPES.map((t) => (
          <div key={t.key} className="border rounded p-4 flex items-center justify-between">
            <div>
              <div className="font-semibold">{t.label}</div>
              <div className="text-xs text-gray-500">{configs[t.key]?.enabled ? "Enabled" : "Disabled"}</div>
            </div>
            <button
              className={`px-4 py-2 rounded ${configs[t.key]?.enabled ? "bg-red-500 text-white" : "bg-green-500 text-white"}`}
              onClick={() => toggleIntegration(t.key, !configs[t.key]?.enabled)}
              disabled={loading}
            >
              {configs[t.key]?.enabled ? "Disable" : "Enable"}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
