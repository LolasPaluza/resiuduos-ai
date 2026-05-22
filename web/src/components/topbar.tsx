"use client";

import { StatusBadge } from "./status-badge";

export function Topbar({ title }: { title: string }) {
  return (
    <header className="h-16 bg-zinc-900 border-b border-zinc-800 flex items-center justify-between px-6">
      <h1 className="text-lg font-semibold text-zinc-100">{title}</h1>
      <StatusBadge />
    </header>
  );
}
