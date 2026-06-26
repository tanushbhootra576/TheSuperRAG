"use client";
import React, { createContext, useContext, useEffect, useState } from "react";

type Theme = "light" | "dark" | "system";

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  isSystem: boolean;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>("system");
  const [isSystem, setIsSystem] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("theme") as Theme;
    if (stored) setTheme(stored);
  }, []);

  useEffect(() => {
    const root = window.document.documentElement;
    root.removeAttribute("data-theme");

    if (theme === "system") {
      setIsSystem(true);
      const systemTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
      if (systemTheme === "dark") root.setAttribute("data-theme", "dark");
    } else {
      setIsSystem(false);
      if (theme === "dark") root.setAttribute("data-theme", "dark");
    }
    localStorage.setItem("theme", theme);
  }, [theme]);

  return <ThemeContext.Provider value={{ theme, setTheme, isSystem }}>{children}</ThemeContext.Provider>;
}

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) throw new Error("useTheme must be used within ThemeProvider");
  return context;
};
