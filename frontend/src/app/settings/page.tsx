"use client";

import { useState, useEffect } from "react";
import { useTheme } from "next-themes";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Save, Moon, Sun } from "lucide-react";
import { useStore } from "@/lib/store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";

const settingsFormSchema = z.object({
  apiKey: z.string().optional(),
  defaultTheme: z.enum(["light", "dark", "system"]),
  autoSave: z.boolean(),
  inferRelationships: z.boolean(),
  detectPrimaryKeys: z.boolean(),
  detectForeignKeys: z.boolean(),
  namingConvention: z.enum(["camelCase", "snake_case", "PascalCase"]),
});

type SettingsFormValues = z.infer<typeof settingsFormSchema>;

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const { settings, setSettings } = useStore();
  const [activeTab, setActiveTab] = useState("general");
  
  // Define default form values
  const defaultValues: SettingsFormValues = {
    apiKey: "",
    defaultTheme: (theme as "light" | "dark" | "system") || "light",
    autoSave: settings.autoSave,
    inferRelationships: settings.detectRelations,
    detectPrimaryKeys: true,
    detectForeignKeys: true,
    namingConvention: "snake_case",
  };
  
  // Initialize form
  const form = useForm<SettingsFormValues>({
    resolver: zodResolver(settingsFormSchema),
    defaultValues,
  });
  
  // Load saved API key on component mount
  useEffect(() => {
    const savedApiKey = localStorage.getItem("gemini_api_key");
    if (savedApiKey) {
      form.setValue("apiKey", savedApiKey);
    }
  }, [form]);
  
  // Form submission handler
  const onSubmit = async (values: SettingsFormValues) => {
    try {
      // Save theme setting
      setTheme(values.defaultTheme);
      
      // Save API key if provided
      if (values.apiKey) {
        localStorage.setItem("gemini_api_key", values.apiKey);
      }
      
      // Update app settings in store
      setSettings({
        ...settings,
        autoSave: values.autoSave,
        detectRelations: values.inferRelationships,
      });
      
      // Save other settings to local storage
      localStorage.setItem("schema_settings", JSON.stringify({
        inferRelationships: values.inferRelationships,
        detectPrimaryKeys: values.detectPrimaryKeys,
        detectForeignKeys: values.detectForeignKeys,
        namingConvention: values.namingConvention,
      }));
      
      toast.success("Settings saved successfully");
    } catch {
      toast.error("Failed to save settings");
    }
  };

  return (
    <div className="container max-w-5xl py-10 space-y-8">
      <div>
        <h1 className="text-3xl font-bold mb-2">Settings</h1>
        <p className="text-muted-foreground">
          Configure your application preferences and API settings
        </p>
      </div>
      
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid grid-cols-3">
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="api">API Keys</TabsTrigger>
          <TabsTrigger value="schema">Schema Preferences</TabsTrigger>
        </TabsList>
        
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <TabsContent value="general" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>General Settings</CardTitle>
                <CardDescription>
                  Configure appearance and behavior settings for the application
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="theme">Theme</Label>
                  <Select
                    value={form.watch("defaultTheme")}
                    onValueChange={(value: "light" | "dark" | "system") => form.setValue("defaultTheme", value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select theme" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="light">
                        <div className="flex items-center gap-2">
                          <Sun className="h-4 w-4" />
                          <span>Light</span>
                        </div>
                      </SelectItem>
                      <SelectItem value="dark">
                        <div className="flex items-center gap-2">
                          <Moon className="h-4 w-4" />
                          <span>Dark</span>
                        </div>
                      </SelectItem>
                      <SelectItem value="system">
                        <div className="flex items-center gap-2">
                          <span>System</span>
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="autosave">Auto-save changes</Label>
                    <p className="text-sm text-muted-foreground">
                      Automatically save schema changes as you make them
                    </p>
                  </div>
                  <Switch
                    id="autosave"
                    checked={form.watch("autoSave")}
                    onCheckedChange={(checked) => form.setValue("autoSave", checked)}
                  />
                </div>
                
                <Separator />
                
                <div className="space-y-2">
                  <h3 className="text-lg font-medium">Export/Import Settings</h3>
                  <p className="text-sm text-muted-foreground">
                    Export your settings to a file or import from a previously saved file
                  </p>
                  <div className="flex gap-2 mt-2">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => {
                        // Export settings
                        const settingsJson = JSON.stringify({
                          theme: form.watch("defaultTheme"),
                          autoSave: form.watch("autoSave"),
                          inferRelationships: form.watch("inferRelationships"),
                          detectPrimaryKeys: form.watch("detectPrimaryKeys"),
                          detectForeignKeys: form.watch("detectForeignKeys"),
                          namingConvention: form.watch("namingConvention"),
                        });
                        
                        const blob = new Blob([settingsJson], { type: 'application/json' });
                        const href = URL.createObjectURL(blob);
                        const link = document.createElement('a');
                        link.href = href;
                        link.download = "schemasage-settings.json";
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        URL.revokeObjectURL(href);
                      }}
                    >
                      Export Settings
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                    >
                      Import Settings
                      <input
                        type="file"
                        className="absolute inset-0 opacity-0 cursor-pointer"
                        accept=".json"
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) {
                            const reader = new FileReader();
                            reader.onload = (e) => {
                              try {
                                const settings = JSON.parse(e.target?.result as string);
                                form.setValue("defaultTheme", settings.theme || "light");
                                form.setValue("autoSave", Boolean(settings.autoSave));
                                form.setValue("inferRelationships", Boolean(settings.inferRelationships));
                                form.setValue("detectPrimaryKeys", Boolean(settings.detectPrimaryKeys));
                                form.setValue("detectForeignKeys", Boolean(settings.detectForeignKeys));
                                form.setValue("namingConvention", settings.namingConvention || "snake_case");
                                toast.success("Settings imported successfully");
                              } catch {
                                toast.error("Failed to import settings: Invalid file format");
                              }
                            };
                            reader.readAsText(file);
                          }
                        }}
                      />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="api" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>API Key Management</CardTitle>
                <CardDescription>
                  Manage your AI provider API keys for schema detection and code generation
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="apiKey">
                    Gemini API Key
                  </Label>
                  <div className="flex gap-2">
                    <Input
                      id="apiKey"
                      type="password"
                      placeholder="Enter your Gemini API key"
                      {...form.register("apiKey")}
                      className="flex-1"
                    />
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Your API key is stored securely in your browser and never sent to our servers
                  </p>
                </div>
                
                <Separator />
                
                <div className="space-y-2">
                  <h3 className="text-lg font-medium">AI Provider Settings</h3>
                  <p className="text-sm text-muted-foreground">
                    Configure AI model settings for schema detection and code generation
                  </p>
                  
                  <div className="mt-4 space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="model">Preferred Model</Label>
                      <Select defaultValue="gemini-pro">
                        <SelectTrigger>
                          <SelectValue placeholder="Select model" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="gemini-pro">Gemini Pro</SelectItem>
                          <SelectItem value="gemini-ultra">Gemini Ultra</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label htmlFor="streaming">Stream AI responses</Label>
                        <p className="text-sm text-muted-foreground">
                          Show AI responses as they&apos;re generated
                        </p>
                      </div>
                      <Switch id="streaming" defaultChecked />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="schema" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Schema Detection Settings</CardTitle>
                <CardDescription>
                  Configure how schemas are detected and relationships are inferred
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="inferRelationships">Infer Relationships</Label>
                    <p className="text-sm text-muted-foreground">
                      Automatically detect relationships between tables
                    </p>
                  </div>
                  <Switch
                    id="inferRelationships"
                    checked={form.watch("inferRelationships")}
                    onCheckedChange={(checked) => form.setValue("inferRelationships", checked)}
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="detectPrimaryKeys">Detect Primary Keys</Label>
                    <p className="text-sm text-muted-foreground">
                      Automatically identify primary keys in tables
                    </p>
                  </div>
                  <Switch
                    id="detectPrimaryKeys"
                    checked={form.watch("detectPrimaryKeys")}
                    onCheckedChange={(checked) => form.setValue("detectPrimaryKeys", checked)}
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="detectForeignKeys">Detect Foreign Keys</Label>
                    <p className="text-sm text-muted-foreground">
                      Automatically identify foreign keys in tables
                    </p>
                  </div>
                  <Switch
                    id="detectForeignKeys"
                    checked={form.watch("detectForeignKeys")}
                    onCheckedChange={(checked) => form.setValue("detectForeignKeys", checked)}
                  />
                </div>
                
                <Separator />
                
                <div className="space-y-2">
                  <Label htmlFor="namingConvention">Naming Convention</Label>
                  <Select
                    value={form.watch("namingConvention")}
                    onValueChange={(value: "camelCase" | "snake_case" | "PascalCase") => 
                      form.setValue("namingConvention", value)
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select naming convention" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="camelCase">camelCase</SelectItem>
                      <SelectItem value="snake_case">snake_case</SelectItem>
                      <SelectItem value="PascalCase">PascalCase</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-sm text-muted-foreground">
                    Default naming convention for generated code
                  </p>
                </div>
                
                <Separator />
                
                <div className="space-y-2">
                  <h3 className="text-lg font-medium">Code Generation Defaults</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Default settings for code generation
                  </p>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="defaultLanguage">Default Language</Label>
                      <Select defaultValue="typescript">
                        <SelectTrigger>
                          <SelectValue placeholder="Select default language" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="typescript">TypeScript</SelectItem>
                          <SelectItem value="python">Python</SelectItem>
                          <SelectItem value="sql">SQL</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="defaultFormat">Default Format</Label>
                      <Select defaultValue="typescript-zod">
                        <SelectTrigger>
                          <SelectValue placeholder="Select default format" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="typescript-zod">TypeScript + Zod</SelectItem>
                          <SelectItem value="typescript-types">TypeScript Types</SelectItem>
                          <SelectItem value="python-dataclass">Python Dataclasses</SelectItem>
                          <SelectItem value="sql-table">SQL Tables</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <div className="mt-6 flex justify-end">
            <Button type="submit" className="flex gap-2 items-center">
              <Save className="h-4 w-4" />
              Save Settings
            </Button>
          </div>
        </form>
      </Tabs>
    </div>
  );
}