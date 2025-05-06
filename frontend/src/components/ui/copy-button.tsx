import { useState } from "react";
import { Button } from "./button";
import { Check, Copy } from "lucide-react";

interface CopyButtonProps {
  text: string;
  label?: string;
  disabled?: boolean;
}

export function CopyButton({ text, label, disabled }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    if (disabled || !text) return;
    
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1000);
  };

  return (
    <Button
      size="sm"
      variant="outline"
      className="absolute right-4 top-4 z-10"
      onClick={copy}
      disabled={disabled || !text}
    >
      {copied ? (
        <>
          <Check className="h-4 w-4" />
          Copied!
        </>
      ) : (
        <>
          <Copy className="h-4 w-4" />
          {label ? label : "Copy"}
        </>
      )}
    </Button>
  );
}