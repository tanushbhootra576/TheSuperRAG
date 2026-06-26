import React from "react";
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
