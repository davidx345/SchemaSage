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
  Boxes
} from "lucide-react";

const navigation = [
  { name: "Dashboard", href: "/", icon: Home },
  { name: "Upload Data", href: "/upload", icon: Upload },
  { name: "Schema View", href: "/schema", icon: Database },
  { name: "Code Generation", href: "/code", icon: Code2 },
];

const secondaryNavigation = [
  { name: "Settings", href: "/settings", icon: Settings },
  { name: "Help", href: "/help", icon: HelpCircle },
];

export function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const pathname = usePathname();

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