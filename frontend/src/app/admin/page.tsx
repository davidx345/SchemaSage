import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/store";

export default function AdminDashboard() {
  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!user) {
      router.replace("/login");
    } else if (!user.is_admin) {
      router.replace("/");
    }
  }, [user, router]);

  if (!user || !user.is_admin) return null;

  return (
    <main className="max-w-4xl mx-auto py-8">
      <h1 className="text-3xl font-bold mb-6">Admin Dashboard</h1>
      <div className="space-y-4">
        <div className="p-4 border rounded">Admin-only analytics, logs, and management features go here.</div>
        {/* Add more admin widgets as needed */}
      </div>
    </main>
  );
}
