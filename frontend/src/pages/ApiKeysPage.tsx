import React from "react";
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
