import os

appshell = """import React from "react";
import { useSidebarStore } from "@/store/useSidebarStore";
import { useBreakpoint } from "@/hooks/useBreakpoint";
import { Menu, X } from "lucide-react";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { isMobile } = useBreakpoint();
  const { isOpen, isCollapsed, toggleMobile, toggleCollapse } = useSidebarStore();

  const sidebarWidth = isCollapsed ? "w-16" : "w-60";

  return (
    <div className="flex h-screen w-full bg-[var(--bg-primary)] overflow-hidden">
      {/* Mobile Top Bar */}
      {isMobile && (
        <div className="fixed top-0 left-0 right-0 h-14 bg-[var(--bg-secondary)] border-b-2 border-[var(--border-strong)] flex items-center px-4 z-50">
          <button onClick={toggleMobile} className="p-2 -ml-2">
            <Menu size={24} />
          </button>
          <h1 className="font-black uppercase ml-2 text-lg">TheSuperRAG</h1>
        </div>
      )}

      {/* Sidebar Overlay (Mobile) */}
      {isMobile && isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40"
          onClick={toggleMobile}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed md:static inset-y-0 left-0 z-50
        ${isMobile ? (isOpen ? "translate-x-0 w-64" : "-translate-x-full w-64") : sidebarWidth}
        transition-all duration-300 ease-in-out
        bg-[var(--bg-secondary)] border-r-2 border-[var(--border-strong)]
        flex flex-col
      `}>
        {/* Sidebar Header */}
        <div className="h-14 flex items-center justify-between px-4 border-b-2 border-[var(--border-strong)] shrink-0">
          {(!isCollapsed || isMobile) && <span className="font-black uppercase tracking-wider">TheSuperRAG</span>}
          {isMobile ? (
            <button onClick={toggleMobile}><X size={20} /></button>
          ) : (
            <button onClick={toggleCollapse} className="text-[var(--text-muted)] hover:text-[var(--text-primary)]">
              <Menu size={20} />
            </button>
          )}
        </div>
        {/* Sidebar Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {/* Mock Nav items */}
          <div className="h-10 bg-[var(--bg-primary)] border-2 border-[var(--border-strong)] flex items-center px-2 font-bold cursor-pointer hover:bg-[var(--accent)] hover:text-[#F4F4F4]">Chat</div>
          <div className="h-10 bg-[var(--bg-primary)] border-2 border-[var(--border-strong)] flex items-center px-2 font-bold cursor-pointer hover:bg-[var(--accent)] hover:text-[#F4F4F4]">Docs</div>
        </div>
      </aside>

      {/* Main Content */}
      <main className={`flex-1 flex flex-col min-w-0 ${isMobile ? "mt-14" : ""} h-[calc(100vh - ${isMobile ? '3.5rem' : '0px'})] overflow-auto`}>
        {children}
      </main>
    </div>
  );
}
"""

error_boundary = """"use client";
import React, { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-screen w-full bg-[var(--bg-primary)] text-[var(--text-primary)] p-4">
          <div className="border-4 border-[var(--border-strong)] p-8 max-w-md w-full bg-[var(--bg-secondary)] shadow-[var(--shadow-lg)]">
            <h1 className="text-2xl font-black uppercase mb-4 text-[var(--error)]">Something went wrong</h1>
            <p className="mb-6 font-medium">{this.state.error?.message || "An unexpected error occurred."}</p>
            <button 
              className="bauhaus-btn primary w-full"
              onClick={() => this.setState({ hasError: false, error: null })}
            >
              Try Again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
"""

with open('src/components/layout/AppShell.tsx', 'w') as f:
    f.write(appshell)

with open('src/components/layout/ErrorBoundary.tsx', 'w') as f:
    f.write(error_boundary)
