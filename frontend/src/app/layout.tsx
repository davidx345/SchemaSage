import type { Metadata } from "next";
import { ThemeProvider } from "@/components/theme-provider";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { Toaster } from "sonner";
import { AIChatDialog } from "@/components/ai-chat-dialog";
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
        <ThemeProvider defaultTheme="system">
          <div className="relative flex min-h-screen">
            <Sidebar />
            <div className="flex-1">
              <Header />
              <main className="p-6">{children}</main>
            </div>
          </div>
          <AIChatDialog />
          <Toaster position="bottom-right" />
        </ThemeProvider>
      </body>
    </html>
  );
}
