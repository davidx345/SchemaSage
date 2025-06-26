"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CrossDatasetRelationships } from "@/components/schema-detection/CrossDatasetRelationships";
import type { Table } from "@/lib/types";

export default function CrossDatasetPage() {
  // For demo: allow user to paste/upload two datasets as JSON
  const [datasetA, setDatasetA] = useState<string>("");
  const [datasetB, setDatasetB] = useState<string>("");
  const [parsedA, setParsedA] = useState<Table[]>([]);
  const [parsedB, setParsedB] = useState<Table[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleParse = () => {
    setError(null);
    try {
      setParsedA(JSON.parse(datasetA));
      setParsedB(JSON.parse(datasetB));
    } catch (e: any) {
      setError("Invalid JSON for one or both datasets.");
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8">
      <h1 className="text-2xl font-bold mb-4">Cross-Dataset Relationship Explorer</h1>
      <Card className="p-4 mb-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <h2 className="font-semibold mb-2">Dataset A (JSON)</h2>
            <textarea
              className="w-full h-40 border rounded p-2"
              value={datasetA}
              onChange={e => setDatasetA(e.target.value)}
              placeholder="Paste array of tables (see docs)"
            />
          </div>
          <div>
            <h2 className="font-semibold mb-2">Dataset B (JSON)</h2>
            <textarea
              className="w-full h-40 border rounded p-2"
              value={datasetB}
              onChange={e => setDatasetB(e.target.value)}
              placeholder="Paste array of tables (see docs)"
            />
          </div>
        </div>
        <Button className="mt-4" onClick={handleParse}>Parse Datasets</Button>
        {error && <div className="text-red-500 mt-2">{error}</div>}
      </Card>
      {(parsedA.length > 0 && parsedB.length > 0) && (
        <CrossDatasetRelationships datasets={[parsedA, parsedB]} />
      )}
    </div>
  );
}
