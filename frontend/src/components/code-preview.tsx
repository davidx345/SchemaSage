"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Copy, Check, Download } from "lucide-react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark, oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import { useTheme } from "next-themes";

interface CodePreviewProps {
  code: string;
  language: string;
  onLanguageChange?: (language: string) => void;
}

const supportedLanguages = [
  { value: "typescript", label: "TypeScript" },
  { value: "python", label: "Python" },
  { value: "sql", label: "SQL" },
  { value: "json", label: "JSON" },
];

export function CodePreview({ code, language, onLanguageChange }: CodePreviewProps) {
  const [copied, setCopied] = useState(false);
  const { theme } = useTheme();
  const [activeTab, setActiveTab] = useState<"preview" | "raw">("preview");

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadCode = () => {
    const blob = new Blob([code], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `schema.${language}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Card className="flex flex-col h-full">
      <div className="flex items-center justify-between border-b p-4">
        <div className="flex items-center gap-4">
          <Select value={language} onValueChange={onLanguageChange}>
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="Select language" />
            </SelectTrigger>
            <SelectContent>
              {supportedLanguages.map((lang) => (
                <SelectItem key={lang.value} value={lang.value}>
                  {lang.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "preview" | "raw")}>
            <TabsList>
              <TabsTrigger value="preview">Preview</TabsTrigger>
              <TabsTrigger value="raw">Raw</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" onClick={copyToClipboard}>
            {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
          </Button>
          <Button variant="ghost" size="icon" onClick={downloadCode}>
            <Download className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="relative flex-1 overflow-auto">
        <Tabs value={activeTab} className="h-full">
          <TabsList className="px-4 border-b">
            <TabsTrigger value="preview">Preview</TabsTrigger>
            <TabsTrigger value="raw">Raw</TabsTrigger>
          </TabsList>
          <TabsContent value="preview" className="p-4">
            <SyntaxHighlighter
              language={language}
              style={theme === "dark" ? oneDark : oneLight}
              customStyle={{
                margin: 0,
                height: "100%",
                backgroundColor: "transparent",
              }}
              showLineNumbers
            >
              {code}
            </SyntaxHighlighter>
          </TabsContent>

          <TabsContent value="raw" className="p-4">
            <pre className="whitespace-pre-wrap break-all">{code}</pre>
          </TabsContent>
        </Tabs>
      </div>
    </Card>
  );
}