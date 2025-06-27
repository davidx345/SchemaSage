"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authApi } from "@/lib/api";
import { motion } from "framer-motion";

export default function SignupPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      await authApi.signup(email, password, fullName);
      router.push("/auth/login");
    } catch (err) {
      setError((err as Error).message || "Signup failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen relative overflow-hidden" style={{ fontFamily: 'Inter, sans-serif' }}>
      {/* Animated SVG background */}
      <svg className="absolute inset-0 w-full h-full -z-10" style={{ pointerEvents: 'none' }} aria-hidden fill="none">
        <defs>
          <radialGradient id="signupBg1" cx="80%" cy="0%" r="100%" gradientTransform="rotate(45)"><stop stopColor="#3A86FF" stopOpacity="0.10" /><stop offset="1" stopColor="#0a0a0a" stopOpacity="0" /></radialGradient>
        </defs>
        <rect width="100%" height="100%" fill="#0a0a0a" />
        <circle cx="80%" cy="10%" r="300" fill="url(#signupBg1)" />
        <circle cx="20%" cy="90%" r="200" fill="#06D6A018" />
      </svg>
      {/* Glassmorphic card */}
      <motion.div
        className="relative z-10 w-full max-w-md p-8 bg-white/10 dark:bg-slate-900/80 rounded-2xl shadow-2xl border border-white/10 backdrop-blur-xl"
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div className="text-center mb-8">
          <h1 className="text-3xl font-extrabold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent mb-1">Create your account</h1>
          <p className="text-slate-400 dark:text-slate-400">Join SchemaSage today</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="fullName">Full Name (optional)</Label>
            <Input
              id="fullName"
              type="text"
              placeholder="Your Name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              disabled={isLoading}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="you@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              disabled={isLoading}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="Your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="new-password"
              disabled={isLoading}
            />
          </div>
          {error && (
            <div className="text-red-500 text-sm text-center">{error}</div>
          )}
          <Button
            type="submit"
            disabled={isLoading}
            className="w-full font-semibold bg-gradient-to-r from-blue-600 to-teal-500 text-white shadow-lg rounded-xl"
          >
            {isLoading ? "Signing up..." : "Sign Up"}
          </Button>
        </form>
        <div className="mt-6 text-center text-sm text-slate-400">
          Already have an account?{" "}
          <Link
            href="/auth/login"
            className="text-blue-400 underline font-medium"
          >
            Sign in
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
