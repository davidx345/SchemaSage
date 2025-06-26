"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Table as UITable, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

interface GlossaryTerm {
  id: string;
  term: string;
  definition: string;
  synonyms?: string[];
  created_at?: string;
  updated_at?: string;
}

export default function GlossaryPage() {
  const [terms, setTerms] = useState<GlossaryTerm[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newTerm, setNewTerm] = useState({ term: "", definition: "", synonyms: "" });
  const [adding, setAdding] = useState(false);

  const fetchTerms = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/project-management/glossary");
      if (!res.ok) throw new Error("Failed to fetch glossary");
      const data = await res.json();
      setTerms(data.terms || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchTerms(); }, []);

  const handleAdd = async () => {
    setAdding(true);
    setError(null);
    try {
      const res = await fetch("/api/project-management/glossary", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          term: newTerm.term,
          definition: newTerm.definition,
          synonyms: newTerm.synonyms.split(",").map(s => s.trim()).filter(Boolean)
        })
      });
      if (!res.ok) throw new Error("Failed to add term");
      setNewTerm({ term: "", definition: "", synonyms: "" });
      fetchTerms();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setAdding(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-8">
      <h1 className="text-2xl font-bold mb-4">Business Glossary</h1>
      <Card className="p-4 mb-4">
        <div className="grid grid-cols-3 gap-2 mb-2">
          <Input
            placeholder="Term"
            value={newTerm.term}
            onChange={e => setNewTerm({ ...newTerm, term: e.target.value })}
          />
          <Input
            placeholder="Synonyms (comma separated)"
            value={newTerm.synonyms}
            onChange={e => setNewTerm({ ...newTerm, synonyms: e.target.value })}
          />
          <Textarea
            placeholder="Definition"
            value={newTerm.definition}
            onChange={e => setNewTerm({ ...newTerm, definition: e.target.value })}
          />
        </div>
        <Button onClick={handleAdd} disabled={adding || !newTerm.term.trim()}>Add Term</Button>
        {error && <div className="text-red-500 mt-2">{error}</div>}
      </Card>
      <Card className="p-4">
        <UITable>
          <TableHeader>
            <TableRow>
              <TableHead>Term</TableHead>
              <TableHead>Definition</TableHead>
              <TableHead>Synonyms</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {terms.map(term => (
              <TableRow key={term.id}>
                <TableCell>{term.term}</TableCell>
                <TableCell>{term.definition}</TableCell>
                <TableCell>{term.synonyms?.join(", ")}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </UITable>
      </Card>
    </div>
  );
}
