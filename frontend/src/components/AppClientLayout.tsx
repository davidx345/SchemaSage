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

// Use a system font stack instead of Google Fonts for offline usage
const fontClassName = "font-sans";

export default function AppClientLayout({ children }: PropsWithChildren) {
  const pathname = usePathname();
  const isLandingPage = pathname === "/";
  const isAuthPage = pathname.startsWith("/auth");
  
  // Apply full-screen layout to all main interface pages
  const isMainInterfacePage = pathname === "/dashboard" || 
                             pathname === "/upload" || 
                             pathname === "/schema" || 
                             pathname === "/code" || 
                             pathname === "/settings" ||
                             pathname.startsWith("/upload") ||
                             pathname.startsWith("/schema") ||
                             pathname.startsWith("/code");

  return (
    <html lang="en" suppressHydrationWarning>
      <body className={fontClassName + " bg-background text-foreground transition-colors duration-300"}>
        <ThemeProvider attribute="class" defaultTheme="light" enableSystem={true}>
          <TooltipProvider>
            {isLandingPage || isAuthPage || isMainInterfacePage ? (
              <>
                {children}
                <Toaster position="bottom-right" />
              </>
            ) : (
              <div className="relative flex min-h-screen bg-background">
                <Sidebar />
                <div className="flex-1">
                  <Header />
                  <main className="p-6">
                    <ErrorBoundary>{children}</ErrorBoundary>
                  </main>
                </div>
              </div>
            )}
            <AIChatDialog />
            <Notifications />
          </TooltipProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
