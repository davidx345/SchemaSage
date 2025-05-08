"use client";

import * as React from "react";
import { ThemeProvider as NextThemesProvider, useTheme } from "next-themes";
import { type ThemeProviderProps } from "next-themes";
import { useEffect, useState } from "react";
import { useStore } from "@/lib/store";

// Create a separate component to handle theme changes
function ThemeWatcher() {
  const { theme } = useTheme();
  const { toggleDarkMode } = useStore();

  // Update the store's darkMode setting when theme changes
  useEffect(() => {
    if (theme === 'dark' || theme === 'light') {
      const isDarkMode = theme === 'dark';
      if (useStore.getState().isDarkMode !== isDarkMode) {
        toggleDarkMode();
      }
    }
  }, [theme, toggleDarkMode]);

  return null;
}

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  const [mounted, setMounted] = useState(false);

  // Ensure component is mounted before accessing window
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <>{children}</>;
  }

  return (
    <NextThemesProvider defaultTheme="light" attribute="class" {...props}>
      <ThemeWatcher />
      {children}
    </NextThemesProvider>
  );
}

export { useTheme } from "next-themes";