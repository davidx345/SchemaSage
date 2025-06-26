import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Table as UITable, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { Table as SchemaTable, Relationship } from "@/lib/types";

interface RelationshipSuggestionsProps {
  tables: SchemaTable[];
  onApply?: (relationships: Relationship[]) => void;
}

export function RelationshipSuggestions({ tables, onApply }: RelationshipSuggestionsProps) {
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<Relationship[]>([]);
  const [error, setError] = useState<string | null>(null);

  const fetchSuggestions = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/schema-detection/relationships/suggest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tables }),
      });
      if (!res.ok) throw new Error("Failed to fetch suggestions");
      const data = await res.json();
      setSuggestions(data.relationships || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="p-4 my-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold">AI Relationship Suggestions</h3>
        <Button onClick={fetchSuggestions} disabled={loading} size="sm">
          {loading ? "Loading..." : "Suggest Relationships"}
        </Button>
      </div>
      {error && <div className="text-red-500 mb-2">{error}</div>}
      {suggestions.length > 0 && (
        <UITable>
          <TableHeader>
            <TableRow>
              <TableHead>Source Table</TableHead>
              <TableHead>Source Column</TableHead>
              <TableHead>Target Table</TableHead>
              <TableHead>Target Column</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Confidence</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {suggestions.map((rel, idx) => (
              <TableRow key={idx}>
                <TableCell>{rel.source_table}</TableCell>
                <TableCell>{rel.source_column}</TableCell>
                <TableCell>{rel.target_table}</TableCell>
                <TableCell>{rel.target_column}</TableCell>
                <TableCell>{rel.type}</TableCell>
                <TableCell>{'confidence' in rel && (rel as any).confidence !== undefined ? (rel as any).confidence.toFixed(2) : '-'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </UITable>
      )}
      {suggestions.length > 0 && onApply && (
        <Button className="mt-2" onClick={() => onApply(suggestions)}>
          Apply Suggested Relationships
        </Button>
      )}
    </Card>
  );
}
