import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from "@/components/ui/tooltip";
import { ModeToggle } from "@/components/mode-toggle";
import { 
  Activity, 
  Plus, 
  Upload, 
  Database, 
  Code, 
  Sparkles, 
  TrendingUp, 
  Clock, 
  FolderOpen,
  Zap,
  Shield,
  Users,
  BarChart3,
  FileText,
  Settings,
  Bell,
  Search
} from "lucide-react";

interface DashboardStats {
  activeProjects: number;
  tablesProcessed: number;
  lastActivity: { timestamp: string; description: string };
  recentProjects: { id: string; name: string; updatedAt: string }[];
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newProjectDialog, setNewProjectDialog] = useState(false);
  const [newProject, setNewProject] = useState({ name: "", description: "" });
  const [creating, setCreating] = useState(false);
  const router = useRouter();
  useEffect(() => {
    async function fetchStats() {
      setLoading(true);
      try {
        // TEMPORARY DEVELOPMENT DATA - REMOVE IN PRODUCTION
        const isDevelopment = true; // Set to false in production
        
        if (isDevelopment) {
          // Mock data for development
          await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate loading
          const mockStats: DashboardStats = {
            activeProjects: 12,
            tablesProcessed: 247,
            lastActivity: {
              timestamp: new Date().toISOString(),
              description: "Generated schema for Orders table"
            },
            recentProjects: [
              { id: "1", name: "E-commerce Platform", updatedAt: new Date(Date.now() - 1000 * 60 * 30).toISOString() },
              { id: "2", name: "User Management System", updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString() },
              { id: "3", name: "Analytics Dashboard", updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString() },
              { id: "4", name: "Inventory Tracker", updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString() },
            ]
          };
          setStats(mockStats);
          setLoading(false);
          return;
        }

        // Original API logic (commented out for development)
        /*
        const res = await fetch("/api/dashboard/summary");
        if (!res.ok) throw new Error("Failed to load dashboard data");
        setStats(await res.json());
        */
      } catch {
        setError("Could not load dashboard data.");
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
  }, []);

  const handleUpload = () => router.push("/upload");
  const handleConnectDb = () => router.push("/upload?tab=database");
  const handleGenerateCode = () => router.push("/code");

  const handleCreateProject = async () => {
    if (!newProject.name.trim()) {
      toast.error("Project name is required");
      return;
    }
    setCreating(true);
    try {
      const res = await fetch("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newProject.name, description: newProject.description })
      });
      if (!res.ok) throw new Error("Failed to create project");
      const data = await res.json();
      toast.success("Project created!");
      setNewProjectDialog(false);
      setNewProject({ name: "", description: "" });
      router.push(`/schema?project=${data.id}`);
    } catch {
      toast.error("Failed to create project");
    } finally {
      setCreating(false);
    }
  };

  // Simulated activity feed (replace with real data if available)
  const activityFeed = [
    { id: 1, description: "Created project 'Sample Project'", timestamp: new Date().toLocaleString() },
    { id: 2, description: "Updated schema for 'Orders'", timestamp: new Date(Date.now() - 3600 * 1000).toLocaleString() },
    { id: 3, description: "Generated code for 'Users'", timestamp: new Date(Date.now() - 2 * 3600 * 1000).toLocaleString() },
  ];  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center text-white"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="w-16 h-16 mx-auto mb-4 border-4 border-blue-400 border-t-transparent rounded-full"
          />
          <p className="text-lg">Loading your dashboard...</p>
        </motion.div>
      </div>
    );
  }
    if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-center text-red-400 bg-red-500/10 p-8 rounded-2xl border border-red-500/20">
          <p className="text-lg">{error}</p>
        </div>
      </div>
    );
  }
  
  if (!stats) return null;  return (
    <TooltipProvider>      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-slate-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0">
        <div className="absolute top-0 -left-4 w-72 h-72 bg-blue-300 dark:bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 dark:opacity-30 animate-blob"></div>
        <div className="absolute top-0 -right-4 w-72 h-72 bg-teal-300 dark:bg-teal-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 dark:opacity-30 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-8 left-20 w-72 h-72 bg-slate-300 dark:bg-slate-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 dark:opacity-30 animate-blob animation-delay-4000"></div>
        <div className="absolute bottom-0 right-20 w-72 h-72 bg-sky-300 dark:bg-sky-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 dark:opacity-30 animate-blob animation-delay-6000"></div>
      </div>

      {/* Grid pattern overlay */}
      <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>

      <div className="relative z-10 p-8 space-y-8">
        {/* Header */}
        <motion.div
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.6 }}
          className="flex items-center justify-between"
        >
          <div className="flex items-center space-x-4">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
              className="p-3 bg-gradient-to-r from-slate-600 to-sky-600 rounded-xl shadow-lg"
            >
              <Sparkles className="w-8 h-8 text-white" />
            </motion.div>
            <div>
              <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Dashboard</h1>
              <p className="text-slate-600 dark:text-gray-300">Welcome back to SchemaSage</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Search Bar */}
            <div className="hidden md:flex items-center space-x-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />                <Input
                  placeholder="Search projects..."
                  className="pl-10 w-64 bg-white/50 dark:bg-white/10 backdrop-blur-sm border border-slate-200 dark:border-white/20 text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-gray-400 focus:border-blue-400 focus:ring-blue-400/20 rounded-xl"
                />
              </div>
            </div>
            
            {/* Notifications */}
            <Button
              variant="outline"
              size="icon"
              className="bg-white/50 dark:bg-white/10 backdrop-blur-sm border border-slate-200 dark:border-white/20 hover:bg-white/70 dark:hover:bg-white/20 rounded-xl"
            >
              <Bell className="w-5 h-5 text-slate-600 dark:text-gray-300" />
            </Button>
            
            {/* Theme Toggle */}
            <ModeToggle />
            
            {/* New Project Button */}
            <Button
              onClick={() => setNewProjectDialog(true)}
              className="bg-gradient-to-r from-slate-600 to-sky-600 hover:from-slate-700 hover:to-sky-700 text-white font-semibold rounded-xl px-6 py-3 transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-slate-500/25 group"
            >
              <Plus className="w-5 h-5 mr-2" />
              New Project
            </Button>
          </div>
        </motion.div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.1, duration: 0.6 }}
          >
            <Card className="bg-white/80 dark:bg-white/10 backdrop-blur-xl border border-slate-200 dark:border-white/20 p-6 hover:bg-white/90 dark:hover:bg-white/15 transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-blue-500/10">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500 dark:text-gray-400 mb-1">Active Projects</p>
                  <p className="text-3xl font-bold text-slate-900 dark:text-white">{stats.activeProjects}</p>
                </div>
                <div className="p-3 bg-gradient-to-r from-slate-500 to-slate-600 rounded-xl">
                  <FolderOpen className="w-6 h-6 text-white" />
                </div>
              </div>
            </Card>
          </motion.div>

          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.6 }}
          >
            <Card className="bg-white/80 dark:bg-white/10 backdrop-blur-xl border border-slate-200 dark:border-white/20 p-6 hover:bg-white/90 dark:hover:bg-white/15 transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-teal-500/10">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500 dark:text-gray-400 mb-1">Tables Processed</p>
                  <p className="text-3xl font-bold text-slate-900 dark:text-white">{stats.tablesProcessed}</p>
                </div>
                <div className="p-3 bg-gradient-to-r from-sky-500 to-sky-600 rounded-xl">
                  <BarChart3 className="w-6 h-6 text-white" />
                </div>
              </div>
            </Card>
          </motion.div>

          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.6 }}
          >
            <Card className="bg-white/80 dark:bg-white/10 backdrop-blur-xl border border-slate-200 dark:border-white/20 p-6 hover:bg-white/90 dark:hover:bg-white/15 transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-green-500/10">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500 dark:text-gray-400 mb-1">Success Rate</p>
                  <p className="text-3xl font-bold text-slate-900 dark:text-white">98%</p>
                </div>
                <div className="p-3 bg-gradient-to-r from-teal-500 to-teal-600 rounded-xl">
                  <TrendingUp className="w-6 h-6 text-white" />
                </div>
              </div>
            </Card>
          </motion.div>

          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.4, duration: 0.6 }}
          >
            <Card className="bg-white/80 dark:bg-white/10 backdrop-blur-xl border border-slate-200 dark:border-white/20 p-6 hover:bg-white/90 dark:hover:bg-white/15 transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-yellow-500/10">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500 dark:text-gray-400 mb-1">Time Saved</p>
                  <p className="text-3xl font-bold text-slate-900 dark:text-white">24h</p>
                </div>
                <div className="p-3 bg-gradient-to-r from-slate-400 to-slate-500 rounded-xl">
                  <Clock className="w-6 h-6 text-white" />
                </div>
              </div>
            </Card>
          </motion.div>
        </div>

        {/* Quick Actions */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.5, duration: 0.6 }}
        >
          <Card className="bg-white/80 dark:bg-white/10 backdrop-blur-xl border border-slate-200 dark:border-white/20 p-8">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6 flex items-center">
              <Zap className="w-6 h-6 mr-3 text-yellow-500" />
              Quick Actions
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    onClick={handleUpload}
                    className="bg-gradient-to-r from-slate-500/20 to-sky-500/20 dark:from-slate-500/20 dark:to-sky-500/20 hover:from-slate-500/30 hover:to-sky-500/30 border border-slate-500/50 text-slate-900 dark:text-white font-semibold rounded-xl p-6 h-auto transition-all duration-300 transform hover:scale-105 group backdrop-blur-sm"
                  >
                    <div className="flex flex-col items-center space-y-3">
                      <Upload className="w-8 h-8 text-slate-600 dark:text-slate-300 group-hover:text-slate-500 dark:group-hover:text-slate-200" />
                      <span>Upload Data</span>
                      <p className="text-xs text-slate-500 dark:text-gray-400 text-center">Import JSON, CSV, or Excel files</p>
                    </div>
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Import data files to generate schemas</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    onClick={handleConnectDb}
                    className="bg-gradient-to-r from-sky-500/20 to-teal-500/20 dark:from-sky-500/20 dark:to-teal-500/20 hover:from-sky-500/30 hover:to-teal-500/30 border border-sky-500/50 text-slate-900 dark:text-white font-semibold rounded-xl p-6 h-auto transition-all duration-300 transform hover:scale-105 group backdrop-blur-sm"
                  >
                    <div className="flex flex-col items-center space-y-3">
                      <Database className="w-8 h-8 text-teal-600 dark:text-teal-300 group-hover:text-teal-500 dark:group-hover:text-teal-200" />
                      <span>Connect Database</span>
                      <p className="text-xs text-slate-500 dark:text-gray-400 text-center">Import from existing databases</p>
                    </div>
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Connect to PostgreSQL, MySQL, or other databases</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    onClick={handleGenerateCode}
                    className="bg-gradient-to-r from-teal-500/20 to-slate-500/20 dark:from-teal-500/20 dark:to-slate-500/20 hover:from-teal-500/30 hover:to-slate-500/30 border border-teal-500/50 text-slate-900 dark:text-white font-semibold rounded-xl p-6 h-auto transition-all duration-300 transform hover:scale-105 group backdrop-blur-sm"
                  >
                    <div className="flex flex-col items-center space-y-3">
                      <Code className="w-8 h-8 text-green-600 dark:text-green-300 group-hover:text-green-500 dark:group-hover:text-green-200" />
                      <span>Generate Code</span>
                      <p className="text-xs text-slate-500 dark:text-gray-400 text-center">Export to SQL, Python, TypeScript</p>
                    </div>
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Generate code from your schemas</TooltipContent>
              </Tooltip>
            </div>
          </Card>
        </motion.div>

        {/* Recent Projects and Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Recent Projects */}
          <motion.div
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.6, duration: 0.6 }}
          >
            <Card className="bg-white/80 dark:bg-white/10 backdrop-blur-xl border border-slate-200 dark:border-white/20 p-8 h-full">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center">
                  <FolderOpen className="w-6 h-6 mr-3 text-slate-600 dark:text-slate-400" />
                  Recent Projects
                </h2>
                <Button
                  onClick={() => setNewProjectDialog(true)}
                  size="sm"
                  className="bg-gradient-to-r from-slate-600 to-sky-600 hover:from-slate-700 hover:to-sky-700 text-white rounded-lg"
                >
                  <Plus className="w-4 h-4 mr-1" />
                  New
                </Button>
              </div>
              <div className="space-y-4">
                {stats.recentProjects.length === 0 ? (
                  <div className="text-center py-8">
                    <FileText className="w-12 h-12 text-slate-400 dark:text-gray-500 mx-auto mb-4" />
                    <p className="text-slate-600 dark:text-gray-400">No recent projects yet</p>
                    <p className="text-sm text-slate-500 dark:text-gray-500 mt-2">Create your first project to get started</p>
                  </div>
                ) : (
                  stats.recentProjects.map((proj, index) => (
                    <motion.div
                      key={proj.id}
                      initial={{ x: -20, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      transition={{ delay: 0.7 + index * 0.1, duration: 0.5 }}
                    >
                      <Card className="bg-white/50 dark:bg-white/5 border border-slate-200 dark:border-white/10 p-4 hover:bg-white/70 dark:hover:bg-white/10 transition-all duration-300 cursor-pointer">
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="font-semibold text-slate-900 dark:text-white">{proj.name}</h3>
                            <p className="text-sm text-slate-500 dark:text-gray-400">
                              Updated {new Date(proj.updatedAt).toLocaleDateString()}
                            </p>
                          </div>
                          <div className="p-2 bg-gradient-to-r from-slate-500 to-slate-600 rounded-lg">
                            <FileText className="w-4 h-4 text-white" />
                          </div>
                        </div>
                      </Card>
                    </motion.div>
                  ))
                )}
              </div>
            </Card>
          </motion.div>

          {/* Activity Feed */}
          <motion.div
            initial={{ x: 20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.7, duration: 0.6 }}
          >
            <Card className="bg-white/80 dark:bg-white/10 backdrop-blur-xl border border-slate-200 dark:border-white/20 p-8 h-full">
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6 flex items-center">
                <Activity className="w-6 h-6 mr-3 text-teal-600 dark:text-teal-400" />
                Activity Feed
              </h2>
              <div className="space-y-4">
                {activityFeed.length === 0 ? (
                  <div className="text-center py-8">
                    <Activity className="w-12 h-12 text-slate-400 dark:text-gray-500 mx-auto mb-4" />
                    <p className="text-slate-600 dark:text-gray-400">No recent activity</p>
                    <p className="text-sm text-slate-500 dark:text-gray-500 mt-2">Start working on projects to see activity</p>
                  </div>
                ) : (
                  activityFeed.map((item, index) => (
                    <motion.div
                      key={item.id}
                      initial={{ x: 20, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      transition={{ delay: 0.8 + index * 0.1, duration: 0.5 }}
                    >
                      <div className="flex items-start space-x-3 p-3 bg-white/50 dark:bg-white/5 rounded-xl border border-slate-200 dark:border-white/10">
                        <div className="p-2 bg-gradient-to-r from-sky-500 to-sky-600 rounded-lg">
                          <Activity className="w-4 h-4 text-white" />
                        </div>
                        <div className="flex-1">
                          <p className="text-slate-900 dark:text-white text-sm">{item.description}</p>
                          <p className="text-xs text-slate-500 dark:text-gray-400 mt-1">{item.timestamp}</p>
                        </div>
                      </div>
                    </motion.div>
                  ))
                )}
              </div>
            </Card>
          </motion.div>
        </div>

        {/* Features Preview */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.8, duration: 0.6 }}
        >
          <Card className="bg-white/80 dark:bg-white/10 backdrop-blur-xl border border-slate-200 dark:border-white/20 p-8">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6 flex items-center">
              <Sparkles className="w-6 h-6 mr-3 text-yellow-500" />
              SchemaSage Features
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center space-y-4">
                <div className="p-4 bg-gradient-to-r from-slate-500 to-slate-600 rounded-xl w-16 h-16 mx-auto flex items-center justify-center">
                  <Shield className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Secure & Private</h3>
                <p className="text-slate-600 dark:text-gray-400 text-sm">Your data is encrypted and never stored on our servers</p>
              </div>
              <div className="text-center space-y-4">
                <div className="p-4 bg-gradient-to-r from-sky-500 to-sky-600 rounded-xl w-16 h-16 mx-auto flex items-center justify-center">
                  <Zap className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Lightning Fast</h3>
                <p className="text-slate-600 dark:text-gray-400 text-sm">Generate complex schemas in seconds with AI assistance</p>
              </div>
              <div className="text-center space-y-4">
                <div className="p-4 bg-gradient-to-r from-teal-500 to-teal-600 rounded-xl w-16 h-16 mx-auto flex items-center justify-center">
                  <Users className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Team Collaboration</h3>
                <p className="text-slate-600 dark:text-gray-400 text-sm">Work together with your team in real-time</p>
              </div>
            </div>
          </Card>
        </motion.div>
      </div>

      {/* New Project Dialog */}
      <Dialog open={newProjectDialog} onOpenChange={setNewProjectDialog}>
        <DialogContent className="bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl border border-slate-200 dark:border-white/20 text-slate-900 dark:text-white">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold">Create New Project</DialogTitle>
          </DialogHeader>
          <div className="space-y-6 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700 dark:text-gray-300">Project Name</label>
              <Input
                placeholder="Enter project name"
                value={newProject.name}
                onChange={e => setNewProject({ ...newProject, name: e.target.value })}
                className="bg-white/50 dark:bg-white/10 border-slate-200 dark:border-white/20 text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-gray-400 focus:border-blue-400 focus:ring-blue-400/20 rounded-xl"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700 dark:text-gray-300">Description (optional)</label>
              <Textarea
                placeholder="Describe your project..."
                value={newProject.description}
                onChange={e => setNewProject({ ...newProject, description: e.target.value })}
                className="bg-white/50 dark:bg-white/10 border-slate-200 dark:border-white/20 text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-gray-400 focus:border-blue-400 focus:ring-blue-400/20 rounded-xl min-h-[100px]"
              />
            </div>
          </div>
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setNewProjectDialog(false)} 
              disabled={creating}
              className="bg-transparent border-slate-200 dark:border-white/20 text-slate-700 dark:text-white hover:bg-slate-100 dark:hover:bg-white/10"
            >
              Cancel
            </Button>
            <Button 
              onClick={handleCreateProject} 
              disabled={creating || !newProject.name.trim()}
              className="bg-gradient-to-r from-slate-600 to-sky-600 hover:from-slate-700 hover:to-sky-700 text-white font-semibold"
            >
              {creating ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  <span>Creating...</span>
                </div>
              ) : (
                "Create Project"
              )}
            </Button>
          </DialogFooter>        </DialogContent>
      </Dialog>
    </div>
    </TooltipProvider>
  );
}
