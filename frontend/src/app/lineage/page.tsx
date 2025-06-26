"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Tooltip, TooltipProvider, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip";
import { Node, Edge } from "reactflow";
import { LineageGraph } from "@/components/lineage/LineageGraph";

export default function LineageExplorerPage() {
  const [schemaJson, setSchemaJson] = useState("");
  const [glossaryJson, setGlossaryJson] = useState("");
  const [contextJson, setContextJson] = useState("");
  const [table, setTable] = useState("");
  const [column, setColumn] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLineage = async (type: "table" | "column") => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`/api/schema-detection/lineage/${type}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          schema: JSON.parse(schemaJson),
          table,
          ...(type === "column" ? { column } : {}),
          glossary: glossaryJson ? JSON.parse(glossaryJson) : undefined,
          context: contextJson ? JSON.parse(contextJson) : undefined
        })
      });
      if (!res.ok) throw new Error("Failed to fetch lineage");
      setResult(await res.json());
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // Helper to build nodes/edges for React Flow
  function buildGraph(result: any): { nodes: Node[]; edges: Edge[] } {
    if (!result) return { nodes: [], edges: [] };
    const nodes: Node[] = [];
    const edges: Edge[] = [];
    // Helper to get business/context info for a node
    const getNodeInfo = (id: string) => {
      if (!result) return null;
      if (id === result.table || id === result.column) return { business_term: result.business_term, context: result.context };
      // Try to find in upstream/downstream (future: backend can return per-node info)
      return null;
    };
    // Add main node
    if (result.table || result.column) {
      nodes.push({
        id: result.table || result.column,
        data: { label: result.table || result.column, info: getNodeInfo(result.table || result.column) },
        position: { x: 0, y: 0 },
        style: { background: "#e0e7ff", border: "2px solid #6366f1" }
      });
    }
    // Add upstream nodes
    (result.upstream || []).forEach((u: string, i: number) => {
      nodes.push({
        id: u,
        data: { label: u, info: getNodeInfo(u) },
        position: { x: -200, y: 100 * (i + 1) },
        style: { background: "#f1f5f9" }
      });
      edges.push({ id: `u-${u}`, source: u, target: result.table || result.column, animated: true, style: { stroke: "#60a5fa" } });
    });
    // Add downstream nodes
    (result.downstream || []).forEach((d: string, i: number) => {
      nodes.push({
        id: d,
        data: { label: d, info: getNodeInfo(d) },
        position: { x: 200, y: 100 * (i + 1) },
        style: { background: "#f1f5f9" }
      });
      edges.push({ id: `d-${d}`, source: result.table || result.column, target: d, animated: true, style: { stroke: "#34d399" } });
    });
    return { nodes, edges };
  }

  // Enhanced graph with tooltips
  function LineageGraphWithTooltips({ nodes, edges }: { nodes: Node[]; edges: Edge[] }) {
    // Wrap node labels in tooltips if info is present
    const nodeTypes = {
      default: ({ data }: any) => (
        <Tooltip>
          <TooltipTrigger asChild>
            <div>{data.label}</div>
          </TooltipTrigger>
          {data.info && (data.info.business_term || data.info.context) && (
            <TooltipContent>
              {data.info.business_term && (
                <div>
                  <b>Business:</b> {data.info.business_term.term}<br />
                  <small>{data.info.business_term.definition}</small>
                </div>
              )}
              {data.info.context && (
                <div className="mt-1 text-xs text-green-700">
                  <b>Context:</b> {JSON.stringify(data.info.context)}
                </div>
              )}
            </TooltipContent>
          )}
        </Tooltip>
      )
    };
    return <LineageGraph nodes={nodes} edges={edges} nodeTypes={nodeTypes} />;
  }

  return (
    <div className="max-w-3xl mx-auto py-8">
      <h1 className="text-2xl font-bold mb-4">Data Lineage & Impact Explorer</h1>
      <Card className="p-4 mb-4">
        <Textarea
          className="mb-2"
          placeholder="Paste schema (JSON)"
          value={schemaJson}
          onChange={e => setSchemaJson(e.target.value)}
          rows={6}
        />
        <Textarea
          className="mb-2"
          placeholder="Paste glossary (JSON, optional)"
          value={glossaryJson}
          onChange={e => setGlossaryJson(e.target.value)}
          rows={3}
        />
        <Textarea
          className="mb-2"
          placeholder="Paste context (JSON, optional)"
          value={contextJson}
          onChange={e => setContextJson(e.target.value)}
          rows={3}
        />
        <div className="flex gap-2 mb-2">
          <Input
            placeholder="Table name"
            value={table}
            onChange={e => setTable(e.target.value)}
          />
          <Input
            placeholder="Column name (optional)"
            value={column}
            onChange={e => setColumn(e.target.value)}
          />
        </div>
        <div className="flex gap-2">
          <Button onClick={() => handleLineage("table")}>Get Table Lineage</Button>
          <Button onClick={() => handleLineage("column")}>Get Column Lineage</Button>
        </div>
        {error && <div className="text-red-500 mt-2">{error}</div>}
      </Card>
      {result && (
        <Card className="p-4 mb-4">
          <div className="mb-2 font-semibold">Result:</div>
          <TooltipProvider>
            <LineageGraphWithTooltips {...buildGraph(result)} />
          </TooltipProvider>
          <pre className="bg-muted p-2 rounded text-xs overflow-x-auto mt-4">{JSON.stringify(result, null, 2)}</pre>
          {result.business_term && (
            <div className="mt-2 text-blue-700">
              <b>Business Term:</b> {result.business_term.term} <br />
              <b>Definition:</b> {result.business_term.definition}
            </div>
          )}
          {result.context && (
            <div className="mt-2 text-green-700">
              <b>Context:</b> {JSON.stringify(result.context)}
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
