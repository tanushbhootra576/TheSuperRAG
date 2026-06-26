"use client";
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
