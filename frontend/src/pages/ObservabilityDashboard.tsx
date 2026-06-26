import React from "react";
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
