import React from 'react';
import Link from 'next/link';

export default function BauhausLandingPage() {
  return (
    <div className="min-h-screen bg-white text-[#111111] font-sans selection:bg-[#FFD230] selection:text-[#111111]">
      
      {/* 
        ========================================
        NAVIGATION 
        ========================================
      */}
      <header className="border-b-4 border-[#111111] flex flex-col md:flex-row items-center justify-between px-6 lg:px-12 py-6 bg-white relative z-50">
        <div className="flex items-center gap-4 w-full md:w-auto justify-between md:justify-start mb-4 md:mb-0">
          <div className="flex items-center gap-4">
            <div className="grid grid-cols-2 w-10 h-10 border-2 border-[#111111]">
              <div className="bg-[#111111] rounded-br-full"></div>
              <div className="bg-[#EF4444]"></div>
              <div className="bg-[#FFD230]"></div>
              <div className="bg-[#2563EB] rounded-tl-full"></div>
            </div>
            <span className="text-2xl font-black uppercase tracking-widest">TheSuperRAG</span>
          </div>
        </div>
        
        <nav className="flex items-center gap-4 md:gap-8 font-bold uppercase tracking-widest text-xs md:text-sm w-full md:w-auto justify-center md:justify-end">
          <Link href="/docs" className="hover:text-[#2563EB] transition-colors decoration-4 underline-offset-8 hover:underline">Documentation</Link>
          <Link href="https://github.com/tanushbhootra576/TheSuperRAG" target="_blank" className="hover:text-[#EF4444] transition-colors decoration-4 underline-offset-8 hover:underline">GitHub</Link>
          <Link href="/chat" className="bg-[#111111] text-white px-6 py-3 hover:bg-[#2563EB] transition-colors border-2 border-[#111111]">
            Launch App
          </Link>
        </nav>
      </header>

      {/* 
        ========================================
        HERO SECTION 
        ========================================
      */}
      <section className="grid grid-cols-1 lg:grid-cols-2 min-h-[85vh] border-b-4 border-[#111111]">
        
        {/* Left Column: Typography */}
        <div className="flex flex-col justify-center p-8 lg:p-16 xl:p-24 border-b-4 lg:border-b-0 lg:border-r-4 border-[#111111] relative bg-[#F9FAFB] overflow-hidden">
          
          <div className="absolute inset-0 grid grid-cols-6 grid-rows-6 pointer-events-none z-0 opacity-10">
            {[...Array(36)].map((_, i) => (
              <div key={i} className="border border-[#111111]"></div>
            ))}
          </div>

          <div className="absolute top-12 left-12 w-16 h-16 bg-[#FFD230] rounded-full border-4 border-[#111111] hidden lg:block"></div>
          
          <div className="mt-12 lg:mt-16 z-10 py-4">
            <h1 className="text-5xl md:text-7xl xl:text-[7rem] font-black leading-tight uppercase tracking-tighter mb-8 text-[#111111]">
              Talk<br/>
              <span className="text-[#2563EB]">To Your</span><br/>
              Data.
            </h1>
            
            <p className="text-base md:text-lg lg:text-xl font-bold max-w-lg mb-12 leading-snug border-l-8 border-[#EF4444] pl-6 py-2 text-[#111111]">
              A blazing fast, locally indexed AI assistant. Stop digging through PDFs. Ask questions and get instant, accurately cited answers.
            </p>
            
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6">
              <Link href="/chat" className="bg-[#EF4444] text-white text-lg font-black uppercase tracking-widest px-8 py-4 border-4 border-[#111111] hover:bg-[#111111] hover:-translate-y-1 hover:translate-x-[-4px] hover:shadow-[8px_8px_0px_#111111] transition-all">
                Start Chatting
              </Link>
              <Link href="https://github.com/tanushbhootra576/TheSuperRAG" target="_blank" className="bg-white text-[#111111] text-lg font-black uppercase tracking-widest px-8 py-4 border-4 border-[#111111] hover:bg-[#FFD230] hover:-translate-y-1 hover:translate-x-[-4px] hover:shadow-[8px_8px_0px_#111111] transition-all">
                GitHub Repo
              </Link>
            </div>
          </div>
        </div>

        {/* Right Column: Bauhaus Geometry */}
        <div className="relative bg-white overflow-hidden flex items-center justify-center p-12 lg:p-24">
          <div className="relative w-full max-w-lg aspect-square">
            <div className="absolute inset-0 grid grid-cols-4 grid-rows-4 pointer-events-none z-0">
              {[...Array(16)].map((_, i) => (
                <div key={i} className="border border-gray-200"></div>
              ))}
            </div>
            <div className="absolute top-[5%] right-[5%] w-[70%] h-[70%] bg-[#2563EB] rounded-bl-full border-8 border-[#111111] z-10 hover:scale-105 transition-transform duration-500 shadow-[16px_16px_0px_#111111]"></div>
            <div className="absolute bottom-[5%] left-[5%] w-[60%] h-[60%] bg-[#EF4444] rounded-tr-full border-8 border-[#111111] z-20 hover:scale-105 transition-transform duration-500 shadow-[16px_16px_0px_#111111]"></div>
            <div className="absolute top-[20%] left-[20%] w-[45%] h-[45%] bg-[#FFD230] border-8 border-[#111111] z-30 rotate-12 hover:rotate-45 transition-transform duration-700 shadow-[16px_16px_0px_#111111]"></div>
            <div className="absolute bottom-[25%] right-[25%] w-[25%] h-[25%] bg-[#111111] rounded-full z-40 hover:scale-75 transition-transform duration-300"></div>
          </div>
        </div>
      </section>

      {/* 
        ========================================
        FEATURES SECTION 
        ========================================
      */}
      <section className="bg-white border-b-4 border-[#111111]">
        <div className="border-b-4 border-[#111111] p-8 lg:p-16 bg-[#FFD230]">
          <h2 className="text-4xl lg:text-6xl font-black uppercase tracking-tighter">Engineered for Accuracy</h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
          
          <div className="p-8 lg:p-12 border-b-4 md:border-b-0 md:border-r-4 border-[#111111] hover:bg-[#F9FAFB] transition-colors">
            <div className="w-16 h-16 bg-[#2563EB] border-4 border-[#111111] rounded-full mb-8 shadow-[6px_6px_0px_#111111]"></div>
            <h3 className="text-2xl font-black uppercase tracking-widest mb-4">Hybrid Search</h3>
            <p className="text-lg font-bold text-gray-700 leading-relaxed border-l-4 border-[#2563EB] pl-4">
              Combines sparse (BM25) and dense (Vector) retrieval to ensure exact keyword matches and semantic meaning are perfectly balanced.
            </p>
          </div>

          <div className="p-8 lg:p-12 border-b-4 md:border-b-0 md:border-r-4 border-[#111111] hover:bg-[#F9FAFB] transition-colors">
            <div className="w-16 h-16 bg-[#EF4444] border-4 border-[#111111] rounded-br-full mb-8 shadow-[6px_6px_0px_#111111]"></div>
            <h3 className="text-2xl font-black uppercase tracking-widest mb-4">Cross-Encoder</h3>
            <p className="text-lg font-bold text-gray-700 leading-relaxed border-l-4 border-[#EF4444] pl-4">
              A powerful secondary model evaluates the retrieved chunks against your query, ensuring only the most relevant context is sent to the LLM.
            </p>
          </div>

          <div className="p-8 lg:p-12 hover:bg-[#F9FAFB] transition-colors border-b-4 md:border-b-0 md:border-r-4 border-[#111111]">
            <div className="w-16 h-16 bg-[#111111] border-4 border-[#111111] rounded-sm mb-8 shadow-[6px_6px_0px_#FFD230]"></div>
            <h3 className="text-2xl font-black uppercase tracking-widest mb-4">BYOK Freedom</h3>
            <p className="text-lg font-bold text-gray-700 leading-relaxed border-l-4 border-[#111111] pl-4">
              Bring Your Own Key! Seamlessly switch between Groq, OpenAI, Anthropic, and Google GenAI without any vendor lock-in.
            </p>
          </div>
          
          <div className="p-8 lg:p-12 hover:bg-[#F9FAFB] transition-colors">
            <div className="w-16 h-16 bg-[#FFD230] border-4 border-[#111111] rounded-tl-full mb-8 shadow-[6px_6px_0px_#111111]"></div>
            <h3 className="text-2xl font-black uppercase tracking-widest mb-4">Zero Server Storage</h3>
            <p className="text-lg font-bold text-gray-700 leading-relaxed border-l-4 border-[#FFD230] pl-4">
              Your files never touch our disk. Documents are stored locally in your browser's IndexedDB and indexed strictly in-memory.
            </p>
          </div>

        </div>
      </section>

      {/* 
        ========================================
        TECH STACK SECTION 
        ========================================
      */}
      <section className="border-b-4 border-[#111111]">
        <div className="grid grid-cols-1 md:grid-cols-2">
          <div className="p-8 lg:p-16 xl:p-24 bg-[#FFD230] border-b-4 md:border-b-0 md:border-r-4 border-[#111111]">
            <h2 className="text-4xl lg:text-6xl font-black uppercase tracking-tighter mb-8 text-[#111111]">
              Built for <br />
              <span className="text-[#EF4444]">Privacy &</span><br />
              Speed.
            </h2>
            <p className="text-lg font-bold text-[#111111] max-w-md leading-relaxed border-l-8 border-[#111111] pl-6 py-2">
              TheSuperRAG runs entirely on your infrastructure. No external vector databases, no cloud storage lock-in. Your data stays yours.
            </p>
          </div>
          <div className="bg-white p-8 lg:p-16 flex flex-col justify-center gap-8">
            <div className="flex items-center gap-6">
               <div className="w-12 h-12 bg-[#2563EB] border-4 border-[#111111]"></div>
               <div>
                  <h4 className="text-xl font-black uppercase tracking-widest">Local Qdrant Engine</h4>
                  <p className="font-bold text-gray-600">On-disk hybrid vector database for maximum retrieval speed.</p>
               </div>
            </div>
            <div className="flex items-center gap-6">
               <div className="w-12 h-12 bg-[#EF4444] border-4 border-[#111111] rounded-full"></div>
               <div>
                  <h4 className="text-xl font-black uppercase tracking-widest">FastAPI Streaming</h4>
                  <p className="font-bold text-gray-600">SSE (Server-Sent Events) streams tokens instantly to the client.</p>
               </div>
            </div>
            <div className="flex items-center gap-6">
               <div className="w-12 h-12 bg-[#111111] border-4 border-[#111111] rotate-45 transform scale-75"></div>
               <div>
                  <h4 className="text-xl font-black uppercase tracking-widest">LangGraph Pipeline</h4>
                  <p className="font-bold text-gray-600">Stateful node execution for robust and predictable query routing.</p>
               </div>
            </div>
            <div className="flex items-center gap-6">
               <div className="w-12 h-12 bg-[#FFD230] border-4 border-[#111111] rounded-tl-full"></div>
               <div>
                  <h4 className="text-xl font-black uppercase tracking-widest">Client-Side IndexedDB</h4>
                  <p className="font-bold text-gray-600">True serverless privacy. Files live securely in your browser storage.</p>
               </div>
            </div>
          </div>
        </div>
      </section>

      {/* 
        ========================================
        HOW IT WORKS SECTION 
        ========================================
      */}
      <section className="grid grid-cols-1 lg:grid-cols-2 border-b-4 border-[#111111]">
        
        <div className="p-8 lg:p-16 xl:p-24 bg-[#111111] text-white border-b-4 lg:border-b-0 lg:border-r-4 border-[#111111]">
          <h2 className="text-4xl lg:text-6xl font-black uppercase tracking-tighter mb-12">How it works</h2>
          
          <div className="space-y-12">
            <div className="flex gap-6 items-start">
              <div className="shrink-0 w-16 h-16 rounded-full bg-[#EF4444] border-4 border-white flex items-center justify-center font-black text-2xl text-white shadow-[6px_6px_0px_white]">1</div>
              <div>
                <h4 className="text-2xl font-black uppercase tracking-widest mb-2">Upload</h4>
                <p className="text-lg font-medium text-gray-300">Securely upload your PDFs and documents. The system automatically extracts the text.</p>
              </div>
            </div>
            
            <div className="flex gap-6 items-start">
              <div className="shrink-0 w-16 h-16 rounded-full bg-[#2563EB] border-4 border-white flex items-center justify-center font-black text-2xl text-white shadow-[6px_6px_0px_white]">2</div>
              <div>
                <h4 className="text-2xl font-black uppercase tracking-widest mb-2">Vectorize</h4>
                <p className="text-lg font-medium text-gray-300">We embed and index your data into a high-performance local vector database.</p>
              </div>
            </div>
            
            <div className="flex gap-6 items-start">
              <div className="shrink-0 w-16 h-16 rounded-full bg-[#FFD230] border-4 border-white flex items-center justify-center font-black text-2xl text-[#111111] shadow-[6px_6px_0px_white]">3</div>
              <div>
                <h4 className="text-2xl font-black uppercase tracking-widest mb-2">Query</h4>
                <p className="text-lg font-medium text-gray-300">Ask complex questions. The AI cites specific sources instantly.</p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-[#EF4444] p-8 lg:p-16 flex items-center justify-center relative overflow-hidden">
           <div className="absolute inset-0 grid grid-cols-3 grid-rows-3 pointer-events-none opacity-20">
              {[...Array(9)].map((_, i) => (
                <div key={i} className="border border-[#111111]"></div>
              ))}
            </div>

           <div className="w-full max-w-md bg-white border-8 border-[#111111] shadow-[16px_16px_0px_#111111] relative z-10 p-8 flex flex-col gap-6 transform hover:scale-105 transition-transform duration-500">
              <div className="w-full h-12 bg-[#2563EB] border-4 border-[#111111] flex items-center px-4 font-bold text-white uppercase tracking-widest">Document Ingest</div>
              <div className="flex gap-4">
                 <div className="w-1/2 h-8 bg-[#FFD230] border-4 border-[#111111]"></div>
                 <div className="w-1/2 h-8 bg-[#FFD230] border-4 border-[#111111]"></div>
              </div>
              <div className="w-full h-32 bg-[#111111] border-4 border-[#111111] relative overflow-hidden flex items-center justify-center text-white font-black text-2xl uppercase tracking-widest">
                 Ready
              </div>
           </div>
        </div>

      </section>

      {/* 
        ========================================
        FOOTER / CTA SECTION 
        ========================================
      */}
      <footer className="bg-white">
        <div className="p-12 lg:p-24 text-center border-b-4 border-[#111111] bg-[#F9FAFB]">
          <h2 className="text-4xl md:text-5xl lg:text-7xl font-black uppercase tracking-tighter mb-12">Ready to Upgrade?</h2>
          <Link href="/chat" className="inline-block bg-[#2563EB] text-white text-xl lg:text-2xl font-black uppercase tracking-widest px-12 py-6 border-4 border-[#111111] hover:bg-[#FFD230] hover:text-[#111111] hover:-translate-y-2 hover:translate-x-[-6px] hover:shadow-[12px_12px_0px_#111111] transition-all">
            Launch TheSuperRAG
          </Link>
        </div>

        <div className="p-6 lg:p-12 flex flex-col md:flex-row items-center justify-between gap-6 font-bold uppercase tracking-widest text-sm">
          <div className="flex items-center gap-4">
            <div className="grid grid-cols-2 w-6 h-6 border-2 border-[#111111]">
              <div className="bg-[#111111] rounded-br-full"></div>
              <div className="bg-[#EF4444]"></div>
              <div className="bg-[#FFD230]"></div>
              <div className="bg-[#2563EB] rounded-tl-full"></div>
            </div>
            <span>© {new Date().getFullYear()} TheSuperRAG</span>
          </div>
          <div className="flex gap-8">
            <Link href="/docs" className="hover:text-[#2563EB]">Docs</Link>
            <Link href="https://github.com/tanushbhootra576/TheSuperRAG" target="_blank" className="hover:text-[#EF4444]">GitHub</Link>
          </div>
        </div>
      </footer>

    </div>
  );
}
