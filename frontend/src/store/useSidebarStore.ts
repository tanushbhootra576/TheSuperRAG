"use client";
import { create } from "zustand";

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
