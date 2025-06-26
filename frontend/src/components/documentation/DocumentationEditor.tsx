import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface DocumentationEditorProps {
  objectId: string;
  initialDoc?: string;
  readOnly?: boolean;
}

export function DocumentationEditor({ objectId, initialDoc = "", readOnly = false }: DocumentationEditorProps) {
  const [doc, setDoc] = useState(initialDoc);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const res = await fetch("/api/schema-detection/documentation/update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ object_id: objectId, documentation: doc })
      });
      if (!res.ok) throw new Error("Failed to save documentation");
      setEditing(false);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card className="p-4 mb-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold">Documentation</h3>
        {!readOnly && !editing && (
          <Button size="sm" onClick={() => setEditing(true)}>Edit</Button>
        )}
      </div>
      {editing ? (
        <>
          <Textarea value={doc} onChange={e => setDoc(e.target.value)} rows={8} />
          <div className="flex gap-2 mt-2">
            <Button onClick={handleSave} disabled={saving}>{saving ? "Saving..." : "Save"}</Button>
            <Button variant="secondary" onClick={() => { setEditing(false); setDoc(initialDoc); }}>Cancel</Button>
          </div>
          {error && <div className="text-red-500 mt-2">{error}</div>}
        </>
      ) : (
        <pre className="bg-muted p-2 rounded text-sm whitespace-pre-wrap">{doc}</pre>
      )}
    </Card>
  );
}
