import axios from 'axios';
import { API_BASE_URL } from "./config";
import type { 
  DetectedSchema, 
  SchemaSettings,
  DatabaseConfig, 
  ApiResponse,
  SchemaResponse, 
  ChatMessage,
  Project,
  CodeGenOptions,
  CodeGenFormat
} from './types';

// API base URL with standard path
const API_BASE = `${API_BASE_URL}/api`;

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 20000, // 20 second timeout
});

export interface ApiError {
  message: string;
  details?: {
    error?: string;
    details?: string[];
    suggestion?: string;
    [key: string]: unknown;
  };
}

// Common fetch wrapper with error handling
// This is a utility function exported for potential future use
export async function fetchWithErrorHandling(url: string, options?: RequestInit) {
  try {
    const response = await fetch(url, options);
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error?.message || `API error: ${response.status}`);
    }
    
    return data;
  } catch (error) {
    console.error("API request failed:", error);
    throw error;
  }
}

export const schemaApi = {
  // Schema Detection
  detectSchema: async (data: string, options: Partial<SchemaSettings> = {}): Promise<ApiResponse<DetectedSchema>> => {
    const response = await fetch(`${API_BASE}/schema/detect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data, settings: options })
    });
    const result = await response.json();
    if (!response.ok) {
      return { success: false, error: { message: result.error?.message || 'Failed to detect schema' } };
    }
    return { success: true, data: result.schema };
  },

  // Project Management
  getProjects: async (): Promise<ApiResponse<Project[]>> => {
    const response = await api.get('/database/projects');
    return response.data;
  },

  createProject: async (name: string): Promise<ApiResponse<Project>> => {
    const response = await api.post('/database/projects', { name });
    return response.data;
  },

  // Schema Management
  getSchema: async (projectId: string): Promise<ApiResponse<SchemaResponse>> => {
    const response = await api.get(`/schema/${projectId}`);
    return response.data;
  },

  updateSchema: async (projectId: string, schema: SchemaResponse): Promise<ApiResponse<SchemaResponse>> => {
    const response = await api.put(`/schema/${projectId}`, schema);
    return response.data;
  },

  // Code Generation
  generateCode: async (
    schema: SchemaResponse, 
    format: CodeGenFormat,
    options: CodeGenOptions
  ): Promise<{success: boolean; data?: string; error?: {message: string}}> => {
    try {
      const response = await fetch(`${API_BASE}/schema/generate-code`, {
        method: "POST",
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          schema_data: schema,
          format,
          options
        })
      });
      const result = await response.json();
      if (!response.ok) {
        return {
          success: false,
          error: { message: result.error?.message || "Failed to generate code" }
        };
      }
      return {
        success: true,
        data: result.code
      };
    } catch (error) {
      return {
        success: false,
        error: { message: error instanceof Error ? error.message : "Unknown error" }
      };
    }
  },

  // AI Chat
  chat: async (
    messages: ChatMessage[], 
    schemaContext?: Record<string, unknown>
  ): Promise<{success: boolean; data?: ChatMessage; error?: {message: string}}> => {
    try {
      const chatRequest = {
        messages: messages.map(msg => ({
          role: msg.role,
          content: msg.content
        })),
        schema_data: schemaContext
      };
      const response = await fetch(`${API_BASE}/schema/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(chatRequest)
      });
      const responseText = await response.text();
      let result;
      try {
        result = JSON.parse(responseText);
      } catch {
        return {
          success: false,
          error: { message: "Invalid response format from server" }
        };
      }
      if (!response.ok) {
        return {
          success: false,
          error: { message: result.message || result.error?.message || "Chat request failed" }
        };
      }
      return {
        success: true,
        data: {
          role: "assistant",
          content: result.response,
          timestamp: new Date().toISOString(),
          suggestions: result.suggestions || []
        }
      };
    } catch (error) {
      return {
        success: false,
        error: { message: error instanceof Error ? error.message : "Unknown error" }
      };
    }
  },

  // Detect schema from file
  detectSchemaFromFile: async (file: File): Promise<{success: boolean; data?: SchemaResponse; error?: {message: string}}> => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await fetch(`${API_BASE}/schema/detect-from-file`, {
        method: "POST",
        body: formData
      });
      const result = await response.json();
      if (!response.ok) {
        return {
          success: false,
          error: { message: result.error?.message || "Failed to detect schema from file" }
        };
      }
      return {
        success: true,
        data: result.schema
      };
    } catch (error) {
      return {
        success: false,
        error: { message: error instanceof Error ? error.message : "Unknown error" }
      };
    }
  }
};

export const handleApiError = (error: unknown): ApiError => {
  if (axios.isAxiosError(error)) {
    if (error.response) {
      return {
        message: error.response.data?.message || 'An error occurred',
        details: error.response.data?.details,
      };
    } else if (error.request) {
      return {
        message: 'No response from server. Is the backend running?',
      };
    } 
  }
  return {
    message: error instanceof Error ? error.message : 'An unexpected error occurred',
  };
};

// Database API functions
export const databaseApi = {
  // Test database connection
  testConnection: async (config: DatabaseConfig): Promise<{success: boolean; message?: string; error?: {message: string}}> => {
    try {
      const response = await fetch(`${API_BASE}/database/test-connection`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config)
      });
      
      const result = await response.json();
      
      if (!response.ok) {
        return {
          success: false,
          error: { message: result.error?.message || "Connection test failed" }
        };
      }
      
      return {
        success: true,
        message: result.message || "Connection successful"
      };
    } catch (error) {
      return {
        success: false,
        error: { message: error instanceof Error ? error.message : "Unknown error" }
      };
    }
  },

  // Import schema from database
  importFromDatabase: async (config: DatabaseConfig): Promise<{success: boolean; data?: SchemaResponse; error?: {message: string}}> => {
    try {
      const response = await fetch(`${API_BASE}/database/import-schema`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config)
      });
      
      const result = await response.json();
      
      if (!response.ok) {
        return {
          success: false,
          error: { message: result.error?.message || "Failed to import schema" }
        };
      }
      
      return {
        success: true,
        data: result.schema
      };
    } catch (error) {
      return {
        success: false,
        error: { message: error instanceof Error ? error.message : "Unknown error" }
      };
    }
  }
};

// MongoDB Project API
export const projectApi = {
  // Get all projects
  getProjects: async (): Promise<ApiResponse<Project[]>> => {
    try {
      const response = await fetch(`${API_BASE}/database/projects`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to fetch projects');
      }

      const data = await response.json();
      return {
        success: true,
        data: data.projects
      };
    } catch (error) {
      console.error('Get projects API error:', error);
      return {
        success: false,
        error: {
          message: error instanceof Error ? error.message : 'Unknown error fetching projects'
        }
      };
    }
  },
  
  // Create new project
  createProject: async (name: string): Promise<ApiResponse<Project>> => {
    try {
      const response = await fetch(`${API_BASE}/database/projects`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to create project');
      }

      const data = await response.json();
      return {
        success: true,
        data: data
      };
    } catch (error) {
      console.error('Create project API error:', error);
      return {
        success: false,
        error: {
          message: error instanceof Error ? error.message : 'Unknown error creating project'
        }
      };
    }
  }
};

// Authentication API
export const authApi = {
  signup: async (email: string, password: string, fullName?: string) => {
    const response = await fetch(`${API_BASE}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, full_name: fullName })
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || data.message || 'Signup failed');
    }
    return data;
  },
  login: async (email: string, password: string) => {
    const params = new URLSearchParams();
    params.append('username', email);
    params.append('password', password);
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: params
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || data.message || 'Login failed');
    }
    return data;
  },
  getMe: async (token: string) => {
    const response = await fetch(`${API_BASE}/auth/me`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || data.message || 'Failed to fetch user');
    }
    return data;
  }
};

// Export specific functions for direct use
export const detectSchemaFromFile = schemaApi.detectSchemaFromFile;