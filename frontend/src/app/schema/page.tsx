"use client";

import { useEffect, useState } from "react";
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
import { projectApi } from "@/lib/api";
import type { SchemaResponse, Relationship } from "@/lib/types";

export default function SchemaPage() {
  const router = useRouter();
  const { currentSchema, setCurrentSchema } = useStore();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);

  // Redirect to upload page if no schema is present
  useEffect(() => {
    if (!currentSchema) {
      toast.error("No schema data found. Please upload data first.");
      router.push("/upload");
    }
  }, [currentSchema, router]);

  // Validate API key on component mount
  useEffect(() => {
    const validateApiKey = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await projectApi.validateApiKey();
        if (!response.success) {
          setError(response.error?.message || "API key validation failed");
          toast.error("API key validation failed. Some features may not work correctly.");
        }
      } catch (err) {
        console.error("API key validation error:", err);
        setError("Failed to validate API key");
      } finally {
        setIsLoading(false);
      }
    };

    validateApiKey();
  }, []);

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

  // Show loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">Loading Schema</h2>
          <p className="text-muted-foreground">
            Please wait while we load your schema...
          </p>
        </div>
      </div>
    );
  }

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
      </div>
    </div>
  );
}