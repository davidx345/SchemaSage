"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
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

export default function CodePage() {
  const router = useRouter();
  const { currentSchema } = useStore();
  const [language, setLanguage] = useState<"typescript" | "python" | "sql">("typescript");
  const [format, setFormat] = useState<CodeGenFormat>("typescript-types");
  const [includeComments, setIncludeComments] = useState<boolean>(true);
  const [includeValidation, setIncludeValidation] = useState<boolean>(true);
  const [generatedCode, setGeneratedCode] = useState<string>("");
  const [isGenerating, setIsGenerating] = useState<boolean>(false);

  // Redirect to upload page if no schema is available
  useEffect(() => {
    if (!currentSchema) {
      toast.error("No schema data found. Please upload data first.");
      router.push("/upload");
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
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-2">No Schema Data</h2>
          <p className="text-muted-foreground mb-4">
            You need to upload data or connect to a database first.<br />
            <span className="text-xs">Tip: Try the sample project from onboarding to explore code generation features.</span>
          </p>
          <Button onClick={() => router.push("/upload")}>Upload Data</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold mb-2">Code Generation</h1>
        <p className="text-muted-foreground">
          Generate code for your database schema in multiple languages and formats.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-12">
        <Card className="p-6 md:col-span-4">
          <div className="space-y-6">
            <div className="space-y-4">
              <h2 className="text-lg font-semibold">Generation Options</h2>
              
              <div className="space-y-3">
                <div className="space-y-1">
                  <Label htmlFor="language">Language</Label>
                  <div className="flex gap-4 items-end">
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Select value={language} onValueChange={handleLanguageChange}>
                          <SelectTrigger className="w-[150px]">
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

                <div className="space-y-1">
                  <Label htmlFor="format">Format</Label>
                  <Select
                    value={format}
                    onValueChange={handleFormatChange}
                  >
                    <SelectTrigger>
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

                <div className="space-y-2 pt-2">
                  <div className="flex items-center space-x-2">
                    <Checkbox 
                      id="comments"
                      checked={includeComments}
                      onCheckedChange={(checked: boolean) => setIncludeComments(checked)}
                    />
                    <Label htmlFor="comments">Include comments</Label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Checkbox 
                      id="validation"
                      checked={includeValidation}
                      onCheckedChange={(checked: boolean) => setIncludeValidation(checked)}
                    />
                    <Label htmlFor="validation">Include validation</Label>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h2 className="text-lg font-semibold mb-3">Schema Summary</h2>
              <div className="rounded-md bg-muted p-4 text-sm">
                <p className="font-medium">Tables: {currentSchema.tables.length}</p>
                <p>Columns: {currentSchema.tables.reduce((sum, table) => sum + table.columns.length, 0)}</p>
                <p>Relationships: {currentSchema.relationships?.length || 0}</p>
              </div>
            </div>

            <Button 
              className="w-full" 
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

        <div className="md:col-span-8 h-[800px]">
          <CodePreview 
            code={generatedCode || `// Select options and click "Generate Code" to get started\n\n// Your ${language} code will appear here`} 
            language={language}
            onLanguageChange={handleLanguageChange}
          />
        </div>
      </div>
    </div>
  );
}