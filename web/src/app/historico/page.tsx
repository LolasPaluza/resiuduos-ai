"use client";

import { Topbar } from "@/components/topbar";
import { apiFetch } from "@/lib/api";
import type { HistoricoItem } from "@/lib/types";
import { usePolling } from "@/lib/use-polling";

export default function HistoricoPage() {
  const { data, error } = usePolling<HistoricoItem[]>(
    () => apiFetch<HistoricoItem[]>("/historico"),
    15000,
  );

  return (
    <>
      <Topbar title="Histórico de turnos" />
      <main className="flex-1 p-6 space-y-4">
        {error && (
          <div className="bg-red-950/30 border border-red-900 text-red-300 rounded-xl p-4 text-sm">
            {error.message}
          </div>
        )}
        {data && data.length === 0 && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-8 text-center text-zinc-500 text-sm">
            Nenhum turno encerrado ainda. Quando você encerrar um turno, ele
            aparece aqui com o link pro relatório PDF.
          </div>
        )}
        {data && data.length > 0 && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-zinc-950 text-xs text-zinc-400 uppercase">
                <tr>
                  <th className="text-left px-4 py-3">ID</th>
                  <th className="text-left px-4 py-3">Início</th>
                  <th className="text-left px-4 py-3">Fim</th>
                  <th className="text-right px-4 py-3">Detecções</th>
                  <th className="text-left px-4 py-3">Arquivo</th>
                </tr>
              </thead>
              <tbody>
                {data.map((t) => (
                  <tr
                    key={t.id}
                    className="border-t border-zinc-800 hover:bg-zinc-950/50"
                  >
                    <td className="px-4 py-3 font-mono text-zinc-300">
                      {t.id}
                    </td>
                    <td className="px-4 py-3 text-zinc-400">
                      {t.inicio
                        ? new Date(t.inicio).toLocaleString("pt-BR")
                        : "—"}
                    </td>
                    <td className="px-4 py-3 text-zinc-400">
                      {t.fim ? new Date(t.fim).toLocaleString("pt-BR") : "—"}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {t.total_deteccoes ?? 0}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-zinc-500">
                      {t.arquivo}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </>
  );
}
