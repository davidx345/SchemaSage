// File Processor for Schema Sage
// Handles file parsing and format detection (CSV, Excel, XML, YAML, SQL, etc)

import React, { useState } from "react";
import DragDrop from "./drag-drop";

interface FileProcessorProps {
  onDataReady: (data: string, fileType: string) => void;
}

export default function FileProcessor({ onDataReady }: FileProcessorProps) {
  const [error, setError] = useState<string | null>(null);

  const handleFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      const ext = file.name.split('.').pop()?.toLowerCase();
      let fileType = "unknown";
      if (["json"].includes(ext!)) fileType = "json";
      else if (["csv"].includes(ext!)) fileType = "csv";
      else if (["xml"].includes(ext!)) fileType = "xml";
      else if (["yaml", "yml"].includes(ext!)) fileType = "yaml";
      else if (["sql"].includes(ext!)) fileType = "sql";
      else if (["xlsx"].includes(ext!)) fileType = "excel";
      else fileType = ext || "unknown";
      if (!text) {
        setError("Failed to read file content.");
        return;
      }
      onDataReady(text, fileType);
    };
    reader.onerror = () => setError("Error reading file.");
    reader.readAsText(file);
  };

  return (
    <div>
      <DragDrop onFileAccepted={handleFile} />
      {error && <div className="text-red-500 mt-2">{error}</div>}
    </div>
  );
}
