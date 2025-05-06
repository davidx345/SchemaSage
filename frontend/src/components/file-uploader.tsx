"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Upload, File, Loader2, AlertCircle, CheckCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatFileSize } from "@/lib/utils";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { detectSchemaFromFile } from "@/lib/api";
import { useStore } from "@/lib/store";
import { toast } from "sonner";

interface FileUploaderProps {
  onDataReady?: (data: string) => void;
  onError?: (error: Error) => void;
  onSchemaDetected?: () => void;
  accept?: Record<string, string[]>;
  maxSize?: number;
}

export function FileUploader({ 
  onDataReady, 
  onError,
  onSchemaDetected,
  accept = {
    "application/json": [".json"],
    "text/csv": [".csv"],
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    "application/xml": [".xml"],
    "application/x-yaml": [".yaml", ".yml"],
    "application/sql": [".sql"],
  },
  maxSize = 10 * 1024 * 1024, // 10MB default
}: FileUploaderProps) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [fileName, setFileName] = useState<string>();
  const [error, setError] = useState<string>();
  const [success, setSuccess] = useState(false);
  const { setCurrentSchema } = useStore();

  // Process the uploaded file
  const processFile = useCallback(async (file: File) => {
    setIsProcessing(true);
    setFileName(file.name);
    setError(undefined);
    setSuccess(false);

    try {
      if (file.size > maxSize) {
        throw new Error(`File size exceeds ${formatFileSize(maxSize)}`);
      }

      // Read file content
      const text = await file.text();
      onDataReady?.(text);

      // Send to backend API for schema detection
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await detectSchemaFromFile(file);
      
      if (response.success && response.data) {
        setCurrentSchema(response.data);
        setSuccess(true);
        toast.success("Schema successfully detected!");
        onSchemaDetected?.();
      } else {
        throw new Error(response.error?.message || "Failed to detect schema");
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to process file";
      setError(message);
      toast.error(`Error: ${message}`);
      console.error("Error processing file:", err);
      onError?.(err instanceof Error ? err : new Error(message));
    } finally {
      setIsProcessing(false);
    }
  }, [maxSize, onDataReady, onError, onSchemaDetected, setCurrentSchema]);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      await processFile(file);
    }
  }, [processFile]);

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept,
    maxFiles: 1,
    maxSize,
    multiple: false,
  });

  // Show file rejection errors
  const rejectionError = fileRejections[0]?.errors[0]?.message;
  const displayError = error || rejectionError;

  return (
    <div className="space-y-4">
      <Card
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed p-8 text-center hover:border-primary/50 transition-colors cursor-pointer",
          isDragActive && "border-primary bg-primary/5",
          displayError && "border-destructive",
          success && "border-green-500"
        )}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-4">
          {isProcessing ? (
            <>
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                Processing {fileName}...
              </p>
            </>
          ) : success ? (
            <>
              <CheckCircle className="h-8 w-8 text-green-500" />
              <div className="space-y-2">
                <p className="font-medium text-green-500">Schema detected successfully!</p>
                <p className="text-sm text-muted-foreground">
                  File: {fileName}
                </p>
              </div>
            </>
          ) : (
            <>
              {isDragActive ? (
                <>
                  <File className="h-8 w-8 text-primary" />
                  <p className="text-primary">Drop your file here</p>
                </>
              ) : (
                <>
                  <Upload className="h-8 w-8 text-muted-foreground" />
                  <div className="space-y-2">
                    <p>Drag & drop your file here</p>
                    <p className="text-sm text-muted-foreground">
                      Supported formats: JSON, CSV, XLSX, XML, YAML, SQL
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Max file size: {formatFileSize(maxSize)}
                    </p>
                  </div>
                  <Button variant="secondary" size="sm">
                    Browse Files
                  </Button>
                </>
              )}
            </>
          )}
        </div>
      </Card>

      {displayError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{displayError}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}