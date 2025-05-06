"use client";

import { useEffect, useState } from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CodeGenFormat } from "@/lib/types";
import { cn } from "@/lib/utils";
import { CopyButton } from "../ui/copy-button";
import type { SchemaResponse } from "@/lib/types";

interface ErrorDetails {
  error?: string;
  details?: string[];
  [key: string]: string[] | string | undefined;
}

interface GenerationError {
  message: string;
  format?: string;
  details?: ErrorDetails;
}

interface APIError {
  response?: {
    data?: {
      message?: string;
      format?: string;
      details?: ErrorDetails;
    };
  };
}

interface GeneratedCodeProps {
  schema: SchemaResponse | null;
  generatedCode: {
    sqlDDL?: string;
    jsonSchema?: string;
    sqlalchemy?: string;
    pythonDataclasses?: string;
  };
  generateCode: (format: string) => Promise<void>;
}

export function GeneratedCode({ schema, generatedCode, generateCode }: GeneratedCodeProps) {
  const [activeTab, setActiveTab] = useState<string>("sql");
  const [error, setError] = useState<GenerationError | null>(null);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);

  useEffect(() => {
    async function generate() {
      if (!schema) return;

      setIsGenerating(true);
      setError(null);

      try {
        // Generate code for current format
        const format = activeTab.toUpperCase() as CodeGenFormat;
        await generateCode(format);
      } catch (e: unknown) {
        console.error("Code generation error:", e);
        const apiError = e as APIError;
        setError({
          message: apiError.response?.data?.message || "Failed to generate code",
          format: apiError.response?.data?.format,
          details: apiError.response?.data?.details,
        });
      } finally {
        setIsGenerating(false);
      }
    }

    generate();
  }, [schema, activeTab, generateCode]);

  if (!schema) {
    return (
      <div className="mt-4">
        <Alert>
          <AlertTitle>No Schema Detected</AlertTitle>
          <AlertDescription>
            Enter some data above to detect and generate schema code.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="mt-4">
      <Tabs defaultValue="sql" value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="sql">SQL DDL</TabsTrigger>
          <TabsTrigger value="json">JSON Schema</TabsTrigger>
          <TabsTrigger value="sqlalchemy">SQLAlchemy</TabsTrigger>
          <TabsTrigger value="pythondataclasses">Python dataclasses</TabsTrigger>
        </TabsList>

        {error && (
          <Alert variant="destructive" className="my-4">
            <AlertTitle>Generation Error</AlertTitle>
            <AlertDescription>
              <p>{error.message}</p>
              {error.details?.error && (
                <pre className="mt-2 whitespace-pre-wrap text-sm">
                  {error.details.error}
                </pre>
              )}
            </AlertDescription>
          </Alert>
        )}

        <TabsContent value="sql">
          <Card className="p-4 relative">
            <CopyButton
              text={generatedCode.sqlDDL || ""}
              label="SQL DDL"
              disabled={isGenerating}
            />
            <ScrollArea
              className={cn(
                "h-[300px] w-full rounded-md border p-4",
                isGenerating && "opacity-50"
              )}
            >
              <pre>
                <code className="language-sql">
                  {isGenerating
                    ? "Generating SQL DDL..."
                    : generatedCode.sqlDDL || "-- No SQL DDL generated yet"}
                </code>
              </pre>
            </ScrollArea>
          </Card>
        </TabsContent>

        <TabsContent value="json">
          <Card className="p-4 relative">
            <CopyButton
              text={generatedCode.jsonSchema || ""}
              label="JSON Schema"
              disabled={isGenerating}
            />
            <ScrollArea
              className={cn(
                "h-[300px] w-full rounded-md border p-4",
                isGenerating && "opacity-50"
              )}
            >
              <pre>
                <code className="language-json">
                  {isGenerating
                    ? "Generating JSON Schema..."
                    : generatedCode.jsonSchema || "// No JSON Schema generated yet"}
                </code>
              </pre>
            </ScrollArea>
          </Card>
        </TabsContent>

        <TabsContent value="sqlalchemy">
          <Card className="p-4 relative">
            <CopyButton
              text={generatedCode.sqlalchemy || ""}
              label="SQLAlchemy Models"
              disabled={isGenerating}
            />
            <ScrollArea
              className={cn(
                "h-[300px] w-full rounded-md border p-4",
                isGenerating && "opacity-50"
              )}
            >
              <pre>
                <code className="language-python">
                  {isGenerating
                    ? "Generating SQLAlchemy models..."
                    : generatedCode.sqlalchemy || "# No SQLAlchemy models generated yet"}
                </code>
              </pre>
            </ScrollArea>
          </Card>
        </TabsContent>

        <TabsContent value="pythondataclasses">
          <Card className="p-4 relative">
            <CopyButton
              text={generatedCode.pythonDataclasses || ""}
              label="Python dataclasses"
              disabled={isGenerating}
            />
            <ScrollArea
              className={cn(
                "h-[300px] w-full rounded-md border p-4",
                isGenerating && "opacity-50"
              )}
            >
              <pre>
                <code className="language-python">
                  {isGenerating
                    ? "Generating Python dataclasses..."
                    : generatedCode.pythonDataclasses || "# No Python dataclasses generated yet"}
                </code>
              </pre>
            </ScrollArea>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}