// Environment variables configuration

// Default to localhost in development, use NEXT_PUBLIC env var in production
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// Feature flags
export const FEATURES = {
  enableChat: true,
  enableCodeGeneration: true,
  enableDatabaseConnections: true
};

// Default settings
export const DEFAULT_SETTINGS = {
  theme: 'system',
  language: 'typescript',
  format: 'typescript-types'
};