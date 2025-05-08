import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";

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
        const res = await fetch("/api/dashboard/summary");
        if (!res.ok) throw new Error("Failed to load dashboard data");
        setStats(await res.json());
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
      const res = await fetch("/api/schema/project", {
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

  if (loading) return <div>Loading dashboard...</div>;
  if (error) return <div className="text-red-500">{error}</div>;
  if (!stats) return null;

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">Active Projects</div>
          <div className="text-2xl font-bold">{stats.activeProjects}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">Tables Processed</div>
          <div className="text-2xl font-bold">{stats.tablesProcessed}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">Last Activity</div>
          <div className="text-base">{stats.lastActivity.description}</div>
          <div className="text-xs text-muted-foreground">{new Date(stats.lastActivity.timestamp).toLocaleString()}</div>
        </Card>
      </div>

      <div>
        <div className="flex justify-between items-center mb-2">
          <h2 className="text-lg font-semibold">Recent Projects</h2>
          <Button onClick={() => setNewProjectDialog(true)}>New Project</Button>
        </div>
        <div className="grid gap-2">
          {stats.recentProjects.length === 0 ? (
            <div className="text-muted-foreground">No recent projects.</div>
          ) : (
            stats.recentProjects.map((proj) => (
              <Card key={proj.id} className="p-3 flex justify-between items-center">
                <span>{proj.name}</span>
                <span className="text-xs text-muted-foreground">{new Date(proj.updatedAt).toLocaleDateString()}</span>
              </Card>
            ))
          )}
        </div>
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-2">Quick Actions</h2>
        <div className="flex gap-4">
          <Button variant="outline" onClick={handleUpload}>Upload Data</Button>
          <Button variant="outline" onClick={handleConnectDb}>Connect Database</Button>
          <Button variant="outline" onClick={handleGenerateCode}>Generate Code</Button>
        </div>
      </div>

      <Dialog open={newProjectDialog} onOpenChange={setNewProjectDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New Project</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <Input
              placeholder="Project Name"
              value={newProject.name}
              onChange={e => setNewProject({ ...newProject, name: e.target.value })}
            />
            <Textarea
              placeholder="Description (optional)"
              value={newProject.description}
              onChange={e => setNewProject({ ...newProject, description: e.target.value })}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setNewProjectDialog(false)} disabled={creating}>Cancel</Button>
            <Button onClick={handleCreateProject} disabled={creating || !newProject.name.trim()}>
              {creating ? "Creating..." : "Create Project"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
