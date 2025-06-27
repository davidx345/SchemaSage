"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { CodePreview } from "@/components/code-preview";
import { useStore } from "@/lib/store";
import { schemaApi } from "@/lib/api";
import { CodeGenFormat } from "@/lib/types";
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { ErrorBoundary } from "@/components/error-boundary";

export default function CodePage() {
  const router = useRouter();
  const { currentSchema } = useStore();
  const [language, setLanguage] = useState<"typescript" | "python" | "sql">("typescript");
  const [format, setFormat] = useState<CodeGenFormat>("typescript-types");
  const [includeComments, setIncludeComments] = useState<boolean>(true);
  const [includeValidation, setIncludeValidation] = useState<boolean>(true);
  const [generatedCode, setGeneratedCode] = useState<string>("");
  const [isGenerating, setIsGenerating] = useState<boolean>(false);

  // Only render content after schema check to prevent double sidebar flash
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (!currentSchema) {
      toast.error("No schema data found. Please upload data first.");
      router.push("/upload");
    } else {
      setChecked(true);
    }
  }, [currentSchema, router]);

  // Handle language selection and update available formats
  const handleLanguageChange = (value: string) => {
    setLanguage(value as "typescript" | "python" | "sql");
    
    // Set default format based on language
    switch (value) {
      case "typescript":
        setFormat("typescript-types");
        break;
      case "python":
        setFormat("python-dataclass");
        break;
      case "sql":
        setFormat("sql-table");
        break;
      default:
        // Use a valid default format instead of empty string
        setFormat("typescript-types");
    }
  };

  // Handle format selection
  const handleFormatChange = (value: string) => {
    setFormat(value as CodeGenFormat);
  };

  // Generate code using the API
  const handleGenerateCode = async () => {
    if (!currentSchema) {
      toast.error("No schema available for code generation");
      return;
    }

    setIsGenerating(true);
    
    try {
      const response = await schemaApi.generateCode(
        currentSchema, 
        format,
        {
          includeComments,
          includeValidation,
          language,
          format // Add the missing format property
        }
      );

      if (response.success && response.data) {
        setGeneratedCode(response.data);
        toast.success("Code generated successfully!");
      } else {
        toast.error(`Failed to generate code: ${response.error?.message}`);
      }
    } catch (error) {
      toast.error(`Error: ${error instanceof Error ? error.message : "Unknown error"}`);
      console.error("Code generation error:", error);
    } finally {
      setIsGenerating(false);
    }
  };  

  // If no schema data, show loading or empty state
  if (!currentSchema) {
    return (
      <div className="relative flex min-h-screen bg-background">
        <Sidebar sidebarCollapsed={false} setSidebarCollapsed={() => {}} />
        <div className="flex-1">
          <Header />
          <main className="p-6">
            <div className="flex items-center justify-center h-[60vh]">
              <div className="text-center max-w-md">
                <div className="mb-6">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-muted flex items-center justify-center shadow-card">
                    <AlertCircle className="w-8 h-8 text-primary" />
                  </div>
                  <h2 className="text-2xl font-bold mb-3">No Schema Data</h2>
                  <p className="text-muted-foreground mb-6">
                    You need to upload data or connect to a database first.
                  </p>
                  <p className="text-xs text-muted-foreground/70 mb-6">
                    Tip: Try the sample project from onboarding to explore code generation features.
                  </p>
                </div>
                <Button 
                  onClick={() => router.push("/upload")}
                  className="cta"
                >
                  Upload Data
                </Button>
              </div>
            </div>
          </main>
        </div>
      </div>
    );
  }

  // Remove the early return that renders sidebar/header if !currentSchema
  // Only render content after schema check to prevent double sidebar flash
  if (!checked) {
    return null; // or a loader if you prefer
  }

  return (
    <div className="relative flex min-h-screen bg-background">
      <Sidebar sidebarCollapsed={false} setSidebarCollapsed={() => {}} />
      <div className="flex-1">
        <Header />
        <main className="p-6">
          <ErrorBoundary>
            <div className="space-y-8">
              <div>
                <h1 className="text-3xl font-bold mb-3">Code Generation</h1>
                <p className="text-muted-foreground">
                  Generate code for your database schema in multiple languages and formats.
                </p>
              </div>
              <div className="grid gap-8 md:grid-cols-12">
                <Card className="p-8 md:col-span-4 card shadow-card">
                  <div className="space-y-6">
                    <div className="space-y-4">
                      <h2 className="text-lg font-semibold">Generation Options</h2>
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="language" className="text-sm font-medium">Language</Label>
                          <div className="flex gap-4 items-end">
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Select value={language} onValueChange={handleLanguageChange}>
                                  <SelectTrigger className="w-[150px] bg-muted">
                                    <SelectValue placeholder="Select language" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="typescript">TypeScript</SelectItem>
                                    <SelectItem value="python">Python</SelectItem>
                                    <SelectItem value="sql">SQL</SelectItem>
                                  </SelectContent>
                                </Select>
                              </TooltipTrigger>
                              <TooltipContent>Select code generation language</TooltipContent>
                            </Tooltip>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="format" className="text-sm font-medium">Format</Label>
                          <Select
                            value={format}
                            onValueChange={handleFormatChange}
                          >
                            <SelectTrigger className="bg-muted">
                              <SelectValue placeholder="Select format" />
                            </SelectTrigger>
                            <SelectContent>
                              {language === "typescript" && (
                                <>
                                  <SelectItem value="typescript-types">TypeScript Interfaces</SelectItem>
                                  <SelectItem value="typescript-zod">TypeScript with Zod</SelectItem>
                                  <SelectItem value="typescript-class">TypeScript Classes</SelectItem>
                                </>
                              )}
                              {language === "python" && (
                                <>
                                  <SelectItem value="python-dataclass">Python Dataclasses</SelectItem>
                                  <SelectItem value="python-pydantic">Python Pydantic</SelectItem>
                                </>
                              )}
                              {language === "sql" && (
                                <>
                                  <SelectItem value="sql-table">SQL Create Tables</SelectItem>
                                  <SelectItem value="sql-migration">SQL Migration</SelectItem>
                                </>
                              )}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-3 pt-2 border-t border-divider">
                          <div className="flex items-center space-x-2">
                            <Checkbox 
                              id="comments"
                              checked={includeComments}
                              onCheckedChange={(checked: boolean) => setIncludeComments(checked)}
                            />
                            <Label htmlFor="comments" className="text-sm">Include comments</Label>
                          </div>
                          <div className="flex items-center space-x-2">
                            <Checkbox 
                              id="validation"
                              checked={includeValidation}
                              onCheckedChange={(checked: boolean) => setIncludeValidation(checked)}
                            />
                            <Label htmlFor="validation" className="text-sm">Include validation</Label>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="border-t border-divider pt-6">
                      <h3 className="text-lg font-semibold mb-4">Schema Summary</h3>
                      <div className="rounded-lg bg-muted border border-divider p-4 text-sm">
                        <div className="space-y-2">
                          <p className="font-medium">Tables: <span className="text-secondary-foreground">{currentSchema.tables.length}</span></p>
                          <p className="font-medium">Columns: <span className="text-success">{currentSchema.tables.reduce((sum, table) => sum + table.columns.length, 0)}</span></p>
                          <p className="font-medium">Relationships: <span className="text-primary">{currentSchema.relationships?.length || 0}</span></p>
                        </div>
                      </div>
                    </div>
                    <Button 
                      className="w-full cta" 
                      onClick={handleGenerateCode}
                      disabled={isGenerating}
                    >
                      {isGenerating ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Generating...
                        </>
                      ) : "Generate Code"}
                    </Button>
                  </div>
                </Card>
                <div className="md:col-span-8">
                  <Card className="h-[800px] card shadow-card">
                    <CodePreview 
                      code={generatedCode || `// Select options and click \"Generate Code\" to get started\n\n// Your ${language} code will appear here`} 
                      language={language}
                      onLanguageChange={handleLanguageChange}
                    />
                  </Card>
                </div>
              </div>
            </div>
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
}