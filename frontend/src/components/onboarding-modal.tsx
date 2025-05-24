"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useStore } from "@/lib/store";
import { toast } from "sonner";

export function OnboardingModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { addRecentProject } = useStore();
  const [loading, setLoading] = useState(false);

  const handleCreateSample = async () => {
    setLoading(true);
    try {
      // Simulate sample project creation (replace with real API if needed)
      const sample = {
        id: "sample-1",
        name: "Sample Project",
        description: "A sample project to explore SchemaSage features.",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        schema: {
          tables: [
            {
              name: "users",
              columns: [
                { name: "id", data_type: "string", is_nullable: false },
                { name: "email", data_type: "string", is_nullable: false }
              ],
              indexes: [],
              primary_key: ["id"],
              foreign_keys: []
            },
            {
              name: "orders",
              columns: [
                { name: "id", data_type: "string", is_nullable: false },
                { name: "user_id", data_type: "string", is_nullable: false }
              ],
              indexes: [],
              primary_key: ["id"],
              foreign_keys: [
                { column: "user_id", ref_table: "users", ref_column: "id" }
              ]
            }
          ],
          relationships: [
            {
              source_table: "orders",
              source_column: "user_id",
              target_table: "users",
              target_column: "id",
              type: "many-to-one" as const
            }
          ]
        }
      };
      addRecentProject(sample);
      toast.success("Sample project created!");
      onClose();
    } catch {
      toast.error("Failed to create sample project");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Welcome to SchemaSage!</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <p className="text-muted-foreground">
            SchemaSage helps you design, visualize, and generate code for your database schemas using AI.<br />
            <span className="block mt-2">Get started in 3 easy steps:</span>
            <ol className="list-decimal ml-6 mt-2 text-sm">
              <li>Create your first project or try a sample project below.</li>
              <li>Upload your data or connect to a database.</li>
              <li>Visualize, edit, and generate code for your schema!</li>
            </ol>
            <span className="block mt-4 text-xs">Need help? <a href="/help" className="underline text-blue-600">Read the docs</a> or <a href="/landing" className="underline text-blue-600">see a demo</a>.</span>
          </p>
        </div>
        <DialogFooter>
          <Button onClick={handleCreateSample} disabled={loading}>
            {loading ? "Creating..." : "Try Sample Project"}
          </Button>
          <Button variant="outline" onClick={onClose}>
            Skip
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
