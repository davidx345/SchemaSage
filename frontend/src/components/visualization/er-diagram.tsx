// ER Diagram Visualization for Schema Sage
// Renders interactive ER diagrams (D3.js, Mermaid, or React-Flow)

import React from "react";
import type { SchemaResponse } from "@/lib/types";

interface ERDiagramProps {
  schema: SchemaResponse | null;
}

export default function ERDiagram({ schema }: ERDiagramProps) {
  if (!schema) {
    return <p className="text-muted-foreground">No schema loaded.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <h3 className="font-semibold mb-2">Tables</h3>
      <ul className="mb-4 list-disc pl-6">
        {schema.tables.map((table) => (
          <li key={table.name}>
            <span className="font-medium">{table.name}</span>
            <ul className="ml-4 list-square">
              {table.columns.map((col) => (
                <li key={col.name}>
                  {col.name} <span className="text-xs text-muted-foreground">({col.data_type})</span>
                  {col.is_primary_key && <span className="ml-1 text-green-600">[PK]</span>}
                  {col.is_foreign_key && <span className="ml-1 text-blue-600">[FK]</span>}
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
      <h3 className="font-semibold mb-2">Relationships</h3>
      {schema.relationships && schema.relationships.length > 0 ? (
        <ul className="list-disc pl-6">
          {schema.relationships.map((rel, idx) => (
            <li key={idx}>
              <span className="font-medium">{rel.source_table}</span>.<span>{rel.source_column}</span>
              {" → "}
              <span className="font-medium">{rel.target_table}</span>.<span>{rel.target_column}</span>
              <span className="ml-2 text-xs text-muted-foreground">({rel.type})</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-muted-foreground">No relationships detected.</p>
      )}
    </div>
  );
}
