import type { Metadata } from "next";
import { ThemeProvider } from "@/components/theme-provider";
import AppClientLayout from "@/components/AppClientLayout";
import "./globals.css";

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
      <body>
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={true}>
          <AppClientLayout>{children}</AppClientLayout>
        </ThemeProvider>
      </body>
    </html>
  );
}
