"use client";

import { apiFetch } from "@/lib/api";
import { usePolling } from "@/lib/use-polling";
import type { StatusResponse } from "@/lib/types";

export function StatusBadge() {
  const { data, error } = usePolling<StatusResponse>(
    () => apiFetch<StatusResponse>("/status"),
    5000,
  );

  let cor = "bg-zinc-500";
  let txt = "verificando...";

  if (error) {
    cor = "bg-red-500";
    txt = "offline";
  } else if (data?.online) {
    if (data.modo_degradado) {
      cor = "bg-amber-500";
      txt = `degradado · ${data.fps?.toFixed(1) ?? "?"} FPS`;
    } else {
      cor = "bg-emerald-500";
      txt = `online · ${data.fps?.toFixed(1) ?? "?"} FPS`;
    }
  }

  return (
    <div className="flex items-center gap-2 text-sm text-zinc-300">
      <span className={`w-2 h-2 rounded-full ${cor} animate-pulse`} />
      <span>{txt}</span>
      {data?.hardware && (
        <span className="text-zinc-500 ml-2">· {data.hardware}</span>
      )}
    </div>
  );
}
