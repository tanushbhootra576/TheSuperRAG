"use client";
import { create } from "zustand";

export interface UploadItem {
  id: string;
  filename: string;
  type: string;
  progress: number;
  status: "idle" | "uploading" | "done" | "error";
  errorMessage?: string;
}

interface UploadStore {
  items: UploadItem[];
  addItem: (item: UploadItem) => void;
  updateItem: (id: string, updates: Partial<UploadItem>) => void;
  removeItem: (id: string) => void;
  clearDone: () => void;
}

export const useUploadStore = create<UploadStore>((set) => ({
  items: [],
  addItem: (item) => set((state) => ({ items: [...state.items, item] })),
  updateItem: (id, updates) => set((state) => ({
    items: state.items.map(item => item.id === id ? { ...item, ...updates } : item)
  })),
  removeItem: (id) => set((state) => ({
    items: state.items.filter(item => item.id !== id)
  })),
  clearDone: () => set((state) => ({
    items: state.items.filter(item => item.status !== "done")
  }))
}));
