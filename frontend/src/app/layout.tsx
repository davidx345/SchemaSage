import type { Metadata } from "next";
import { ThemeProvider } from "@/components/theme-provider";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { Toaster } from "sonner";
import { AIChatDialog } from "@/components/ai-chat-dialog";
import { ErrorBoundary } from "@/components/error-boundary";
import { Notifications } from "@/components/notifications";
import "./globals.css";

// Use a system font stack instead of Google Fonts for offline usage
const fontClassName = "font-sans";

export const metadata: Metadata = {
  title: "SchemaSage",
  description: "Database Schema Design and Code Generation Tool",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={fontClassName}>
        <ThemeProvider attribute="class" defaultTheme="light" enableSystem={false}>
          <div className="relative flex min-h-screen">
            <Sidebar />
            <div className="flex-1">
              <Header />
              <main className="p-6">
                <ErrorBoundary>
                  {children}
                </ErrorBoundary>
              </main>
            </div>
          </div>
          <AIChatDialog />
          <Notifications />
          <Toaster position="bottom-right" />
        </ThemeProvider>
      </body>
    </html>
  );
}
