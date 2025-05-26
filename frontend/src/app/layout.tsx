import type { Metadata } from "next";
import AppClientLayout from "@/components/AppClientLayout"; // Import the new client layout component
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
  return <AppClientLayout>{children}</AppClientLayout>;
}
