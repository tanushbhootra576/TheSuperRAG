import os

os.makedirs('src/components/documents', exist_ok=True)
os.makedirs('src/components/chat', exist_ok=True)
os.makedirs('src/components/filters', exist_ok=True)

# P1.2 Chunking
chunking_config = """import React, { useState } from "react";
import { Brain, FileText, LayoutGrid, Network } from "lucide-react";

export function ChunkingConfig() {
  const [strategy, setStrategy] = useState("semantic");
  const [chunkSize, setChunkSize] = useState(512);
  const [overlap, setOverlap] = useState(10);

  const strategies = [
    { id: "semantic", name: "Semantic", icon: <Brain size={24}/>, desc: "Groups by meaning, not length", tag: "Essays, reports" },
    { id: "recursive", name: "Recursive", icon: <FileText size={24}/>, desc: "Splits at natural text boundaries", tag: "Code, Markdown" },
    { id: "sliding", name: "Sliding Window", icon: <LayoutGrid size={24}/>, desc: "Fixed-size with overlap", tag: "Dense PDFs" },
    { id: "parent", name: "Parent-Child", icon: <Network size={24}/>, desc: "Small search, big context", tag: "Long documents" },
  ];

  const showSliders = strategy === "recursive" || strategy === "sliding";

  return (
    <div className="bg-[var(--bg-primary)] border-4 border-[var(--border-strong)] p-4">
      <h3 className="font-black uppercase mb-4">Chunking Strategy</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {strategies.map(s => (
          <button 
            key={s.id}
            onClick={() => setStrategy(s.id)}
            className={`p-3 border-4 text-left transition-all ${strategy === s.id ? 'border-[var(--accent)] bg-[var(--accent-muted)]' : 'border-[var(--border-strong)] bg-[var(--bg-secondary)]'}`}
          >
            <div className="flex items-center gap-2 font-bold mb-1">{s.icon} {s.name}</div>
            <p className="text-xs text-[var(--text-muted)] mb-2 h-8">{s.desc}</p>
            <span className="text-[10px] bg-[var(--border-strong)] text-[var(--bg-primary)] px-1 uppercase font-bold">{s.tag}</span>
          </button>
        ))}
      </div>
      
      {showSliders && (
        <div className="space-y-4 border-t-2 border-[var(--border-strong)] pt-4">
          <div>
            <div className="flex justify-between font-bold text-sm mb-1">
              <span>Chunk Size (tokens)</span>
              <span>{chunkSize}</span>
            </div>
            <input type="range" min="128" max="2048" step="128" value={chunkSize} onChange={e => setChunkSize(Number(e.target.value))} className="w-full accent-[var(--accent)]" />
          </div>
          <div>
            <div className="flex justify-between font-bold text-sm mb-1">
              <span>Overlap (%)</span>
              <span>{overlap}%</span>
            </div>
            <input type="range" min="0" max="50" step="5" value={overlap} onChange={e => setOverlap(Number(e.target.value))} className="w-full accent-[var(--accent)]" />
          </div>
        </div>
      )}
    </div>
  );
}
"""

reindex_modal = """import React from "react";
import { AlertTriangle } from "lucide-react";
import { ChunkingConfig } from "./ChunkingConfig";

export function ReindexModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-[var(--bg-primary)] border-4 border-[var(--border-strong)] max-w-2xl w-full shadow-[var(--shadow-lg)] flex flex-col max-h-[90vh]">
        <div className="p-4 border-b-2 border-[var(--border-strong)] flex justify-between items-center bg-[var(--bg-secondary)]">
          <h2 className="font-black uppercase text-xl">Re-index Document</h2>
          <button onClick={onClose} className="font-bold">✕</button>
        </div>
        
        <div className="p-4 overflow-y-auto">
          <div className="bg-[var(--accent-muted)] border-l-4 border-[var(--accent)] p-3 mb-6 flex gap-3">
            <AlertTriangle className="text-[var(--accent)] shrink-0" />
            <p className="text-sm font-medium">This will replace all existing chunks for this document. It may take a few minutes.</p>
          </div>
          <ChunkingConfig />
        </div>
        
        <div className="p-4 border-t-2 border-[var(--border-strong)] bg-[var(--bg-secondary)] flex justify-end gap-2">
          <button onClick={onClose} className="bauhaus-btn">Cancel</button>
          <button className="bauhaus-btn primary">Confirm & Re-index</button>
        </div>
      </div>
    </div>
  );
}
"""

# P1.3 Query Controls
query_enhancements = """import React, { useState } from "react";
import { Zap, ChevronDown, ChevronUp } from "lucide-react";

export function QueryEnhancements() {
  const [expanded, setExpanded] = useState(false);
  const [hyde, setHyde] = useState(false);
  const [multi, setMulti] = useState(false);
  const [web, setWeb] = useState(false);

  const activeCount = [hyde, multi, web].filter(Boolean).length;

  return (
    <div className="mb-2">
      <button 
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-sm font-bold text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
      >
        <Zap size={16} className={activeCount > 0 ? "text-[var(--warning)]" : ""} /> 
        Search options {activeCount > 0 && `(${activeCount} active)`}
        {expanded ? <ChevronUp size={16}/> : <ChevronDown size={16}/>}
      </button>

      {expanded && (
        <div className="mt-2 border-2 border-[var(--border-strong)] bg-[var(--bg-secondary)] p-3 space-y-3 flex flex-col md:flex-row md:space-y-0 md:space-x-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={hyde} onChange={e => setHyde(e.target.checked)} className="w-4 h-4 accent-[var(--accent)]" />
            <span className="text-sm font-bold">HyDE</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={multi} onChange={e => setMulti(e.target.checked)} className="w-4 h-4 accent-[var(--accent)]" />
            <span className="text-sm font-bold">Multi-query</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={web} onChange={e => setWeb(e.target.checked)} className="w-4 h-4 accent-[var(--accent)]" />
            <span className="text-sm font-bold">Web Fallback</span>
          </label>
        </div>
      )}
    </div>
  );
}
"""

reasoning_trace = """import React, { useState } from "react";
import { Search, ChevronDown, ChevronUp } from "lucide-react";

export function ReasoningTrace() {
  const [expanded, setExpanded] = useState(false);
  
  return (
    <div className="mt-2 text-sm w-full">
      <button 
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 font-bold text-[var(--accent)] bg-[var(--accent-muted)] px-2 py-1 border border-[var(--accent)] rounded-sm"
      >
        <Search size={14}/> {expanded ? "Hide reasoning" : "Show reasoning steps (3 hops)"}
        {expanded ? <ChevronUp size={14}/> : <ChevronDown size={14}/>}
      </button>
      
      {expanded && (
        <div className="mt-2 pl-2 border-l-2 border-[var(--border-strong)] space-y-3 py-1">
          <div className="relative pl-4">
            <div className="absolute w-2 h-2 rounded-full bg-[var(--border-strong)] -left-[5px] top-1.5" />
            <p className="font-bold">Step 1 of 3</p>
            <p className="italic text-[var(--text-muted)]">"Who is the CEO of Acme Corp?"</p>
            <div className="flex gap-1 mt-1"><span className="text-xs bg-[var(--bg-secondary)] border border-[var(--border-strong)] px-1">Q3_Report.pdf</span></div>
          </div>
          <div className="relative pl-4">
            <div className="absolute w-2 h-2 rounded-full bg-[var(--border-strong)] -left-[5px] top-1.5" />
            <p className="font-bold">Step 2 of 3</p>
            <p className="italic text-[var(--text-muted)]">"What is John Smith's salary?"</p>
          </div>
          <div className="relative pl-4">
            <div className="absolute w-2 h-2 rounded-full bg-[var(--accent)] -left-[5px] top-1.5" />
            <p className="font-bold text-[var(--accent)]">Combined into final answer</p>
          </div>
        </div>
      )}
    </div>
  );
}
"""

# P1.4 Metadata filter
filter_panel = """import React from "react";

export function FilterPanel() {
  return (
    <div className="flex flex-col h-full bg-[var(--bg-secondary)] p-4 overflow-y-auto space-y-6">
      <div className="flex justify-between items-center border-b-2 border-[var(--border-strong)] pb-2">
        <h2 className="font-black uppercase tracking-wider">Filters</h2>
        <span className="text-xs bg-[var(--accent)] text-[#F4F4F4] font-bold px-2 py-0.5 rounded-full">3 active</span>
      </div>

      <div>
        <h3 className="font-bold mb-2">Search within</h3>
        <input type="text" placeholder="Find document..." className="w-full p-2 border-2 border-[var(--border-strong)] bg-[var(--bg-primary)] mb-2 text-sm" />
        <div className="space-y-1 max-h-32 overflow-y-auto">
          <label className="flex items-center gap-2"><input type="checkbox" defaultChecked className="accent-[var(--accent)]"/> <span className="text-sm truncate">Employee_Handbook_2024.pdf</span></label>
          <label className="flex items-center gap-2"><input type="checkbox" defaultChecked className="accent-[var(--accent)]"/> <span className="text-sm truncate">Q3_Financials.xlsx</span></label>
        </div>
      </div>

      <div>
        <h3 className="font-bold mb-2">File type</h3>
        <div className="flex flex-wrap gap-2">
          {['PDF', 'DOCX', 'Web', 'CSV'].map(type => (
            <button key={type} className="border-2 border-[var(--border-strong)] px-2 py-1 text-xs font-bold bg-[var(--bg-primary)] hover:bg-[var(--accent-muted)]">{type}</button>
          ))}
        </div>
      </div>

      <div>
        <h3 className="font-bold mb-2">Tags</h3>
        <div className="flex flex-wrap gap-1">
          {['HR', 'Finance', 'Engineering', '2024'].map(tag => (
            <span key={tag} className="border border-[var(--border-strong)] px-2 py-0.5 text-xs bg-white rounded-full cursor-pointer hover:border-[var(--accent)]">#{tag}</span>
          ))}
        </div>
      </div>
    </div>
  );
}
"""

filter_bar = """import React from "react";
import { Filter, X } from "lucide-react";

export function FilterBar({ onOpen }: { onOpen: () => void }) {
  return (
    <div className="flex items-center gap-2 overflow-x-auto p-2 border-b-2 border-[var(--border-strong)] bg-[var(--bg-primary)] hide-scrollbar">
      <button onClick={onOpen} className="flex items-center gap-1 shrink-0 font-bold text-sm bg-[var(--bg-secondary)] border-2 border-[var(--border-strong)] px-2 py-1">
        <Filter size={14}/> + Filters
      </button>
      
      {['Employee_Handbook...', 'Q3_Fin...', 'PDF'].map(f => (
        <div key={f} className="flex items-center gap-1 shrink-0 bg-[var(--accent)] text-[#F4F4F4] font-bold text-xs px-2 py-1 rounded-sm">
          {f} <X size={12} className="cursor-pointer"/>
        </div>
      ))}
    </div>
  );
}
"""

# P1.5 Versioning
version_history = """import React, { useState } from "react";
import { VersionDiffModal } from "./VersionDiffModal";
import { RollbackConfirm } from "./RollbackConfirm";

export function VersionHistory() {
  const [diffOpen, setDiffOpen] = useState(false);
  const [rollbackOpen, setRollbackOpen] = useState(false);

  return (
    <div className="p-4">
      <h2 className="font-black uppercase text-xl mb-6">Version History</h2>
      
      <div className="relative border-l-4 border-[var(--border-strong)] ml-4 space-y-8 pb-8">
        {/* v3 (Current) */}
        <div className="relative pl-6">
          <div className="absolute w-4 h-4 bg-[var(--accent)] border-2 border-[var(--bg-primary)] rounded-full -left-[10px] top-1" />
          <div className="flex items-center gap-2 mb-1">
            <span className="font-bold text-lg">v3</span>
            <span className="bg-[var(--accent)] text-[#F4F4F4] text-[10px] font-bold px-1 uppercase">Current</span>
            <span className="text-[var(--text-muted)] text-sm">Today, 2:30 PM</span>
          </div>
          <p className="text-sm font-medium mb-2">Uploaded by Sarah J.</p>
          <div className="flex gap-2 mb-3">
            <span className="bg-[var(--success)] text-white text-xs px-2 py-0.5 rounded-full font-bold">+12 chunks</span>
            <span className="bg-[var(--error)] text-white text-xs px-2 py-0.5 rounded-full font-bold">-2 chunks</span>
          </div>
          <div className="flex gap-2">
            <button onClick={() => setDiffOpen(true)} className="text-sm font-bold underline">View diff</button>
          </div>
        </div>

        {/* v2 */}
        <div className="relative pl-6">
          <div className="absolute w-4 h-4 bg-[var(--bg-secondary)] border-2 border-[var(--border-strong)] rounded-full -left-[10px] top-1" />
          <div className="flex items-center gap-2 mb-1">
            <span className="font-bold text-lg">v2</span>
            <span className="text-[var(--text-muted)] text-sm">Oct 12, 2024</span>
          </div>
          <p className="text-sm font-medium mb-3">Uploaded by Admin</p>
          <div className="flex gap-2">
            <button onClick={() => setDiffOpen(true)} className="text-sm font-bold underline">View diff</button>
            <button onClick={() => setRollbackOpen(true)} className="text-sm font-bold text-[var(--error)] underline">Roll back here</button>
          </div>
        </div>
      </div>

      <VersionDiffModal isOpen={diffOpen} onClose={() => setDiffOpen(false)} />
      <RollbackConfirm isOpen={rollbackOpen} onClose={() => setRollbackOpen(false)} />
    </div>
  );
}
"""

version_diff = """import React from "react";

export function VersionDiffModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-[60] bg-black/80 flex items-center justify-center p-2 md:p-8">
      <div className="bg-[var(--bg-primary)] w-full h-full md:h-[90vh] flex flex-col border-4 border-[var(--border-strong)]">
        <div className="p-4 border-b-4 border-[var(--border-strong)] flex justify-between items-center bg-[var(--bg-secondary)]">
          <h2 className="font-black uppercase text-xl">v2 → v3 Diff</h2>
          <button onClick={onClose} className="bauhaus-btn">Close</button>
        </div>
        <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
          <div className="flex-1 border-b-2 md:border-b-0 md:border-r-2 border-[var(--border-strong)] p-4 overflow-y-auto bg-[#ffeef0]">
            <h3 className="font-bold mb-4 text-[var(--error)]">Old Version (v2)</h3>
            <p className="line-through text-[var(--text-secondary)]">This paragraph was completely removed in v3 to update the facts.</p>
          </div>
          <div className="flex-1 p-4 overflow-y-auto bg-[#eefaf2]">
            <h3 className="font-bold mb-4 text-[var(--success)]">New Version (v3)</h3>
            <p className="text-[var(--success)] font-medium">This is the brand new paragraph added in v3.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
"""

rollback_confirm = """import React from "react";

export function RollbackConfirm({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-[60] bg-black/50 flex items-center justify-center p-4">
      <div className="bg-[var(--bg-primary)] border-4 border-[var(--border-strong)] max-w-md w-full p-6 shadow-[var(--shadow-lg)]">
        <h2 className="font-black uppercase text-xl text-[var(--error)] mb-2">Roll back to v2?</h2>
        <p className="font-medium mb-4">This will replace the current index. This action cannot be undone.</p>
        <div className="flex justify-end gap-2 mt-6">
          <button onClick={onClose} className="bauhaus-btn">Cancel</button>
          <button className="bauhaus-btn primary bg-[var(--error)]">Confirm Rollback</button>
        </div>
      </div>
    </div>
  );
}
"""

files = {
    'src/components/documents/ChunkingConfig.tsx': chunking_config,
    'src/components/documents/ReindexModal.tsx': reindex_modal,
    'src/components/chat/QueryEnhancements.tsx': query_enhancements,
    'src/components/chat/ReasoningTrace.tsx': reasoning_trace,
    'src/components/filters/FilterPanel.tsx': filter_panel,
    'src/components/filters/FilterBar.tsx': filter_bar,
    'src/components/documents/VersionHistory.tsx': version_history,
    'src/components/documents/VersionDiffModal.tsx': version_diff,
    'src/components/documents/RollbackConfirm.tsx': rollback_confirm,
}

for path, content in files.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
