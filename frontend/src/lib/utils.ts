import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { Column, Table, SchemaResponse } from "./types";

// Tailwind class merging utility
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Schema validation and analysis utilities
export function validateSchema(schema: SchemaResponse): string[] {
  const errors: string[] = [];

  if (!schema.tables || !Array.isArray(schema.tables)) {
    errors.push("Schema must contain a tables array");
    return errors;
  }

  // Check for duplicate table names
  const tableNames = new Set<string>();
  schema.tables.forEach((table) => {
    if (tableNames.has(table.name)) {
      errors.push(`Duplicate table name: ${table.name}`);
    }
    tableNames.add(table.name);
  });

  // Validate relationships
  schema.relationships?.forEach((rel) => {
    const sourceTable = schema.tables.find(t => t.name === rel.source_table);
    const targetTable = schema.tables.find(t => t.name === rel.target_table);

    if (!sourceTable) {
      errors.push(`Source table not found: ${rel.source_table}`);
    }
    if (!targetTable) {
      errors.push(`Target table not found: ${rel.target_table}`);
    }

    if (sourceTable && !sourceTable.columns.find(c => c.name === rel.source_column)) {
      errors.push(`Source column ${rel.source_column} not found in table ${rel.source_table}`);
    }
    if (targetTable && !targetTable.columns.find(c => c.name === rel.target_column)) {
      errors.push(`Target column ${rel.target_column} not found in table ${rel.target_table}`);
    }
  });

  return errors;
}

// Data type inference and normalization
export function normalizeDataType(type: string): string {
  type = type.toLowerCase();
  
  // Map common variations to standard types
  const typeMap: Record<string, string> = {
    'int': 'integer',
    'number': 'integer',
    'float': 'decimal',
    'double': 'decimal',
    'str': 'string',
    'text': 'string',
    'char': 'string',
    'varchar': 'string',
    'bool': 'boolean',
    'datetime': 'timestamp',
    'date': 'date',
    'time': 'time',
  };

  return typeMap[type] || type;
}

/**
 * Format a file size in bytes to a human readable string
 */
export function formatFileSize(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let size = bytes;
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }

  return `${Math.round(size * 100) / 100} ${units[unitIndex]}`;
}

// Format relative time for display
export function formatRelativeTime(date: string | Date): string {
  const now = new Date();
  const past = new Date(date);
  const diffInSeconds = Math.floor((now.getTime() - past.getTime()) / 1000);

  const intervals = {
    year: 31536000,
    month: 2592000,
    week: 604800,
    day: 86400,
    hour: 3600,
    minute: 60,
  };

  for (const [unit, seconds] of Object.entries(intervals)) {
    const interval = Math.floor(diffInSeconds / seconds);
    if (interval >= 1) {
      return `${interval} ${unit}${interval === 1 ? '' : 's'} ago`;
    }
  }

  return 'just now';
}

// Generate a slug from a string
export function generateSlug(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w ]+/g, '')
    .replace(/ +/g, '-');
}

// Extract table relationships from foreign keys
export function inferRelationships(tables: Table[]) {
  const relationships = [];

  for (const table of tables) {
    for (const column of table.columns) {
      if (column.references) {
        relationships.push({
          source_table: table.name,
          source_column: column.name,
          target_table: column.references.table,
          target_column: column.references.column,
          type: "many-to-one", // Default to many-to-one, can be refined later
        });
      }
    }
  }

  return relationships;
}

// Generate suggested indexes based on column usage
export function suggestIndexes(table: Table) {
  const suggestions = [];

  // Primary key should be indexed
  const pkColumn = table.columns.find(c => c.is_primary_key);
  if (pkColumn) {
    suggestions.push({
      name: `${table.name}_pk`,
      columns: [pkColumn.name],
      unique: true,
    });
  }

  // Foreign keys should be indexed
  table.columns
    .filter(c => c.is_foreign_key)
    .forEach(column => {
      suggestions.push({
        name: `${table.name}_${column.name}_fk`,
        columns: [column.name],
        unique: false,
      });
    });

  return suggestions;
}

// Analyze column statistics
export function analyzeColumn(column: Column, data: unknown[]) {
  const stats = {
    total_rows: data.length,
    non_null_count: 0,
    null_count: 0,
    unique_count: 0,
    unique_percentage: 0,
    sample_values: [] as unknown[],
  };

  const uniqueValues = new Set();

  data.forEach(value => {
    if (value === null || value === undefined) {
      stats.null_count++;
    } else {
      stats.non_null_count++;
      uniqueValues.add(value);
      if (stats.sample_values.length < 5 && !stats.sample_values.includes(value)) {
        stats.sample_values.push(value);
      }
    }
  });

  stats.unique_count = uniqueValues.size;
  stats.unique_percentage = (stats.unique_count / stats.total_rows) * 100;

  return stats;
}

// Deep clone an object
export function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj));
}

/**
 * Format API errors for consistent display
 */
export function formatApiError(error: unknown): string {
  if (typeof error === 'string') {
    return error;
  }
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === 'object' && error !== null) {
    // Handle API error objects
    const errorObj = error as Record<string, unknown>;
    if (
      typeof errorObj.error === 'object' &&
      errorObj.error !== null &&
      'message' in errorObj.error &&
      typeof (errorObj.error as Record<string, unknown>).message === 'string'
    ) {
      return (errorObj.error as { message: string }).message;
    }
    if ('message' in errorObj && typeof errorObj.message === 'string') {
      return errorObj.message;
    }
  }
  return 'An unknown error occurred';
}

/**
 * Truncate a string with ellipsis if it exceeds a certain length
 */
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength) + '...';
}

/**
 * Generate a random ID
 */
export function generateId(): string {
  return Math.random().toString(36).substring(2, 9);
}
