"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Database,
  FileUp,
  Code,
  ArrowRight,
  Activity,
  Files,
  Loader2,
  Plus,
} from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";
import { projectApi } from "@/lib/api";
import { Project } from "@/lib/types";
import { useStore, useAuth } from "@/lib/store";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { OnboardingModal } from "@/components/onboarding-modal";

export default function Dashboard() {
  const { token } = useAuth();
  const router = useRouter();

  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    activeProjects: 0,
    totalTables: 0,
    lastActivity: { time: "", description: "" },
  });
  const [isNewProjectDialogOpen, setIsNewProjectDialogOpen] = useState(false);
  const [newProject, setNewProject] = useState({ name: "", description: "" });
  const [createLoading, setCreateLoading] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const { addRecentProject } = useStore();

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!token) {
      router.replace("/auth/login");
    }
  }, [token, router]);

  // Fetch projects data
  useEffect(() => {
    async function fetchProjectsData() {
      try {
        setLoading(true);
        const response = await projectApi.getProjects();

        if (response.success && response.data) {
          setProjects(response.data);

          // Calculate statistics
          const active = response.data.length; // No status property, so just count all
          const tables = response.data.reduce((sum, project) => {
            return sum + (project.schema?.tables?.length || 0);
          }, 0);

          // Get last activity
          let lastActivity = { time: "2hrs", description: "No recent activity" };
          if (response.data.length > 0) {
            const sorted = [...response.data].sort(
              (a, b) =>
                new Date(b.updated_at || b.created_at).getTime() -
                new Date(a.updated_at || a.created_at).getTime()
            );

            if (sorted[0]) {
              const project = sorted[0];
              lastActivity = {
                time: formatRelativeTime(project.updated_at || project.created_at),
                description: `Updated ${project.name}`,
              };
            }
          }

          setStats({
            activeProjects: active,
            totalTables: tables,
            lastActivity,
          });
        }
      } catch (error) {
        console.error("Failed to fetch projects:", error);
        toast.error("Failed to load projects data");
      } finally {
        setLoading(false);
      }
    }

    fetchProjectsData();
  }, []);

  // Handle creating a new project
  const handleCreateProject = async () => {
    if (!newProject.name.trim()) {
      toast.error("Project name is required");
      return;
    }

    try {
      setCreateLoading(true);
      const response = await projectApi.createProject(newProject.name);

      if (response.success && response.data) {
        toast.success(`Project "${newProject.name}" created successfully!`);
        addRecentProject(response.data);
        setIsNewProjectDialogOpen(false);
        setNewProject({ name: "", description: "" });

        // Navigate to schema page with the new project
        router.push(`/schema?project=${response.data.id}`);
      } else {
        toast.error(response.error?.message || "Failed to create project");
      }
    } catch (error) {
      console.error("Project creation error:", error);
      toast.error("An error occurred while creating the project");
    } finally {
      setCreateLoading(false);
    }
  };

  // Handle navigation to upload page
  const handleUploadData = () => {
    router.push("/upload");
  };

  // Handle navigation to database connection page
  const handleConnectDatabase = () => {
    router.push("/upload?tab=database");
  };

  // Handle navigation to code generation page
  const handleGenerateCode = () => {
    router.push("/code");
  };

  useEffect(() => {
    if (!loading && projects.length === 0 && !localStorage.getItem("onboardingDismissed")) {
      setShowOnboarding(true);
    }
  }, [loading, projects]);

  const handleOnboardingClose = () => {
    setShowOnboarding(false);
    localStorage.setItem("onboardingDismissed", "1");
  };

  if (!token) return null;

  return (
    <div className="space-y-8">
      <OnboardingModal open={showOnboarding} onClose={handleOnboardingClose} />
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold mb-2">Welcome back!</h1>
          <p className="text-muted-foreground">
            Here&apos;s what&apos;s happening with your projects.
          </p>
        </div>
        <Button onClick={() => setIsNewProjectDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New Project
        </Button>
      </div>

      {/* Metrics */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="p-6">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-primary" />
            <h3 className="font-semibold">Active Projects</h3>
          </div>
          <div className="mt-4">
            {loading ? (
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Loading...</span>
              </div>
            ) : (
              <>
                <div className="text-3xl font-bold">{stats.activeProjects}</div>
                <p className="text-sm text-muted-foreground">
                  {projects.length} total projects
                </p>
              </>
            )}
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center gap-2">
            <Files className="h-4 w-4 text-primary" />
            <h3 className="font-semibold">Tables Processed</h3>
          </div>
          <div className="mt-4">
            {loading ? (
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Loading...</span>
              </div>
            ) : (
              <>
                <div className="text-3xl font-bold">{stats.totalTables}</div>
                <p className="text-sm text-muted-foreground">
                  Across all projects
                </p>
              </>
            )}
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-primary" />
            <h3 className="font-semibold">Last Activity</h3>
          </div>
          <div className="mt-4">
            {loading ? (
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Loading...</span>
              </div>
            ) : (
              <>
                <div className="text-3xl font-bold">{stats.lastActivity.time}</div>
                <p className="text-sm text-muted-foreground">
                  {stats.lastActivity.description}
                </p>
              </>
            )}
          </div>
        </Card>
      </div>

      {/* Recent Projects */}
      <Card>
        <div className="p-6 flex justify-between items-center border-b">
          <div>
            <h3 className="font-semibold">Recent Projects</h3>
            <p className="text-sm text-muted-foreground">
              Your most recently updated schemas
            </p>
          </div>
          {projects.length > 0 && (
            <Button variant="ghost" onClick={() => router.push("/projects")}>
              View All
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          )}
        </div>

        {loading ? (
          <div className="p-8 flex justify-center items-center">
            <Loader2 className="h-6 w-6 animate-spin mr-2" />
            <span>Loading projects...</span>
          </div>
        ) : projects.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-muted-foreground mb-4">
              You don&apos;t have any projects yet
            </p>
            <Button onClick={() => setIsNewProjectDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Create your first project
            </Button>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Project Name</TableHead>
                <TableHead>Tables</TableHead>
                <TableHead>Last Modified</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {projects.slice(0, 5).map((project) => (
                <TableRow key={project.id}>
                  <TableCell className="font-medium">{project.name}</TableCell>
                  <TableCell>
                    {project.schema?.tables?.length || 0} tables
                  </TableCell>
                  <TableCell>
                    {formatRelativeTime(
                      project.updated_at || project.created_at
                    )}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        router.push(`/schema?project=${project.id}`)
                      }
                    >
                      View Schema
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>

      {/* Quick Actions */}
      <Card>
        <div className="p-6">
          <h3 className="font-semibold mb-4">Quick Actions</h3>
          <div className="grid gap-4 md:grid-cols-3">
            <Button
              variant="outline"
              className="h-auto p-4 justify-start"
              onClick={handleUploadData}
            >
              <FileUp className="mr-2 h-4 w-4" />
              <div className="text-left">
                <div className="font-semibold">Upload Data</div>
                <div className="text-sm text-muted-foreground">
                  Import JSON or CSV files
                </div>
              </div>
            </Button>
            <Button
              variant="outline"
              className="h-auto p-4 justify-start"
              onClick={handleConnectDatabase}
            >
              <Database className="mr-2 h-4 w-4" />
              <div className="text-left">
                <div className="font-semibold">Connect Database</div>
                <div className="text-sm text-muted-foreground">
                  Import from existing DB
                </div>
              </div>
            </Button>
            <Button
              variant="outline"
              className="h-auto p-4 justify-start"
              onClick={handleGenerateCode}
            >
              <Code className="mr-2 h-4 w-4" />
              <div className="text-left">
                <div className="font-semibold">Generate Code</div>
                <div className="text-sm text-muted-foreground">
                  Export schema to code
                </div>
              </div>
            </Button>
          </div>
        </div>
      </Card>

      {/* New Project Dialog */}
      <Dialog
        open={isNewProjectDialogOpen}
        onOpenChange={setIsNewProjectDialogOpen}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Project</DialogTitle>
            <DialogDescription>
              Create a new database schema project. You can upload data or start
              from scratch.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="name">Project Name</Label>
              <Input
                id="name"
                placeholder="My Database Schema"
                value={newProject.name}
                onChange={(e) =>
                  setNewProject({ ...newProject, name: e.target.value })
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Description (Optional)</Label>
              <Textarea
                id="description"
                placeholder="A brief description of your project"
                value={newProject.description}
                onChange={(e) =>
                  setNewProject({ ...newProject, description: e.target.value })
                }
                className="min-h-[100px]"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsNewProjectDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateProject}
              disabled={createLoading || !newProject.name.trim()}
            >
              {createLoading && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Create Project
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
