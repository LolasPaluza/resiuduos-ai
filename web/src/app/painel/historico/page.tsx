"use client";

import { useMemo } from "react";

import { Topbar } from "@/components/topbar";
import { apiFetch } from "@/lib/api";
import type { HistoricoItem } from "@/lib/types";
import { usePolling } from "@/lib/use-polling";

export default function HistoricoPage() {
  const { data, error } = usePolling<HistoricoItem[]>(
    () => apiFetch<HistoricoItem[]>("/historico"),
    15000,
  );

  const grafico = useMemo(() => {
    if (!data) return [];
    const porDia = new Map<string, number>();
    for (const t of data) {
      if (!t.inicio) continue;
      const dia = t.inicio.slice(0, 10);
      porDia.set(dia, (porDia.get(dia) || 0) + (t.total_deteccoes || 0));
    }
    const hoje = new Date();
    const dias: { dia: string; label: string; valor: number }[] = [];
    for (let i = 29; i >= 0; i--) {
      const d = new Date(hoje);
      d.setDate(d.getDate() - i);
      const k = d.toISOString().slice(0, 10);
      dias.push({
        dia: k,
        label: `${d.getDate().toString().padStart(2, "0")}/${(d.getMonth() + 1)
          .toString()
          .padStart(2, "0")}`,
        valor: porDia.get(k) || 0,
      });
    }
    return dias;
  }, [data]);

  const max = useMemo(
    () => Math.max(1, ...grafico.map((g) => g.valor)),
    [grafico],
  );
  const totalMes = useMemo(
    () => grafico.reduce((a, b) => a + b.valor, 0),
    [grafico],
  );

  return (
    <>
      <Topbar title="Histórico de turnos" />
      <main className="flex-1 p-6 space-y-6">
        {error && (
          <div className="bg-red-950/30 border border-red-900 text-red-300 rounded-xl p-4 text-sm">
            {error.message}
          </div>
        )}

        <section className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <div className="flex items-baseline justify-between mb-4">
            <h2 className="text-base font-semibold">
              Produção — últimos 30 dias
            </h2>
            <div className="text-sm text-zinc-400 tabular-nums">
              total: <span className="text-zinc-100">{totalMes}</span>{" "}
              detecções
            </div>
          </div>
          <div className="flex items-end gap-0.5 h-40">
            {grafico.map((g) => {
              const alturaPct = (g.valor / max) * 100;
              return (
                <div key={g.dia} className="flex-1 group relative">
                  <div
                    className={`w-full rounded-sm transition-all ${
                      g.valor === 0
                        ? "bg-zinc-800"
                        : "bg-gradient-to-t from-emerald-700 to-emerald-500"
                    } group-hover:from-emerald-600 group-hover:to-emerald-400`}
                    style={{
                      height: g.valor === 0 ? "4px" : `${alturaPct}%`,
                      minHeight: "4px",
                    }}
                  />
                  <div className="absolute -top-7 left-1/2 -translate-x-1/2 px-2 py-0.5 bg-zinc-950 text-xs text-zinc-100 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                    {g.label}: {g.valor}
                  </div>
                </div>
              );
            })}
          </div>
          <div className="flex justify-between text-xs text-zinc-600 mt-2">
            <span>{grafico[0]?.label}</span>
            <span>{grafico[Math.floor(grafico.length / 2)]?.label}</span>
            <span>{grafico[grafico.length - 1]?.label}</span>
          </div>
        </section>

        {data && data.length === 0 && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-8 text-center text-zinc-500 text-sm">
            Nenhum turno encerrado ainda. Quando você encerrar um turno, ele
            aparece aqui com o link pro relatório PDF.
          </div>
        )}
        {data && data.length > 0 && (
          <section className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
            <div className="px-6 py-3 border-b border-zinc-800 text-sm font-semibold">
              Turnos encerrados ({data.length})
            </div>
            <div className="overflow-x-auto">
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
                        {t.fim
                          ? new Date(t.fim).toLocaleString("pt-BR")
                          : "—"}
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
          </section>
        )}
      </main>
    </>
  );
}
