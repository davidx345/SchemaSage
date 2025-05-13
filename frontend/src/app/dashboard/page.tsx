import Dashboard from "../../components/dashboard";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/store";

export default function DashboardPage() {
  const { token } = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (!token) {
      router.replace("/auth/login");
    }
  }, [token, router]);
  if (!token) return null;
  return <Dashboard />;
}
