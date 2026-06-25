import React from 'react';
import Link from 'next/link';

export default function DocsPage() {
  return (
    <div className="min-h-screen bg-white text-[#111111] font-sans scroll-smooth">
      
      {/* Navigation */}
      <header className="border-b-4 border-[#111111] flex flex-col md:flex-row items-center justify-between px-6 lg:px-12 py-4 bg-white sticky top-0 z-50">
        <div className="flex items-center gap-4 w-full md:w-auto justify-between md:justify-start mb-4 md:mb-0">
          <Link href="/" className="flex items-center gap-4">
            <div className="grid grid-cols-2 w-8 h-8 border-2 border-[#111111]">
              <div className="bg-[#111111] rounded-br-full"></div>
              <div className="bg-[#EF4444]"></div>
              <div className="bg-[#FFD230]"></div>
              <div className="bg-[#2563EB] rounded-tl-full"></div>
            </div>
            <span className="text-xl font-black uppercase tracking-widest hover:text-[#2563EB] transition-colors">TheSuperRAG</span>
          </Link>
        </div>
        <nav className="flex items-center gap-4 md:gap-8 font-bold uppercase tracking-widest text-xs md:text-sm w-full md:w-auto justify-center md:justify-end">
          <Link href="/docs" className="text-[#2563EB] decoration-4 underline-offset-8 underline">Documentation</Link>
          <Link href="https://github.com/tanushbhootra576/TheSuperRAG" target="_blank" className="hover:text-[#EF4444] transition-colors decoration-4 underline-offset-8 hover:underline">GitHub</Link>
          <Link href="/chat" className="bg-[#111111] text-white px-5 py-2.5 hover:bg-[#2563EB] transition-colors border-2 border-[#111111]">
            Launch App
          </Link>
        </nav>
      </header>

      {/* Docs Content */}
      <div className="max-w-7xl mx-auto flex">
        
        {/* Sidebar */}
        <aside className="w-64 border-r-4 border-[#111111] min-h-[calc(100vh-73px)] p-8 hidden md:block bg-[#F9FAFB]">
          <div className="space-y-8 sticky top-24">
            
            <div>
              <h3 className="font-black text-sm text-[#111111] uppercase tracking-widest mb-4 border-b-2 border-[#111111] pb-2">Getting Started</h3>
              <ul className="space-y-3 text-sm font-bold uppercase tracking-wider text-gray-500">
                <li><a href="#introduction" className="hover:text-[#2563EB] transition-colors">Introduction</a></li>
                <li><a href="#installation" className="hover:text-[#2563EB] transition-colors">Installation</a></li>
                <li><a href="#quick-start" className="hover:text-[#2563EB] transition-colors">Quick Start</a></li>
              </ul>
            </div>

            <div>
              <h3 className="font-black text-sm text-[#111111] uppercase tracking-widest mb-4 border-b-2 border-[#111111] pb-2">Core Concepts</h3>
              <ul className="space-y-3 text-sm font-bold uppercase tracking-wider text-gray-500">
                <li><a href="#document-ingestion" className="hover:text-[#EF4444] transition-colors">Document Ingestion</a></li>
                <li><a href="#hybrid-search" className="hover:text-[#EF4444] transition-colors">Hybrid Search</a></li>
                <li><a href="#cross-encoder" className="hover:text-[#EF4444] transition-colors">Cross-Encoder</a></li>
              </ul>
            </div>

          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8 md:p-16 max-w-4xl">
          
          <div id="introduction" className="mb-16 pt-8 scroll-mt-24">
            <h1 className="text-5xl md:text-6xl font-black uppercase tracking-tighter mb-8 border-b-8 border-[#111111] pb-4">Introduction</h1>
            <p className="text-xl font-bold text-gray-700 leading-relaxed mb-6 border-l-8 border-[#2563EB] pl-6 py-2">
              TheSuperRAG is a next-generation Retrieval-Augmented Generation (RAG) platform.
            </p>
            <p className="text-lg text-gray-600 leading-relaxed mb-8">
              It allows you to ingest PDF documents, process them into vectorized knowledge graphs, and chat with an AI that references your data with extreme precision using Hybrid Search and Cross-Encoder re-ranking.
            </p>
          </div>

          <div id="installation" className="mb-16 pt-8 scroll-mt-24">
            <h2 className="text-4xl font-black uppercase tracking-tight mb-6 flex items-center gap-4">
              <span className="w-8 h-8 bg-[#EF4444] inline-block border-2 border-[#111111]"></span>
              Installation
            </h2>
            <p className="text-lg text-gray-600 leading-relaxed mb-4">
              Clone the repository and install the dependencies to get started. Ensure you have Node.js and Python installed.
            </p>
            <div className="bg-[#111111] text-white p-6 border-4 border-gray-300 shadow-[8px_8px_0px_#EF4444] mb-4">
              <code className="text-sm font-mono block mb-2">git clone https://github.com/tanushbhootra576/TheSuperRAG.git</code>
              <code className="text-sm font-mono block mb-2">cd TheSuperRAG/frontend</code>
              <code className="text-sm font-mono block">npm install</code>
            </div>
          </div>

          <div id="quick-start" className="mb-16 pt-8 scroll-mt-24">
            <h2 className="text-4xl font-black uppercase tracking-tight mb-6 flex items-center gap-4">
              <span className="w-8 h-8 bg-[#FFD230] rounded-full inline-block border-2 border-[#111111]"></span>
              Quick Start
            </h2>
            <p className="text-lg text-gray-600 leading-relaxed mb-4">
              Once dependencies are installed, you can start the development server. Navigate to the frontend directory and run:
            </p>
            <div className="bg-[#111111] text-white p-6 border-4 border-gray-300 shadow-[8px_8px_0px_#FFD230] mb-6">
              <code className="text-sm font-mono block">npm run dev</code>
            </div>
            <p className="text-lg text-gray-600 leading-relaxed">
              Then, open <a href="http://localhost:3000" className="text-[#2563EB] font-bold underline decoration-2 underline-offset-4">http://localhost:3000</a> in your browser. Upload your PDFs in the sidebar and click "Initialize Database" to begin!
            </p>
          </div>

          <div id="document-ingestion" className="mb-16 pt-8 scroll-mt-24">
            <h2 className="text-4xl font-black uppercase tracking-tight mb-6 flex items-center gap-4">
              <span className="w-0 h-0 border-l-[16px] border-l-transparent border-r-[16px] border-r-transparent border-b-[28px] border-b-[#2563EB] inline-block"></span>
              Document Ingestion
            </h2>
            <p className="text-lg text-gray-600 leading-relaxed mb-4">
              Our ingestion pipeline handles complex PDFs securely. When you upload a document, it is immediately parsed, and its text is extracted.
            </p>
            <ul className="space-y-3 text-lg text-gray-600 list-disc pl-6 font-medium">
              <li>Documents are split into semantic chunks.</li>
              <li>Chunks are vectorized using a high-performance embedding model.</li>
              <li>Indexed locally in the Vector Database.</li>
            </ul>
          </div>

          <div id="hybrid-search" className="mb-16 pt-8 scroll-mt-24">
            <h2 className="text-4xl font-black uppercase tracking-tight mb-6 border-l-8 border-[#111111] pl-6">
              Hybrid Search
            </h2>
            <p className="text-lg text-gray-600 leading-relaxed mb-4">
              To guarantee that the AI never hallucinates, we use Hybrid Search. 
            </p>
            <p className="text-lg text-gray-600 leading-relaxed font-bold bg-[#F9FAFB] p-6 border-4 border-[#111111] shadow-[6px_6px_0px_#111111]">
              <span className="text-[#2563EB]">Dense Search (Vector):</span> Finds conceptual matches even if exact words differ.<br/><br/>
              <span className="text-[#EF4444]">Sparse Search (BM25):</span> Finds exact keyword matches (crucial for names, IDs, and domain jargon).
            </p>
          </div>

          <div id="cross-encoder" className="mb-16 pt-8 scroll-mt-24">
            <h2 className="text-4xl font-black uppercase tracking-tight mb-6 border-l-8 border-[#EF4444] pl-6">
              Cross-Encoder Re-ranking
            </h2>
            <p className="text-lg text-gray-600 leading-relaxed mb-6">
              After Hybrid Search fetches the top candidates, a Cross-Encoder model evaluates them. Unlike bi-encoders, the cross-encoder computes attention across both the query and the chunk simultaneously.
            </p>
            <div className="w-full bg-[#111111] text-white p-8 border-b-8 border-[#EF4444]">
              <p className="text-xl font-black uppercase tracking-widest">Result: Unmatched Precision.</p>
              <p className="text-gray-400 mt-2 font-medium">Only the highest-scoring context is passed to the LLM generation phase.</p>
            </div>
          </div>

        </main>
      </div>
    </div>
  );
}
