"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

export default function ConsistencyCheckPage() {
  const [tablesJson, setTablesJson] = useState("");
  const [relationshipsJson, setRelationshipsJson] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCheck = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("/api/project-management/schema/consistency-check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: "demo", // For now, static or can be extended
          tables: JSON.parse(tablesJson),
          relationships: relationshipsJson ? JSON.parse(relationshipsJson) : undefined
        })
      });
      if (!res.ok) throw new Error("Failed to check consistency");
      setResult(await res.json());
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-8">
      <h1 className="text-2xl font-bold mb-4">Schema Consistency Check</h1>
      <Card className="p-4 mb-4">
        <Textarea
          className="mb-2"
          placeholder="Paste array of tables (JSON)"
          value={tablesJson}
          onChange={e => setTablesJson(e.target.value)}
          rows={8}
        />
        <Textarea
          className="mb-2"
          placeholder="Paste array of relationships (JSON, optional)"
          value={relationshipsJson}
          onChange={e => setRelationshipsJson(e.target.value)}
          rows={4}
        />
        <Button onClick={handleCheck} disabled={loading || !tablesJson.trim()}>
          {loading ? "Checking..." : "Check Consistency"}
        </Button>
        {error && <div className="text-red-500 mt-2">{error}</div>}
      </Card>
      {result && (
        <Card className="p-4">
          <div className="mb-2 font-semibold">Result:</div>
          <div className={result.consistent ? "text-green-600" : "text-red-600"}>
            {result.consistent ? "Schema is consistent!" : "Schema has issues."}
          </div>
          {result.issues?.length > 0 && (
            <ul className="list-disc ml-6 mt-2">
              {result.issues.map((issue: string, idx: number) => (
                <li key={idx}>{issue}</li>
              ))}
            </ul>
          )}
          {result.suggestions?.length > 0 && (
            <div className="mt-2 text-blue-600">
              Suggestions:
              <ul className="list-disc ml-6">
                {result.suggestions.map((s: string, idx: number) => (
                  <li key={idx}>{s}</li>
                ))}
              </ul>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
