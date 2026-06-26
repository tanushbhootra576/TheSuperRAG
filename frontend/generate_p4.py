import os

os.makedirs('src/components/admin', exist_ok=True)
os.makedirs('src/components/chat', exist_ok=True)
os.makedirs('src/pages', exist_ok=True)

# P4.1
job_queue_monitor = """import React from "react";
import { Activity, Clock, AlertTriangle, CheckCircle, RefreshCcw } from "lucide-react";

export function JobQueueMonitor() {
  const jobs = [
    { id: "job_9x8f", type: "Document Ingestion", status: "processing", progress: 65, time: "2m 14s" },
    { id: "job_2k1a", type: "Graph Update", status: "pending", progress: 0, time: "waiting" },
    { id: "job_p4m9", type: "Re-indexing", status: "failed", progress: 32, time: "failed" },
    { id: "job_7v3x", type: "Cache Cleanup", status: "done", progress: 100, time: "14s" },
  ];

  return (
    <div className="bg-[var(--bg-primary)] border-4 border-[var(--border-strong)] mt-6">
      <div className="p-4 border-b-4 border-[var(--border-strong)] bg-[var(--bg-secondary)] flex justify-between items-center">
        <h2 className="font-black uppercase text-lg flex items-center gap-2"><Activity size={20}/> Background Jobs</h2>
        <button className="flex items-center gap-1 text-xs font-bold hover:text-[var(--accent)]"><RefreshCcw size={14}/> Refresh</button>
      </div>
      
      <div className="p-4 space-y-3">
        {jobs.map(j => (
          <div key={j.id} className="border-2 border-[var(--border-strong)] p-3 flex flex-col md:flex-row md:items-center justify-between gap-3 bg-[var(--bg-primary)]">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-bold">{j.type}</span>
                <span className="text-[10px] text-[var(--text-muted)] font-mono">{j.id}</span>
              </div>
              <div className="h-2 w-full bg-[var(--bg-secondary)] border border-[var(--border-strong)] overflow-hidden">
                <div 
                  className={`h-full ${j.status === 'failed' ? 'bg-[var(--error)]' : j.status === 'done' ? 'bg-[var(--success)]' : 'bg-[var(--accent)]'}`} 
                  style={{ width: `${j.progress}%` }} 
                />
              </div>
            </div>
            
            <div className="flex items-center gap-4 text-xs font-bold w-48 justify-end">
              <span className="flex items-center gap-1 text-[var(--text-muted)] w-16"><Clock size={12}/> {j.time}</span>
              <span className={`w-24 text-right uppercase ${j.status === 'failed' ? 'text-[var(--error)]' : j.status === 'processing' ? 'text-[var(--accent)]' : j.status === 'done' ? 'text-[var(--success)]' : 'text-[var(--text-muted)]'}`}>
                {j.status === 'processing' && <Activity size={12} className="inline mr-1 animate-pulse"/>}
                {j.status === 'failed' && <AlertTriangle size={12} className="inline mr-1"/>}
                {j.status === 'done' && <CheckCircle size={12} className="inline mr-1"/>}
                {j.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
"""

# P4.2
observability_dashboard = """import React from "react";
import { PageContainer } from "@/components/layout/PageContainer";
import { Activity, Clock, DollarSign, Database } from "lucide-react";

export default function ObservabilityDashboard() {
  const stats = [
    { label: "Avg Latency", value: "1.4s", icon: <Clock size={20}/>, color: "var(--accent)" },
    { label: "Total Cost", value: "$42.50", icon: <DollarSign size={20}/>, color: "var(--warning)" },
    { label: "Token Count", value: "1.2M", icon: <Database size={20}/>, color: "var(--success)" },
    { label: "Success Rate", value: "99.2%", icon: <Activity size={20}/>, color: "var(--error)" },
  ];

  return (
    <PageContainer className="py-8">
      <h1 className="text-3xl font-black uppercase mb-2">LLM Observability</h1>
      <p className="text-[var(--text-muted)] font-medium mb-8">Traces, latency, and cost analysis</p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {stats.map(s => (
          <div key={s.label} className="bg-[var(--bg-secondary)] border-4 border-[var(--border-strong)] p-4 flex flex-col items-center text-center">
            <div className="text-[var(--text-muted)] mb-2" style={{ color: s.color }}>{s.icon}</div>
            <div className="text-2xl font-black mb-1">{s.value}</div>
            <div className="text-xs font-bold uppercase text-[var(--text-muted)]">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="bg-[var(--bg-primary)] border-4 border-[var(--border-strong)] mb-8">
        <div className="p-4 border-b-2 border-[var(--border-strong)] bg-[var(--bg-secondary)] flex justify-between items-center">
          <h2 className="font-black uppercase text-lg">Recent Traces</h2>
          <div className="flex gap-2">
            <button className="bauhaus-btn text-xs py-1">Export CSV</button>
            <button className="bauhaus-btn primary text-xs py-1">Open LangSmith</button>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-[var(--bg-secondary)] border-b-2 border-[var(--border-strong)] uppercase text-xs">
              <tr>
                <th className="p-3">Query</th>
                <th className="p-3">Model</th>
                <th className="p-3">Latency</th>
                <th className="p-3">Tokens</th>
                <th className="p-3">Cost</th>
              </tr>
            </thead>
            <tbody>
              {[1,2,3].map(i => (
                <tr key={i} className="border-b border-[var(--border-strong)] hover:bg-[var(--bg-secondary)] cursor-pointer">
                  <td className="p-3 font-medium">"What is the CEO's salary?"</td>
                  <td className="p-3 text-[10px] font-bold"><span className="bg-[#e1f5fe] text-[#0277bd] border border-[#0277bd] px-1 rounded-sm">gpt-4o</span></td>
                  <td className="p-3 text-[var(--text-muted)]">1.2s</td>
                  <td className="p-3 text-[var(--text-muted)]">4,021</td>
                  <td className="p-3 font-mono text-[10px] text-[var(--error)]">$0.02</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </PageContainer>
  );
}
"""

# P4.3
cache_manager = """import React from "react";
import { Database, Zap, Trash2 } from "lucide-react";

export function CacheManager() {
  return (
    <div className="bg-[var(--bg-primary)] border-4 border-[var(--border-strong)] mt-6">
      <div className="p-4 border-b-4 border-[var(--border-strong)] bg-[var(--bg-secondary)] flex justify-between items-center">
        <h2 className="font-black uppercase text-lg flex items-center gap-2"><Zap size={20} className="text-[var(--warning)]"/> Semantic Cache</h2>
      </div>
      
      <div className="p-4 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="col-span-1 space-y-4">
          <div className="border-2 border-[var(--border-strong)] p-3 text-center">
            <div className="text-3xl font-black text-[var(--success)] mb-1">42%</div>
            <div className="text-xs font-bold uppercase text-[var(--text-muted)]">Cache Hit Rate</div>
          </div>
          <div className="border-2 border-[var(--border-strong)] p-3 text-center">
            <div className="text-3xl font-black mb-1">1,204</div>
            <div className="text-xs font-bold uppercase text-[var(--text-muted)]">Active Entries</div>
          </div>
          <button className="bauhaus-btn w-full flex items-center justify-center gap-2 text-[var(--error)] border-[var(--error)] hover:bg-[var(--error)] hover:text-white">
            <Trash2 size={16}/> Flush Cache
          </button>
        </div>
        
        <div className="col-span-2 border-2 border-[var(--border-strong)] p-4 bg-[var(--bg-secondary)]">
          <h3 className="font-bold uppercase text-sm mb-4 border-b-2 border-[var(--border-strong)] pb-2">Cache Settings</h3>
          
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-xs font-bold mb-1">
                <span>Similarity Threshold (0.92)</span>
              </div>
              <input type="range" min="80" max="99" defaultValue="92" className="w-full accent-[var(--accent)]" />
              <p className="text-[10px] text-[var(--text-muted)] mt-1">Lower = more hits but potential inaccuracies.</p>
            </div>
            
            <div>
              <div className="flex justify-between text-xs font-bold mb-1">
                <span>Time To Live (TTL)</span>
              </div>
              <select className="w-full p-2 border-2 border-[var(--border-strong)] bg-[var(--bg-primary)] font-bold text-sm">
                <option>1 Hour</option>
                <option selected>24 Hours</option>
                <option>7 Days</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
"""

# P4.4
feedback_dialog = """import React, { useState } from "react";
import { ThumbsDown, MessageSquare, Send, X } from "lucide-react";

export function FeedbackDialog({ isOpen, onClose }: { isOpen: boolean, onClose: () => void }) {
  const [reason, setReason] = useState("");

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[80] bg-black/50 flex items-center justify-center p-4">
      <div className="bg-[var(--bg-primary)] border-4 border-[var(--border-strong)] w-full max-w-md shadow-[var(--shadow-lg)]">
        <div className="p-3 border-b-2 border-[var(--border-strong)] bg-[var(--bg-secondary)] flex justify-between items-center text-[var(--error)]">
          <h2 className="font-black uppercase flex items-center gap-2"><ThumbsDown size={18}/> Report Issue</h2>
          <button onClick={onClose} className="text-black"><X size={20}/></button>
        </div>
        
        <div className="p-4 space-y-4">
          <div>
            <h3 className="font-bold text-sm mb-2">What was wrong with the answer?</h3>
            <div className="grid grid-cols-2 gap-2">
              {['Hallucination', 'Off Topic', 'Incomplete', 'Wrong Source'].map(r => (
                <button 
                  key={r}
                  onClick={() => setReason(r)}
                  className={`border-2 p-2 text-xs font-bold transition-colors ${reason === r ? 'border-[var(--accent)] bg-[var(--accent-muted)]' : 'border-[var(--border-strong)] bg-[var(--bg-secondary)]'}`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>

          <div>
            <h3 className="font-bold text-sm mb-2">Additional details (optional)</h3>
            <textarea 
              placeholder="Tell us more about the issue..." 
              className="w-full p-2 border-2 border-[var(--border-strong)] bg-[var(--bg-secondary)] min-h-[80px] text-sm resize-none"
            />
          </div>

          <div className="bg-[#fff3e0] border border-[#ffb74d] p-2 text-[10px] font-medium text-[#e65100]">
            This feedback is sent to administrators to improve the retriever via RLHF.
          </div>

          <button className="bauhaus-btn primary w-full flex items-center justify-center gap-2 mt-2">
            <Send size={16}/> Submit Feedback
          </button>
        </div>
      </div>
    </div>
  );
}
"""

rlhf_dashboard = """import React from "react";
import { PageContainer } from "@/components/layout/PageContainer";
import { ThumbsUp, ThumbsDown, Download, BrainCircuit } from "lucide-react";

export default function RLHFDashboard() {
  return (
    <PageContainer className="py-8">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-3xl font-black uppercase">RLHF Training Data</h1>
          <p className="text-[var(--text-muted)] font-medium">User feedback collected for fine-tuning</p>
        </div>
        <button className="bauhaus-btn primary flex items-center gap-2"><Download size={16}/> Export JSONL Dataset</button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="border-4 border-[var(--border-strong)] p-4 bg-[var(--bg-secondary)] flex items-center gap-4">
          <div className="w-12 h-12 bg-[var(--success)] text-white rounded-full flex items-center justify-center"><ThumbsUp size={24}/></div>
          <div>
            <div className="text-2xl font-black">1,402</div>
            <div className="text-xs font-bold uppercase text-[var(--text-muted)]">Positive Signals</div>
          </div>
        </div>
        <div className="border-4 border-[var(--border-strong)] p-4 bg-[var(--bg-secondary)] flex items-center gap-4">
          <div className="w-12 h-12 bg-[var(--error)] text-white rounded-full flex items-center justify-center"><ThumbsDown size={24}/></div>
          <div>
            <div className="text-2xl font-black">143</div>
            <div className="text-xs font-bold uppercase text-[var(--text-muted)]">Negative Signals</div>
          </div>
        </div>
        <div className="border-4 border-[var(--border-strong)] p-4 bg-[var(--accent)] text-white flex flex-col justify-center items-center text-center cursor-pointer hover:bg-[var(--accent-hover)] transition-colors">
          <BrainCircuit size={24} className="mb-2"/>
          <div className="font-black uppercase">Fine-tune Reranker</div>
          <div className="text-[10px] font-medium opacity-80 mt-1">Requires 500+ signals</div>
        </div>
      </div>

      <div className="bg-[var(--bg-primary)] border-4 border-[var(--border-strong)]">
        <div className="p-3 border-b-2 border-[var(--border-strong)] bg-[var(--bg-secondary)]">
          <h3 className="font-black uppercase">Recent Negative Feedback</h3>
        </div>
        <div className="p-4 space-y-4">
          {[1,2].map(i => (
            <div key={i} className="border-2 border-[var(--border-strong)] p-3">
              <div className="flex justify-between items-start mb-2 border-b-2 border-[var(--border-strong)] pb-2">
                <p className="font-bold italic">"What are the integration limits?"</p>
                <span className="bg-[var(--error)] text-white text-[10px] font-bold uppercase px-2 py-0.5">Hallucination</span>
              </div>
              <p className="text-sm text-[var(--text-muted)] mb-2">User comment: "The answer invented an API rate limit of 100/min which is not in our docs."</p>
              <div className="flex items-center gap-2">
                <button className="text-xs font-bold underline text-[var(--accent)]">View Trace</button>
                <button className="text-xs font-bold underline text-[var(--error)]">Exclude from training</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </PageContainer>
  );
}
"""

# P4.5
api_keys_page = """import React from "react";
import { PageContainer } from "@/components/layout/PageContainer";
import { Key, Plus, Trash2, Copy } from "lucide-react";

export default function ApiKeysPage() {
  return (
    <PageContainer className="py-8">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-3xl font-black uppercase">API Keys</h1>
          <p className="text-[var(--text-muted)] font-medium">Manage developer access and rate limits</p>
        </div>
        <button className="bauhaus-btn primary flex items-center gap-2"><Plus size={16}/> New Key</button>
      </div>

      <div className="bg-[#e1f5fe] border-2 border-[#0277bd] p-4 mb-8 flex gap-3 text-sm text-[#0277bd]">
        <Key className="shrink-0"/>
        <div>
          <p className="font-bold mb-1">Developer API is active</p>
          <p className="font-medium text-xs">Default rate limit is 60 req/min. Keys shown here have access to all your workspaces.</p>
        </div>
      </div>

      <div className="bg-[var(--bg-primary)] border-4 border-[var(--border-strong)] overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-[var(--bg-secondary)] border-b-2 border-[var(--border-strong)] uppercase text-xs">
            <tr>
              <th className="p-4">Name</th>
              <th className="p-4">Key Hash</th>
              <th className="p-4">Created</th>
              <th className="p-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-[var(--border-strong)] hover:bg-[var(--bg-secondary)]">
              <td className="p-4 font-bold">Production App</td>
              <td className="p-4 font-mono text-xs text-[var(--text-muted)] flex items-center gap-2">
                tsr_live_••••••••••••x8F <Copy size={12} className="cursor-pointer hover:text-[var(--text-primary)]"/>
              </td>
              <td className="p-4 text-[var(--text-muted)]">2 days ago</td>
              <td className="p-4 text-right">
                <button className="text-[var(--error)] hover:text-red-700 p-1 border border-transparent hover:border-[var(--error)]"><Trash2 size={16}/></button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </PageContainer>
  );
}
"""

# P4.6
connector_marketplace = """import React from "react";
import { PageContainer } from "@/components/layout/PageContainer";
import { Cloud, CheckCircle, PlusCircle } from "lucide-react";

export default function ConnectorMarketplace() {
  const connectors = [
    { name: "Slack", desc: "Ingest channel messages and threads", connected: true, color: "#4A154B" },
    { name: "Notion", desc: "Sync pages and databases", connected: false, color: "#000000" },
    { name: "Google Drive", desc: "Sync Docs, Sheets, and Slides", connected: true, color: "#0F9D58" },
    { name: "Confluence", desc: "Ingest spaces and articles", connected: false, color: "#172B4D" },
  ];

  return (
    <PageContainer className="py-8">
      <h1 className="text-3xl font-black uppercase mb-2">Connectors</h1>
      <p className="text-[var(--text-muted)] font-medium mb-8">Link external data sources to your knowledge graph</p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {connectors.map(c => (
          <div key={c.name} className="bg-[var(--bg-primary)] border-4 border-[var(--border-strong)] flex flex-col h-full">
            <div className="p-4 flex-1">
              <div className="w-12 h-12 rounded-lg flex items-center justify-center text-white font-black text-xl mb-4" style={{ backgroundColor: c.color }}>
                {c.name[0]}
              </div>
              <h3 className="font-black uppercase text-lg mb-2">{c.name}</h3>
              <p className="text-sm font-medium text-[var(--text-muted)]">{c.desc}</p>
            </div>
            
            <div className="p-4 border-t-2 border-[var(--border-strong)] bg-[var(--bg-secondary)] flex justify-between items-center">
              {c.connected ? (
                <span className="flex items-center gap-1 text-[var(--success)] font-bold text-xs uppercase"><CheckCircle size={14}/> Connected</span>
              ) : (
                <span className="text-[var(--text-muted)] font-bold text-xs uppercase">Not Connected</span>
              )}
              
              <button className={`bauhaus-btn text-xs py-1 px-3 ${c.connected ? 'border-[var(--border-strong)] text-black hover:bg-[var(--error)] hover:text-white' : 'primary'}`}>
                {c.connected ? 'Manage' : 'Connect'}
              </button>
            </div>
          </div>
        ))}

        <div className="border-4 border-dashed border-[var(--border-strong)] bg-[var(--bg-secondary)] flex flex-col items-center justify-center p-6 text-center text-[var(--text-muted)] hover:bg-[var(--bg-primary)] hover:border-[var(--accent)] hover:text-[var(--accent)] transition-colors cursor-pointer min-h-[250px]">
          <PlusCircle size={32} className="mb-4" />
          <h3 className="font-black uppercase mb-2">Build Custom Connector</h3>
          <p className="text-xs font-medium">Use the Plugin SDK to connect your own data source.</p>
        </div>
      </div>
    </PageContainer>
  );
}
"""

files = {
    'src/components/admin/JobQueueMonitor.tsx': job_queue_monitor,
    'src/pages/ObservabilityDashboard.tsx': observability_dashboard,
    'src/components/admin/CacheManager.tsx': cache_manager,
    'src/components/chat/FeedbackDialog.tsx': feedback_dialog,
    'src/pages/RLHFDashboard.tsx': rlhf_dashboard,
    'src/pages/ApiKeysPage.tsx': api_keys_page,
    'src/pages/ConnectorMarketplace.tsx': connector_marketplace,
}

for path, content in files.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
