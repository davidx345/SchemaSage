"use client";

import { Card } from "@/components/ui/card";
// import { SchemaForm } from "@/components/schema-detection/schema-form";
// import { GeneratedCode } from "@/components/schema-detection/generated-code";
// import { Settings } from "@/components/schema-detection/settings";
// import { ErrorBoundary } from "@/components/error-boundary";
// import Link from "next/link";
import { Button } from "@/components/ui/button";
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
  // CalendarDays,
  Files,
} from "lucide-react";

export default function Dashboard() {
  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold mb-2">Welcome back!</h1>
          <p className="text-muted-foreground">
            Here&apos;s what&apos;s happening with your projects.
          </p>
        </div>
        <Button>
          <FileUp className="mr-2 h-4 w-4" />
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
            <div className="text-3xl font-bold">12</div>
            <p className="text-sm text-muted-foreground">
              +2 from last month
            </p>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center gap-2">
            <Files className="h-4 w-4 text-primary" />
            <h3 className="font-semibold">Tables Processed</h3>
          </div>
          <div className="mt-4">
            <div className="text-3xl font-bold">156</div>
            <p className="text-sm text-muted-foreground">
              +23 from last month
            </p>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-primary" />
            <h3 className="font-semibold">Last Activity</h3>
          </div>
          <div className="mt-4">
            <div className="text-3xl font-bold">2hrs</div>
            <p className="text-sm text-muted-foreground">
              Code generation for ProjectX
            </p>
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
          <Button variant="ghost">
            View All
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Project Name</TableHead>
              <TableHead>Tables</TableHead>
              <TableHead>Last Modified</TableHead>
              <TableHead>Status</TableHead>
              <TableHead></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {[
              {
                name: "E-commerce Database",
                tables: 12,
                modified: "2 hours ago",
                status: "Active",
              },
              {
                name: "Blog Platform",
                tables: 8,
                modified: "1 day ago",
                status: "Draft",
              },
              {
                name: "User Management",
                tables: 5,
                modified: "3 days ago",
                status: "Complete",
              },
            ].map((project) => (
              <TableRow key={project.name}>
                <TableCell className="font-medium">
                  {project.name}
                </TableCell>
                <TableCell>{project.tables} tables</TableCell>
                <TableCell>{project.modified}</TableCell>
                <TableCell>
                  <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    project.status === "Active"
                      ? "bg-primary/10 text-primary"
                      : project.status === "Draft"
                      ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-500"
                      : "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-500"
                  }`}>
                    {project.status}
                  </div>
                </TableCell>
                <TableCell>
                  <Button variant="ghost" size="sm">
                    View Schema
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      {/* Quick Actions */}
      <Card>
        <div className="p-6">
          <h3 className="font-semibold mb-4">Quick Actions</h3>
          <div className="grid gap-4 md:grid-cols-3">
            <Button variant="outline" className="h-auto p-4 justify-start">
              <FileUp className="mr-2 h-4 w-4" />
              <div className="text-left">
                <div className="font-semibold">Upload Data</div>
                <div className="text-sm text-muted-foreground">
                  Import JSON or CSV files
                </div>
              </div>
            </Button>
            <Button variant="outline" className="h-auto p-4 justify-start">
              <Database className="mr-2 h-4 w-4" />
              <div className="text-left">
                <div className="font-semibold">Connect Database</div>
                <div className="text-sm text-muted-foreground">
                  Import from existing DB
                </div>
              </div>
            </Button>
            <Button variant="outline" className="h-auto p-4 justify-start">
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
    </div>
  );
}
