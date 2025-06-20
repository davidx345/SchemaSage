"use client";

import { ReactNode } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ModeToggle } from "@/components/mode-toggle";
import { 
  Sparkles, 
  Bell, 
  Search, 
  Home,
  Upload,
  Database,
  Code,
  Settings,
  HelpCircle,
  User
} from "lucide-react";
import Link from "next/link";

interface MainLayoutProps {
  children: ReactNode;
  title: string;
  subtitle?: string;
  currentPage: "dashboard" | "upload" | "schema" | "code" | "settings" | "help";
}

export function MainLayout({ children, title, subtitle, currentPage }: MainLayoutProps) {
  const navigationItems = [
    { id: "dashboard", label: "Dashboard", icon: Home, href: "/dashboard" },
    { id: "upload", label: "Upload Data", icon: Upload, href: "/upload" },
    { id: "schema", label: "Schema View", icon: Database, href: "/schema" },
    { id: "code", label: "Code Generation", icon: Code, href: "/code" },
    { id: "settings", label: "Settings", icon: Settings, href: "/settings" },
    { id: "help", label: "Help", icon: HelpCircle, href: "/help" },
  ];

  return (    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-slate-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0">
        <div className="absolute top-0 -left-4 w-72 h-72 bg-slate-300 dark:bg-slate-600 rounded-full mix-blend-multiply filter blur-xl opacity-10 dark:opacity-20 animate-blob"></div>
        <div className="absolute top-0 -right-4 w-72 h-72 bg-sky-200 dark:bg-sky-600 rounded-full mix-blend-multiply filter blur-xl opacity-15 dark:opacity-25 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-8 left-20 w-72 h-72 bg-slate-200 dark:bg-slate-700 rounded-full mix-blend-multiply filter blur-xl opacity-10 dark:opacity-20 animate-blob animation-delay-4000"></div>
        <div className="absolute bottom-0 right-20 w-72 h-72 bg-teal-200 dark:bg-teal-600 rounded-full mix-blend-multiply filter blur-xl opacity-15 dark:opacity-25 animate-blob animation-delay-6000"></div>
      </div>

      {/* Grid pattern overlay */}
      <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>

      <div className="relative z-10 flex min-h-screen">
        {/* Sidebar Navigation */}
        <motion.div
          initial={{ x: -100, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.6 }}
          className="w-72 bg-white/80 dark:bg-white/10 backdrop-blur-xl border-r border-slate-200 dark:border-white/20 p-6"
        >
          {/* Logo */}
          <div className="flex items-center space-x-3 mb-8">            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
              className="p-2 bg-gradient-to-r from-slate-600 to-sky-600 rounded-lg shadow-lg"
            >
              <Sparkles className="w-6 h-6 text-white" />
            </motion.div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 dark:text-white">SchemaSage</h1>
              <p className="text-xs text-slate-600 dark:text-gray-400">AI-Powered Schema Design</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="space-y-2">
            {navigationItems.map((item, index) => {
              const Icon = item.icon;
              const isActive = item.id === currentPage;
              
              return (
                <motion.div
                  key={item.id}
                  initial={{ x: -20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: index * 0.1, duration: 0.5 }}
                >
                  <Link href={item.href}>
                    <Button
                      variant={isActive ? "default" : "ghost"}                      className={`w-full justify-start h-12 rounded-xl transition-all duration-300 ${
                        isActive
                          ? "bg-gradient-to-r from-slate-600 to-sky-600 text-white shadow-lg hover:from-slate-700 hover:to-sky-700"
                          : "text-slate-700 dark:text-gray-300 hover:bg-white/50 dark:hover:bg-white/10 hover:text-slate-900 dark:hover:text-white"
                      }`}
                    >
                      <Icon className="w-5 h-5 mr-3" />
                      {item.label}
                    </Button>
                  </Link>
                </motion.div>
              );
            })}
          </nav>

          {/* User Section */}
          <div className="absolute bottom-6 left-6 right-6">
            <div className="bg-white/50 dark:bg-white/5 backdrop-blur-sm rounded-xl p-4 border border-slate-200 dark:border-white/10">
              <div className="flex items-center space-x-3">                <div className="w-10 h-10 bg-gradient-to-r from-slate-600 to-sky-600 rounded-full flex items-center justify-center">
                  <User className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-900 dark:text-white truncate">Developer</p>
                  <p className="text-xs text-slate-600 dark:text-gray-400 truncate">dev@schemasage.com</p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <motion.div
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.6 }}
            className="bg-white/80 dark:bg-white/10 backdrop-blur-xl border-b border-slate-200 dark:border-white/20 p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white">{title}</h1>
                {subtitle && (
                  <p className="text-slate-600 dark:text-gray-300 mt-1">{subtitle}</p>
                )}
              </div>
              
              <div className="flex items-center space-x-4">
                {/* Search Bar */}
                <div className="hidden md:flex items-center space-x-2">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      placeholder="Search..."
                      className="pl-10 w-64 bg-white/50 dark:bg-white/10 backdrop-blur-sm border border-slate-200 dark:border-white/20 text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-gray-400 focus:border-sky-500 focus:ring-sky-500/20 rounded-xl"
                    />
                  </div>
                </div>
                
                {/* Notifications */}
                <Button
                  variant="outline"
                  size="icon"
                  className="bg-white/50 dark:bg-white/10 backdrop-blur-sm border border-slate-200 dark:border-white/20 hover:bg-white/70 dark:hover:bg-white/20 rounded-xl"
                >
                  <Bell className="w-5 h-5 text-slate-600 dark:text-gray-300" />
                </Button>
                
                {/* Theme Toggle */}
                <ModeToggle />
              </div>
            </div>
          </motion.div>

          {/* Page Content */}
          <main className="flex-1 p-8">
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.2, duration: 0.6 }}
            >
              {children}
            </motion.div>
          </main>
        </div>
      </div>
    </div>
  );
}
