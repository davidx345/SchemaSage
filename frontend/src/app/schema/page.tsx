"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { Loader2, AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SchemaVisualization } from "@/components/schema-visualization";
import { RelationshipEditor } from "@/components/relationship-editor";
import { useStore } from "@/lib/store";
import type { SchemaResponse, Relationship } from "@/lib/types";
import { CodePreview } from "@/components/code-preview";

export default function SchemaPage() {
  const router = useRouter();
  const { currentSchema, setCurrentSchema } = useStore();
  const [error, setError] = useState<string | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);

  // --- Code Generation State ---
  const [codeGenLanguage, setCodeGenLanguage] = useState<string>("python");
  const [codeGenFormat, setCodeGenFormat] = useState<string>("python-dataclass");
  const [isGeneratingCode, setIsGeneratingCode] = useState(false);
  const [generatedCode, setGeneratedCode] = useState<string>("");
  const codeDownloadRef = useRef<HTMLAnchorElement>(null);

  // Redirect to upload page if no schema is present
  useEffect(() => {
    if (!currentSchema) {
      toast.error("No schema data found. Please upload data first.");
      router.push("/upload");
    }
  }, [currentSchema, router]);

  // Handle relationship updates
  const handleRelationshipUpdate = async (relationships: Relationship[]) => {
    if (!currentSchema) return;
    
    setIsUpdating(true);
    setError(null);
    
    try {
      // Create a new schema object with updated relationships
      const updatedSchema: SchemaResponse = {
        ...currentSchema,
        relationships: relationships
      };
      
      // Update the schema in global state
      setCurrentSchema(updatedSchema);
      
      toast.success("Relationships updated successfully!");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      setError(`Failed to update relationships: ${message}`);
      toast.error(`Failed to update relationships: ${message}`);
      console.error("Error saving relationships:", error);
    } finally {
      setIsUpdating(false);
    }
  };

  // --- Code Generation Handler ---
  const handleGenerateCode = async () => {
    if (!currentSchema) return;
    setIsGeneratingCode(true);
    setGeneratedCode("");
    try {
      // Call backend API for code generation
      const response = await fetch("/api/code/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          schema: currentSchema,
          options: {
            language: codeGenLanguage,
            format: codeGenFormat
          }
        }),
      });
      const data = await response.json();
      if (response.ok && data.code) {
        setGeneratedCode(data.code);
        toast.success("Code generated successfully!");
      } else {
        toast.error(data.error?.message || "Failed to generate code");
      }
    } catch {
      toast.error("Error generating code");
    } finally {
      setIsGeneratingCode(false);
    }
  };

  // --- Download Handler ---
  const handleDownloadCode = () => {
    if (!generatedCode) return;
    const blob = new Blob([generatedCode], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    if (codeDownloadRef.current) {
      codeDownloadRef.current.href = url;
      codeDownloadRef.current.download = `schema.${codeGenLanguage === "python" ? "py" : codeGenLanguage === "typescript" ? "ts" : "sql"}`;
      codeDownloadRef.current.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    }
  };

  // Show error state
  if (error) {
    return (
      <div className="space-y-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
        <Button onClick={() => router.push("/upload")}>
          Back to Upload
        </Button>
      </div>
    );
  }

  // If no schema data, show empty state
  if (!currentSchema) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-2">No Schema Data</h2>
          <p className="text-muted-foreground mb-4">
            You need to upload data or connect to a database first.
          </p>
          <Button onClick={() => router.push("/upload")}>
            Upload Data
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Schema Visualization</h1>
          <p className="text-muted-foreground">
            View and edit your database schema
          </p>
        </div>
        <Select defaultValue="current-project">
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Select project" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="current-project">Current Project</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="grid gap-6 grid-cols-1">
        <Card className="col-span-1">
          {isUpdating ? (
            <div className="flex items-center justify-center p-6">
              <Loader2 className="h-6 w-6 animate-spin mr-2" />
              <span>Updating schema...</span>
            </div>
          ) : (
            <SchemaVisualization schema={currentSchema} />
          )}
        </Card>
        <RelationshipEditor 
          schema={currentSchema} 
          onUpdate={handleRelationshipUpdate}
        />
        {/* --- Code Generation Section --- */}
        <Card className="col-span-1 p-6">
          <div className="flex flex-col md:flex-row md:items-end gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium mb-1">Language</label>
              <Select value={codeGenLanguage} onValueChange={setCodeGenLanguage}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="python">Python</SelectItem>
                  <SelectItem value="typescript">TypeScript</SelectItem>
                  <SelectItem value="sql">SQL</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Format</label>
              <Select value={codeGenFormat} onValueChange={setCodeGenFormat}>
                <SelectTrigger className="w-56">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {codeGenLanguage === "python" && <>
                    <SelectItem value="python-dataclass">Python Dataclass</SelectItem>
                    <SelectItem value="python-pydantic">Pydantic Model</SelectItem>
                  </>}
                  {codeGenLanguage === "typescript" && <>
                    <SelectItem value="typescript-types">TypeScript Types</SelectItem>
                    <SelectItem value="typescript-zod">Zod Schema</SelectItem>
                    <SelectItem value="typescript-class">Class</SelectItem>
                  </>}
                  {codeGenLanguage === "sql" && <>
                    <SelectItem value="sql-table">SQL Table</SelectItem>
                    <SelectItem value="sql-migration">SQL Migration</SelectItem>
                  </>}
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handleGenerateCode} disabled={isGeneratingCode} className="md:ml-4">
              {isGeneratingCode ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Generate Code
            </Button>
            <a ref={codeDownloadRef} style={{ display: "none" }} />
            {generatedCode && (
              <Button variant="outline" onClick={handleDownloadCode} className="md:ml-2">
                Download
              </Button>
            )}
          </div>
          {generatedCode && (
            <CodePreview code={generatedCode} language={codeGenLanguage} />
          )}
        </Card>
      </div>
    </div>
  );
}