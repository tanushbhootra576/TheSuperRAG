'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import dynamic from 'next/dynamic';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Mic, Send, Copy, Share, Edit2, Trash2, Maximize2, Minimize2, Settings, FileText, UploadCloud, MessageSquare, Plus, ChevronDown, ChevronRight, Check } from 'lucide-react';

const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false });

// ── Types ─────────────────────────────────────────────────────────────────────
type SourceDoc = {
  file: string;
  page: string;
  snippet: string;
};

type Confidence = {
  score: number;
  label: 'High' | 'Medium' | 'Low' | string;
  emoji: string;
};

type Message = {
  role: 'user' | 'assistant';
  content: string;
  confidence?: Confidence;
  docs?: SourceDoc[];
};

type Toast = {
  id: number;
  message: string;
  type: 'success' | 'info' | 'error';
};

const API = 'http://127.0.0.1:8000';

// ── Confidence styling ────────────────────────────────────────────────────────
const confColor: Record<string, string> = {
  High: '#10b981',
  Medium: '#f59e0b',
  Low: '#ef4444',
};

// ── Main Component ────────────────────────────────────────────────────────────
export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content:
        'Hello! I am **TheSuperRAG** — powered by hybrid search, cross-encoder re-ranking, and self-healing. I cite my sources and show a confidence score with every answer.\n\nInitialise the database in the sidebar to begin.',
    },
  ]);

  const [input, setInput] = useState('');
  const [isInitializing, setIsInitializing] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [liveStatus, setLiveStatus] = useState<string | null>(null);

  // Documents
  const [documents, setDocuments] = useState<string[]>([]);
  const [selectedDocs, setSelectedDocs] = useState<string[]>([]);
  const [deletingDoc, setDeletingDoc] = useState<string | null>(null);

  // Upload
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Sessions
  const [sessions, setSessions] = useState<{id: string, title: string, updated_at: string}[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);

  // UI state
  const [healCount, setHealCount] = useState(0);
  const [expandedCitations, setExpandedCitations] = useState<Set<number>>(new Set());
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [hybridEnabled, setHybridEnabled] = useState(false);
  const [activeTab, setActiveTab] = useState<'documents' | 'upload' | 'history' | 'graph'>('documents');
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [isGraphExpanded, setIsGraphExpanded] = useState(false);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  
  //Settings state
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [llmModel, setLlmModel] = useState('llama-3.1-8b-instant');
  const [temperature, setTemperature] = useState(0.0);
  const [useCrossEncoder, setUseCrossEncoder] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const toastCounter = useRef(0);

  // ── Utilities ──────────────────────────────────────────────────────────────

  const addToast = useCallback((message: string, type: Toast['type'] = 'success') => {
    const id = ++toastCounter.current;
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 5000);
  }, []);

  const fetchDocuments = useCallback(async () => {
    try {
      const res = await fetch(`${API}/documents`);
      const data = await res.json();
      setDocuments(data.documents || []);
    } catch {
      /* backend not reachable yet */
    }
  }, []);

  const fetchSessions = useCallback(async () => {
    try {
      const res = await fetch(`${API}/sessions`);
      const data = await res.json();
      setSessions(data.sessions || []);
    } catch {}
  }, []);

  const loadSession = async (id: string) => {
    setSessionId(id);
    setExpandedCitations(new Set());
    try {
      const res = await fetch(`${API}/sessions/${id}/messages`);
      const data = await res.json();
      if (data.messages && data.messages.length > 0) {
        setMessages(data.messages);
      } else {
        setMessages([{ role: 'assistant', content: 'Session loaded. Start chatting!' }]);
      }
    } catch {}
  };

  const createSession = async () => {
    try {
      const res = await fetch(`${API}/sessions`, { method: 'POST' });
      const data = await res.json();
      setSessionId(data.id);
      setMessages([{ role: 'assistant', content: 'New chat started. I am ready!' }]);
      fetchSessions();
    } catch {}
  };

  const deleteSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await fetch(`${API}/sessions/${id}`, { method: 'DELETE' });
      if (sessionId === id) {
        setSessionId(null);
        setMessages([{ role: 'assistant', content: 'Select or start a new chat.' }]);
      }
      fetchSessions();
    } catch {}
  };

  const saveSessionName = async (id: string) => {
    try {
      await fetch(`${API}/sessions/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: editingTitle })
      });
      setEditingSessionId(null);
      fetchSessions();
    } catch {}
  };

  const exportChat = () => {
    const text = messages.map(m => `**${m.role.toUpperCase()}**\n${m.content}\n\n`).join('');
    const blob = new Blob([text], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat_export_${new Date().getTime()}.md`;
    a.click();
  };

  const fetchGraph = async () => {
    try {
      const res = await fetch(`${API}/graph`);
      const data = await res.json();
      setGraphData(data);
    } catch {}
  };

  useEffect(() => {
    if (activeTab === 'graph') {
      fetchGraph();
    }
  }, [activeTab]);


  // ── Effects ────────────────────────────────────────────────────────────────

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, liveStatus]);

  // Check existing backend status on mount, including in-progress inits
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await fetch(`${API}/status`);
        const d = await res.json();
        if (d.initialized) {
          setIsInitialized(true);
          setDocuments(d.documents || []);
          setHybridEnabled(d.hybrid_search ?? false);
          fetchSessions();
        } else if (d.init_in_progress) {
          // A previous init is still running in the background — resume polling
          setIsInitializing(true);
          const poll = setInterval(async () => {
            try {
              const r = await fetch(`${API}/status`);
              const s = await r.json();
              if (s.initialized) {
                clearInterval(poll);
                setIsInitialized(true);
                setDocuments(s.documents || []);
                setHybridEnabled(s.hybrid_search ?? false);
                setIsInitializing(false);
                addToast(`System ready -- ${(s.documents || []).length} document(s) indexed.`, 'success');
              } else if (s.init_error) {
                clearInterval(poll);
                setIsInitializing(false);
                addToast(`Init failed: ${s.init_error}`, 'error');
              }
            } catch {}
          }, 2000);
        }
      } catch {}
    };
    checkStatus();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // SSE: auto-indexing notifications from watchdog
  useEffect(() => {
    const es = new EventSource(`${API}/events`);
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === 'document_indexed') {
          addToast(`✅ Auto-indexed: "${data.file}" (${data.chunks} chunks)`, 'success');
          fetchDocuments();
        }
      } catch {}
    };
    es.onerror = () => {};
    return () => es.close();
  }, [addToast, fetchDocuments]);

  // ── Handlers ───────────────────────────────────────────────────────────────

  const handleInit = async () => {
    setIsInitializing(true);
    try {
      // POST /init starts the background initialisation thread and returns immediately
      await fetch(`${API}/init`, { method: 'POST' });

      // Poll /status every 2 seconds until initialized or error
      const poll = async () => {
        try {
          const res = await fetch(`${API}/status`);
          const data = await res.json();

          if (data.initialized) {
            setIsInitialized(true);
            setDocuments(data.documents || []);
            setHybridEnabled(data.hybrid_search ?? false);
            setIsInitializing(false);
            addToast(`System ready -- ${(data.documents || []).length} document(s) indexed.`, 'success');
          } else if (data.init_error) {
            setIsInitializing(false);
            addToast(`Init failed: ${data.init_error}`, 'error');
          } else {
            // Still loading -- keep polling
            setTimeout(poll, 2000);
          }
        } catch {
          // Backend not reachable, keep trying for a bit
          setTimeout(poll, 3000);
        }
      };
      setTimeout(poll, 1000);
    } catch {
      addToast('Cannot connect to backend. Is the server running on port 8000?', 'error');
      setIsInitializing(false);
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !isInitialized || isGenerating) return;

    const userQuery = input.trim();
    setInput('');
    const historyPayload = messages.slice(1).map((m) => ({
      role: m.role,
      content: m.content,
    }));
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: userQuery },
      { role: 'assistant', content: '', confidence: undefined, docs: [] } // placeholder for streaming
    ]);
    setIsGenerating(true);
    setLiveStatus('Starting search…');

    try {
      const response = await fetch(`${API}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: userQuery,
          history: historyPayload,
          selected_documents: selectedDocs,
          session_id: sessionId,
          llm_model: llmModel,
          temperature: temperature,
          use_cross_encoder: useCrossEncoder,
        }),
      });

      if (!response.body) throw new Error('No readable stream');
      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const raw = line.slice(6).trim();
          if (raw === '[DONE]') break;
          if (!raw) continue;

          try {
            const parsed = JSON.parse(raw);
            if (parsed.type === 'status') {
              setLiveStatus(parsed.message);
              if (parsed.event === 'heal') setHealCount((n) => n + 1);
            } else if (parsed.type === 'token') {
              setMessages((prev) => {
                const newMsgs = [...prev];
                const last = newMsgs[newMsgs.length - 1];
                if (last.role === 'assistant') {
                  last.content += parsed.content;
                }
                return newMsgs;
              });
            } else if (parsed.type === 'final') {
              setMessages((prev) => {
                const newMsgs = [...prev];
                const last = newMsgs[newMsgs.length - 1];
                if (last.role === 'assistant') {
                  // We already appended the text via tokens, just update docs/confidence
                  // Wait! If there were no tokens (e.g. from a router node), we might need to set the content.
                  if (parsed.message && !last.content) {
                    last.content = parsed.message;
                  }
                  last.docs = parsed.docs || [];
                  last.confidence = parsed.confidence;
                }
                return newMsgs;
              });
              setLiveStatus(null);
              setIsGenerating(false);
            }
          } catch {}
        }
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'An error occurred. Please try again.' },
      ]);
    } finally {
      setLiveStatus(null);
      setIsGenerating(false);
    }
  };

  const toggleDocSelection = (doc: string) => {
    setSelectedDocs((prev) =>
      prev.includes(doc) ? prev.filter((d) => d !== doc) : [...prev, doc]
    );
  };

  const handleDeleteDoc = async (doc: string) => {
    if (!confirm(`Remove "${doc}" from the index and disk?`)) return;
    setDeletingDoc(doc);
    try {
      const res = await fetch(`${API}/documents/${encodeURIComponent(doc)}`, {
        method: 'DELETE',
      });
      if (res.ok) {
        addToast(`"${doc}" removed successfully.`, 'success');
        setDocuments((prev) => prev.filter((d) => d !== doc));
        setSelectedDocs((prev) => prev.filter((d) => d !== doc));
      } else {
        addToast(`Failed to remove "${doc}".`, 'error');
      }
    } catch {
      addToast('Delete failed. Check backend connection.', 'error');
    }
    setDeletingDoc(null);
  };

  // Upload handlers
  const uploadFiles = async (files: FileList | File[]) => {
    const pdfs = Array.from(files).filter((f) => f.name.toLowerCase().endsWith('.pdf'));
    if (!pdfs.length) {
      addToast('Please select PDF files only.', 'error');
      return;
    }
    setUploading(true);
    let uploaded = 0;
    for (const file of pdfs) {
      try {
        const fd = new FormData();
        fd.append('file', file);
        const res = await fetch(`${API}/upload`, { method: 'POST', body: fd });
        if (res.ok) {
          uploaded++;
          await fetchDocuments();
        }
      } catch {}
    }
    setUploading(false);
    if (uploaded > 0) addToast(`${uploaded} PDF(s) uploaded and indexed.`, 'success');
    else addToast('Upload failed. Is the server running?', 'error');
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    uploadFiles(e.dataTransfer.files);
  };

  const toggleCitations = (idx: number) => {
    setExpandedCitations((prev) => {
      const next = new Set(prev);
      next.has(idx) ? next.delete(idx) : next.add(idx);
      return next;
    });
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  const searchScopeLabel =
    selectedDocs.length === 0
      ? `All ${documents.length} document(s)`
      : `${selectedDocs.length} selected document(s)`;

  return (
    <div className="flex h-screen bg-white text-[#111111] font-sans overflow-hidden">

      {/* ── Toast Notifications ──────────────────────────────────────────── */}
      <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`px-4 py-3 rounded-xl shadow-2xl text-sm font-medium backdrop-blur-sm border
              pointer-events-auto animate-in slide-in-from-top-2 duration-300
              ${t.type === 'success' ? 'bg-emerald-900/90 border-emerald-500/40 text-emerald-100' : ''}
              ${t.type === 'error' ? 'bg-red-900/90 border-red-500/40 text-red-100' : ''}
              ${t.type === 'info' ? 'bg-sky-900/90 border-sky-500/40 text-sky-100' : ''}
            `}
          >
            {t.message}
          </div>
        ))}
      </div>

      {/* ──Settings Modal ────────────────────────────────────────────────── */}
      {isSettingsOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="glass-panel w-[400px] rounded-2xl border border-slate-700 p-6 shadow-2xl relative">
            <h3 className="text-lg font-bold text-slate-100 mb-4">ModelSettings</h3>
            
            <div className="space-y-5">
              <div>
                <label className="text-xs font-semibold text-gray-500 mb-2 block">LLM Provider</label>
                <select
                  value={llmModel}
                  onChange={(e) => setLlmModel(e.target.value)}
                  className="w-full bg-slate-900/60 border border-slate-700/60 text-slate-200 rounded-lg p-2.5 text-sm focus:border-sky-500 focus:outline-none"
                >
                  <option value="llama-3.1-8b-instant">Llama 3.1 8B (Fast)</option>
                  <option value="llama-3.1-70b-versatile">Llama 3.1 70B (Smart)</option>
                  <option value="mixtral-8x7b-32768">Mixtral 8x7b</option>
                  <option value="gemma2-9b-it">Gemma 2 9B</option>
                </select>
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="text-xs font-semibold text-gray-500">Temperature (Creativity)</label>
                  <span className="text-xs text-[#111111] font-medium">{temperature.toFixed(1)}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="w-full accent-sky-500"
                />
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/40 border border-slate-800">
                <div>
                  <p className="text-sm font-semibold text-slate-200">Cross-Encoder Re-ranking</p>
                  <p className="text-[10px] text-gray-500">Improves accuracy, slightly slower.</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={useCrossEncoder}
                    onChange={(e) => setUseCrossEncoder(e.target.checked)}
                  />
                  <div className="w-9 h-5 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-sky-500"></div>
                </label>
              </div>
            </div>

            <button
              onClick={() => setIsSettingsOpen(false)}
              className="mt-6 w-full bg-slate-100 text-slate-900 hover:bg-white font-semibold py-2.5 rounded-lg transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      )}
      {/* Fullscreen Graph Overlay */}
      {isGraphExpanded && (
        <div className="fixed inset-0 z-50 bg-black/90 flex flex-col items-center justify-center backdrop-blur-sm">
          <div className="absolute top-6 right-6 z-50">
            <button
              onClick={() => setIsGraphExpanded(false)}
              className="p-2 bg-slate-800/80 hover:bg-slate-700 text-white rounded-lg transition-colors border border-slate-700"
            >
              <Minimize2 size={20} />
            </button>
          </div>
          <div className="w-[90vw] h-[90vh] bg-slate-900/60 rounded-2xl border border-slate-800/80 overflow-hidden relative shadow-2xl">
            {graphData.nodes.length > 0 ? (
              <ForceGraph2D
                graphData={graphData}
                width={typeof window !== 'undefined' ? window.innerWidth * 0.9 : 800}
                height={typeof window !== 'undefined' ? window.innerHeight * 0.9 : 600}
                nodeAutoColorBy="group"
                nodeLabel="id"
                linkDirectionalArrowLength={4}
                linkDirectionalArrowRelPos={1}
                linkColor={() => 'rgba(255,255,255,0.3)'}
                backgroundColor="rgba(0,0,0,0)"
              />
            ) : (
              <div className="absolute inset-0 flex items-center justify-center">
                <p className="text-gray-500 font-medium">No graph data extracted.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Sidebar Overlay ─────────────────────────────────────────────────── */}
      {isSidebarOpen && <div className="fixed inset-0 bg-black/60 z-30 md:hidden" onClick={() => setIsSidebarOpen(false)} />}

      {/* ── Sidebar ───────────────────────────────────────────────────────── */}
      <aside className={`fixed md:static inset-y-0 left-0 w-[22%] bg-white border-r border-[#E5E7EB] flex flex-col z-40 transition-transform duration-300 ${isSidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}`}>
        {/* Gradient accent bar */}
        

        {/* Branding */}
        <div className="p-8 pb-4 flex flex-col gap-8">
          <div className="grid grid-cols-2 w-12 h-12" style={{ gap: '2px' }}>
            <div className="bg-[#111111] rounded-tl-full"></div>
            <div className="bg-[#EF4444] rounded-tr-full"></div>
            <div className="bg-[#FFD230] rounded-full"></div>
            <div className="bg-[#2563EB]"></div>
          </div>
          <h1 className="text-3xl font-bold text-[#111111] leading-[1.1] tracking-tight">
            TheSuperRAG
          </h1>
        </div>

        {/* System Status */}
        <div className="px-6 mt-2">
          <div className="bg-[#F9FAFB] rounded-2xl p-5 border border-[#E5E7EB]">
            <p className="text-[11px] font-bold text-gray-500 uppercase tracking-widest mb-3">
              System Status
            </p>
            <div className="flex items-center gap-3 mb-3">
              <div
                className={`w-2.5 h-2.5 rounded-full ${
                  isInitialized ? 'bg-[#10b981]' : 'bg-[#ef4444]'
                }`}
              />
              <span className="text-[14px] font-semibold text-[#111111]">
                {isInitialized ? 'Active & Ready' : 'Offline'}
              </span>
            </div>
            
            {isInitialized && (
              <div className="space-y-1.5 text-[12px]">
                <div className="text-gray-600">
                  {hybridEnabled ? 'Hybrid Search (Dense + BM25)' : 'Dense Search'}
                </div>
                <div className="text-gray-600">
                  Cross-Encoder Re-ranking: ON
                </div>
              </div>
            )}
            
            {!isInitialized && (
              <button
                id="init-btn"
                onClick={handleInit}
                disabled={isInitializing}
                className="w-full py-3 rounded-full text-sm font-semibold transition-all
                  bg-[#2563EB] text-white hover:bg-blue-700 shadow-sm
                  disabled:opacity-50 disabled:shadow-none"
              >
                {isInitializing ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                    Indexing...
                  </span>
                ) : (
                  'Initialize Database'
                )}
              </button>
            )}
          </div>
        </div>

        {/* Navigation Menu (Tabs) */}
        {isInitialized && (
          <nav className="flex-1 px-6 mt-6 flex flex-col gap-2.5">
            {(['documents', 'upload', 'history', 'graph'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex items-center gap-4 px-5 py-3.5 rounded-full font-medium text-[15px] transition-all capitalize
                  ${activeTab === tab
                    ? 'bg-[#EBF1FF] text-[#2563EB] shadow-sm'
                    : 'text-[#111111] hover:bg-[#F3F4F6]'
                  }`}
              >
                {tab === 'documents' ? <FileText size={18} /> : 
                 tab === 'upload' ? <UploadCloud size={18} /> : 
                 tab === 'history' ? <Copy size={18} /> : 
                 <Share size={18} />} 
                {tab === 'documents' ? 'Docs' : tab}
              </button>
            ))}
            
            <button 
              onClick={() => setIsSettingsOpen(true)} 
              className="flex items-center gap-4 px-5 py-3.5 mt-2 text-[#111111] hover:bg-[#F3F4F6] rounded-full font-medium text-[15px] transition-colors"
            >
              <Settings size={18} /> Settings
            </button>
          </nav>
        )}
{/* Document Manager */}
        {isInitialized && activeTab === 'documents' && (
          <div className="px-6 flex-1 overflow-y-auto pb-6">
            <div className="rounded-xl border border-[#E5E7EB] overflow-hidden bg-[#F9FAFB]">
              <div className="px-4 py-3 border-b border-[#E5E7EB] flex items-center justify-between bg-white">
                <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">
                  Indexed Documents
                </p>
                {selectedDocs.length > 0 && (
                  <button
                    onClick={() => setSelectedDocs([])}
                    className="text-[10px] text-[#2563EB] hover:text-blue-700 font-semibold"
                  >
                    Clear filter
                  </button>
                )}
              </div>

              {documents.length === 0 ? (
                <p className="p-4 text-xs text-gray-500 text-center">
                  No documents indexed. Upload PDFs to get started.
                </p>
              ) : (
                <ul className="divide-y divide-[#E5E7EB]">
                  {documents.map((doc) => {
                    const isSelected = selectedDocs.includes(doc);
                    const isDeleting = deletingDoc === doc;
                    return (
                      <li
                        key={doc}
                        className={`flex items-center gap-3 px-4 py-2.5 transition-colors
                          ${isSelected ? 'bg-[#EBF1FF]' : 'hover:bg-white'}`}
                      >
                        {/* Checkbox / selection */}
                        <button
                          id={`doc-select-${doc}`}
                          onClick={() => toggleDocSelection(doc)}
                          className={`w-4 h-4 rounded border-2 flex items-center justify-center shrink-0 transition-all
                            ${isSelected ? 'bg-[#2563EB] border-[#2563EB]' : 'border-gray-300 hover:border-[#2563EB]'
                            }`}
                        >
                          {isSelected && (
                            <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 10 8">
                              <path
                                d="M1 4l3 3 5-6"
                                stroke="currentColor"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                              />
                            </svg>
                          )}
                        </button>

                        {/* Filename */}
                        <span
                          className={`flex-1 text-xs truncate cursor-pointer transition-colors
                            ${isSelected ? 'text-[#111111] font-semibold' : 'text-gray-600'}`}
                          onClick={() => toggleDocSelection(doc)}
                          title={doc}
                        >
                          {doc}
                        </span>

                        {/* Delete */}
                        <button
                          id={`doc-delete-${doc}`}
                          onClick={() => handleDeleteDoc(doc)}
                          disabled={isDeleting}
                          className="text-gray-400 hover:text-red-500 transition-colors shrink-0 disabled:opacity-40"
                          title={`Delete ${doc}`}
                        >
                          {isDeleting ? (
                            <svg className="animate-spin w-3.5 h-3.5" viewBox="0 0 24 24" fill="none">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                            </svg>
                          ) : (
                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          )}
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}

              {/* Search scope indicator */}
              {documents.length > 0 && (
                <div className="px-4 py-2.5 border-t border-[#E5E7EB] bg-white">
                  <p className="text-[10px] text-gray-500">
                     Searching: <span className="text-[#111111] font-medium">{searchScopeLabel}</span>
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Upload Panel */}
        {isInitialized && activeTab === 'upload' && (
          <div className="px-6 flex-1">
            <div
              id="upload-dropzone"
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`
                relative border-2 border-dashed rounded-xl p-6 text-center cursor-pointer
                transition-all duration-200 select-none
                ${isDragging
                  ? 'border-[#2563EB] bg-[#EBF1FF] scale-[1.02]'
                  : 'border-gray-300 hover:border-[#2563EB] hover:bg-gray-50'
                }
                ${uploading ? 'pointer-events-none opacity-60' : ''}
              `}
            >
              {uploading ? (
                <div className="flex flex-col items-center gap-3">
                  <svg className="animate-spin h-8 w-8 text-white" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  <p className="text-sm text-[#111111] font-medium">Uploading & indexing…</p>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-3">
                  <div className={`transition-transform duration-200 ${isDragging ? 'scale-110' : ''}`}>
                    <svg className="h-10 w-10 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-300">
                      {isDragging ? 'Drop to upload' : 'Drop PDFs here'}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">or click to browse</p>
                  </div>
                </div>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                multiple
                className="hidden"
                onChange={(e) => e.target.files && uploadFiles(e.target.files)}
              />
            </div>

            <p className="text-[10px] text-slate-600 text-center mt-3">
               You can also drop PDFs directly into the DATA/ folder — they&apos;ll be auto-indexed instantly.
            </p>
          </div>
        )}

        {/* History Panel */}
        {isInitialized && activeTab === 'history' && (
          <div className="px-6 flex-1 overflow-y-auto pb-6">
            <button
              onClick={createSession}
              className="w-full py-2 mb-3 rounded-lg text-xs font-semibold bg-sky-600 hover:bg-sky-500 text-white transition-colors"
            >
              + New Chat
            </button>
            <div className="space-y-2">
              {sessions.map((s) => (
                <button
                  key={s.id}
                  onClick={() => loadSession(s.id)}
                  className={`w-full text-left p-3 rounded-xl border text-sm transition-all ${
                    sessionId === s.id
                      ? 'bg-slate-800 border-sky-500/50 text-white'
                      : 'bg-slate-900/40 border-slate-800/60 text-gray-500 hover:bg-slate-800/60'
                  }`}
                >
                  <p className="font-medium truncate">{s.title}</p>
                  <p className="text-[10px] opacity-60 mt-1">{new Date(s.updated_at).toLocaleString()}</p>
                </button>
              ))}
              {sessions.length === 0 && (
                <p className="text-xs text-center text-gray-500 mt-4">No chat history found.</p>
              )}
            </div>
          </div>
        )}

        {/* Graph Panel */}
        {isInitialized && activeTab === 'graph' && (
          <div className="px-2 flex-1 overflow-hidden pb-6">
            <div className="flex items-center justify-between px-4 mb-2">
              <h3 className="text-xs font-semibold text-gray-500">Knowledge Graph</h3>
              <button 
                onClick={() => setIsGraphExpanded(true)}
                className="text-gray-500 hover:text-white transition-colors p-1 bg-slate-800/50 rounded-md"
                title="Expand Graph"
              >
                <Maximize2 size={14} />
              </button>
            </div>
            <div className="w-full h-full bg-slate-900/50 rounded-xl border border-slate-800/60 overflow-hidden relative group">
              {graphData.nodes.length > 0 ? (
                <ForceGraph2D
                  graphData={graphData}
                  width={290}
                  height={400}
                  nodeAutoColorBy="group"
                  nodeLabel="id"
                  linkDirectionalArrowLength={3.5}
                  linkDirectionalArrowRelPos={1}
                  linkColor={() => 'rgba(255,255,255,0.2)'}
                  backgroundColor="rgba(0,0,0,0)"
                />
              ) : (
                <div className="absolute inset-0 flex items-center justify-center p-4 text-center text-xs text-gray-500">
                  No graph entities extracted yet.
                </div>
              )}
            </div>
          </div>
        )}

        {/* Metrics */}
        <div className="px-6 py-4 border-t border-[#E5E7EB] mt-auto shrink-0 bg-white">
          <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-3">
            Session Metrics
          </p>
          <div className="grid grid-cols-2 gap-2">
            {[
              { label: 'Documents', value: documents.length, color: 'sky' },
              { label: 'Self-Heals', value: healCount, color: 'amber' },
            ].map(({ label, value, color }) => (
              <div
                key={label}
                className={`bg-${color}-500/5 border border-${color}-500/20 rounded-lg p-3 text-center`}
              >
                <p className={`text-xl font-bold text-${color}-400`}>{value}</p>
                <p className="text-[10px] text-gray-500 mt-0.5">{label}</p>
              </div>
            ))}
          </div>
        </div>
      </aside>

      {/* ── Main Chat Area ────────────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col relative overflow-hidden bg-white">
        {/* Subtle background glow */}
        

        {/* Header */}
        <div className="w-full flex items-center justify-center py-6 shrink-0 z-10 bg-white">
          <div className="w-24 h-[1px] bg-[#E5E7EB]"></div>
          <span className="mx-4 text-xs font-semibold text-[#111111] tracking-widest uppercase">Today</span>
          <div className="w-24 h-[1px] bg-[#E5E7EB]"></div>
        </div>
{/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6 z-0 max-w-4xl mx-auto w-full">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[78%] ${
                  msg.role === 'user'
                    ? 'bg-[#FFD230] text-[#111111] rounded-[24px] rounded-br-[8px] px-6 py-4'
                    : 'bg-[#F3F4F6] text-[#111111] rounded-[24px] rounded-bl-[8px] px-6 py-4 shadow-sm border-none'
                }`}
              >
                {msg.role === 'assistant' && (
                  <div className="flex items-center gap-3 mb-2.5">
                    <div className="w-8 h-8 rounded-full border-2 border-[#2563EB] bg-white flex items-center justify-center shrink-0">
                      <div className="w-2.5 h-2.5 bg-[#111111] rounded-full"></div>
                    </div>
                    <span className="text-[13px] font-bold text-[#111111]">
                      SuperRAG
                    </span>
                  </div>
                )}

                {/* Message body */}
                <div className={`whitespace-pre-wrap leading-relaxed text-[15px] ${msg.role === 'assistant' ? 'markdown-body text-[#111111]' : 'text-[#111111]'}`}>
                  {msg.role === 'assistant' ? (
                    <>
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                      <div className="text-[11px] text-gray-500 mt-2 text-left">10:30 AM</div>
                    </>
                  ) : (
                    <>
                      {msg.content}
                      <div className="text-[11px] text-gray-600 mt-2 text-right">10:30 AM</div>
                    </>
                  )}
                </div>

                {/* Assistant Message Actions (Copy / Share) */}
                {msg.role === 'assistant' && (
                  <div className="mt-4 flex flex-wrap items-center gap-3">
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(msg.content);
                        addToast('Copied to clipboard!', 'success');
                      }}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white hover:bg-gray-50 text-[#111111] transition-colors border border-[#E5E7EB] text-xs font-medium shadow-sm"
                    >
                      <Copy size={14} /> Copy
                    </button>
                    <button
                      onClick={async () => {
                        const shareText = `Check out this response from SuperRAG:

${msg.content}`;
                        if (navigator.share) {
                          try {
                            await navigator.share({ title: 'SuperRAG Response', text: shareText });
                          } catch (err) {
                            console.log('Share cancelled');
                          }
                        } else {
                          navigator.clipboard.writeText(shareText);
                          addToast('Copied to clipboard (Share not supported)!', 'success');
                        }
                      }}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white hover:bg-gray-50 text-[#111111] transition-colors border border-[#E5E7EB] text-xs font-medium shadow-sm"
                    >
                      <Share size={14} /> Share
                    </button>
                  </div>
                )}
                
                {/* Confidence Badge */}
                {msg.confidence && msg.confidence.score > 0 && (
                  <div className="mt-3 flex items-center gap-2">
                    <span
                      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border"
                      style={{
                        backgroundColor: `${confColor[msg.confidence.label] || '#6b7280'}18`,
                        borderColor: `${confColor[msg.confidence.label] || '#6b7280'}35`,
                        color: confColor[msg.confidence.label] || '#9ca3af',
                      }}
                    >
                      {msg.confidence.emoji}
                      <span>{msg.confidence.label} Confidence</span>
                      <span className="opacity-70">({msg.confidence.score}/10)</span>
                    </span>
                  </div>
                )}

                {/* Source Citations */}
                {msg.docs && msg.docs.length > 0 && (
                  <div className="mt-4 border-t border-gray-200 pt-3">
                    <button
                      id={`citations-toggle-${idx}`}
                      onClick={() => toggleCitations(idx)}
                      className="flex items-center gap-2 text-xs text-[#2563EB] hover:text-blue-700 transition-colors font-semibold"
                    >
                      <svg
                        className={`w-3.5 h-3.5 transition-transform duration-200 ${expandedCitations.has(idx) ? 'rotate-90' : ''}`}
                        fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                      </svg>
                      {msg.docs.length} Source{msg.docs.length > 1 ? 's' : ''} cited
                    </button>

                    {expandedCitations.has(idx) && (
                      <div className="mt-3 space-y-2">
                        {msg.docs.map((doc, di) => (
                          <div
                            key={di}
                            className="bg-white rounded-xl p-3 border border-gray-200 shadow-sm"
                          >
                            <div className="flex items-center gap-2 mb-1.5">
                              <span className="text-[#2563EB] text-xs"><FileText size={12} /></span>
                              <span className="text-xs font-semibold text-[#111111] truncate">
                                {doc.file}
                              </span>
                              {doc.page !== 'N/A' && (
                                <span className="ml-auto shrink-0 bg-[#EBF1FF] text-[#2563EB] text-[10px] font-medium px-2.5 py-0.5 rounded-full">
                                  Page {doc.page}
                                </span>
                              )}
                            </div>
                            <p className="text-[11px] text-gray-600 leading-relaxed line-clamp-3">
                              {doc.snippet}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Live status ticker */}
          {liveStatus && (
            <div className="flex justify-start">
              <div className="bg-[#EBF1FF] text-[#2563EB] rounded-[24px] rounded-bl-[8px] px-5 py-3.5 flex items-center gap-3 max-w-[78%]">
                <div className="relative shrink-0">
                  <div className="w-4 h-4 border-2 border-[#2563EB] border-t-transparent rounded-full animate-spin" />
                </div>
                <span className="text-sm font-medium animate-pulse">{liveStatus}</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="shrink-0 border-t border-[#E5E7EB] bg-white p-6 z-10">
          <form onSubmit={handleSend} className="max-w-4xl mx-auto flex gap-3 items-end relative">
            <div className="flex-1 relative">
              <textarea
                id="chat-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend(e as unknown as React.FormEvent);
                  }
                }}
                placeholder="Type your message..."
                disabled={!isInitialized || isGenerating}
                rows={1}
                className="w-full bg-white border-[1.5px] border-[#E5E7EB] text-[#111111] rounded-full
                  py-4 pl-6 pr-16 resize-none
                  focus:outline-none focus:border-[#2563EB] focus:ring-0
                  disabled:opacity-50 text-[15px] leading-relaxed
                  transition-all shadow-sm placeholder:text-gray-400"
                style={{ maxHeight: '120px', overflowY: 'auto' }}
              />
              <button
                type="submit"
                id="send-btn"
                disabled={!input.trim() || !isInitialized || isGenerating}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 h-[40px] w-[40px] rounded-full flex items-center justify-center
                  bg-[#2563EB] hover:bg-blue-700
                  disabled:bg-gray-200 disabled:text-gray-400
                  text-white shadow-md transition-all duration-200 z-10"
              >
                {isGenerating ? (
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                ) : (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
                )}
              </button>
            </div>
          </form>
          <p className="text-center text-[11px] text-gray-400 mt-3 font-medium">
            Enter to send · Shift+Enter for new line
          </p>
        </div>

      </main>
      {/* Right Decorative Strip */}
      <aside className="hidden lg:flex w-[10%] border-l border-[#E5E7EB] bg-white flex-col h-full shrink-0">
        <div className="flex-1 bg-[#FFD230]"></div>
        <div className="flex-1 bg-[#2563EB]"></div>
        <div className="flex-[2] bg-[#EF4444]"></div>
        <div className="pb-[100%] bg-[#111111] rounded-tl-full mt-auto relative"><div className="absolute inset-0"></div></div>
      </aside>
    </div>
  );
}
