import os

os.makedirs('src/components/upload', exist_ok=True)
os.makedirs('src/store', exist_ok=True)

store_upload = """import { create } from "zustand";

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
"""

upload_zone = """import React, { useCallback, useState } from "react";
import { UploadCloud, FileText, FileSpreadsheet, FileVideo } from "lucide-react";
import { useUploadStore } from "@/store/useUploadStore";

export function UploadZone() {
  const [isDragOver, setIsDragOver] = useState(false);
  const { addItem, updateItem } = useUploadStore();

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      Array.from(e.dataTransfer.files).forEach(file => {
        if (file.size > 200 * 1024 * 1024) {
          alert(`File ${file.name} is too large (> 200MB)`);
          return;
        }
        
        const id = Math.random().toString(36).substring(7);
        addItem({
          id,
          filename: file.name,
          type: file.type,
          progress: 0,
          status: "uploading"
        });
        
        // Mock upload progress
        let p = 0;
        const int = setInterval(() => {
          p += 20;
          updateItem(id, { progress: p });
          if (p >= 100) {
            clearInterval(int);
            updateItem(id, { status: "done" });
            setTimeout(() => {
              // Auto dismiss handled by store or component
            }, 3000);
          }
        }, 500);
      });
    }
  }, [addItem, updateItem]);

  return (
    <div 
      className={`border-4 border-dashed p-8 text-center transition-colors ${isDragOver ? 'border-[var(--accent)] bg-[var(--accent-muted)]' : 'border-[var(--border-strong)] bg-[var(--bg-secondary)]'}`}
      onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={handleDrop}
    >
      <UploadCloud size={48} className="mx-auto mb-4 text-[var(--text-muted)]" />
      <p className="font-bold text-lg mb-2">{isDragOver ? "Drop to upload" : "Drag files here or click to browse"}</p>
      <p className="text-[var(--text-muted)] text-sm">PDF, DOCX, TXT, CSV, Excel, PPT (Max 200MB)</p>
      <input type="file" className="hidden" id="file-upload" multiple onChange={(e) => {
        // Trigger manual upload same as drop
      }}/>
      <label htmlFor="file-upload" className="bauhaus-btn primary mt-4 inline-block cursor-pointer">
        Browse Files
      </label>
    </div>
  );
}
"""

url_ingester = """import React, { useState } from "react";
import { Youtube, Link as LinkIcon, File } from "lucide-react";

export function URLIngester() {
  const [tab, setTab] = useState<"files"|"youtube"|"web">("files");
  const [url, setUrl] = useState("");

  return (
    <div className="border-4 border-[var(--border-strong)] bg-[var(--bg-primary)] p-4">
      <div className="flex gap-2 mb-4 border-b-2 border-[var(--border-strong)] pb-2">
        <button onClick={() => setTab("files")} className={`flex items-center gap-2 px-3 py-1 font-bold uppercase ${tab==='files' ? 'bg-[var(--accent)] text-[#F4F4F4]' : 'bg-[var(--bg-secondary)]'}`}><File size={16}/> Files</button>
        <button onClick={() => setTab("youtube")} className={`flex items-center gap-2 px-3 py-1 font-bold uppercase ${tab==='youtube' ? 'bg-[var(--accent)] text-[#F4F4F4]' : 'bg-[var(--bg-secondary)]'}`}><Youtube size={16}/> YouTube</button>
        <button onClick={() => setTab("web")} className={`flex items-center gap-2 px-3 py-1 font-bold uppercase ${tab==='web' ? 'bg-[var(--accent)] text-[#F4F4F4]' : 'bg-[var(--bg-secondary)]'}`}><LinkIcon size={16}/> Web URL</button>
      </div>

      {tab === "files" && (
        <p className="text-[var(--text-muted)]">Use the upload zone above.</p>
      )}

      {tab === "youtube" && (
        <div className="flex flex-col gap-4">
          <input 
            type="text" 
            placeholder="Paste YouTube URL..." 
            className="w-full p-2 border-2 border-[var(--border-strong)] bg-[var(--bg-secondary)]"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
          {url && (
            <div className="border-2 border-[var(--border-strong)] p-2 flex gap-4">
              <div className="w-32 h-20 bg-[var(--bg-secondary)] flex items-center justify-center">Thumbnail</div>
              <div>
                <h4 className="font-bold">Video Title Preview</h4>
                <p className="text-sm text-[var(--text-muted)]">12:34</p>
                <button className="bauhaus-btn primary text-xs mt-2">Ingest Transcript</button>
              </div>
            </div>
          )}
        </div>
      )}

      {tab === "web" && (
        <div className="flex flex-col gap-4">
          <textarea 
            placeholder="Paste Web URLs (one per line)..." 
            className="w-full p-2 border-2 border-[var(--border-strong)] bg-[var(--bg-secondary)] min-h-[100px]"
          />
          <button className="bauhaus-btn">Fetch & Preview</button>
        </div>
      )}
    </div>
  );
}
"""

upload_queue = """import React from "react";
import { useUploadStore } from "@/store/useUploadStore";
import { X, CheckCircle, Loader2, AlertTriangle } from "lucide-react";

export function UploadQueue() {
  const { items, removeItem } = useUploadStore();

  if (items.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 w-80 bg-[var(--bg-primary)] border-4 border-[var(--border-strong)] shadow-[var(--shadow-lg)] z-50">
      <div className="bg-[var(--border-strong)] text-[var(--bg-primary)] px-3 py-2 font-bold uppercase text-sm flex justify-between items-center">
        <span>Upload Queue ({items.length})</span>
      </div>
      <div className="max-h-60 overflow-y-auto p-2 space-y-2">
        {items.map((item) => (
          <div key={item.id} className="border-2 border-[var(--border-strong)] p-2 bg-[var(--bg-secondary)] relative">
            <div className="flex justify-between items-start mb-2">
              <span className="font-bold text-sm truncate pr-6">{item.filename}</span>
              <button onClick={() => removeItem(item.id)} className="absolute top-2 right-2 text-[var(--text-muted)] hover:text-[var(--error)]">
                <X size={16} />
              </button>
            </div>
            
            <div className="h-2 w-full bg-[var(--bg-primary)] border border-[var(--border-strong)] relative overflow-hidden">
              <div 
                className={`absolute top-0 left-0 bottom-0 transition-all ${item.status === 'error' ? 'bg-[var(--error)]' : item.status === 'done' ? 'bg-[var(--success)]' : 'bg-[var(--accent)]'}`}
                style={{ width: `${item.progress}%` }}
              />
            </div>
            
            <div className="flex items-center gap-1 mt-1 text-xs font-medium">
              {item.status === 'uploading' && <><Loader2 size={12} className="animate-spin text-[var(--accent)]"/> Uploading {item.progress}%</>}
              {item.status === 'done' && <><CheckCircle size={12} className="text-[var(--success)]"/> Complete</>}
              {item.status === 'error' && <><AlertTriangle size={12} className="text-[var(--error)]"/> {item.errorMessage || "Error"}</>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
"""

with open('src/store/useUploadStore.ts', 'w') as f: f.write(store_upload)
with open('src/components/upload/UploadZone.tsx', 'w') as f: f.write(upload_zone)
with open('src/components/upload/URLIngester.tsx', 'w') as f: f.write(url_ingester)
with open('src/components/upload/UploadQueue.tsx', 'w') as f: f.write(upload_queue)
