"use client";

import { useStore } from "@/lib/store";
import { Tooltip, TooltipProvider, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip";
import { useEffect, useRef, useState } from "react";
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
  Shield,
  Menu,
  X,
  ChevronRight
} from "lucide-react";
import { useAuth } from "@/lib/store";
import { useRouter } from "next/navigation";
import type { Dispatch, SetStateAction } from "react";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: Home },
  { name: "Upload Data", href: "/upload", icon: Upload },
  { name: "Schema View", href: "/schema", icon: Database },
  { name: "Code Generation", href: "/code", icon: Code2 },
  { name: "Cross-Dataset", href: "/cross-dataset", icon: Boxes },
  { name: "Glossary", href: "/glossary", icon: User },
  { name: "Consistency Check", href: "/consistency-check", icon: Settings },
  { name: "Lineage Explorer", href: "/lineage", icon: BarChart3 },
  { name: "Data Cleaning", href: "/data-cleaning", icon: Shield },
  { name: "Integrations", href: "/integrations", icon: Boxes },
];

const secondaryNavigation = [
  { name: "Settings", href: "/settings", icon: Settings },
  { name: "Help", href: "/help", icon: HelpCircle },
];

// Focus trap utility
function useFocusTrap(active: boolean, trapRef: React.RefObject<HTMLDivElement | null>) {
  useEffect(() => {
    if (!active || !trapRef.current) return;
    const node = trapRef.current;
    const focusable = node.querySelectorAll<HTMLElement>(
      'a, button, textarea, input, select, [tabindex]:not([tabindex="-1"])'
    );
    if (focusable.length) (focusable[0] as HTMLElement).focus();
    function handleKey(e: KeyboardEvent) {
      if (e.key !== "Tab") return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          (last as HTMLElement).focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          (first as HTMLElement).focus();
        }
      }
    }
    node.addEventListener("keydown", handleKey);
    return () => node.removeEventListener("keydown", handleKey);
  }, [active, trapRef]);
}

export function Sidebar({ sidebarCollapsed, setSidebarCollapsed }: { sidebarCollapsed: boolean, setSidebarCollapsed: Dispatch<SetStateAction<boolean>> }) {
  const { user, logout } = useAuth();
  const router = useRouter();

  const sidebarWidth = sidebarCollapsed ? "w-[72px] min-w-[72px] max-w-[72px]" : "w-[260px] min-w-[260px] max-w-[260px]";

  return (
    <TooltipProvider>
      <div
        id="main-sidebar"
        role="navigation"
        aria-label="Main navigation sidebar"
        className={`fixed top-0 left-0 h-screen z-40 flex flex-col border-r bg-background shadow-xl transition-all duration-300 ${sidebarWidth}`}
        style={{ minWidth: sidebarCollapsed ? 72 : 260, maxWidth: sidebarCollapsed ? 72 : 260 }}
      >
        <div className="flex h-14 items-center border-b px-3 relative">
          <Link
            href="/"
            className="flex items-center space-x-2"
            tabIndex={0}
            aria-label="Go to home"
          >
            <Boxes className="h-6 w-6" />
            {!sidebarCollapsed && <span className="font-semibold">Schema Sage</span>}
          </Link>
          {/* Collapse/Expand button */}
          <button
            className="absolute -right-4 top-1/2 -translate-y-1/2 flex items-center justify-center w-8 h-8 rounded-full bg-background border border-border shadow hover:bg-muted transition-all duration-300"
            onClick={() => setSidebarCollapsed((c) => !c)}
            aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            tabIndex={0}
          >
            {sidebarCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>
        <ScrollArea className="flex-1">
          <div className="space-y-4 py-4">
            <div className="px-3">
              <div className="space-y-1">
                {navigation.map((item) => (
                  <Tooltip key={item.href} delayDuration={sidebarCollapsed ? 0 : 9999}>
                    <TooltipTrigger asChild>
                      <Link href={item.href} tabIndex={0} aria-label={item.name}>
                        <Button
                          variant={usePathname() === item.href ? "secondary" : "ghost"}
                          className={`w-full justify-start text-base font-medium rounded-lg group transition-all duration-300 ${sidebarCollapsed ? "justify-center px-0" : "px-3"}`}
                          tabIndex={0}
                        >
                          <item.icon className={`h-5 w-5 group-hover:scale-110 transition-transform duration-200 ${sidebarCollapsed ? "mx-auto" : "mr-2"}`} />
                          {!sidebarCollapsed && item.name}
                        </Button>
                      </Link>
                    </TooltipTrigger>
                    {sidebarCollapsed && (
                      <TooltipContent side="right" className="ml-2">
                        {item.name}
                      </TooltipContent>
                    )}
                  </Tooltip>
                ))}
              </div>
            </div>
            <div className="px-3">
              <div className="space-y-1">
                {secondaryNavigation.map((item) => (
                  <Tooltip key={item.href} delayDuration={sidebarCollapsed ? 0 : 9999}>
                    <TooltipTrigger asChild>
                      <Link href={item.href} tabIndex={0} aria-label={item.name}>
                        <Button
                          variant="ghost"
                          className={`w-full justify-start text-base font-medium rounded-lg group transition-all duration-300 ${sidebarCollapsed ? "justify-center px-0" : "px-3"}`}
                          tabIndex={0}
                        >
                          <item.icon className={`h-5 w-5 group-hover:scale-110 transition-transform duration-200 ${sidebarCollapsed ? "mx-auto" : "mr-2"}`} />
                          {!sidebarCollapsed && item.name}
                        </Button>
                      </Link>
                    </TooltipTrigger>
                    {sidebarCollapsed && (
                      <TooltipContent side="right" className="ml-2">
                        {item.name}
                      </TooltipContent>
                    )}
                  </Tooltip>
                ))}
              </div>
            </div>
          </div>
        </ScrollArea>
        <div className={`border-t px-4 py-3 flex items-center gap-3 mt-auto ${sidebarCollapsed ? "justify-center" : ""}`}>
          <div className={`flex items-center gap-2 cursor-pointer ${sidebarCollapsed ? "justify-center w-full" : ""}`}
            onClick={() => router.push("/settings")}
            tabIndex={0}
            aria-label="Profile"
          >
            <User className="h-6 w-6 text-muted-foreground" />
            {!sidebarCollapsed && (
              <div className="flex flex-col">
                <span className="font-medium text-sm">{user?.fullName || user?.email || "User"}</span>
                <span className="text-xs text-muted-foreground">Profile</span>
              </div>
            )}
          </div>
          {!sidebarCollapsed && (
            <Button size="sm" variant="outline" className="ml-auto" onClick={logout}>Logout</Button>
          )}
        </div>
      </div>
    </TooltipProvider>
  );
}