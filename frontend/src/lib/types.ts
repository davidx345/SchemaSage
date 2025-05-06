export interface ColumnStatistics {
  total_rows: number
  non_null_count: number
  null_count: number
  unique_count: number
  unique_percentage: number
  sample_values: Array<string | number | boolean>
}

export interface Column {
  name: string;
  data_type: string;
  nullable?: boolean;
  is_primary_key?: boolean;
  is_foreign_key?: boolean;
  references?: {
    table: string;
    column: string;
  };
}

export interface Table {
  name: string;
  columns: Column[];
}

export interface Index {
  name: string;
  columns: string[];
  unique?: boolean;
}

export interface Relationship {
  source_table: string;
  source_column: string;
  target_table: string;
  target_column: string;
  type: RelationType;
}

export type RelationType = 'one-to-one' | 'one-to-many' | 'many-to-one' | 'many-to-many';

export interface SchemaResponse {
  tables: Table[];
  relationships?: Relationship[];
}

export interface Project {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  schema?: SchemaResponse;
}

export interface DetectedSchema {
  schema: SchemaResponse;
  confidence: number;
  warnings?: string[];
}

export interface SchemaSettings {
  inferRelationships: boolean;
  detectPrimaryKeys: boolean;
  detectForeignKeys: boolean;
  namingConvention: 'camelCase' | 'snake_case' | 'PascalCase';
}

export interface DatabaseConfig {
  type: 'mysql' | 'postgresql' | 'sqlite' | 'mongodb';
  host?: string;
  port?: number;
  database: string;
  username?: string;
  password?: string;
  connectionString?: string;
}

export interface CodeGenOptions {
  language: 'typescript' | 'python' | 'sql';
  format: CodeGenFormat;
  includeComments: boolean;
  includeValidation: boolean;
}

export type CodeGenFormat = 
  | 'typescript-types'
  | 'typescript-zod'
  | 'typescript-class'
  | 'python-dataclass'
  | 'python-pydantic'
  | 'sql-table'
  | 'sql-migration';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  suggestions?: string[];
}

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: {
    message: string;
    details?: unknown;
  };
}

export interface SchemaDetectResponse {
  schema: SchemaResponse;
  metadata?: Record<string, unknown>;
}

// UI Store Types
export interface StoreState {
  currentSchema: SchemaResponse | null;
  settings: {
    darkMode: boolean;
    compactMode: boolean;
    autoSave: boolean;
    detectRelations: boolean;
    inferTypes: boolean;
    generateNullableFields: boolean;
    generateIndexes: boolean;
  };
  chatHistory: ChatMessage[];
  recentProjects: Project[];
  currentProject: Project | null;
  setChatHistory: (messages: ChatMessage[]) => void;
}