"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Loader2, Database, AlertCircle, CheckCircle } from "lucide-react";
import { toast } from "sonner";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useStore } from "@/lib/store";
import { databaseApi } from "@/lib/api";

// Form schema for database connection
const databaseSchema = z.object({
  type: z.enum(["postgresql", "mysql", "sqlite", "mongodb"]),
  host: z.string().optional(),
  port: z.coerce.number().int().positive().optional(),
  database: z.string().min(1, "Database name is required"),
  username: z.string().optional(),
  password: z.string().optional(),
  connectionString: z.string().optional(),
  ssl: z.boolean().optional(),
});

// For type safety with the form
type DatabaseFormValues = z.infer<typeof databaseSchema>;

// Connection status
type ConnectionStatus = {
  status: 'idle' | 'testing' | 'connected' | 'importing' | 'completed' | 'error';
  message?: string;
  progress?: number;
};

export function DatabaseConnection() {
  const router = useRouter();
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
    status: 'idle',
    progress: 0,
  });
  const [error, setError] = useState<string | null>(null);
  const { setCurrentSchema } = useStore();
  const [activeTab, setActiveTab] = useState<string>('standard');
  
  // Initialize the form
  const form = useForm<DatabaseFormValues>({
    resolver: zodResolver(databaseSchema),
    defaultValues: {
      type: "postgresql",
      host: "localhost",
      port: 5432,
      database: "",
      username: "",
      password: "",
      connectionString: "",
      ssl: false,
    },
  });
  
  // Form submission handler
  const onSubmit = async (values: DatabaseFormValues) => {
    // Reset status
    setError(null);
    setConnectionStatus({ status: 'testing', progress: 10, message: 'Testing connection...' });
    
    try {
      // Test connection first
      const testResult = await databaseApi.testConnection(values);
      
      if (!testResult.success) {
        throw new Error(testResult.error?.message || "Connection test failed");
      }
      
      setConnectionStatus({ status: 'connected', progress: 30, message: 'Connection successful! Importing schema...' });
      toast.success("Database connection successful!");
      
      // Short delay to show progress
      await new Promise(resolve => setTimeout(resolve, 500));
      setConnectionStatus({ status: 'importing', progress: 50, message: 'Importing schema structure...' });
      
      // Import schema from database
      const importResult = await databaseApi.importFromDatabase(values);
      
      if (!importResult.success || !importResult.data) {
        throw new Error(importResult.error?.message || "Failed to import schema");
      }
      
      // Update progress
      setConnectionStatus({ status: 'importing', progress: 80, message: 'Processing relationships...' });
      await new Promise(resolve => setTimeout(resolve, 300));
      
      // Store schema in global state
      setCurrentSchema(importResult.data);
      
      // Complete
      setConnectionStatus({ status: 'completed', progress: 100, message: 'Schema imported successfully!' });
      toast.success("Schema imported successfully!");
      
      // Short delay to show completion message
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Navigate to schema page
      router.push("/schema");
      
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to connect to database";
      setError(message);
      setConnectionStatus({ status: 'error', message });
      toast.error(`Error: ${message}`);
    }
  };

  // Handle database type change
  const handleDatabaseTypeChange = (type: string) => {
    const defaultPorts: Record<string, number> = {
      postgresql: 5432,
      mysql: 3306,
      mongodb: 27017,
      sqlite: 0,
    };

    form.setValue('port', defaultPorts[type as keyof typeof defaultPorts]);
  };
  
  // Handle tab change
  const handleTabChange = (value: string) => {
    setActiveTab(value);
    // Clear connection string when switching to standard tab
    if (value === 'standard') {
      form.setValue('connectionString', '');
    }
  };

  // Check if form is in loading state
  const isLoading = connectionStatus.status === 'testing' || 
                    connectionStatus.status === 'importing' || 
                    connectionStatus.status === 'connected';

  return (
    <Card className="p-6">
      <div className="space-y-6">
        <div className="space-y-2">
          <h2 className="text-lg font-semibold">Connect to Database</h2>
          <p className="text-sm text-muted-foreground">
            Import a schema directly from your database.
          </p>
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Connection Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        {connectionStatus.status === 'completed' && (
          <Alert variant="default" className="bg-green-50 text-green-800 dark:bg-green-950 dark:text-green-300">
            <CheckCircle className="h-4 w-4" />
            <AlertTitle>Success</AlertTitle>
            <AlertDescription>{connectionStatus.message}</AlertDescription>
          </Alert>
        )}
        
        {isLoading && (
          <div className="space-y-2">
            <div className="flex items-center justify-between mb-1">
              <p className="text-sm font-medium">{connectionStatus.message}</p>
              <span className="text-sm">{connectionStatus.progress}%</span>
            </div>
            <div className="w-full h-2 bg-gray-200 rounded">
              <div
                className="h-2 bg-blue-500 rounded transition-all duration-300"
                style={{ width: `${connectionStatus.progress}%` }}
              />
            </div>
          </div>
        )}

        <Tabs value={activeTab} onValueChange={handleTabChange}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="standard">Standard</TabsTrigger>
            <TabsTrigger value="connectionString">Connection String</TabsTrigger>
          </TabsList>

          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 mt-4">
              <TabsContent value="standard">
                <FormField
                  control={form.control}
                  name="type"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Database Type</FormLabel>
                      <Select
                        onValueChange={(value) => {
                          field.onChange(value);
                          handleDatabaseTypeChange(value);
                        }}
                        defaultValue={field.value}
                        disabled={isLoading}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select database type" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="postgresql">PostgreSQL</SelectItem>
                          <SelectItem value="mysql">MySQL</SelectItem>
                          <SelectItem value="sqlite">SQLite</SelectItem>
                          <SelectItem value="mongodb">MongoDB</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {form.watch("type") !== "sqlite" && (
                  <>
                    <div className="grid grid-cols-2 gap-4">
                      <FormField
                        control={form.control}
                        name="host"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Host</FormLabel>
                            <FormControl>
                              <Input placeholder="localhost" {...field} disabled={isLoading} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="port"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Port</FormLabel>
                            <FormControl>
                              <Input
                                type="number"
                                {...field}
                                disabled={isLoading}
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <FormField
                        control={form.control}
                        name="username"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Username</FormLabel>
                            <FormControl>
                              <Input {...field} disabled={isLoading} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="password"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Password</FormLabel>
                            <FormControl>
                              <Input
                                type="password"
                                {...field}
                                disabled={isLoading}
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>
                    
                    <FormField
                      control={form.control}
                      name="ssl"
                      render={({ field }) => (
                        <FormItem className="flex flex-row items-center space-x-3 space-y-0 rounded-md border p-3">
                          <FormControl>
                            <input
                              type="checkbox"
                              className="h-4 w-4"
                              checked={field.value}
                              onChange={(e) => field.onChange(e.target.checked)}
                              disabled={isLoading}
                            />
                          </FormControl>
                          <div className="space-y-1 leading-none">
                            <FormLabel>Use SSL connection</FormLabel>
                            <FormDescription>
                              Enable SSL/TLS for secure database connection
                            </FormDescription>
                          </div>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </>
                )}

                <FormField
                  control={form.control}
                  name="database"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        {form.watch("type") === "sqlite" ? "File Path" : "Database Name"}
                      </FormLabel>
                      <FormControl>
                        <Input {...field} disabled={isLoading} />
                      </FormControl>
                      <FormDescription>
                        {form.watch("type") === "sqlite"
                          ? "Path to SQLite database file"
                          : "Name of the database to connect to"}
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </TabsContent>

              <TabsContent value="connectionString">
                <FormField
                  control={form.control}
                  name="connectionString"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Connection String</FormLabel>
                      <FormControl>
                        <Input {...field} disabled={isLoading} />
                      </FormControl>
                      <FormDescription>
                        {form.watch("type") === "postgresql"
                          ? "Example: postgresql://user:password@localhost:5432/database"
                          : form.watch("type") === "mysql"
                          ? "Example: mysql://user:password@localhost:3306/database"
                          : form.watch("type") === "mongodb"
                          ? "Example: mongodb://user:password@localhost:27017/database"
                          : "Example: sqlite:///path/to/database.db"}
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="type"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Database Type</FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        defaultValue={field.value}
                        disabled={isLoading}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select database type" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="postgresql">PostgreSQL</SelectItem>
                          <SelectItem value="mysql">MySQL</SelectItem>
                          <SelectItem value="sqlite">SQLite</SelectItem>
                          <SelectItem value="mongodb">MongoDB</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </TabsContent>

              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {connectionStatus.message || "Processing..."}
                  </>
                ) : (
                  <>
                    <Database className="mr-2 h-4 w-4" />
                    Connect & Import Schema
                  </>
                )}
              </Button>
            </form>
          </Form>
        </Tabs>
      </div>
    </Card>
  );
}