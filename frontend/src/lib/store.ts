import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Project, SchemaResponse, DatabaseConfig, ChatMessage } from './types';

interface StoreState {
  // Project State
  currentProject: Project | null;
  currentSchema: SchemaResponse | null;
  recentProjects: Project[];
  
  // UI State
  isDarkMode: boolean;
  sidebarCollapsed: boolean;
  activeTab: string;

  // Settings
  settings: {
    detectRelations: boolean;
    inferTypes: boolean;
    generateNullableFields: boolean;
    generateIndexes: boolean;
  };

  // Database Connections
  savedConnections: DatabaseConfig[];

  // Chat history
  chatHistory: ChatMessage[];

  // Actions
  setCurrentProject: (project: Project | null) => void;
  setCurrentSchema: (schema: SchemaResponse | null) => void;
  addRecentProject: (project: Project) => void;
  removeRecentProject: (projectId: string) => void;
  toggleDarkMode: () => void;
  toggleSidebar: () => void;
  setActiveTab: (tab: string) => void;
  updateSettings: (settings: Partial<StoreState['settings']>) => void;
  addDatabaseConnection: (connection: DatabaseConfig) => void;
  removeDatabaseConnection: (connectionId: string) => void;
  setChatHistory: (messages: ChatMessage[]) => void;
  resetStore: () => void;
}

export const useStore = create<StoreState>()(
  persist(
    (set) => ({
      // Initial State
      currentProject: null,
      currentSchema: null,
      recentProjects: [],
      isDarkMode: false,
      sidebarCollapsed: false,
      activeTab: 'schema',
      settings: {
        detectRelations: true,
        inferTypes: true,
        generateNullableFields: true,
        generateIndexes: true,
      },
      savedConnections: [],
      chatHistory: [],

      // Actions
      setCurrentProject: (project) => set({ currentProject: project }),
      
      setCurrentSchema: (schema) => set({ currentSchema: schema }),
      
      addRecentProject: (project) => set((state) => ({
        recentProjects: [
          project,
          ...state.recentProjects.filter((p) => p.id !== project.id)
        ].slice(0, 5),
      })),
      
      removeRecentProject: (projectId) => set((state) => ({
        recentProjects: state.recentProjects.filter((p) => p.id !== projectId),
      })),
      
      toggleDarkMode: () => set((state) => ({
        isDarkMode: !state.isDarkMode,
      })),
      
      toggleSidebar: () => set((state) => ({
        sidebarCollapsed: !state.sidebarCollapsed,
      })),
      
      setActiveTab: (tab) => set({ activeTab: tab }),
      
      updateSettings: (newSettings) => set((state) => ({
        settings: { ...state.settings, ...newSettings },
      })),
      
      addDatabaseConnection: (connection) => set((state) => ({
        savedConnections: [...state.savedConnections, connection],
      })),
      
      removeDatabaseConnection: (connectionId) => set((state) => ({
        savedConnections: state.savedConnections.filter(
          (conn) => conn.database !== connectionId
        ),
      })),
      
      setChatHistory: (messages) => set({ chatHistory: messages }),
      
      resetStore: () => set({
        currentSchema: null,
        currentProject: null,
        chatHistory: []
      }),
    }),
    {
      name: 'schema-sage-storage',
      partialize: (state) => ({
        isDarkMode: state.isDarkMode,
        settings: state.settings,
        savedConnections: state.savedConnections,
        recentProjects: state.recentProjects,
      }),
    }
  )
);