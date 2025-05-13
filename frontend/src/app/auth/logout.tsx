"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function LogoutPage() {
  const router = useRouter();
  useEffect(() => {
    localStorage.removeItem("token");
    router.push("/auth/login");
  }, [router]);
  return <div className="text-center mt-16">Logging out...</div>;
}
