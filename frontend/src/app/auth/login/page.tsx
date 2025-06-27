"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Eye, EyeOff } from "lucide-react";
import { authApi } from "@/lib/api";
import { useAuth } from "@/lib/store";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const { setToken, setUser } = useAuth();

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      const data = await authApi.login(email, password);
      localStorage.setItem("token", data.access_token);
      setToken(data.access_token);
      setUser({ email, is_admin: data.user.is_admin });
      if (data.user.is_admin) {
        router.push("/admin");
      } else {
        router.push("/dashboard");
      }
    } catch (err) {
      setError((err as Error).message || "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden" style={{ fontFamily: 'Inter, sans-serif' }}>
      {/* Animated SVG background */}
      <svg className="absolute inset-0 w-full h-full -z-10" style={{ pointerEvents: 'none' }} aria-hidden fill="none">
        <defs>
          <radialGradient id="loginBg1" cx="80%" cy="0%" r="100%" gradientTransform="rotate(45)"><stop stopColor="#3A86FF" stopOpacity="0.10" /><stop offset="1" stopColor="#0a0a0a" stopOpacity="0" /></radialGradient>
        </defs>
        <rect width="100%" height="100%" fill="#0a0a0a" />
        <circle cx="80%" cy="10%" r="300" fill="url(#loginBg1)" />
        <circle cx="20%" cy="90%" r="200" fill="#06D6A018" />
      </svg>
      <div className="relative z-10 flex items-center justify-center min-h-screen w-full">
        <motion.div
          className="w-full max-w-md p-8 bg-white/10 dark:bg-slate-900/80 rounded-2xl shadow-2xl border border-white/10 backdrop-blur-xl"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="mb-8 text-center">
            <h1 className="text-4xl font-bold mb-2 text-center">Sign in</h1>
            <p className="text-lg text-center mb-8">Welcome back! Please enter your details.</p>
          </div>
          <form onSubmit={handleSubmit} className="space-y-6">
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
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  disabled={isLoading}
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-blue-400"
                  onClick={() => setShowPassword((v) => !v)}
                  tabIndex={-1}
                >
                  {showPassword ? (
                    <EyeOff className="w-5 h-5" />
                  ) : (
                    <Eye className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>
            {error && (
              <div className="text-red-500 text-sm text-center">{error}</div>
            )}
            <Button type="submit" disabled={isLoading} className="w-full font-semibold bg-gradient-to-r from-blue-600 to-teal-500 text-white shadow-lg rounded-xl">
              {isLoading ? "Signing in..." : "Sign In"}
            </Button>
          </form>
          <div className="mt-6 text-center text-sm text-slate-400">
            Don&apos;t have an account?{" "}
            <Link
              href="/auth/signup"
              className="text-blue-400 underline font-medium"
            >
              Sign up
            </Link>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
