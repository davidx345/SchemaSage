import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Project, SchemaResponse, DatabaseConfig, ChatMessage } from './types';

interface Notification {
  id: string;
  message: string;
  type?: "info" | "success" | "error";
}

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
    autoSave: boolean;
    detectRelations: boolean;
    inferTypes: boolean;
    generateNullableFields: boolean;
    generateIndexes: boolean;
    compactMode: boolean;
  };

  // Database Connections
  savedConnections: DatabaseConfig[];

  // Chat history
  chatHistory: ChatMessage[];

  // Notifications
  notifications: Notification[];

  // Actions
  setCurrentProject: (project: Project | null) => void;
  setCurrentSchema: (schema: SchemaResponse | null) => void;
  addRecentProject: (project: Project) => void;
  removeRecentProject: (projectId: string) => void;
  toggleDarkMode: () => void;
  toggleSidebar: () => void;
  setActiveTab: (tab: string) => void;
  updateSettings: (settings: Partial<StoreState['settings']>) => void;
  setSettings: (settings: StoreState['settings']) => void;
  addDatabaseConnection: (connection: DatabaseConfig) => void;
  removeDatabaseConnection: (connectionId: string) => void;
  setChatHistory: (messages: ChatMessage[]) => void;
  resetStore: () => void;
  addNotification: (notification: Notification) => void;
  removeNotification: (id: string) => void;
  // Granular project/user management stubs
  addUserToProject?: (projectId: string, userId: string) => void;
  removeUserFromProject?: (projectId: string, userId: string) => void;
  setProjectRole?: (projectId: string, userId: string, role: string) => void;
}

interface AuthState {
  token: string | null;
  user: { email: string; fullName?: string; is_admin?: boolean } | null;
  setToken: (token: string | null) => void;
  setUser: (user: { email: string; fullName?: string; is_admin?: boolean } | null) => void;
  logout: () => void;
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
        autoSave: true,
        detectRelations: true,
        inferTypes: true,
        generateNullableFields: true,
        generateIndexes: true,
        compactMode: false,
      },
      savedConnections: [],
      chatHistory: [],
      notifications: [],

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
      setSettings: (settings) => set(() => ({
        settings: settings,
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
        chatHistory: [],
      }),
      addNotification: (notification: Notification) => set((state) => ({ notifications: [...state.notifications, notification] })),
      removeNotification: (id: string) => set((state) => ({ notifications: state.notifications.filter(n => n.id !== id) })),
      
      // Granular project/user management stubs
      addUserToProject: () => {},
      removeUserFromProject: () => {},
      setProjectRole: () => {},
    }),
    {
      name: 'schema-sage-storage',
      partialize: (state: StoreState) => ({
        isDarkMode: state.isDarkMode,
        settings: state.settings,
        savedConnections: state.savedConnections,
        recentProjects: state.recentProjects,
      }),
    }
  )
);

export const useAuth = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setToken: (token) => set({ token }),
      setUser: (user) => set({ user }),
      logout: () => set({ token: null, user: null })
    }),
    {
      name: 'schema-sage-auth',
      partialize: (state) => ({ token: state.token, user: state.user })
    }
  )
);