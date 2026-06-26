import React from 'react';

export function PageContainer({ children, className = "" }: { children: React.ReactNode, className?: string }) {
  return (
    <div className={`flex-1 w-full h-full bg-white text-black p-8 overflow-y-auto ${className}`}>
      {children}
    </div>
  );
}
