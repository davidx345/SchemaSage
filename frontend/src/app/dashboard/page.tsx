'use client';
import Dashboard from "../../components/dashboard";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/store";

export default function DashboardPage() {
  const { token } = useAuth();
  const router = useRouter();
  
  // TEMPORARY DEVELOPMENT BYPASS - REMOVE IN PRODUCTION
  const isDevelopment = true; // Set to false in production
  
  useEffect(() => {
    // Skip auth check in development mode
    if (isDevelopment) {
      console.log("Development mode: Bypassing dashboard authentication");
      return;
    }
    
    // Original auth logic (commented out for development)
    if (!token) {
      router.replace("/auth/login");
    }
  }, [token, router, isDevelopment]);
  
  // Allow access in development mode
  if (!isDevelopment && !token) return null;
    // Return the dashboard component directly
  return <Dashboard />;
}
