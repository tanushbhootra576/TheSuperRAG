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
        'Hello! I am **TheSuperRAG v2** — powered by hybrid search, cross-encoder re-ranking, and self-healing. I cite my sources and show a confidence score with every answer.\n\nInitialise the database in the sidebar to begin.',
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
    <div className="flex h-screen bg-transparent text-slate-100 font-sans overflow-hidden">

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
                <label className="text-xs font-semibold text-slate-400 mb-2 block">LLM Provider</label>
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
                  <label className="text-xs font-semibold text-slate-400">Temperature (Creativity)</label>
                  <span className="text-xs text-white font-medium">{temperature.toFixed(1)}</span>
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
                  <p className="text-[10px] text-slate-500">Improves accuracy, slightly slower.</p>
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
                <p className="text-slate-500 font-medium">No graph data extracted.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Sidebar Overlay ─────────────────────────────────────────────────── */}
      {isSidebarOpen && <div className="fixed inset-0 bg-black/60 z-30 md:hidden" onClick={() => setIsSidebarOpen(false)} />}

      {/* ── Sidebar ───────────────────────────────────────────────────────── */}
      <aside className={`fixed md:static inset-y-0 left-0 w-80 glass-panel border-r border-slate-800/50 flex flex-col z-40 transition-transform duration-300 ${isSidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}`}>
        {/* Gradient accent bar */}
        <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-slate-700 to-slate-800" />

        {/* Branding */}
        <div className="p-6 pb-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold  text-white">
              TheSuperRAG v2
            </h1>
            <p className="text-xs text-slate-500 mt-0.5">Self-Healing · Hybrid · Re-Ranked</p>
          </div>
          <button
            onClick={() => setIsSettingsOpen(true)}
            className="text-slate-400 hover:text-white transition-colors bg-slate-900 hover:bg-slate-800 p-2 rounded-lg border border-slate-800/60"
            title="Settings"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 15a3 3 0 100-6 3 3 0 000 6z"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
          </button>
        </div>

        {/* System Status */}
        <div className="px-6 pb-4">
          <div className="glass-panel rounded-xl p-4 border border-slate-800/60 bg-slate-950/40 relative overflow-hidden group hover:border-slate-700/80 transition-all duration-300">
            <div className="absolute inset-0 bg-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3 relative z-10">
              System Status
            </p>
            <div className="flex items-center gap-2.5 mb-3 relative z-10">
              <div
                className={`w-2 h-2 rounded-full transition-all ${
                  isInitialized
                    ? 'bg-emerald-400 '
                    : 'bg-red-400 '
                }`}
              />
              <span className="text-sm font-medium text-slate-100 drop-shadow-md">
                {isInitialized ? 'Active & Ready' : 'Offline'}
              </span>
            </div>
            {isInitialized && (
              <div className="space-y-1 text-xs">
                <div className="flex items-center gap-1.5 text-slate-400">
                  <span>{hybridEnabled ? 'Hybrid Search (Dense + BM25)' : 'Dense Search'}</span>
                </div>
                <div className="flex items-center gap-1.5 text-slate-400">
                  <span>Cross-Encoder Re-ranking: ON</span>
                </div>
              </div>
            )}
            {!isInitialized && (
              <button
                id="init-btn"
                onClick={handleInit}
                disabled={isInitializing}
                className="mt-3 w-full py-2.5 rounded-lg text-sm font-semibold transition-all
                  bg-white text-black
                  hover:bg-slate-200
                  
                  disabled:opacity-50 disabled:shadow-none"
              >
                {isInitializing ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                    Indexing…
                  </span>
                ) : (
                  'Initialize Database'
                )}
              </button>
            )}
          </div>
        </div>

        {/* Tabs: Documents | Upload | History | Graph */}
        {isInitialized && (
          <div className="px-6 flex gap-1 mb-2">
            {(['documents', 'upload', 'history', 'graph'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex-1 py-1.5 text-[10px] font-semibold rounded-lg transition-all capitalize
                  ${activeTab === tab
                    ? 'bg-slate-800 text-white border border-slate-700'
                    : 'text-slate-500 hover:text-slate-300'
                  }`}
              >
                {tab === 'documents' ? 'Docs' : tab === 'upload' ? 'Upload' : tab === 'history' ? 'Hist' : 'Graph'}
              </button>
            ))}
          </div>
        )}

        {/* Document Manager */}
        {isInitialized && activeTab === 'documents' && (
          <div className="px-6 flex-1 overflow-y-auto pb-6">
            <div className="glass-panel rounded-xl border border-slate-800/60 overflow-hidden bg-slate-950/40">
              <div className="px-4 py-3 border-b border-slate-800/60 flex items-center justify-between bg-slate-900/40">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                  Indexed Documents
                </p>
                {selectedDocs.length > 0 && (
                  <button
                    onClick={() => setSelectedDocs([])}
                    className="text-[10px] text-white hover:text-white"
                  >
                    Clear filter
                  </button>
                )}
              </div>

              {documents.length === 0 ? (
                <p className="p-4 text-xs text-slate-500 text-center">
                  No documents indexed. Upload PDFs to get started.
                </p>
              ) : (
                <ul className="divide-y divide-slate-800/60">
                  {documents.map((doc) => {
                    const isSelected = selectedDocs.includes(doc);
                    const isDeleting = deletingDoc === doc;
                    return (
                      <li
                        key={doc}
                        className={`flex items-center gap-3 px-4 py-2.5 transition-colors
                          ${isSelected ? 'bg-sky-500/5' : 'hover:bg-slate-800/40'}`}
                      >
                        {/* Checkbox / selection */}
                        <button
                          id={`doc-select-${doc}`}
                          onClick={() => toggleDocSelection(doc)}
                          className={`w-4 h-4 rounded border-2 flex items-center justify-center shrink-0 transition-all
                            ${isSelected
                              ? 'bg-sky-500 border-sky-500'
                              : 'border-slate-600 hover:border-sky-400'
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
                            ${isSelected ? 'text-white' : 'text-slate-300'}`}
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
                          className="text-slate-600 hover:text-red-400 transition-colors shrink-0 disabled:opacity-40"
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
                <div className="px-4 py-2.5 border-t border-slate-800 bg-slate-900/60">
                  <p className="text-[10px] text-slate-500">
                     Searching: <span className="text-white font-medium">{searchScopeLabel}</span>
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
                  ? 'border-sky-400 bg-slate-800/50 scale-[1.02]'
                  : 'border-slate-700 hover:border-sky-600 hover:bg-sky-500/5'
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
                  <p className="text-sm text-white font-medium">Uploading & indexing…</p>
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
                    <p className="text-xs text-slate-500 mt-1">or click to browse</p>
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
                      : 'bg-slate-900/40 border-slate-800/60 text-slate-400 hover:bg-slate-800/60'
                  }`}
                >
                  <p className="font-medium truncate">{s.title}</p>
                  <p className="text-[10px] opacity-60 mt-1">{new Date(s.updated_at).toLocaleString()}</p>
                </button>
              ))}
              {sessions.length === 0 && (
                <p className="text-xs text-center text-slate-500 mt-4">No chat history found.</p>
              )}
            </div>
          </div>
        )}

        {/* Graph Panel */}
        {isInitialized && activeTab === 'graph' && (
          <div className="px-2 flex-1 overflow-hidden pb-6">
            <div className="flex items-center justify-between px-4 mb-2">
              <h3 className="text-xs font-semibold text-slate-400">Knowledge Graph</h3>
              <button 
                onClick={() => setIsGraphExpanded(true)}
                className="text-slate-500 hover:text-white transition-colors p-1 bg-slate-800/50 rounded-md"
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
                <div className="absolute inset-0 flex items-center justify-center p-4 text-center text-xs text-slate-500">
                  No graph entities extracted yet.
                </div>
              )}
            </div>
          </div>
        )}

        {/* Metrics */}
        <div className="px-6 py-4 border-t border-slate-800/60 mt-auto shrink-0">
          <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3">
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
                <p className="text-[10px] text-slate-500 mt-0.5">{label}</p>
              </div>
            ))}
          </div>
        </div>
      </aside>

      {/* ── Main Chat Area ────────────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col relative overflow-hidden bg-transparent">
        {/* Subtle background glow */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(14,165,233,0.08),transparent)] pointer-events-none z-0" />

        {/* Header */}
        <div className="border-b border-slate-800/40 glass-panel px-8 py-4 shrink-0 z-10">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-slate-200 text-sm">Document Intelligence Chat</h2>
              <p className="text-xs text-slate-500 mt-0.5">
                {isInitialized
                  ? `Searching ${selectedDocs.length > 0 ? `${selectedDocs.length} selected` : 'all'} document(s)`
                  : 'Initialise to begin'}
              </p>
            </div>
            <div className="flex items-center gap-3">
              {isInitialized && (
                <button onClick={exportChat} className="text-xs text-slate-400 hover:text-slate-200 border border-slate-700 rounded-md px-2 py-1 transition-colors">
                  Export Markdown
                </button>
              )}
              {isInitialized && selectedDocs.length > 0 && (
                <div className="flex items-center gap-2 bg-slate-800/50 border border-sky-500/25 rounded-full px-3 py-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-pulse" />
                  <span className="text-xs text-white font-medium">
                    Filtered: {selectedDocs.length} doc{selectedDocs.length > 1 ? 's' : ''}
                  </span>
                  <button onClick={() => setSelectedDocs([])} className="text-sky-600 hover:text-white ml-1 text-xs">✕</button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6 z-0">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[78%] rounded-2xl ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-br from-sky-500 to-indigo-600 text-white rounded-br-sm shadow-[0_4px_20px_rgba(14,165,233,0.3)] px-5 py-4'
                    : 'glass-panel text-slate-100 rounded-bl-sm shadow-[0_4px_20px_rgba(0,0,0,0.3)] px-5 py-4 border border-slate-800/60 bg-slate-900/50'
                }`}
              >
                {msg.role === 'assistant' && (
                  <div className="flex items-center gap-2 mb-2.5">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg">
                      <MessageSquare size={12} color="white" />
                    </div>
                    <span className="text-[10px] font-bold text-slate-300 uppercase tracking-widest">
                      SuperRAG
                    </span>
                  </div>
                )}

                {/* Message body */}
                <div className={`whitespace-pre-wrap leading-relaxed text-[14.5px] ${msg.role === 'assistant' ? 'markdown-body text-slate-200' : 'text-white'}`}>
                  {msg.role === 'assistant' ? (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                  ) : (
                    msg.content
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
                      className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-slate-800/60 hover:bg-slate-700/80 text-slate-400 hover:text-white transition-colors border border-slate-700/50 text-xs font-medium"
                    >
                      <Copy size={13} /> Copy
                    </button>
                    <button
                      onClick={async () => {
                        const shareText = `Check out this response from SuperRAG:\n\n${msg.content}`;
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
                      className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-slate-800/60 hover:bg-slate-700/80 text-slate-400 hover:text-white transition-colors border border-slate-700/50 text-xs font-medium"
                    >
                      <Share size={13} /> Share
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
                  <div className="mt-3 border-t border-slate-700/40 pt-3">
                    <button
                      id={`citations-toggle-${idx}`}
                      onClick={() => toggleCitations(idx)}
                      className="flex items-center gap-2 text-xs text-white hover:text-white transition-colors font-medium"
                    >
                      <svg
                        className={`w-3.5 h-3.5 transition-transform duration-200 ${expandedCitations.has(idx) ? 'rotate-90' : ''}`}
                        fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                      </svg>
                      {msg.docs.length} Source{msg.docs.length > 1 ? 's' : ''} cited
                    </button>

                    {expandedCitations.has(idx) && (
                      <div className="mt-2 space-y-2">
                        {msg.docs.map((doc, di) => (
                          <div
                            key={di}
                            className="bg-slate-900/60 rounded-lg p-3 border border-slate-700/30"
                          >
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-white text-xs"></span>
                              <span className="text-xs font-semibold text-slate-200 truncate">
                                {doc.file}
                              </span>
                              {doc.page !== 'N/A' && (
                                <span className="ml-auto shrink-0 bg-slate-700 text-slate-400 text-[10px] px-2 py-0.5 rounded-full">
                                  Page {doc.page}
                                </span>
                              )}
                            </div>
                            <p className="text-[11px] text-slate-500 leading-relaxed line-clamp-2">
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
              <div className="bg-slate-800/50 border border-sky-500/20 backdrop-blur-sm rounded-2xl rounded-bl-sm px-5 py-3.5 flex items-center gap-3 max-w-[78%]">
                <div className="relative shrink-0">
                  <div className="w-4 h-4 border-2 border-sky-400 border-t-transparent rounded-full animate-spin" />
                </div>
                <span className="text-sm text-white/90 animate-pulse">{liveStatus}</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="shrink-0 border-t border-slate-800/40 glass-panel p-5 z-10">
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
                placeholder={
                  !isInitialized
                    ? 'Initialise the database first…'
                    : selectedDocs.length > 0
                    ? `Search in ${selectedDocs.length} selected document(s)…`
                    : 'Ask about your policies, regulations, or documentation…'
                }
                disabled={!isInitialized || isGenerating}
                rows={1}
                className="w-full bg-slate-900/60 border border-slate-700/60 text-white rounded-xl
                  py-3.5 pl-5 pr-12 resize-none
                  focus:outline-none focus:border-sky-500/50 focus:ring-1 focus:ring-sky-500/30
                  disabled:opacity-50 text-[14.5px] leading-relaxed
                  transition-all shadow-[inset_0_2px_4px_rgba(0,0,0,0.2)] placeholder:text-slate-600 backdrop-blur-sm"
                style={{ maxHeight: '120px', overflowY: 'auto' }}
              />
              <button
                type="button"
                onClick={() => setIsRecording(!isRecording)}
                className={`absolute right-3 top-1/2 -translate-y-1/2 p-1.5 rounded-lg transition-all ${
                  isRecording ? 'text-red-400 bg-red-400/10 animate-pulse' : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
                }`}
              >
                <Mic size={18} />
              </button>
            </div>
            <button
              type="submit"
              id="send-btn"
              disabled={!input.trim() || !isInitialized || isGenerating}
              className="shrink-0 h-12 w-12 rounded-xl flex items-center justify-center
                bg-gradient-to-br from-sky-500 to-indigo-600
                hover:bg-slate-200
                disabled:bg-slate-800 disabled:text-slate-500
                text-white shadow-[0_0_20px_rgba(14,165,233,0.3)]
                hover:shadow-[0_0_25px_rgba(14,165,233,0.5)]
                disabled:shadow-none
                transition-all duration-200"
            >
              {isGenerating ? (
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
              ) : (
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.269 20.876L5.999 12zm0 0h7.5" />
                </svg>
              )}
            </button>
          </form>
          <p className="text-center text-[11px] text-slate-600 mt-2">
            Enter to send · Shift+Enter for new line
          </p>
        </div>
      </main>
    </div>
  );
}
