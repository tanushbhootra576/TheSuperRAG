import React from "react";
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
