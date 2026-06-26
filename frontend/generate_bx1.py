import os

os.makedirs('src/components/nav', exist_ok=True)

mobile_bottom_nav = """import React from "react";
import { MessageSquare, FileText, Search, BarChart2, Settings } from "lucide-react";

export function MobileBottomNav({ activeTab = "chat" }: { activeTab?: string }) {
  const tabs = [
    { id: "chat", label: "Chat", icon: <MessageSquare size={20} />, badge: true },
    { id: "docs", label: "Docs", icon: <FileText size={20} />, badge: false },
    { id: "search", label: "Search", icon: <Search size={20} />, badge: false },
    { id: "dashboard", label: "Dashboard", icon: <BarChart2 size={20} />, badge: false },
    { id: "settings", label: "Settings", icon: <Settings size={20} />, badge: false },
  ];

  const handleTap = () => {
    if (typeof navigator !== "undefined" && navigator.vibrate) {
      navigator.vibrate(10);
    }
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-[var(--bg-secondary)] border-t-2 border-[var(--border-strong)] pb-[env(safe-area-inset-bottom)] z-40">
      <div className="flex justify-between px-2 h-16">
        {tabs.map((t) => {
          const isActive = activeTab === t.id;
          return (
            <button 
              key={t.id}
              onClick={handleTap}
              className={`flex-1 flex flex-col items-center justify-center relative transition-colors ${isActive ? 'text-[var(--accent)]' : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'}`}
            >
              <div className="relative">
                {t.icon}
                {t.badge && <div className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-[var(--error)] rounded-full border border-[var(--bg-secondary)]" />}
              </div>
              {isActive && <span className="text-[10px] font-bold mt-1 uppercase tracking-wide">{t.label}</span>}
              {isActive && <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-8 h-1 bg-[var(--accent)]" />}
            </button>
          );
        })}
      </div>
    </div>
  );
}
"""

mobile_top_bar = """import React from "react";
import { Menu, Search, Settings } from "lucide-react";
import { useSidebarStore } from "@/store/useSidebarStore";

export function MobileTopBar({ title = "TheSuperRAG" }: { title?: string }) {
  const { toggleMobile } = useSidebarStore();

  return (
    <div className="fixed top-0 left-0 right-0 h-[calc(56px+env(safe-area-inset-top))] pt-[env(safe-area-inset-top)] z-40 bg-[var(--bg-primary)]/80 backdrop-blur-md border-b-2 border-[var(--border-strong)]">
      <div className="flex h-[56px] items-center justify-between px-4">
        <div className="flex items-center gap-3">
          <button onClick={toggleMobile} className="text-[var(--text-primary)] -ml-2 p-2">
            <Menu size={24} />
          </button>
          <h1 className="font-black uppercase tracking-wider text-lg truncate">{title}</h1>
        </div>
        <div className="flex items-center gap-2">
          <button className="p-2 text-[var(--text-primary)]">
            <Search size={20} />
          </button>
          <button className="p-2 text-[var(--text-primary)]">
            <Settings size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}
"""

sidebar_drawer = """import React, { useEffect, useState } from "react";
import { useSidebarStore } from "@/store/useSidebarStore";
import { X, LogOut, Settings } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export function SidebarDrawer() {
  const { isOpen, toggleMobile } = useSidebarStore();
  const [touchStart, setTouchStart] = useState<number | null>(null);

  const handleTouchStart = (e: React.TouchEvent) => setTouchStart(e.targetTouches[0].clientX);
  const handleTouchMove = (e: React.TouchEvent) => {
    if (!touchStart) return;
    const currentTouch = e.targetTouches[0].clientX;
    const diff = touchStart - currentTouch;
    if (diff > 80) toggleMobile();
  };

  useEffect(() => {
    if (isOpen) document.body.style.overflow = "hidden";
    else document.body.style.overflow = "unset";
    return () => { document.body.style.overflow = "unset"; };
  }, [isOpen]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.5 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black z-40"
            onClick={toggleMobile}
          />
          <motion.div
            initial={{ x: "-100%" }}
            animate={{ x: 0 }}
            exit={{ x: "-100%" }}
            transition={{ type: "tween", duration: 0.3 }}
            onTouchStart={handleTouchStart}
            onTouchMove={handleTouchMove}
            className="fixed top-0 left-0 bottom-0 w-[280px] bg-[var(--bg-secondary)] border-r-2 border-[var(--border-strong)] z-50 flex flex-col pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)]"
          >
            <div className="h-16 flex items-center justify-between px-4 border-b-2 border-[var(--border-strong)] shrink-0 bg-[var(--bg-primary)]">
              <span className="font-black uppercase tracking-wider text-lg">TheSuperRAG</span>
              <button onClick={toggleMobile}><X size={24} /></button>
            </div>
            
            <div className="p-4 border-b-2 border-[var(--border-strong)] flex items-center gap-3">
              <div className="w-10 h-10 bg-[var(--accent)] rounded-full flex items-center justify-center text-[#F4F4F4] font-bold">JD</div>
              <div>
                <p className="font-bold text-sm">John Doe</p>
                <p className="text-xs text-[var(--text-muted)]">Engineering Team</p>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-2">
              <div className="h-12 bg-[var(--bg-primary)] border-2 border-[var(--border-strong)] flex items-center px-4 font-bold uppercase text-sm">Chats</div>
              <div className="h-12 bg-[var(--bg-primary)] border-2 border-[var(--border-strong)] flex items-center px-4 font-bold uppercase text-sm">Documents</div>
              <div className="h-12 bg-[var(--bg-primary)] border-2 border-[var(--border-strong)] flex items-center px-4 font-bold uppercase text-sm">Integrations</div>
            </div>

            <div className="p-4 border-t-2 border-[var(--border-strong)] space-y-2">
              <button className="flex items-center gap-3 w-full p-2 font-bold hover:bg-[var(--bg-primary)]">
                <Settings size={20} /> Settings
              </button>
              <button className="flex items-center gap-3 w-full p-2 font-bold text-[var(--error)] hover:bg-[var(--bg-primary)]">
                <LogOut size={20} /> Sign Out
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
"""

command_palette = """import React, { useState, useEffect } from "react";
import { Search, FileText, Settings, MessageSquare, X } from "lucide-react";

export function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      }
      if (e.key === "Escape") setIsOpen(false);
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[10vh] bg-black/50 px-4">
      <div className="w-full max-w-2xl bg-[var(--bg-primary)] border-4 border-[var(--border-strong)] shadow-[var(--shadow-lg)] flex flex-col overflow-hidden">
        <div className="flex items-center p-4 border-b-2 border-[var(--border-strong)] bg-[var(--bg-secondary)]">
          <Search size={24} className="text-[var(--text-muted)]" />
          <input 
            type="text" 
            autoFocus 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search documents, chats, settings..." 
            className="flex-1 bg-transparent border-none outline-none px-4 font-bold text-lg text-[var(--text-primary)]"
          />
          <button onClick={() => setIsOpen(false)} className="text-[var(--text-muted)] bg-transparent">
            <X size={24} />
          </button>
        </div>
        
        <div className="max-h-[60vh] overflow-y-auto">
          <div className="p-2">
            <div className="px-3 py-1 text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">Recent Documents</div>
            <button className="w-full flex items-center gap-3 p-3 text-left hover:bg-[var(--accent)] hover:text-[#F4F4F4] group transition-colors">
              <FileText size={18} className="text-[var(--accent)] group-hover:text-[#F4F4F4]" />
              <span className="font-bold text-sm">Q3_Financial_Report.pdf</span>
            </button>
            <button className="w-full flex items-center gap-3 p-3 text-left hover:bg-[var(--accent)] hover:text-[#F4F4F4] group transition-colors">
              <FileText size={18} className="text-[var(--accent)] group-hover:text-[#F4F4F4]" />
              <span className="font-bold text-sm">Employee_Handbook_2024.docx</span>
            </button>
          </div>
          
          <div className="p-2 border-t-2 border-[var(--border-strong)]">
            <div className="px-3 py-1 text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">Actions</div>
            <button className="w-full flex items-center gap-3 p-3 text-left hover:bg-[var(--accent)] hover:text-[#F4F4F4] group transition-colors">
              <MessageSquare size={18} className="text-[var(--text-muted)] group-hover:text-[#F4F4F4]" />
              <span className="font-bold text-sm">New Chat</span>
            </button>
            <button className="w-full flex items-center gap-3 p-3 text-left hover:bg-[var(--accent)] hover:text-[#F4F4F4] group transition-colors">
              <Settings size={18} className="text-[var(--text-muted)] group-hover:text-[#F4F4F4]" />
              <span className="font-bold text-sm">Settings</span>
            </button>
          </div>
        </div>
        <div className="bg-[var(--bg-secondary)] border-t-2 border-[var(--border-strong)] p-2 text-xs text-center text-[var(--text-muted)] font-bold">
          Use ↑↓ arrows to navigate, Enter to select, Esc to dismiss
        </div>
      </div>
    </div>
  );
}
"""

files = {
    'src/components/nav/MobileBottomNav.tsx': mobile_bottom_nav,
    'src/components/nav/MobileTopBar.tsx': mobile_top_bar,
    'src/components/nav/SidebarDrawer.tsx': sidebar_drawer,
    'src/components/nav/CommandPalette.tsx': command_palette,
}

for path, content in files.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
