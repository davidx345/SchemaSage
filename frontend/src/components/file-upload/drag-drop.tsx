// Drag and Drop File Upload for Schema Sage
// Handles drag-and-drop file uploads for schema detection

import React, { useRef } from "react";

interface DragDropProps {
  onFileAccepted: (file: File) => void;
}

export default function DragDrop({ onFileAccepted }: DragDropProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFileAccepted(e.dataTransfer.files[0]);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileAccepted(e.target.files[0]);
    }
  };

  return (
    <div
      onDrop={handleDrop}
      onDragOver={e => e.preventDefault()}
      onClick={handleClick}
      className="border-2 border-dashed rounded-md p-6 text-center cursor-pointer hover:bg-accent"
      style={{ minHeight: 120 }}
    >
      <input
        type="file"
        ref={fileInputRef}
        style={{ display: "none" }}
        onChange={handleFileChange}
        accept=".json,.csv,.xlsx,.xml,.yaml,.yml,.sql"
      />
      <p>Drag and drop a file here, or click to select</p>
    </div>
  );
}
