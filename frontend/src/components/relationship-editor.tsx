"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Plus, Trash2 } from "lucide-react";
import type { SchemaResponse, Relationship, RelationType } from "@/lib/types";

interface RelationshipEditorProps {
  schema: SchemaResponse;
  onUpdate?: (relationships: Relationship[]) => void;
}

interface EditingRelationship extends Omit<Relationship, 'id'> {
  tempId: string; // Internal ID for UI management
}

export function RelationshipEditor({ schema, onUpdate }: RelationshipEditorProps) {
  const [relationships, setRelationships] = useState<EditingRelationship[]>(
    schema.relationships?.map((rel, index) => ({
      ...rel,
      tempId: `rel-${index}`,
    })) || []
  );

  const addRelationship = () => {
    if (!schema.tables.length) return;
    
    const sourceTable = schema.tables[0];
    const targetTable = schema.tables.length > 1 ? schema.tables[1] : schema.tables[0];
    
    const newRel: EditingRelationship = {
      source_table: sourceTable.name,
      source_column: sourceTable.columns[0]?.name || "",
      target_table: targetTable.name,
      target_column: targetTable.columns[0]?.name || "",
      type: "many-to-one",
      tempId: `rel-${relationships.length}`,
    };

    const updated = [...relationships, newRel];
    setRelationships(updated);
    // Convert EditingRelationship[] to Relationship[] by removing tempId
    const cleanedRelationships = updated.map(({ source_table, source_column, target_table, target_column, type }) => ({
      source_table,
      source_column,
      target_table,
      target_column,
      type
    }));
    onUpdate?.(cleanedRelationships);
  };

  const removeRelationship = (tempId: string) => {
    const updated = relationships.filter((rel) => rel.tempId !== tempId);
    setRelationships(updated);
    const cleanedRelationships = updated.map(({ source_table, source_column, target_table, target_column, type }) => ({
      source_table,
      source_column,
      target_table,
      target_column,
      type
    }));
    onUpdate?.(cleanedRelationships);
  };

  const handleSourceTableChange = (value: string, index: number) => {
    const updated = [...relationships];
    updated[index] = {
      ...updated[index],
      source_table: value,
      source_column: schema.tables.find(t => t.name === value)?.columns[0]?.name || "",
    };
    setRelationships(updated);
    const cleanedRelationships = updated.map(({ source_table, source_column, target_table, target_column, type }) => ({
      source_table,
      source_column,
      target_table,
      target_column,
      type
    }));
    onUpdate?.(cleanedRelationships);
  };

  const handleSourceColumnChange = (value: string, index: number) => {
    const updated = [...relationships];
    updated[index] = {
      ...updated[index],
      source_column: value,
    };
    setRelationships(updated);
    const cleanedRelationships = updated.map(({ source_table, source_column, target_table, target_column, type }) => ({
      source_table,
      source_column,
      target_table,
      target_column,
      type
    }));
    onUpdate?.(cleanedRelationships);
  };

  const handleTargetTableChange = (value: string, index: number) => {
    const updated = [...relationships];
    updated[index] = {
      ...updated[index],
      target_table: value,
      target_column: schema.tables.find(t => t.name === value)?.columns[0]?.name || "",
    };
    setRelationships(updated);
    const cleanedRelationships = updated.map(({ source_table, source_column, target_table, target_column, type }) => ({
      source_table,
      source_column,
      target_table,
      target_column,
      type
    }));
    onUpdate?.(cleanedRelationships);
  };

  const handleTargetColumnChange = (value: string, index: number) => {
    const updated = [...relationships];
    updated[index] = {
      ...updated[index],
      target_column: value,
    };
    setRelationships(updated);
    const cleanedRelationships = updated.map(({ source_table, source_column, target_table, target_column, type }) => ({
      source_table,
      source_column,
      target_table,
      target_column,
      type
    }));
    onUpdate?.(cleanedRelationships);
  };

  const handleRelationTypeChange = (value: RelationType, index: number) => {
    const updated = [...relationships];
    updated[index] = {
      ...updated[index],
      type: value,
    };
    setRelationships(updated);
    const cleanedRelationships = updated.map(({ source_table, source_column, target_table, target_column, type }) => ({
      source_table,
      source_column,
      target_table,
      target_column,
      type
    }));
    onUpdate?.(cleanedRelationships);
  };

  return (
    <Card className="p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Table Relationships</h3>
        <Button variant="outline" size="sm" onClick={addRelationship}>
          <Plus className="h-4 w-4 mr-2" />
          Add Relationship
        </Button>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Source Table</TableHead>
              <TableHead>Source Column</TableHead>
              <TableHead>Relationship Type</TableHead>
              <TableHead>Target Table</TableHead>
              <TableHead>Target Column</TableHead>
              <TableHead className="w-[50px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {relationships.map((rel, index) => (
              <TableRow key={rel.tempId}>
                <TableCell>
                  <Select
                    value={rel.source_table}
                    onValueChange={(value) => handleSourceTableChange(value, index)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {schema.tables.map((table) => (
                        <SelectItem key={table.name} value={table.name}>
                          {table.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </TableCell>
                <TableCell>
                  <Select
                    value={rel.source_column}
                    onValueChange={(value) => handleSourceColumnChange(value, index)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {schema.tables
                        .find((t) => t.name === rel.source_table)
                        ?.columns.map((col) => (
                          <SelectItem key={col.name} value={col.name}>
                            {col.name}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </TableCell>
                <TableCell>
                  <Select
                    value={rel.type}
                    onValueChange={(value) => handleRelationTypeChange(value as RelationType, index)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="one-to-one">One-to-One</SelectItem>
                      <SelectItem value="one-to-many">One-to-Many</SelectItem>
                      <SelectItem value="many-to-one">Many-to-One</SelectItem>
                      <SelectItem value="many-to-many">Many-to-Many</SelectItem>
                    </SelectContent>
                  </Select>
                </TableCell>
                <TableCell>
                  <Select
                    value={rel.target_table}
                    onValueChange={(value) => handleTargetTableChange(value, index)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {schema.tables.map((table) => (
                        <SelectItem key={table.name} value={table.name}>
                          {table.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </TableCell>
                <TableCell>
                  <Select
                    value={rel.target_column}
                    onValueChange={(value) => handleTargetColumnChange(value, index)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {schema.tables
                        .find((t) => t.name === rel.target_table)
                        ?.columns.map((col) => (
                          <SelectItem key={col.name} value={col.name}>
                            {col.name}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => removeRelationship(rel.tempId)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </Card>
  );
}