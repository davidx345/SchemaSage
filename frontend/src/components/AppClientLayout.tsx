"use client";

import { usePathname } from "next/navigation";
import type { PropsWithChildren } from "react";
import { ThemeProvider } from "@/components/theme-provider";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { Toaster } from "sonner";
import { AIChatDialog } from "@/components/ai-chat-dialog";
import { ErrorBoundary } from "@/components/error-boundary";
import { Notifications } from "@/components/notifications";
import { TooltipProvider } from "@/components/ui/tooltip";
import { useState } from "react";

// Use a system font stack instead of Google Fonts for offline usage
const fontClassName = "font-sans";

export default function AppClientLayout({ children }: PropsWithChildren) {
  const pathname = usePathname();
  const isLandingPage = pathname === "/";
  const isAuthPage = pathname.startsWith("/auth");
  const showSidebar = !isLandingPage && !isAuthPage;
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <>
      {/* No <html> or <body> tags here, let Next.js handle them */}
      {showSidebar ? (
        <>
          <Sidebar sidebarCollapsed={sidebarCollapsed} setSidebarCollapsed={setSidebarCollapsed} />
          <div className={sidebarCollapsed ? "min-h-screen md:ml-[72px]" : "min-h-screen md:ml-[260px]"}>
            <Header />
            <main className="p-6">
              <ErrorBoundary>{children}</ErrorBoundary>
            </main>
          </div>
        </>
      ) : (
        <>
          {children}
          <Toaster position="bottom-right" />
        </>
      )}
      <AIChatDialog />
      <Notifications />
    </>
  );
}
