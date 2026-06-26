import React from "react";
import { PageContainer } from "@/components/layout/PageContainer";
import { Play, TrendingUp, TrendingDown } from "lucide-react";

export default function EvalDashboard() {
  const metrics = [
    { name: "Faithfulness", score: "0.84", trend: "+2%", up: true, color: "var(--success)" },
    { name: "Relevancy", score: "0.91", trend: "+5%", up: true, color: "var(--success)" },
    { name: "Context Precision", score: "0.62", trend: "-4%", up: false, color: "var(--warning)" },
    { name: "Context Recall", score: "0.78", trend: "+1%", up: true, color: "var(--success)" },
  ];

  return (
    <PageContainer className="py-8">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-3xl font-black uppercase">Evaluation Dashboard</h1>
          <p className="text-[var(--text-muted)] font-medium">RAGAS metrics & Golden Set testing</p>
        </div>
        <button className="bauhaus-btn primary flex items-center gap-2"><Play size={16}/> Run Golden Set</button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {metrics.map(m => (
          <div key={m.name} className="bg-[var(--bg-secondary)] border-4 border-[var(--border-strong)] p-4 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-16 h-16 opacity-10 rounded-bl-full" style={{ backgroundColor: m.color }} />
            <h3 className="text-xs font-bold uppercase text-[var(--text-muted)] mb-2">{m.name}</h3>
            <div className="text-3xl font-black mb-2">{m.score}</div>
            <div className={`flex items-center gap-1 text-xs font-bold ${m.up ? 'text-[var(--success)]' : 'text-[var(--error)]'}`}>
              {m.up ? <TrendingUp size={12}/> : <TrendingDown size={12}/>} {m.trend} vs last week
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-[var(--bg-primary)] border-4 border-[var(--border-strong)] p-4 h-64 flex items-center justify-center">
            <span className="font-bold text-[var(--text-muted)]">[Trend Chart Placeholder - Recharts]</span>
          </div>
          
          <div className="bg-[var(--bg-primary)] border-4 border-[var(--border-strong)]">
            <div className="p-3 border-b-2 border-[var(--border-strong)] bg-[var(--bg-secondary)]">
              <h3 className="font-black uppercase">Worst Performing Queries</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b-2 border-[var(--border-strong)] bg-[var(--bg-secondary)] uppercase text-xs">
                    <th className="p-3">Query</th>
                    <th className="p-3 text-center">Faith.</th>
                    <th className="p-3 text-center">Prec.</th>
                    <th className="p-3 text-center">Recall</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-[var(--border-strong)]">
                    <td className="p-3 font-medium truncate max-w-[200px]">"What is the Q4 revenue projection?"</td>
                    <td className="p-3 text-center text-[var(--error)] font-bold">0.42</td>
                    <td className="p-3 text-center text-[var(--warning)] font-bold">0.60</td>
                    <td className="p-3 text-center font-bold">0.81</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-[var(--bg-primary)] border-4 border-[var(--border-strong)] p-4">
            <h3 className="font-black uppercase mb-4 border-b-2 border-[var(--border-strong)] pb-2">Sample Rate</h3>
            <input type="range" className="w-full accent-[var(--accent)] mb-2" defaultValue="10" />
            <div className="flex justify-between text-sm font-bold">
              <span>Evaluate 10% of queries</span>
            </div>
            <p className="text-xs text-[var(--text-muted)] mt-2">247 queries evaluated this week</p>
          </div>
          
          <div className="bg-[var(--bg-primary)] border-4 border-[var(--border-strong)] p-4">
            <h3 className="font-black uppercase mb-4 border-b-2 border-[var(--border-strong)] pb-2">Golden Test Set</h3>
            <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2">
              {[1,2,3].map(i => (
                <div key={i} className="border-2 border-[var(--border-strong)] p-2 text-sm bg-[var(--bg-secondary)]">
                  <p className="font-bold italic mb-1">Q: Who is the CEO?</p>
                  <p className="text-[var(--success)] font-medium text-xs">A: John Smith</p>
                </div>
              ))}
            </div>
            <button className="bauhaus-btn w-full mt-4 text-xs">Add Golden Q&A</button>
          </div>
        </div>
      </div>
    </PageContainer>
  );
}
