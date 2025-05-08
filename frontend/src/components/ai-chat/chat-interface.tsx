// AI Chat Interface for Schema Sage
// Provides interactive chat UI for schema analysis and modification

import React, { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/input";
import type { SchemaResponse } from "@/lib/types";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ChatInterfaceProps {
  schema: SchemaResponse;
}

export default function ChatInterface({ schema }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async () => {
    if (!input.trim() || !schema) {
      setError(!schema ? "No schema loaded. Please load a schema first." : null);
      return;
    }
    setError(null);
    const userMessage: Message = { role: "user", content: input };
    setMessages((msgs) => [...msgs, userMessage]);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch("/api/schema/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: [...messages, userMessage], schema_data: schema })
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Unprocessable request");
      }
      const data = await res.json();
      setMessages((msgs) => [...msgs, { role: "assistant", content: data.response }]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Sorry, there was an error.");
      setMessages((msgs) => [...msgs, { role: "assistant", content: "Sorry, there was an error." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="p-4 w-full max-w-xl mx-auto">
      <div className="h-64 overflow-y-auto mb-4 bg-muted rounded p-2">
        {messages.length === 0 && <div className="text-muted-foreground">Ask me anything about your schema or code!</div>}
        {messages.map((msg, idx) => (
          <div key={idx} className={msg.role === "user" ? "text-right" : "text-left text-primary"}>
            <span className={msg.role === "user" ? "font-semibold" : "font-medium"}>
              {msg.role === "user" ? "You: " : "Assistant: "}
            </span>
            {msg.content}
          </div>
        ))}
        {error && <div className="text-red-500 text-sm mt-2">{error}</div>}
      </div>
      <div className="flex gap-2">
        <Textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Type your question..."
          className="flex-1"
          rows={2}
          disabled={loading || !schema}
        />
        <Button onClick={sendMessage} disabled={loading || !input.trim() || !schema}>
          {loading ? "..." : "Send"}
        </Button>
      </div>
    </Card>
  );
}
