"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  ChevronLeft,
  Home,
  Upload,
  Database,
  Code2,
  Settings,
  HelpCircle,
  Boxes,
  User,
  BarChart3,
  Shield
} from "lucide-react";
import { useAuth } from "@/lib/store";
import { useRouter } from "next/navigation";

const navigation = [
  { name: "Dashboard", href: "/", icon: Home },
  { name: "Upload Data", href: "/upload", icon: Upload },
  { name: "Schema View", href: "/schema", icon: Database },
  { name: "Code Generation", href: "/code", icon: Code2 },
  { name: "Cross-Dataset", href: "/cross-dataset", icon: Boxes },
  { name: "Glossary", href: "/glossary", icon: User },
  { name: "Consistency Check", href: "/consistency-check", icon: Settings },
  { name: "Lineage Explorer", href: "/lineage", icon: BarChart3 },
  { name: "Data Cleaning", href: "/data-cleaning", icon: Shield },
  { name: "Integrations", href: "/integrations", icon: Boxes }, // <-- new link
];

const secondaryNavigation = [
  { name: "Settings", href: "/settings", icon: Settings },
  { name: "Help", href: "/help", icon: HelpCircle },
];

export function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const router = useRouter();

  return (
    <div
      className={cn(
        "relative flex flex-col border-r bg-background duration-300 ease-in-out",
        isCollapsed ? "w-[60px]" : "w-[240px]"
      )}
    >
      <div className="flex h-14 items-center border-b px-3">
        <Link
          href="/"
          className="flex items-center space-x-2"
          onClick={(e) => e.preventDefault()}
        >
          {/* Removed blue blob/shadow, only show clean logo */}
          <Boxes className="h-6 w-6" />
          {!isCollapsed && <span className="font-semibold">Schema Sage</span>}
        </Link>
      </div>
      
      <ScrollArea className="flex-1">
        <div className="space-y-4 py-4">
          <div className="px-3">
            <div className="space-y-1">
              {navigation.map((item) => (
                <Link key={item.href} href={item.href}>
                  <Button
                    variant={pathname === item.href ? "secondary" : "ghost"}
                    className={cn(
                      "w-full justify-start",
                      isCollapsed && "justify-center"
                    )}
                  >
                    <item.icon className="mr-2 h-4 w-4" />
                    {!isCollapsed && item.name}
                  </Button>
                </Link>
              ))}
            </div>
          </div>

          <div className="px-3">
            <div className="space-y-1">
              {secondaryNavigation.map((item) => (
                <Link key={item.href} href={item.href}>
                  <Button
                    variant="ghost"
                    className={cn(
                      "w-full justify-start",
                      isCollapsed && "justify-center"
                    )}
                  >
                    <item.icon className="mr-2 h-4 w-4" />
                    {!isCollapsed && item.name}
                  </Button>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </ScrollArea>

      {/* User info/profile at bottom */}
      <div className="border-t px-4 py-3 flex items-center gap-3 mt-auto">
        <div className="flex items-center gap-2 cursor-pointer" onClick={() => router.push("/settings")}> 
          <User className="h-6 w-6 text-muted-foreground" />
          {!isCollapsed && (
            <div className="flex flex-col">
              <span className="font-medium text-sm">{user?.fullName || user?.email || "User"}</span>
              <span className="text-xs text-muted-foreground">Profile</span>
            </div>
          )}
        </div>
        {!isCollapsed && (
          <Button size="sm" variant="outline" className="ml-auto" onClick={logout}>Logout</Button>
        )}
      </div>

      <Button
        variant="ghost"
        className="absolute -right-4 top-7 h-6 w-6 rounded-full p-0 z-50"
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        <ChevronLeft
          className={cn("h-4 w-4", isCollapsed && "rotate-180")}
        />
      </Button>
    </div>
  );
}