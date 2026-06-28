'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import dynamic from 'next/dynamic';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Link from 'next/link';
import { Mic, Send, Copy, Share, Edit2, Trash2, Maximize2, Minimize2, Settings, FileText, UploadCloud, MessageSquare, Plus, ChevronDown, ChevronRight, Check, Menu, Clock, Network, Database, Home } from 'lucide-react';

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
export default function ChatPage() {
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
  
  //Settings and UI modal states
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isDocsOpen, setIsDocsOpen] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isMemoryOpen, setIsMemoryOpen] = useState(false);
  const [memoryText, setMemoryText] = useState('');

  const fetchMemory = async () => {
    try {
      const res = await fetch(`${API}/user/memory`);
      if (res.ok) {
        const data = await res.json();
        setMemoryText(data.memory || '');
      }
    } catch {}
  };

  const saveMemory = async () => {
    try {
      const res = await fetch(`${API}/user/memory`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ memory: memoryText }),
      });
      if (res.ok) {
        addToast('Memory updated', 'success');
        setIsMemoryOpen(false);
      } else {
        addToast('Failed to save memory', 'error');
      }
    } catch {
      addToast('Error saving memory', 'error');
    }
  };

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const toastCounter = useRef(0);


  // ── Voice Input & TTS (P3.4) ──────────────────────────────────────────────
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const handleStartRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('file', audioBlob, 'recording.webm');
        
        try {
          addToast('Transcribing audio...', 'info');
          const res = await fetch(API + '/api/voice/transcribe', {
            method: 'POST',
            body: formData,
          });
          if (res.ok) {
            const data = await res.json();
            setInput((prev) => prev + (prev ? ' ' : '') + data.transcript);
            addToast(`Transcribed (Confidence: ${data.confidence})`, 'success');
          } else {
            addToast('Transcription failed', 'error');
          }
        } catch (err) {
          addToast('Transcription error', 'error');
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      addToast('Microphone access denied or error', 'error');
    }
  };

  const handleStopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop());
    }
  };

  const playTTS = async (text: string) => {
    try {
      addToast('Synthesizing speech...', 'info');
      const res = await fetch(API + '/api/voice/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, voice: 'neutral', speed: 1.0 }),
      });
      if (!res.ok) throw new Error('TTS failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.play();
    } catch (err) {
      addToast('Could not play audio', 'error');
    }
  };

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
    if (isGraphExpanded) {
      fetchGraph();
    }
  }, [isGraphExpanded]);


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

  // SSE: auto-indexing notifications from POST /upload
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
          llm_model: 'llama-3.1-8b-instant',
          temperature: 0.0,
          use_cross_encoder: true,
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
            } else if (parsed.type === 'decomposed') {
              setLiveStatus(` Analyzing ${parsed.sub_queries?.length || 1} distinct parts of your question...`);
            } else if (parsed.type === 'tool_start') {
              const toolName = parsed.tool === 'web_search' ? 'Web' : parsed.tool === 'sql_query' ? 'Database' : 'Knowledge Base';
              setLiveStatus(` Querying ${toolName}: "${parsed.query}"`);
            } else if (parsed.type === 'tool_done') {
              const toolName = parsed.tool === 'web_search' ? 'Web' : parsed.tool === 'sql_query' ? 'Database' : 'Knowledge Base';
              setLiveStatus(` Found ${parsed.result_count} results from ${toolName}`);
            } else if (parsed.type === 'metadata') {
              setLiveStatus(` Synthesizing answer from sources...`);
            } else if (parsed.type === 'token') {
              setMessages((prev) => {
                const newMsgs = [...prev];
                const last = { ...newMsgs[newMsgs.length - 1] };
                if (last.role === 'assistant') {
                  last.content += parsed.content;
                }
                newMsgs[newMsgs.length - 1] = last;
                return newMsgs;
              });
            } else if (parsed.type === 'final') {
              setMessages((prev) => {
                const newMsgs = [...prev];
                const last = { ...newMsgs[newMsgs.length - 1] };
                if (last.role === 'assistant') {
                  if (parsed.message && !last.content) {
                    last.content = parsed.message;
                  }
                  last.docs = parsed.docs || [];
                  last.confidence = parsed.confidence;
                }
                newMsgs[newMsgs.length - 1] = last;
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

  const uploadFiles = async (files: FileList | File[]) => {
    const supportedExts = ['.pdf', '.docx', '.txt', '.md', '.csv', '.xlsx', '.pptx', '.png', '.jpg', '.jpeg', '.bmp', '.tiff'];
    const validFiles = Array.from(files).filter((f) => supportedExts.some(ext => f.name.toLowerCase().endsWith(ext)));
    if (!validFiles.length) {
      addToast('Please select supported files only.', 'error');
      return;
    }
    setUploading(true);
    let uploaded = 0;
    for (const file of validFiles) {
      try {
        const fd = new FormData();
        fd.append('file', file);
        if (sessionId) fd.append('session_id', sessionId);
        const res = await fetch(`${API}/upload`, { method: 'POST', body: fd });
        if (res.ok) {
          uploaded++;
          await fetchDocuments();
        }
      } catch {}
    }
    setUploading(false);
    if (uploaded > 0) addToast(`${uploaded} file(s) uploaded and indexed.`, 'success');
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

      {/* ──Upload Modal ────────────────────────────────────────────────── */}
      {isUploadOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-200" onClick={() => setIsUploadOpen(false)}>
          <div className="w-full max-w-[500px] bg-white border-[3px] border-[#111111] p-6 shadow-[8px_8px_0px_0px_rgba(17,17,17,1)] relative" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-black text-[#111111] uppercase tracking-tight flex items-center gap-2">
                <UploadCloud size={24} className="text-[#2563EB]"/> Ingest Data
              </h3>
              <button onClick={() => setIsUploadOpen(false)} className="text-[#111111] hover:text-[#EF4444] transition-colors"><Plus className="w-8 h-8 rotate-45" strokeWidth={3} /></button>
            </div>
            
            <div className="flex flex-col gap-6">
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Or paste a URL (Web page or YouTube)"
                  className="flex-1 px-4 py-3 text-sm bg-white border-[2px] border-[#111111] text-[#111111] focus:outline-none focus:border-[#2563EB] focus:ring-0 placeholder:text-gray-400 font-medium"
                  onKeyDown={async (e) => {
                    if (e.key === 'Enter') {
                      const url = e.currentTarget.value.trim();
                      if (!url) return;
                      e.currentTarget.value = '';
                      setUploading(true);
                      try {
                        const fd = new FormData();
                        fd.append('url', url);
                        if (sessionId) fd.append('session_id', sessionId);
                        const res = await fetch(`${API}/upload`, { method: 'POST', body: fd });
                        if (res.ok) {
                          addToast(`URL indexed successfully.`, 'success');
                          fetchDocuments();
                        } else {
                          addToast(`Failed to index URL.`, 'error');
                        }
                      } catch {
                        addToast(`Failed to index URL.`, 'error');
                      }
                      setUploading(false);
                    }
                  }}
                />
              </div>
              
              <div
                id="upload-dropzone"
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`
                  relative border-[3px] border-dashed border-[#111111] p-10 text-center cursor-pointer
                  transition-all duration-200 select-none bg-gray-50
                  ${isDragging
                    ? 'border-[#2563EB] bg-[#2563EB]/10 scale-[1.02]'
                    : 'hover:border-[#2563EB] hover:bg-[#FFD230]/10'
                  }
                  ${uploading ? 'pointer-events-none opacity-60' : ''}
                `}
              >
                {uploading ? (
                  <div className="flex flex-col items-center gap-4">
                    <svg className="animate-spin h-10 w-10 text-[#2563EB]" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                    <p className="text-sm text-[#111111] font-bold uppercase tracking-widest">Uploading & indexing…</p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-4">
                    <div className={`transition-transform duration-200 ${isDragging ? 'scale-110 text-[#2563EB]' : 'text-[#111111]'}`}>
                      <UploadCloud className="h-12 w-12" strokeWidth={2} />
                    </div>
                    <div>
                      <p className="text-base font-black text-[#111111] uppercase">
                        {isDragging ? 'Drop to upload' : 'Drop files here or click to browse'}
                      </p>
                      <p className="text-xs text-gray-500 mt-2 font-medium">PDF, DOCX, TXT, CSV, PPTX, Images</p>
                    </div>
                  </div>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.txt,.md,.csv,.xlsx,.pptx,.png,.jpg,.jpeg,.bmp,.tiff"
                  multiple
                  className="hidden"
                  onChange={(e) => e.target.files && uploadFiles(e.target.files)}
                />
              </div>

              <p className="text-[11px] text-gray-500 font-medium text-center">
                 You can also drop files directly into the DATA/ folder — they'll be auto-indexed instantly.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ──Docs Library Modal ────────────────────────────────────────────────── */}
      {isDocsOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-200" onClick={() => setIsDocsOpen(false)}>
          <div className="w-full max-w-[600px] max-h-[80vh] flex flex-col bg-white border-[3px] border-[#111111] p-6 shadow-[8px_8px_0px_0px_rgba(17,17,17,1)] relative" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-6 shrink-0">
              <h3 className="text-xl font-black text-[#111111] uppercase tracking-tight flex items-center gap-2">
                <Database size={24} className="text-[#FFD230]" strokeWidth={2.5}/> Docs Library
              </h3>
              <button onClick={() => setIsDocsOpen(false)} className="text-[#111111] hover:text-[#EF4444] transition-colors"><Plus className="w-8 h-8 rotate-45" strokeWidth={3}/></button>
            </div>
            
            <div className="flex-1 overflow-y-auto min-h-0 bg-white border-[2px] border-[#111111]">
              <div className="px-4 py-3 border-b-[2px] border-[#111111] flex items-center justify-between sticky top-0 bg-gray-50 z-10">
                <p className="text-[11px] font-black text-[#111111] uppercase tracking-widest">
                  Indexed Documents
                </p>
                {selectedDocs.length > 0 && (
                  <button
                    onClick={() => setSelectedDocs([])}
                    className="text-[11px] text-[#2563EB] hover:text-blue-700 font-black uppercase transition-colors"
                  >
                    Clear filter
                  </button>
                )}
              </div>

              {documents.length === 0 ? (
                <p className="p-8 text-sm text-gray-500 font-medium text-center">
                  No documents indexed. Upload files to get started.
                </p>
              ) : (
                <ul className="divide-y-[2px] divide-[#111111]">
                  {documents.map((doc) => {
                    const isSelected = selectedDocs.includes(doc);
                    const isDeleting = deletingDoc === doc;
                    return (
                      <li
                        key={doc}
                        className={`flex items-center gap-3 px-4 py-3 transition-colors
                          ${isSelected ? 'bg-[#FFD230]/20' : 'hover:bg-gray-50'}`}
                      >
                        {/* Checkbox / selection */}
                        <button
                          onClick={() => toggleDocSelection(doc)}
                          className={`w-5 h-5 border-[2px] flex items-center justify-center shrink-0 transition-all
                            ${isSelected ? 'bg-[#2563EB] border-[#2563EB]' : 'bg-white border-[#111111] hover:border-[#2563EB]'
                            }`}
                        >
                          {isSelected && <Check className="w-4 h-4 text-white" strokeWidth={4} />}
                        </button>

                        {/* Filename */}
                        <span
                          className={`flex-1 text-sm truncate cursor-pointer transition-colors
                            ${isSelected ? 'text-[#111111] font-black' : 'text-gray-700 font-semibold'}`}
                          onClick={() => toggleDocSelection(doc)}
                          title={doc}
                        >
                          {doc}
                        </span>

                        {/* Delete */}
                        <button
                          onClick={() => handleDeleteDoc(doc)}
                          disabled={isDeleting}
                          className="text-[#111111] hover:text-[#EF4444] transition-colors shrink-0 disabled:opacity-40 p-1"
                          title={`Delete ${doc}`}
                        >
                          {isDeleting ? (
                            <svg className="animate-spin w-5 h-5" viewBox="0 0 24 24" fill="none">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                            </svg>
                          ) : (
                            <Trash2 className="w-5 h-5" strokeWidth={2.5}/>
                          )}
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
            
            {/* Search scope indicator */}
            {documents.length > 0 && (
              <div className="mt-5 shrink-0 flex items-center justify-between">
                <p className="text-xs text-gray-600 font-medium">
                   Searching scope: <span className="text-[#111111] font-black uppercase">{searchScopeLabel}</span>
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ──Settings Modal Removed ────────────────────────────────────────── */}
      {/* Fullscreen Graph Overlay */}
      {isGraphExpanded && (
        <div className="fixed inset-0 z-50 bg-black/90 flex flex-col items-center justify-center backdrop-blur-sm">
          <div className="absolute top-6 right-6 z-50">
            <button
              onClick={() => setIsGraphExpanded(false)}
              className="p-3 bg-white text-[#111111] border-[3px] border-[#111111] shadow-[4px_4px_0px_0px_rgba(17,17,17,1)] active:shadow-none active:translate-y-1 active:translate-x-1 hover:bg-[#EF4444] hover:text-white transition-all"
            >
              <Minimize2 size={24} strokeWidth={3} />
            </button>
          </div>
          <div className="w-[90vw] h-[90vh] bg-white border-[4px] border-[#111111] overflow-hidden relative shadow-[16px_16px_0px_0px_rgba(17,17,17,1)]">
            {graphData.nodes.length > 0 ? (
              <ForceGraph2D
                graphData={graphData}
                width={typeof window !== 'undefined' ? window.innerWidth * 0.9 : 800}
                height={typeof window !== 'undefined' ? window.innerHeight * 0.9 : 600}
                nodeAutoColorBy="group"
                nodeLabel="id"
                linkDirectionalArrowLength={4}
                linkDirectionalArrowRelPos={1}
                linkColor={() => '#111111'}
                backgroundColor="#ffffff"
              />
            ) : (
              <div className="absolute inset-0 flex items-center justify-center">
                <p className="text-[#111111] font-black uppercase tracking-widest text-xl">No graph data extracted.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Sidebar Overlay ─────────────────────────────────────────────────── */}
      {isSidebarOpen && <div className="fixed inset-0 bg-black/60 z-30 md:hidden" onClick={() => setIsSidebarOpen(false)} />}

      {/* ── Sidebar ───────────────────────────────────────────────────────── */}
      <aside className={`fixed md:static inset-y-0 left-0 w-80 max-w-[85vw] md:w-[22%] md:max-w-none bg-white border-r border-[#E5E7EB] flex flex-col z-40 transition-transform duration-300 ${isSidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}`}>
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

        {/* Permanent History Panel */}
        {isInitialized && (
          <div className="px-6 flex-1 overflow-y-auto pb-6 mt-6">
            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-3">
              Recent Chats
            </p>
            <button
              onClick={createSession}
              className="w-full py-2.5 mb-4 rounded-xl text-[13px] font-semibold bg-[#111111] hover:bg-[#333333] text-white transition-all shadow-sm"
            >
              + New Chat
            </button>
            <div className="space-y-2">
              {sessions.map((s) => (
                <div
                  key={s.id}
                  className={`relative w-full text-left p-3 rounded-xl border text-sm transition-all group ${
                    sessionId === s.id
                      ? 'bg-white border-[#2563EB] shadow-sm text-[#111111]'
                      : 'bg-transparent border-transparent text-gray-500 hover:bg-white hover:border-gray-200'
                  }`}
                >
                  {editingSessionId === s.id ? (
                    <div className="flex items-center gap-2">
                      <input 
                        type="text" 
                        value={editingTitle} 
                        onChange={(e) => setEditingTitle(e.target.value)} 
                        onKeyDown={(e) => { if (e.key === 'Enter') saveSessionName(s.id); }}
                        className="w-full border rounded px-2 py-1 text-xs focus:outline-none focus:border-[#2563EB]" 
                        autoFocus 
                        onClick={(e) => e.stopPropagation()}
                      />
                      <button onClick={(e) => { e.stopPropagation(); saveSessionName(s.id); }}><Check className="w-4 h-4 text-green-500" /></button>
                    </div>
                  ) : (
                    <div onClick={() => loadSession(s.id)} className="w-full cursor-pointer">
                      <p className="font-medium truncate pr-10">{s.title}</p>
                      <p className="text-[10px] opacity-60 mt-1">{new Date(s.updated_at).toLocaleString()}</p>
                    </div>
                  )}
                  {editingSessionId !== s.id && (
                    <div className="absolute top-3 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button onClick={(e) => { e.stopPropagation(); setEditingTitle(s.title); setEditingSessionId(s.id); }} className="p-1 hover:bg-gray-100 rounded text-gray-500 hover:text-blue-500"><Edit2 className="w-3.5 h-3.5" /></button>
                      <button onClick={(e) => deleteSession(s.id, e)} className="p-1 hover:bg-gray-100 rounded text-gray-500 hover:text-red-500"><Trash2 className="w-3.5 h-3.5" /></button>
                    </div>
                  )}
                </div>
              ))}
              {sessions.length === 0 && (
                <p className="text-xs text-center text-gray-500 mt-4">No chat history found.</p>
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
        
        {/* Memory Editor Modal */}
        {isMemoryOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="bg-white rounded-2xl w-full max-w-md shadow-2xl overflow-hidden flex flex-col">
              <div className="p-4 border-b flex justify-between items-center">
                <h3 className="font-bold text-gray-800">User Memory Editor</h3>
                <button onClick={() => setIsMemoryOpen(false)} className="text-gray-400 hover:text-gray-600">×</button>
              </div>
              <div className="p-4">
                <p className="text-xs text-gray-500 mb-2">Edit what the system remembers about you.</p>
                <textarea
                  className="w-full h-32 border rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={memoryText}
                  onChange={(e) => setMemoryText(e.target.value)}
                />
              </div>
              <div className="p-4 bg-gray-50 border-t flex justify-end gap-2">
                <button onClick={() => setIsMemoryOpen(false)} className="px-4 py-2 text-sm font-medium text-gray-600">Cancel</button>
                <button onClick={saveMemory} className="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-xl hover:bg-blue-700">Save</button>
              </div>
            </div>
          </div>
        )}

        {/* Floating Right Toolbar */}
        <div className="absolute right-4 md:right-6 top-6 flex flex-col gap-3 z-30">
          <Link href="/" title="Home" className="p-3 bg-white border border-[#E5E7EB] rounded-full shadow-sm hover:shadow-md hover:bg-[#F9FAFB] text-gray-500 hover:text-[#2563EB] transition-all group">
            <Home className="w-5 h-5 group-hover:scale-110 transition-transform" />
          </Link>
          <button 
            onClick={() => { setIsMemoryOpen(true); fetchMemory(); }} 
            title="Memory Editor" 
            className="p-3 bg-white border border-[#E5E7EB] rounded-full shadow-sm hover:shadow-md hover:bg-[#F9FAFB] text-gray-500 hover:text-purple-600 transition-all group"
          >
            <Settings className="w-5 h-5 group-hover:scale-110 transition-transform" />
          </button>
          <button 
            onClick={() => setIsGraphExpanded(true)} 
            className="p-3 bg-white border border-[#E5E7EB] rounded-full shadow-sm hover:shadow-md hover:bg-[#F9FAFB] text-gray-500 hover:text-[#10b981] transition-all group" 
            title="Knowledge Graph"
          >
            <Network className="w-5 h-5 group-hover:scale-110 transition-transform" />
          </button>

        </div>
        {/* Subtle background glow */}
        

        {/* Header */}
        <div className="w-full flex items-center justify-between md:justify-center py-4 px-4 md:px-0 md:py-6 shrink-0 z-10 bg-white border-b border-[#E5E7EB] md:border-none">
          <button className="md:hidden p-2 rounded-md hover:bg-gray-100" onClick={() => setIsSidebarOpen(true)}>
            <Menu size={24} />
          </button>
          <div className="flex items-center">
            <div className="hidden md:block w-24 h-[1px] bg-[#E5E7EB]"></div>
            <span className="mx-4 text-xs font-semibold text-[#111111] tracking-widest uppercase">Today</span>
            <div className="hidden md:block w-24 h-[1px] bg-[#E5E7EB]"></div>
          </div>
          <div className="w-10 md:hidden"></div> {/* Spacer for centering flex */}
        </div>
{/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6 z-0 max-w-4xl mx-auto w-full">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[90%] md:max-w-[78%] ${
                  msg.role === 'user'
                    ? 'bg-[#FFD230] text-[#111111] rounded-[24px] rounded-br-[8px] px-5 py-3 md:px-6 md:py-4'
                    : 'bg-[#F3F4F6] text-[#111111] rounded-[24px] rounded-bl-[8px] px-5 py-3 md:px-6 md:py-4 shadow-sm border-none'
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
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white hover:bg-gray-50 text-[#111111] transition-colors border border-[#E5E7EB] text-xs font-medium shadow-sm"
                    >
                      <Share size={14} /> Share
                    </button>
                    {sessionId && (
                      <button
                        onClick={async () => {
                          try {
                            addToast('Evaluating response...', 'info');
                            const res = await fetch(`${API}/sessions/${sessionId}/evaluate`, { method: 'POST' });
                            if (res.ok) {
                              const data = await res.json();
                              addToast(`Evaluation: Faithfulness ${data.faithfulness_score.toFixed(2)}, Relevance ${data.answer_relevance_score.toFixed(2)}`, 'success');
                            } else {
                              addToast('Evaluation failed', 'error');
                            }
                          } catch {
                            addToast('Evaluation error', 'error');
                          }
                        }}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white hover:bg-green-50 text-green-700 transition-colors border border-green-200 text-xs font-medium shadow-sm ml-auto"
                      >
                        <Check size={14} /> Evaluate
                      </button>
                    )}
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
              <div className="bg-[#EBF1FF] text-[#2563EB] rounded-[24px] rounded-bl-[8px] px-5 py-3.5 flex items-center gap-3 max-w-[90%] md:max-w-[78%]">
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
        <div className="shrink-0 border-t border-[#E5E7EB] bg-white p-4 md:p-6 z-10">
          <form onSubmit={handleSend} className="max-w-4xl mx-auto flex gap-2 md:gap-3 items-end relative">
            
            {/* Quick Actions */}
            <div className="flex gap-1 md:gap-2 pb-2 md:pb-2.5">
              <button
                type="button"
                onClick={() => setIsDocsOpen(true)}
                className="p-2.5 md:p-3 rounded-full text-gray-500 hover:text-[#111111] hover:bg-gray-100 transition-colors"
                title="Docs Library"
              >
                <Database className="w-5 h-5 md:w-5 md:h-5" />
              </button>
              <button
                type="button"
                onClick={() => setIsUploadOpen(true)}
                className="p-2.5 md:p-3 rounded-full text-gray-500 hover:text-[#2563EB] hover:bg-blue-50 transition-colors"
                title="Upload Data"
              >
                <Plus className="w-5 h-5 md:w-5 md:h-5" />
              </button>
            </div>

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
                className="w-full bg-white border-[1.5px] border-[#E5E7EB] text-[#111111] rounded-3xl md:rounded-full
                  py-3 pl-4 pr-24 md:py-4 md:pl-6 md:pr-24 resize-none
                  focus:outline-none focus:border-[#2563EB] focus:ring-0
                  disabled:opacity-50 text-[14px] md:text-[15px] leading-relaxed
                  transition-all shadow-sm placeholder:text-gray-400"
                style={{ maxHeight: '120px', overflowY: 'auto' }}
              />

              {/* Voice Input Button */}
              <button
                type="button"
                onClick={isRecording ? handleStopRecording : handleStartRecording}
                disabled={!isInitialized || isGenerating}
                className={`absolute right-12 md:right-14 bottom-2 md:bottom-3 p-2 rounded-full transition-all ${
                  isRecording 
                    ? 'bg-red-100 text-red-500 animate-pulse hover:bg-red-200' 
                    : 'text-gray-400 hover:bg-gray-100 hover:text-gray-600'
                }`}
                title={isRecording ? 'Stop Recording' : 'Record Audio'}
              >
                <Mic className="w-4 h-4 md:w-5 md:h-5" />
              </button>

              <button
                type="submit"
                id="send-btn"
                disabled={!input.trim() || !isInitialized || isGenerating}
                className="absolute right-2 bottom-2 md:bottom-2.5 h-[36px] w-[36px] md:h-[40px] md:w-[40px] rounded-full flex items-center justify-center
                  bg-[#2563EB] hover:bg-blue-700
                  disabled:bg-gray-200 disabled:text-gray-400
                  text-white shadow-md transition-all duration-200 z-10"
              >
                {isGenerating ? (
                  <svg className="animate-spin h-4 w-4 md:h-5 md:w-5" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                ) : (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="md:w-[20px] md:h-[20px]"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
                )}
              </button>
            </div>
          </form>
          <p className="text-center text-[10px] md:text-[11px] text-gray-400 mt-2 md:mt-3 font-medium">
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
