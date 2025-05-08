"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FileUploader } from "@/components/file-uploader";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle, AlertTriangle, Check, Database, FileJson, Loader2 } from "lucide-react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useStore } from "@/lib/store";
import { toast } from "sonner";
import { databaseApi } from "@/lib/api";
import type { DatabaseConfig, SchemaResponse, ApiResponse } from "@/lib/types";

export default function UploadPage() {
  // File upload state
  const router = useRouter();
  const { setCurrentSchema } = useStore();
  const [activeTab, setActiveTab] = useState<string>("file");
  const [isConnecting, setIsConnecting] = useState<boolean>(false);
  const [dbConfig, setDbConfig] = useState<DatabaseConfig>({
    host: "localhost",
    port: 5432,
    username: "postgres",
    password: "",
    database: "",
    type: "postgresql"
  });
  const [connectionStatus, setConnectionStatus] = useState<"idle" | "testing" | "success" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [importedSchema, setImportedSchema] = useState<SchemaResponse | null>(null);

  // Test database connection
  const testDbConnection = async () => {
    setConnectionStatus("testing");

    try {
      const response = await databaseApi.testConnection(dbConfig);

      if (response.success) {
        setConnectionStatus("success");
        toast.success("Database connection successful!");
      } else {
        setConnectionStatus("error");
        setErrorMessage(response.error?.message || "Failed to connect to database");
        toast.error(`Connection failed: ${response.error?.message}`);
      }
    } catch (error) {
      setConnectionStatus("error");
      setErrorMessage(error instanceof Error ? error.message : "An unknown error occurred");
      toast.error(`Error: ${error instanceof Error ? error.message : "Unknown error"}`);
    }
  };

  // Import schema from database
  const importFromDatabase = async () => {
    // Test connection first if not already tested successfully
    if (connectionStatus !== "success") {
      await testDbConnection();

      // If connection test failed, don't proceed with import
      if (connectionStatus === "error" || connectionStatus === "testing") {
        return;
      }
    }

    setIsConnecting(true);
    setErrorMessage("");
    setImportedSchema(null);
    try {
      const response: ApiResponse<SchemaResponse> = await databaseApi.importFromDatabase(dbConfig);
      if (response.success && response.data) {
        setCurrentSchema(response.data);
        setImportedSchema(response.data);
        toast.success("Schema imported successfully!");
        setTimeout(() => router.push("/schema"), 1200);
      } else {
        toast.error(`Failed to import schema: ${response.error?.message}`);
        setErrorMessage(response.error?.message || "Unknown error");
      }
    } catch (error) {
      console.error("Schema import error:", error);
      toast.error(`Error: ${error instanceof Error ? error.message : "Unknown error"}`);
      setErrorMessage(error instanceof Error ? error.message : "An unknown error occurred");
    } finally {
      setIsConnecting(false);
    }
  };

  // Handle form input changes
  const handleConfigChange = (key: keyof DatabaseConfig, value: string | number) => {
    setDbConfig((prev) => ({ ...prev, [key]: value }));

    // Reset connection status when configuration changes
    if (connectionStatus !== "idle") {
      setConnectionStatus("idle");
    }
  };

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-6">Import Schema</h1>

      <Tabs defaultValue={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2 mb-8">
          <TabsTrigger value="file" className="flex items-center gap-2">
            <FileJson className="h-4 w-4" />
            <span>From File</span>
          </TabsTrigger>
          <TabsTrigger value="database" className="flex items-center gap-2">
            <Database className="h-4 w-4" />
            <span>From Database</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="file" className="mt-0">
          <Card>
            <CardHeader>
              <CardTitle>Upload SQL or JSON Schema File</CardTitle>
              <CardDescription>
                Upload a SQL dump file, JSON Schema, or other supported format to detect your database schema.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <FileUploader
                onDataReady={() => {
                  // We'll handle the schema detection in handleFileUpload
                }}
                onSchemaDetected={() => {
                  router.push("/schema");
                }}
                onError={(error: Error) => {
                  setErrorMessage(error.message);
                }}
                accept={{
                  'application/json': ['.json'],
                  'application/sql': ['.sql'],
                  'application/yaml': ['.yml', '.yaml']
                }}
              />

              {errorMessage && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Error</AlertTitle>
                  <AlertDescription>{errorMessage}</AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="database" className="mt-0">
          <Card>
            <CardHeader>
              <CardTitle>Connect to Database</CardTitle>
              <CardDescription>
                Connect directly to your database to import the schema.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="type">Database Type</Label>
                  <Select
                    value={dbConfig.type}
                    onValueChange={(value) => handleConfigChange("type", value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select database type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="postgresql">PostgreSQL</SelectItem>
                      <SelectItem value="mysql">MySQL</SelectItem>
                      <SelectItem value="sqlite">SQLite</SelectItem>
                      <SelectItem value="mongodb">MongoDB</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="host">Host</Label>
                  <Input
                    id="host"
                    value={dbConfig.host}
                    onChange={(e) => handleConfigChange("host", e.target.value)}
                    placeholder="localhost"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="port">Port</Label>
                  <Input
                    id="port"
                    type="number"
                    value={(dbConfig.port ?? "").toString()}
                    onChange={(e) => handleConfigChange("port", parseInt(e.target.value))}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="database">Database Name</Label>
                  <Input
                    id="database"
                    value={dbConfig.database}
                    onChange={(e) => handleConfigChange("database", e.target.value)}
                    placeholder="my_database"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="username">Username</Label>
                  <Input
                    id="username"
                    value={dbConfig.username}
                    onChange={(e) => handleConfigChange("username", e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    value={dbConfig.password}
                    onChange={(e) => handleConfigChange("password", e.target.value)}
                  />
                </div>
              </div>

              {connectionStatus === "success" && (
                <Alert className="bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-900">
                  <Check className="h-4 w-4 text-green-600 dark:text-green-400" />
                  <AlertTitle className="text-green-600 dark:text-green-400">Connected</AlertTitle>
                  <AlertDescription className="text-green-600 dark:text-green-400">
                    Successfully connected to the database.
                  </AlertDescription>
                </Alert>
              )}

              {connectionStatus === "error" && (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle>Connection Failed</AlertTitle>
                  <AlertDescription>{errorMessage}</AlertDescription>
                </Alert>
              )}

              <div className="flex gap-4">
                <Button
                  variant="outline"
                  onClick={testDbConnection}
                  disabled={connectionStatus === "testing" || isConnecting}
                  className="flex-1"
                >
                  {connectionStatus === "testing" ? (
                    <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Testing...</>
                  ) : "Test Connection"}
                </Button>
                <Button
                  onClick={importFromDatabase}
                  disabled={isConnecting}
                  className="flex-1"
                >
                  {isConnecting ? (
                    <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Importing...</>
                  ) : "Import Schema"}
                </Button>
              </div>
              {isConnecting && (
                <div className="flex items-center gap-2 mt-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" /> Importing schema from database...
                </div>
              )}
              {importedSchema && (
                <div className="mt-4 p-4 border rounded bg-muted">
                  <div className="font-semibold mb-2">Imported Tables:</div>
                  <ul className="list-disc ml-6">
                    {importedSchema.tables?.map((t) => (
                      <li key={t.name}>{t.name}</li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}