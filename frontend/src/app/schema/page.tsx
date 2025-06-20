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
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip";
import { MainLayout } from "@/components/main-layout";

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
  };  // Show error state
  if (error) {
    return (
      <MainLayout title="Schema Visualization" currentPage="schema">
        <div className="space-y-6 max-w-2xl mx-auto pt-12">
          <Alert variant="destructive" className="bg-red-50/50 backdrop-blur-sm border-red-200/50">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>          <div className="text-center">
            <Button 
              onClick={() => router.push("/upload")}
              className="bg-gradient-to-r from-slate-600 to-blue-600 hover:from-slate-700 hover:to-blue-700 text-white"
            >
              Back to Upload
            </Button>
          </div>
        </div>
      </MainLayout>
    );
  }

  // If no schema data, show empty state
  if (!currentSchema) {
    return (
      <MainLayout title="Schema Visualization" currentPage="schema">
        <div className="flex items-center justify-center h-[60vh]">
          <div className="text-center max-w-md">
            <div className="mb-6">              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-r from-blue-100 to-teal-100 dark:from-blue-900/20 dark:to-teal-900/20 flex items-center justify-center">
                <AlertCircle className="w-8 h-8 text-blue-600 dark:text-blue-400" />
              </div><h2 className="text-2xl font-bold mb-3 bg-gradient-to-r from-slate-600 to-sky-600 bg-clip-text text-transparent">
                Ready to View Schema
              </h2>
              <p className="text-muted-foreground mb-6">
                You need to upload data or connect to a database first.
              </p>
              <p className="text-xs text-muted-foreground/70 mb-6">
                💡 Tip: Try the sample project from onboarding to explore features.
              </p>
            </div>            <Button 
              onClick={() => router.push("/upload")}
              className="bg-gradient-to-r from-slate-600 to-blue-600 hover:from-slate-700 hover:to-blue-700 text-white"
            >
              Upload Data
            </Button>
          </div>
        </div>
      </MainLayout>
    );
  }  return (
    <MainLayout 
      title="Schema Visualization" 
      subtitle="View and edit your database schema"
      currentPage="schema"
    >
      <div className="space-y-8">
        <div className="flex justify-between items-center">
          <div>            <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-slate-700 to-sky-600 bg-clip-text text-transparent">
              Schema Visualization
            </h1>
            <p className="text-muted-foreground mt-2">
              View and edit your database schema
            </p>
          </div>
          <Tooltip>
            <TooltipTrigger asChild>
              <Select defaultValue="current-project">
                <SelectTrigger className="w-[200px] bg-background/50 backdrop-blur-sm border-border/50">
                  <SelectValue placeholder="Select project" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="current-project">Current Project</SelectItem>
                </SelectContent>
              </Select>
            </TooltipTrigger>
            <TooltipContent>Select a project to view its schema</TooltipContent>
          </Tooltip>
        </div>

        <div className="grid gap-8 grid-cols-1">
          <Card className="col-span-1 bg-background/50 backdrop-blur-sm border-border/50 shadow-lg">
            {isUpdating ? (
              <div className="flex items-center justify-center p-8">
                <Loader2 className="h-6 w-6 animate-spin mr-2 text-blue-500" />
                <span>Updating schema...</span>
              </div>
            ) : (
              <SchemaVisualization schema={currentSchema} />
            )}
          </Card>
          
          <div className="bg-background/50 backdrop-blur-sm border border-border/50 rounded-lg shadow-lg">
            <RelationshipEditor 
              schema={currentSchema} 
              onUpdate={handleRelationshipUpdate}
            />
          </div>
          
          {/* --- Code Generation Section --- */}
          <Card className="col-span-1 p-8 bg-background/50 backdrop-blur-sm border-border/50 shadow-lg">
            <div className="mb-6">              <h3 className="text-xl font-semibold mb-2 bg-gradient-to-r from-teal-600 to-sky-600 bg-clip-text text-transparent">
                Code Generation
              </h3>
              <p className="text-muted-foreground text-sm">
                Generate code from your schema in multiple languages and formats
              </p>
            </div>
            
            <div className="flex flex-col md:flex-row md:items-end gap-4 mb-6">
              <div>
                <label className="block text-sm font-medium mb-2">Language</label>
                <Select value={codeGenLanguage} onValueChange={setCodeGenLanguage}>
                  <SelectTrigger className="w-40 bg-background/50">
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
                <label className="block text-sm font-medium mb-2">Format</label>
                <Select value={codeGenFormat} onValueChange={setCodeGenFormat}>
                  <SelectTrigger className="w-56 bg-background/50">
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
              <div className="flex gap-2">
                <Button 
                  onClick={handleGenerateCode} 
                  disabled={isGeneratingCode} 
                  className="bg-gradient-to-r from-slate-600 to-sky-600 hover:from-slate-700 hover:to-sky-700 text-white"
                >
                  {isGeneratingCode ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  Generate Code
                </Button>
                <a ref={codeDownloadRef} style={{ display: "none" }} />
                {generatedCode && (
                  <Button 
                    variant="outline" 
                    onClick={handleDownloadCode}
                    className="bg-background/50 hover:bg-background/70"
                  >
                    Download
                  </Button>
                )}
              </div>
            </div>
            
            {generatedCode && (
              <div className="bg-background/30 rounded-lg p-4 border border-border/30">
                <CodePreview code={generatedCode} language={codeGenLanguage} />
              </div>
            )}
          </Card>
        </div>
      </div>
    </MainLayout>
  );
}