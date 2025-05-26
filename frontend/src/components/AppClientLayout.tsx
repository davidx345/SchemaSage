
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

// Use a system font stack instead of Google Fonts for offline usage
const fontClassName = "font-sans";

export default function AppClientLayout({ children }: PropsWithChildren) {
  const pathname = usePathname();
  const isLandingPage = pathname === "/";
  const isAuthPage = pathname.startsWith("/auth");

  return (
    <html lang="en" suppressHydrationWarning>
      <body className={fontClassName}>
        <ThemeProvider attribute="class" defaultTheme="light" enableSystem={false}>
          {isLandingPage || isAuthPage ? (
            <>
              {children}
              <Toaster position="bottom-right" />
            </>
          ) : (
            <div className="relative flex min-h-screen">
              <Sidebar />
              <div className="flex-1">
                <Header />
                <main className="p-6">
                  <ErrorBoundary>{children}</ErrorBoundary>
                </main>
              </div>
            </div>
          )}
          {!isLandingPage && !isAuthPage && <AIChatDialog />}
          {!isLandingPage && !isAuthPage && <Notifications />}
          <Toaster position="bottom-right" />
        </ThemeProvider>
      </body>
    </html>
  );
}
