"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/input";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Card } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ApiError } from "@/lib/api";
import FileProcessor from "../file-upload/file-processor";
import { schemaApi } from "@/lib/api";
import type { SchemaResponse } from "@/lib/types";
import ERDiagram from "../visualization/er-diagram";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import ChatInterface from "@/components/ai-chat/chat-interface";

interface ValidationError {
  message: string;
  details?: {
    details?: string[];
    error?: string;
    suggestion?: string;
    [key: string]: unknown;
  };
}

export function SchemaForm() {
  const [input, setInput] = useState("");
  const [error, setError] = useState<ValidationError | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [schema, setSchema] = useState<SchemaResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) {
      setError({
        message: "Please enter some data to analyze",
        details: { error: "Input cannot be empty" },
      });
      return;
    }

    setIsLoading(true);
    setError(null);
      try {
      const result = await schemaApi.detectSchema(input);
      if (result.success && result.data) {
        setSchema(result.data.schema);
      } else {
        setError({
          message: result.error?.message || "Failed to detect schema",
          details: {
            error: result.error?.message || "Schema detection returned no data",
          }
        });
      }
    } catch (error: unknown) {
      console.error("Schema detection error:", error);
      const apiError = error as ApiError;
      setError({
        message: apiError.message || "Failed to detect schema",
        details: {
          error: apiError.details?.error || "An unexpected error occurred",
          suggestion: apiError.details?.suggestion,
        }
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    if (error) setError(null); // Clear error when input changes
  };

  const validateInput = (value: string): boolean => {
    if (!value.trim()) return false;

    // Try parsing as JSON
    try {
      JSON.parse(value);
      return true;
    } catch {
      // If not JSON, check if it looks like CSV
      // Simple check: contains commas and newlines
      return value.includes(",") && value.includes("\n");
    }
  };
  const handleFileData = async (data: string) => {
    setError(null);
    setIsLoading(true);
    try {
      const response = await schemaApi.detectSchema(data);
      if (response.success && response.data) {
        setSchema(response.data.schema);
      } else {
        setError({
          message: response.error?.message || "Failed to detect schema from file",
          details: {
            error: response.error?.message || "Schema detection returned no data",
          }
        });
      }
    } catch (err) {
      const errorObj = err as ApiError;
      setError({
        message: errorObj.message || "Failed to detect schema from file.",
        details: { error: errorObj.message || "Failed to detect schema from file." },
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="p-4">
      <Tabs defaultValue="schema" className="w-full">
        <TabsList>
          <TabsTrigger value="schema">Schema</TabsTrigger>
          <TabsTrigger value="er">ER Diagram</TabsTrigger>
          <TabsTrigger value="chat">Chat</TabsTrigger>
        </TabsList>
        <TabsContent value="schema">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <ScrollArea className="h-[200px] w-full rounded-md border">
                <Textarea
                  placeholder="Paste your JSON or CSV data here..."
                  value={input}
                  onChange={handleInputChange}
                  className="min-h-[200px] resize-none border-0"
                  disabled={isLoading}
                />
              </ScrollArea>

              {error && (
                <Alert variant="destructive">
                  <AlertTitle>{error.message}</AlertTitle>
                  <AlertDescription>
                    <p>{String(error.details?.error)}</p>
                    {error.details?.suggestion && (
                      <p className="mt-2 text-sm opacity-90">{String(error.details.suggestion)}</p>
                    )}
                  </AlertDescription>
                </Alert>
              )}
            </div>

            <div className="flex justify-between items-center">
              <p className="text-sm text-muted-foreground">
                {isLoading ? "Detecting schema... This may take a few seconds." : " "}
              </p>
              <Button
                type="submit"
                disabled={isLoading || !validateInput(input)}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Detecting Schema...
                  </>
                ) : (
                  "Detect Schema"
                )}
              </Button>
            </div>
          </form>
          <FileProcessor onDataReady={handleFileData} />
          {schema && (
            <pre className="bg-muted p-2 rounded text-xs overflow-x-auto mt-2">
              {JSON.stringify(schema, null, 2)}
            </pre>
          )}
        </TabsContent>
        <TabsContent value="er">
          <ERDiagram schema={schema} />
        </TabsContent>
        <TabsContent value="chat">
          {schema && <ChatInterface schema={schema} />}
        </TabsContent>
      </Tabs>
    </Card>
  );
}