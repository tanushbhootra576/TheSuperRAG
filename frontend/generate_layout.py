import os

os.makedirs('src/components/layout', exist_ok=True)
os.makedirs('src/hooks', exist_ok=True)
os.makedirs('src/lib', exist_ok=True)
os.makedirs('src/store', exist_ok=True)
os.makedirs('src/components/ui', exist_ok=True)
os.makedirs('src/providers', exist_ok=True)

hooks_media = """import { useState, useEffect } from "react";

export function useMediaQuery(query: string) {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia(query);
    setMatches(mediaQuery.matches);
    const handler = (event: MediaQueryListEvent) => setMatches(event.matches);
    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, [query]);

  return matches;
}
"""

hooks_breakpoint = """import { useMediaQuery } from "./useMediaQuery";

export function useBreakpoint() {
  const isMobile = useMediaQuery("(max-width: 767px)");
  const isTablet = useMediaQuery("(min-width: 768px) and (max-width: 1023px)");
  const isDesktop = useMediaQuery("(min-width: 1024px)");

  return { isMobile, isTablet, isDesktop };
}
"""

hooks_safearea = """import { useState, useEffect } from "react";

export function useSafeArea() {
  const [safeArea, setSafeArea] = useState({ top: 0, bottom: 0, left: 0, right: 0 });

  useEffect(() => {
    const getSafeArea = () => {
      const computedStyle = getComputedStyle(document.documentElement);
      return {
        top: parseInt(computedStyle.getPropertyValue("env(safe-area-inset-top)")) || 0,
        bottom: parseInt(computedStyle.getPropertyValue("env(safe-area-inset-bottom)")) || 0,
        left: parseInt(computedStyle.getPropertyValue("env(safe-area-inset-left)")) || 0,
        right: parseInt(computedStyle.getPropertyValue("env(safe-area-inset-right)")) || 0,
      };
    };
    setSafeArea(getSafeArea());
  }, []);

  return safeArea;
}
"""

store_sidebar = """import { create } from "zustand";

interface SidebarState {
  isOpen: boolean;
  isCollapsed: boolean;
  toggleMobile: () => void;
  toggleCollapse: () => void;
}

export const useSidebarStore = create<SidebarState>((set) => ({
  isOpen: false,
  isCollapsed: false,
  toggleMobile: () => set((state) => ({ isOpen: !state.isOpen })),
  toggleCollapse: () => set((state) => ({ isCollapsed: !state.isCollapsed })),
}));
"""

lib_motion = """export const fadeIn = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
};

export const slideUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: 20 },
};

export const slideInLeft = {
  initial: { opacity: 0, x: -20 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -20 },
};

export const staggerChildren = {
  animate: { transition: { staggerChildren: 0.1 } },
};
"""

provider_theme = """"use client";
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
"""

ui_theme_toggle = """"use client";
import { useTheme } from "@/providers/ThemeProvider";
import { Sun, Moon, Laptop } from "lucide-react";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="flex items-center gap-1 border-2 border-[var(--border-strong)] p-1 bg-[var(--bg-secondary)]">
      <button onClick={() => setTheme("light")} className={`p-1 ${theme === 'light' ? 'bg-[var(--accent)] text-[#F4F4F4]' : 'text-[var(--text-muted)]'}`}>
        <Sun size={18} />
      </button>
      <button onClick={() => setTheme("system")} className={`p-1 ${theme === 'system' ? 'bg-[var(--accent)] text-[#F4F4F4]' : 'text-[var(--text-muted)]'}`}>
        <Laptop size={18} />
      </button>
      <button onClick={() => setTheme("dark")} className={`p-1 ${theme === 'dark' ? 'bg-[var(--accent)] text-[#F4F4F4]' : 'text-[var(--text-muted)]'}`}>
        <Moon size={18} />
      </button>
    </div>
  );
}
"""

layout_page_container = """import React from "react";

export function PageContainer({ children, className = "" }: { children: React.ReactNode, className?: string }) {
  return (
    <div className={`max-w-[1200px] mx-auto px-[var(--spacing-page-x-mobile)] md:px-[var(--spacing-page-x-tablet)] lg:px-[var(--spacing-page-x-desktop)] w-full ${className}`}>
      {children}
    </div>
  );
}
"""

layout_two_column = """import React from "react";

export function TwoColumn({ left, right, leftWidth = "w-64" }: { left: React.ReactNode; right: React.ReactNode; leftWidth?: string }) {
  return (
    <div className="flex flex-col md:flex-row w-full gap-4 h-full">
      <div className={`md:${leftWidth} flex-shrink-0 border-b-2 md:border-b-0 md:border-r-2 border-[var(--border-strong)]`}>
        {left}
      </div>
      <div className="flex-1 min-w-0 h-full">
        {right}
      </div>
    </div>
  );
}
"""

layout_split_pane = """import React, { useState } from "react";
import { useBreakpoint } from "@/hooks/useBreakpoint";

export function SplitPane({ left, right }: { left: React.ReactNode; right: React.ReactNode }) {
  const { isMobile } = useBreakpoint();
  const [activeTab, setActiveTab] = useState<"left"|"right">("left");

  if (isMobile) {
    return (
      <div className="flex flex-col h-full">
        <div className="flex border-b-2 border-[var(--border-strong)]">
          <button onClick={() => setActiveTab("left")} className={`flex-1 p-2 font-bold uppercase ${activeTab === 'left' ? 'bg-[var(--accent)] text-[#F4F4F4]' : 'bg-[var(--bg-secondary)]'}`}>Chat</button>
          <button onClick={() => setActiveTab("right")} className={`flex-1 p-2 font-bold uppercase ${activeTab === 'right' ? 'bg-[var(--accent)] text-[#F4F4F4]' : 'bg-[var(--bg-secondary)]'}`}>Source</button>
        </div>
        <div className="flex-1 overflow-auto">
          {activeTab === "left" ? left : right}
        </div>
      </div>
    );
  }

  return (
    <div className="flex w-full h-full border-2 border-[var(--border-strong)]">
      <div className="flex-1 min-w-[300px] border-r-2 border-[var(--border-strong)] overflow-auto">
        {left}
      </div>
      <div className="w-[480px] flex-shrink-0 bg-[var(--bg-secondary)] overflow-auto">
        {right}
      </div>
    </div>
  );
}
"""

files = {
    'src/hooks/useMediaQuery.ts': hooks_media,
    'src/hooks/useBreakpoint.ts': hooks_breakpoint,
    'src/hooks/useSafeArea.ts': hooks_safearea,
    'src/store/useSidebarStore.ts': store_sidebar,
    'src/lib/motion.ts': lib_motion,
    'src/providers/ThemeProvider.tsx': provider_theme,
    'src/components/ui/ThemeToggle.tsx': ui_theme_toggle,
    'src/components/layout/PageContainer.tsx': layout_page_container,
    'src/components/layout/TwoColumn.tsx': layout_two_column,
    'src/components/layout/SplitPane.tsx': layout_split_pane,
}

for path, content in files.items():
    with open(path, 'w') as f:
        f.write(content)
