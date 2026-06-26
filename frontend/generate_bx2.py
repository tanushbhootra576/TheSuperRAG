import os

chat_layout = """import React, { useRef, useState } from "react";
import { FilterPanel } from "@/components/filters/FilterPanel";
import { FilterBar } from "@/components/filters/FilterBar";
import { useBreakpoint } from "@/hooks/useBreakpoint";
import { useVirtualizer } from "@tanstack/react-virtual";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";

export function ChatLayout() {
  const { isDesktop, isTablet, isMobile } = useBreakpoint();
  const [showFilters, setShowFilters] = useState(isDesktop);
  
  const messages = Array.from({ length: 50 }).map((_, i) => ({
    id: i,
    text: `Message content ${i}`,
    role: i % 2 === 0 ? "user" : "assistant",
  }));

  const parentRef = useRef<HTMLDivElement>(null);
  const rowVirtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 100,
  });

  return (
    <div className="flex h-full w-full overflow-hidden relative">
      {/* Sidebar Filters */}
      {(isDesktop || (isTablet && showFilters)) && (
        <div className={`shrink-0 w-60 border-r-2 border-[var(--border-strong)] z-10 ${isTablet ? 'absolute inset-y-0 left-0 bg-[var(--bg-primary)]' : ''}`}>
          <FilterPanel />
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full min-w-0 bg-[var(--bg-primary)]">
        {isMobile && <FilterBar onOpen={() => setShowFilters(true)} />}

        {/* Messages List (Virtualized) */}
        <div ref={parentRef} className="flex-1 overflow-y-auto px-2 md:px-4 hide-scrollbar">
          <div
            style={{
              height: `${rowVirtualizer.getTotalSize()}px`,
              width: '100%',
              position: 'relative',
            }}
          >
            {rowVirtualizer.getVirtualItems().map((virtualRow) => (
              <div
                key={virtualRow.index}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  transform: `translateY(${virtualRow.start}px)`,
                }}
                className="py-2"
              >
                <MessageBubble msg={messages[virtualRow.index]} />
              </div>
            ))}
          </div>
        </div>

        {/* Input Area */}
        <div className="shrink-0 p-2 md:p-4 bg-[var(--bg-primary)] border-t-2 border-[var(--border-strong)] pb-[max(16px,env(safe-area-inset-bottom))]">
          <ChatInput />
        </div>
      </div>
      
      {/* Mobile Filter Sheet */}
      {isMobile && showFilters && (
        <div className="fixed inset-0 z-50 bg-black/50 flex flex-col justify-end">
          <div className="bg-[var(--bg-primary)] h-[60vh] rounded-t-xl overflow-hidden border-t-4 border-[var(--border-strong)]">
            <button onClick={() => setShowFilters(false)} className="w-full py-2 bg-[var(--bg-secondary)] font-bold text-center border-b-2 border-[var(--border-strong)]">Close Filters</button>
            <div className="h-full pb-10"><FilterPanel /></div>
          </div>
        </div>
      )}
    </div>
  );
}
"""

message_bubble = """import React, { useState } from "react";
import { Copy, ThumbsUp, ThumbsDown, PlayCircle } from "lucide-react";

export function MessageBubble({ msg }: { msg: any }) {
  const isUser = msg.role === "user";
  const [showMore, setShowMore] = useState(false);

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"} group`}>
      <div className={`relative max-w-[85%] md:max-w-[75%] p-3 md:p-4 border-2 md:border-4 border-[var(--border-strong)] ${isUser ? "bg-[var(--accent-muted)] border-[var(--accent)]" : "bg-[var(--bg-secondary)]"}`}>
        
        {/* Actions Toolbar */}
        {!isUser && (
          <div className="opacity-0 group-hover:opacity-100 absolute -top-4 right-2 bg-[var(--bg-primary)] border-2 border-[var(--border-strong)] flex items-center shadow-sm transition-opacity">
            <button className="p-1 hover:bg-[var(--bg-secondary)]"><Copy size={12}/></button>
            <button className="p-1 hover:bg-[var(--bg-secondary)]"><PlayCircle size={12}/></button>
            <button className="p-1 hover:bg-[var(--bg-secondary)]"><ThumbsUp size={12}/></button>
            <button className="p-1 hover:bg-[var(--bg-secondary)]"><ThumbsDown size={12}/></button>
          </div>
        )}

        <div className={`font-medium leading-relaxed ${!showMore && !isUser ? 'line-clamp-[10]' : ''}`}>
          {msg.text}
          {!isUser && <p className="mt-2 text-sm">Long text example to demonstrate line clamp...</p>}
        </div>

        {!isUser && !showMore && (
          <button onClick={() => setShowMore(true)} className="text-xs font-bold text-[var(--accent)] mt-2">
            Show more
          </button>
        )}

        <div className={`text-[10px] mt-2 font-bold uppercase tracking-wider ${isUser ? "text-[var(--accent)] text-right" : "text-[var(--text-muted)]"}`}>
          12:34 PM
        </div>
      </div>
    </div>
  );
}
"""

chat_input = """import React, { useState, useRef, useEffect } from "react";
import { ArrowUp, Paperclip, Mic, ChevronUp } from "lucide-react";

export function ChatInput() {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  }, [text]);

  return (
    <div className="max-w-[800px] mx-auto w-full relative">
      <button className="absolute -top-8 left-1/2 -translate-x-1/2 bg-[var(--bg-secondary)] border-2 border-[var(--border-strong)] text-[10px] font-bold px-2 py-0.5 rounded-t-md flex items-center gap-1 hover:bg-[var(--accent-muted)]">
        <ChevronUp size={12}/> Search Options
      </button>

      <div className="relative border-4 border-[var(--border-strong)] bg-[var(--bg-primary)] focus-within:border-[var(--accent)] transition-colors shadow-[var(--shadow-md)] flex items-end p-2 gap-2">
        <button className="p-2 text-[var(--text-muted)] hover:text-[var(--text-primary)] shrink-0 bg-[var(--bg-secondary)] border-2 border-[var(--border-strong)]">
          <Paperclip size={20} />
        </button>
        
        <textarea
          ref={textareaRef}
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder="Ask a question..."
          className="flex-1 bg-transparent border-none outline-none resize-none max-h-[150px] py-2 font-medium"
          rows={1}
        />
        
        {text.length === 0 ? (
          <button className="p-2 text-[var(--accent)] shrink-0 bg-[var(--accent-muted)] border-2 border-[var(--accent)] hover:bg-[var(--accent)] hover:text-white transition-colors">
            <Mic size={20} />
          </button>
        ) : (
          <button className="p-2 text-white shrink-0 bg-[var(--accent)] border-2 border-[var(--border-strong)] hover:bg-[var(--accent-hover)] transition-colors">
            <ArrowUp size={20} />
          </button>
        )}
      </div>
    </div>
  );
}
"""

files = {
    'src/components/chat/ChatLayout.tsx': chat_layout,
    'src/components/chat/MessageBubble.tsx': message_bubble,
    'src/components/chat/ChatInput.tsx': chat_input,
}

for path, content in files.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
