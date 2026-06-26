import os

os.makedirs('src/components/admin', exist_ok=True)

# P3.1
role_manager = """import React from "react";
import { Shield, Check } from "lucide-react";

export function RoleManager() {
  const roles = [
    { name: "Admin", desc: "Full access", users: 2, color: "var(--error)" },
    { name: "Editor", desc: "Can manage documents", users: 5, color: "var(--warning)" },
    { name: "Viewer", desc: "Chat only", users: 24, color: "var(--success)" },
  ];

  return (
    <div className="bg-[var(--bg-primary)] border-4 border-[var(--border-strong)] p-4">
      <h2 className="font-black uppercase mb-4 text-xl flex items-center gap-2">
        <Shield size={24}/> Roles & Permissions
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {roles.map(r => (
          <div key={r.name} className="border-4 border-[var(--border-strong)] p-3 bg-[var(--bg-secondary)] relative overflow-hidden">
            <div className="absolute top-0 right-0 w-8 h-8 opacity-20" style={{ backgroundColor: r.color }} />
            <h3 className="font-black uppercase text-lg mb-1">{r.name}</h3>
            <p className="text-xs font-bold text-[var(--text-muted)] mb-4">{r.desc}</p>
            
            <div className="flex justify-between items-end border-t-2 border-[var(--border-strong)] pt-2">
              <span className="text-xs font-bold">{r.users} users</span>
              <button className="text-xs font-bold underline hover:text-[var(--accent)]">Edit</button>
            </div>
          </div>
        ))}
      </div>
      
      <button className="bauhaus-btn primary mt-4 text-sm">+ Create Custom Role</button>
    </div>
  );
}
"""

user_list = """import React from "react";
import { Search, MoreVertical } from "lucide-react";

export function UserList() {
  const users = [
    { id: 1, name: "Alice Johnson", email: "alice@acme.com", role: "Admin", status: "Active" },
    { id: 2, name: "Bob Smith", email: "bob@acme.com", role: "Editor", status: "Active" },
    { id: 3, name: "Charlie Davis", email: "charlie@acme.com", role: "Viewer", status: "Inactive" },
  ];

  return (
    <div className="bg-[var(--bg-primary)] border-4 border-[var(--border-strong)] mt-6">
      <div className="p-4 border-b-4 border-[var(--border-strong)] bg-[var(--bg-secondary)] flex justify-between items-center">
        <h2 className="font-black uppercase text-lg">Directory</h2>
        <div className="flex items-center gap-2 bg-[var(--bg-primary)] border-2 border-[var(--border-strong)] px-2">
          <Search size={16} className="text-[var(--text-muted)]" />
          <input type="text" placeholder="Search users..." className="bg-transparent outline-none border-none py-1 text-sm font-bold w-32 md:w-48" />
        </div>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="bg-[var(--bg-secondary)] border-b-2 border-[var(--border-strong)] uppercase text-xs font-bold">
              <th className="p-3">User</th>
              <th className="p-3">Role</th>
              <th className="p-3">Status</th>
              <th className="p-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id} className="border-b border-[var(--border-strong)] hover:bg-[var(--bg-secondary)]">
                <td className="p-3">
                  <div className="font-bold">{u.name}</div>
                  <div className="text-[10px] text-[var(--text-muted)]">{u.email}</div>
                </td>
                <td className="p-3"><span className="bg-[var(--bg-primary)] border border-[var(--border-strong)] px-2 py-0.5 text-xs font-bold">{u.role}</span></td>
                <td className="p-3">
                  <span className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase ${u.status === 'Active' ? 'text-[var(--success)]' : 'text-[var(--text-muted)]'}`}>
                    <div className={`w-2 h-2 rounded-full ${u.status === 'Active' ? 'bg-[var(--success)]' : 'bg-[var(--text-muted)]'}`} /> {u.status}
                  </span>
                </td>
                <td className="p-3 text-right"><button className="p-1 hover:bg-[var(--bg-primary)] border border-transparent hover:border-[var(--border-strong)]"><MoreVertical size={16}/></button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
"""

# P3.2
citation_badge = """import React from "react";

export function CitationBadge({ id, onClick }: { id: number, onClick: () => void }) {
  return (
    <sup 
      onClick={onClick}
      className="inline-flex items-center justify-center w-4 h-4 ml-0.5 rounded-full bg-[var(--accent)] text-[#F4F4F4] text-[9px] font-black cursor-pointer hover:scale-125 transition-transform"
    >
      {id}
    </sup>
  );
}
"""

source_preview_modal = """import React from "react";
import { FileText, ExternalLink, X } from "lucide-react";

export function SourcePreviewModal({ isOpen, onClose }: { isOpen: boolean, onClose: () => void }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[70] bg-black/50 flex items-center justify-center p-4">
      <div className="bg-[var(--bg-primary)] border-4 border-[var(--border-strong)] w-full max-w-lg shadow-[var(--shadow-lg)] flex flex-col max-h-[80vh]">
        <div className="p-3 border-b-2 border-[var(--border-strong)] bg-[var(--bg-secondary)] flex justify-between items-center">
          <div className="flex items-center gap-2 font-bold text-sm">
            <FileText size={16} className="text-[var(--accent)]" /> 
            Q3_Financial_Report.pdf
          </div>
          <button onClick={onClose}><X size={20}/></button>
        </div>
        
        <div className="p-4 overflow-y-auto bg-[#fffdf0]">
          <div className="flex justify-between items-center mb-2 border-b-2 border-[var(--border-strong)] pb-1">
            <span className="text-xs font-bold text-[var(--text-muted)] uppercase">Page 14 · Chunk #42</span>
            <span className="text-[10px] font-bold bg-[var(--success)] text-white px-1">94% Relevance</span>
          </div>
          
          <p className="font-serif text-sm leading-relaxed">
            <mark className="bg-[var(--warning)] text-black px-1">The CEO, John Smith, announced that</mark> the Q3 revenue exceeded expectations by 15%, reaching a total of $42.5 million. This growth was primarily driven by the enterprise software division...
          </p>
        </div>
        
        <div className="p-3 border-t-2 border-[var(--border-strong)] bg-[var(--bg-secondary)]">
          <button className="bauhaus-btn w-full flex justify-center items-center gap-2 text-sm">
            <ExternalLink size={16}/> View Full Document
          </button>
        </div>
      </div>
    </div>
  );
}
"""

# P3.3
follow_up_pills = """import React from "react";
import { Sparkles } from "lucide-react";

export function FollowUpPills() {
  const suggestions = [
    "What were Q2 revenues?",
    "Compare with last year",
    "Who leads enterprise division?"
  ];

  return (
    <div className="flex flex-wrap gap-2 mt-4">
      {suggestions.map((s, i) => (
        <button key={i} className="flex items-center gap-1 bg-[var(--bg-primary)] border-2 border-[var(--border-strong)] px-3 py-1.5 text-xs font-bold hover:bg-[var(--accent-muted)] hover:border-[var(--accent)] transition-colors">
          <Sparkles size={12} className="text-[var(--accent)]" /> {s}
        </button>
      ))}
    </div>
  );
}
"""

# P3.4
voice_recorder = """import React, { useState } from "react";
import { Mic, Square, Loader2 } from "lucide-react";

export function VoiceRecorder() {
  const [state, setState] = useState<"idle"|"recording"|"processing">("idle");
  const [seconds, setSeconds] = useState(0);

  // Note: Actual MediaRecorder logic goes here. Mocking for UI.
  const toggleRecord = () => {
    if (state === "idle") {
      setState("recording");
      // start timer
    } else if (state === "recording") {
      setState("processing");
      setTimeout(() => setState("idle"), 2000);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <button 
        onClick={toggleRecord}
        className={`w-12 h-12 flex items-center justify-center rounded-full border-4 border-[var(--border-strong)] shadow-[var(--shadow-sm)] transition-all ${state === 'recording' ? 'bg-[var(--error)] border-[var(--error)] animate-pulse' : state === 'processing' ? 'bg-[var(--warning)]' : 'bg-[var(--bg-secondary)] hover:bg-[var(--accent-muted)]'}`}
      >
        {state === "idle" && <Mic size={20} className="text-[var(--text-primary)]" />}
        {state === "recording" && <Square size={16} className="text-[#F4F4F4]" fill="currentColor" />}
        {state === "processing" && <Loader2 size={20} className="animate-spin text-black" />}
      </button>
      
      {state === "recording" && (
        <div className="font-mono text-sm font-bold text-[var(--error)] animate-pulse">00:0{seconds}</div>
      )}
      {state === "processing" && (
        <div className="text-xs font-bold uppercase text-[var(--warning)]">Transcribing...</div>
      )}
    </div>
  );
}
"""

audio_player = """import React, { useState } from "react";
import { Play, Pause, Volume2 } from "lucide-react";

export function AudioPlayer() {
  const [playing, setPlaying] = useState(false);
  
  return (
    <div className="flex items-center gap-3 bg-[var(--bg-secondary)] border-2 border-[var(--border-strong)] p-2 w-64 max-w-full">
      <button onClick={() => setPlaying(!playing)} className="w-8 h-8 bg-[var(--accent)] text-[#F4F4F4] flex items-center justify-center hover:bg-[var(--accent-hover)] shrink-0">
        {playing ? <Pause size={16} fill="currentColor"/> : <Play size={16} fill="currentColor" className="ml-1"/>}
      </button>
      <div className="flex-1">
        <div className="h-2 bg-[var(--bg-primary)] border border-[var(--border-strong)] w-full overflow-hidden">
          <div className="h-full bg-[var(--accent)] w-1/3" />
        </div>
      </div>
      <Volume2 size={16} className="text-[var(--text-muted)] shrink-0" />
    </div>
  );
}
"""

# P3.5
export_menu = """import React, { useState } from "react";
import { Download, FileText, FileCode, FileSpreadsheet, ChevronDown } from "lucide-react";

export function ExportMenu() {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative">
      <button onClick={() => setOpen(!open)} className="bauhaus-btn flex items-center gap-2 text-xs py-1 px-2">
        <Download size={14}/> Export <ChevronDown size={14}/>
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-40 bg-[var(--bg-primary)] border-4 border-[var(--border-strong)] shadow-[var(--shadow-md)] z-50 flex flex-col">
          <button className="flex items-center gap-2 px-3 py-2 text-sm font-bold hover:bg-[var(--accent)] hover:text-[#F4F4F4] text-left">
            <FileText size={14}/> PDF Document
          </button>
          <button className="flex items-center gap-2 px-3 py-2 text-sm font-bold hover:bg-[var(--accent)] hover:text-[#F4F4F4] text-left border-y-2 border-[var(--border-strong)]">
            <FileCode size={14}/> Markdown
          </button>
          <button className="flex items-center gap-2 px-3 py-2 text-sm font-bold hover:bg-[var(--accent)] hover:text-[#F4F4F4] text-left">
            <FileSpreadsheet size={14}/> CSV (Data only)
          </button>
        </div>
      )}
    </div>
  );
}
"""

share_dialog = """import React from "react";
import { Share2, Link, Copy, X } from "lucide-react";

export function ShareDialog({ isOpen, onClose }: { isOpen: boolean, onClose: () => void }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-[var(--bg-primary)] border-4 border-[var(--border-strong)] w-full max-w-sm shadow-[var(--shadow-lg)]">
        <div className="p-3 border-b-2 border-[var(--border-strong)] bg-[var(--bg-secondary)] flex justify-between items-center">
          <h2 className="font-black uppercase flex items-center gap-2"><Share2 size={18}/> Share Chat</h2>
          <button onClick={onClose}><X size={20}/></button>
        </div>
        
        <div className="p-4 space-y-4">
          <p className="text-sm font-medium">Create a public link to share this conversation. The link will expire in 7 days.</p>
          
          <div className="flex bg-[var(--bg-secondary)] border-2 border-[var(--border-strong)] p-1">
            <div className="flex-1 flex items-center gap-2 px-2 overflow-hidden text-[var(--text-muted)] text-sm">
              <Link size={14} className="shrink-0"/>
              <span className="truncate">https://thesuperrag.app/share/x8j92k</span>
            </div>
            <button className="bauhaus-btn primary py-1 px-3 text-xs shrink-0 flex items-center gap-1">
              <Copy size={12}/> Copy
            </button>
          </div>

          <label className="flex items-center gap-2 text-sm font-bold cursor-pointer">
            <input type="checkbox" className="accent-[var(--accent)] w-4 h-4" /> Include cited documents
          </label>
        </div>
      </div>
    </div>
  );
}
"""

files = {
    'src/components/admin/RoleManager.tsx': role_manager,
    'src/components/admin/UserList.tsx': user_list,
    'src/components/chat/CitationBadge.tsx': citation_badge,
    'src/components/chat/SourcePreviewModal.tsx': source_preview_modal,
    'src/components/chat/FollowUpPills.tsx': follow_up_pills,
    'src/components/chat/VoiceRecorder.tsx': voice_recorder,
    'src/components/chat/AudioPlayer.tsx': audio_player,
    'src/components/chat/ExportMenu.tsx': export_menu,
    'src/components/chat/ShareDialog.tsx': share_dialog,
}

for path, content in files.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
