"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Table as UITable, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function DataCleaningDashboard() {
  const [table, setTable] = useState("");
  const [dataJson, setDataJson] = useState("");
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [applied, setApplied] = useState<any[]>([]);
  const [cleanedData, setCleanedData] = useState<any[]>([]);

  const handleSuggest = async () => {
    setLoading(true);
    setError(null);
    setSuggestions([]);
    setApplied([]);
    setCleanedData([]);
    try {
      const res = await fetch("/api/schema-detection/data-cleaning/suggest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ table, data: JSON.parse(dataJson) })
      });
      if (!res.ok) throw new Error("Failed to get suggestions");
      const data = await res.json();
      setSuggestions(data.suggestions || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/schema-detection/data-cleaning/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ table, data: JSON.parse(dataJson), actions: suggestions })
      });
      if (!res.ok) throw new Error("Failed to apply cleaning");
      const data = await res.json();
      setApplied(data.applied_actions || []);
      setCleanedData(data.cleaned_data || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8">
      <h1 className="text-2xl font-bold mb-4">Data Cleaning Dashboard</h1>
      <Card className="p-4 mb-4">
        <div className="mb-2">
          <input
            className="border rounded px-2 py-1 w-1/2 mb-2"
            placeholder="Table name"
            value={table}
            onChange={e => setTable(e.target.value)}
          />
          <Textarea
            className="mb-2"
            placeholder="Paste data sample (JSON array of rows)"
            value={dataJson}
            onChange={e => setDataJson(e.target.value)}
            rows={8}
          />
          <Button onClick={handleSuggest} disabled={loading || !table || !dataJson.trim()}>
            {loading ? "Analyzing..." : "Suggest Cleaning"}
          </Button>
        </div>
        {error && <div className="text-red-500 mt-2">{error}</div>}
      </Card>
      {suggestions.length > 0 && (
        <Card className="p-4 mb-4">
          <h2 className="font-semibold mb-2">Cleaning Suggestions</h2>
          <UITable>
            <TableHeader>
              <TableRow>
                <TableHead>Column</TableHead>
                <TableHead>Issue</TableHead>
                <TableHead>Suggestion</TableHead>
                <TableHead>Confidence</TableHead>
                <TableHead>Fix Code</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {suggestions.map((s, idx) => (
                <TableRow key={idx}>
                  <TableCell>{s.column}</TableCell>
                  <TableCell>{s.issue}</TableCell>
                  <TableCell>{s.suggestion}</TableCell>
                  <TableCell>{(s.confidence * 100).toFixed(0)}%</TableCell>
                  <TableCell><pre className="text-xs whitespace-pre-wrap">{s.fix_code}</pre></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </UITable>
          <Button className="mt-4" onClick={handleApply} disabled={loading}>Apply All Fixes</Button>
        </Card>
      )}
      {applied.length > 0 && (
        <Card className="p-4 mb-4">
          <h2 className="font-semibold mb-2">Applied Actions</h2>
          <pre className="bg-muted p-2 rounded text-xs overflow-x-auto">{JSON.stringify(applied, null, 2)}</pre>
        </Card>
      )}
      {cleanedData.length > 0 && (
        <Card className="p-4 mb-4">
          <h2 className="font-semibold mb-2">Cleaned Data (Preview)</h2>
          <pre className="bg-muted p-2 rounded text-xs overflow-x-auto">{JSON.stringify(cleanedData, null, 2)}</pre>
        </Card>
      )}
    </div>
  );
}
