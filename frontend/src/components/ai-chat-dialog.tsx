"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar } from "@/components/ui/avatar";
import { Loader2, Send, Bot, User } from "lucide-react";
import { cn } from "@/lib/utils";
import { useStore } from "@/lib/store";
import { schemaApi } from "@/lib/api";
import { ChatMessage } from "@/lib/types";
import { formatDistanceToNow } from "date-fns";
import ReactMarkdown from "react-markdown";

export function AIChatDialog() {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [input, setInput] = useState("");
  const { currentSchema, chatHistory, setChatHistory } = useStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Listen for custom event to open the chat dialog
  useEffect(() => {
    const handleOpenEvent = () => setIsOpen(true);
    document.addEventListener("toggle-ai-chat", handleOpenEvent);
    return () => {
      document.removeEventListener("toggle-ai-chat", handleOpenEvent);
    };
  }, []);

  // Auto-scroll to the bottom when messages are added
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  // Send a message to the AI assistant
  const sendMessage = async () => {
    if (!input.trim()) return;
    
    // Add user message to chat history
    const userMessage: ChatMessage = {
      role: "user",
      content: input.trim(),
      timestamp: new Date().toISOString()
    };
    
    // Update the chat history with the user message first
    const updatedHistory = [...chatHistory, userMessage];
    setChatHistory(updatedHistory);
    setInput("");
    setIsLoading(true);
    
    try {
      // Prepare schema context - pass the full schema object
      const schemaContext = currentSchema ? { ...currentSchema } : undefined;
      
      // Call the chat API with the updated history
      const response = await schemaApi.chat(updatedHistory, schemaContext);
      
      if (response.success && response.data) {
        setChatHistory([...updatedHistory, response.data]);
      } else {
        // Add error message as an assistant message
        const errorMessage: ChatMessage = {
          role: "assistant",
          content: `Sorry, I encountered an error: ${response.error?.message || "Unknown error"}. Please try again with a different question.`,
          timestamp: new Date().toISOString()
        };
        setChatHistory([...updatedHistory, errorMessage]);
      }
    } catch (error) {
      console.error("Chat API error:", error);
      // Add error message
      const errorMessage: ChatMessage = {
        role: "assistant",
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : "Unknown error"}. Please check your connection and try again.`,
        timestamp: new Date().toISOString()
      };
      setChatHistory([...updatedHistory, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage();
  };

  // Initialize with a welcome message if chat history is empty
  useEffect(() => {
    if (chatHistory.length === 0) {
      const welcomeMessage: ChatMessage = {
        role: "assistant",
        content: "Hi! I'm your schema assistant. Ask me anything about your database schema, and I'll help you understand it better. I can also help with optimization suggestions, relationship advice, and more.",
        timestamp: new Date().toISOString()
      };
      setChatHistory([welcomeMessage]);
    }
  }, [chatHistory, setChatHistory]);

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent className="sm:max-w-[500px] h-[600px] flex flex-col p-0">
        <DialogHeader className="p-4 border-b">
          <DialogTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            Schema AI Assistant
          </DialogTitle>
          <DialogDescription>
            Ask questions about your database schema
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4">
            {chatHistory.map((message, index) => (
              <div
                key={index}
                className={cn(
                  "flex gap-3 text-sm",
                  message.role === "assistant" ? "flex-row" : "flex-row-reverse"
                )}
              >
                <Avatar className={cn(
                  "h-8 w-8 rounded-full border",
                  message.role === "assistant"
                    ? "bg-primary/10 text-primary"
                    : "bg-muted"
                )}>
                  {message.role === "assistant" ? (
                    <Bot className="h-4 w-4" />
                  ) : (
                    <User className="h-4 w-4" />
                  )}
                </Avatar>
                <div className="flex flex-col gap-1 max-w-[350px]">
                  <div
                    className={cn(
                      "rounded-lg p-3",
                      message.role === "assistant"
                        ? "bg-muted"
                        : "bg-primary text-primary-foreground"
                    )}
                  >
                    {message.role === "assistant" ? (
                      <div className="prose dark:prose-invert prose-sm">
                        <ReactMarkdown>
                          {message.content}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      message.content
                    )}
                  </div>
                  {message.timestamp && (
                    <span className="text-xs text-muted-foreground px-2">
                      {formatDistanceToNow(new Date(message.timestamp), { addSuffix: true })}
                    </span>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        <DialogFooter className="p-4 border-t flex flex-row gap-2">
          <form onSubmit={handleSubmit} className="flex w-full gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about your schema..."
              disabled={isLoading}
              className="flex-1"
            />
            <Button type="submit" size="icon" disabled={isLoading || !input.trim()}>
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </form>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}