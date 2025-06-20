"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Eye, EyeOff, Sparkles, ArrowRight, Shield, Zap, Users, CheckCircle } from "lucide-react";

export default function RegisterPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    // Basic validation still in place
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    setIsLoading(true);

    // TEMPORARY DEVELOPMENT BYPASS - REMOVE IN PRODUCTION
    console.log("Development mode: Bypassing registration");
    await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate loading
    setIsLoading(false);
    router.push("/dashboard");
    return;

    // Original registration logic (commented out for development)
    /*
    try {
      const response = await api.post("/auth/register", {
        name,
        email,
        password,
      });

      if (response.data.access_token) {
        setToken(response.data.access_token);
        router.push("/dashboard");
      } else {
        setError("Registration failed: No access token received.");
      }
    } catch (err) {
      if (
        axios.isAxiosError(err) &&
        err.response &&
        err.response.data &&
        typeof err.response.data.detail === "string"
      ) {
        setError(err.response.data.detail);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unexpected error occurred during registration.");
      }
      console.error("Registration error:", err);
    } finally {
      setIsLoading(false);
    }
    */
  };

  return (    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0">
        <div className="absolute top-0 -left-4 w-72 h-72 bg-slate-600 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob"></div>
        <div className="absolute top-0 -right-4 w-72 h-72 bg-sky-600 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-2000"></div>        <div className="absolute -bottom-8 left-20 w-72 h-72 bg-slate-500 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-4000"></div>
        <div className="absolute bottom-0 right-20 w-72 h-72 bg-teal-500 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-6000"></div>
      </div>

      {/* Grid pattern overlay */}
      <div className="absolute inset-0 bg-grid-pattern opacity-10"></div>

      <div className="relative z-10 flex min-h-screen">
        {/* Left side - Branding */}
        <motion.div 
          initial={{ x: -100, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="hidden lg:flex lg:w-1/2 flex-col justify-center items-center p-12 text-white"
        >
          <motion.div 
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.6 }}
            className="text-center space-y-8"
          >
            <div className="flex items-center justify-center space-x-3 mb-8">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                className="p-3 bg-gradient-to-r from-slate-600 to-sky-600 rounded-xl"
              >
                <Sparkles className="w-8 h-8 text-white" />
              </motion.div>
              <motion.h1 
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.4, duration: 0.6 }}
                className="text-4xl font-bold bg-gradient-to-r from-white via-slate-200 to-sky-200 bg-clip-text text-transparent"
              >
                SchemaSage
              </motion.h1>
            </div>
            
            <motion.h2 
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.6, duration: 0.6 }}
              className="text-3xl font-bold mb-4"
            >
              Join the Revolution
            </motion.h2>
            
            <motion.p 
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.8, duration: 0.6 }}
              className="text-lg text-gray-300 max-w-md"
            >
              Start your journey with AI-powered schema generation. Transform your data into intelligent database designs in minutes, not hours.
            </motion.p>

            <motion.div 
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 1, duration: 0.6 }}
              className="grid grid-cols-2 gap-4 mt-12"
            >
              <div className="flex items-center space-x-2 text-sm text-gray-300">
                <Shield className="w-5 h-5 text-green-400" />
                <span>Secure & Private</span>
              </div>
              <div className="flex items-center space-x-2 text-sm text-gray-300">
                <Zap className="w-5 h-5 text-yellow-400" />
                <span>Lightning Fast</span>
              </div>
              <div className="flex items-center space-x-2 text-sm text-gray-300">
                <Sparkles className="w-5 h-5 text-blue-400" />
                <span>AI-Powered</span>
              </div>
              <div className="flex items-center space-x-2 text-sm text-gray-300">
                <Users className="w-5 h-5 text-teal-400" />
                <span>Team Friendly</span>
              </div>
            </motion.div>

            <motion.div 
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 1.2, duration: 0.6 }}
              className="mt-8 p-6 bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10"
            >
              <h3 className="text-lg font-semibold mb-3 text-teal-300">What&apos;s included:</h3>
              <div className="space-y-2 text-sm text-gray-300">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-400" />
                  <span>Unlimited schema generation</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-400" />
                  <span>Multi-format export (SQL, JSON, etc.)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-400" />
                  <span>AI-powered optimizations</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-400" />
                  <span>Real-time collaboration</span>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </motion.div>

        {/* Right side - Register form */}
        <motion.div 
          initial={{ x: 100, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="flex-1 flex items-center justify-center p-8"
        >
          <motion.div 
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.6 }}
            className="w-full max-w-md"
          >
            {/* Glass card */}
            <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-3xl p-8 shadow-2xl">
              <motion.div 
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.4, duration: 0.5 }}
                className="text-center mb-8"
              >
                <h2 className="text-3xl font-bold text-white mb-2">Create Account</h2>
                <p className="text-gray-300">Start your SchemaSage journey today</p>
              </motion.div>

              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mb-6 p-4 bg-red-500/20 border border-red-500/30 rounded-xl text-red-200 text-sm"
                >
                  {error}
                </motion.div>
              )}

              <form onSubmit={handleSubmit} className="space-y-6">
                <motion.div 
                  initial={{ x: -20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.5, duration: 0.5 }}
                  className="space-y-2"
                >
                  <Label htmlFor="name" className="text-white font-medium">
                    Full Name
                  </Label>
                  <Input
                    id="name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}                    required
                    disabled={isLoading}
                    className="bg-white/10 border-white/20 text-white placeholder:text-gray-400 focus:border-blue-400 focus:ring-blue-400/20 rounded-xl h-12"
                    placeholder="John Doe"
                  />
                </motion.div>

                <motion.div 
                  initial={{ x: -20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.6, duration: 0.5 }}
                  className="space-y-2"
                >
                  <Label htmlFor="email" className="text-white font-medium">
                    Email
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}                    required
                    disabled={isLoading}
                    className="bg-white/10 border-white/20 text-white placeholder:text-gray-400 focus:border-blue-400 focus:ring-blue-400/20 rounded-xl h-12"
                    placeholder="you@example.com"
                  />
                </motion.div>

                <motion.div 
                  initial={{ x: -20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.7, duration: 0.5 }}
                  className="space-y-2"
                >
                  <Label htmlFor="password" className="text-white font-medium">
                    Password
                  </Label>
                  <div className="relative">                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      disabled={isLoading}
                      className="bg-white/10 border-white/20 text-white placeholder:text-gray-400 focus:border-blue-400 focus:ring-blue-400/20 rounded-xl h-12 pr-12"
                      placeholder="••••••••"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                    >
                      {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </motion.div>

                <motion.div 
                  initial={{ x: -20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.8, duration: 0.5 }}
                  className="space-y-2"
                >
                  <Label htmlFor="confirmPassword" className="text-white font-medium">
                    Confirm Password
                  </Label>
                  <div className="relative">                    <Input
                      id="confirmPassword"
                      type={showConfirmPassword ? "text" : "password"}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                      disabled={isLoading}
                      className="bg-white/10 border-white/20 text-white placeholder:text-gray-400 focus:border-blue-400 focus:ring-blue-400/20 rounded-xl h-12 pr-12"
                      placeholder="••••••••"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                    >
                      {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </motion.div>

                <motion.div 
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.9, duration: 0.5 }}
                >
                  <Button
                    type="submit"
                    disabled={isLoading}
                    className="w-full bg-gradient-to-r from-slate-600 to-sky-600 hover:from-slate-700 hover:to-sky-700 text-white font-semibold rounded-xl h-12 transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98] shadow-lg hover:shadow-slate-500/25 group"
                  >
                    {isLoading ? (
                      <div className="flex items-center space-x-2">
                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                        <span>Creating account...</span>
                      </div>
                    ) : (
                      <div className="flex items-center space-x-2">
                        <span>Create Account</span>
                        <ArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-1" />
                      </div>
                    )}
                  </Button>
                </motion.div>

                <motion.div 
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 1, duration: 0.5 }}
                  className="text-center text-xs text-gray-400"
                >                  By creating an account, you agree to our{" "}
                  <Link href="/terms" className="text-blue-300 hover:text-blue-200 transition-colors">
                    Terms of Service
                  </Link>{" "}
                  and{" "}
                  <Link href="/privacy" className="text-blue-300 hover:text-blue-200 transition-colors">
                    Privacy Policy
                  </Link>
                </motion.div>
              </form>

              <motion.div 
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 1.1, duration: 0.5 }}
                className="mt-8 text-center"
              >
                <p className="text-gray-300">
                  Already have an account?{" "}                  <Link 
                    href="/auth/login" 
                    className="text-blue-300 hover:text-blue-200 transition-colors font-semibold"
                  >
                    Sign in
                  </Link>
                </p>
              </motion.div>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}
