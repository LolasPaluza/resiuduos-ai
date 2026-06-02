"use client";

import { useState } from "react";

import { Topbar } from "@/components/topbar";
import { apiFetch, ApiError } from "@/lib/api";
import { CLASSES_RESIDUO, CORES_CLASSE } from "@/lib/config";
import type { TurnoResponse } from "@/lib/types";
import { usePolling } from "@/lib/use-polling";

export default function TurnoPage() {
  const { data, error } = usePolling<TurnoResponse>(
    () => apiFetch<TurnoResponse>("/turno/atual"),
    2000,
  );
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function iniciar() {
    setBusy(true);
    setMsg(null);
    try {
      await apiFetch("/turno/novo", { method: "POST" });
      setMsg("Turno iniciado.");
    } catch (e) {
      setMsg(`Falhou: ${(e as ApiError).message}`);
    } finally {
      setBusy(false);
    }
  }

  async function encerrar() {
    if (!confirm("Encerrar o turno e gerar o relatório?")) return;
    setBusy(true);
    setMsg(null);
    try {
      await apiFetch("/turno/encerrar", { method: "POST" });
      setMsg("Turno encerrado. Relatório gerado em dados/relatorios/.");
    } catch (e) {
      setMsg(`Falhou: ${(e as ApiError).message}`);
    } finally {
      setBusy(false);
    }
  }

  const t = data?.turno;
  const ativo = data?.ativo;
  const contagens = t?.contagens || {};
  const kg = data?.kg_estimados || {};

  return (
    <>
      <Topbar title="Turno ao vivo" />
      <main className="flex-1 p-6 space-y-6">
        {error && (
          <div className="bg-red-950/30 border border-red-900 text-red-300 rounded-xl p-4 text-sm">
            {error.message}
          </div>
        )}
        {msg && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-3 text-sm">
            {msg}
          </div>
        )}

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-3">
              {ativo && (
                <span className="w-3 h-3 rounded-full bg-emerald-500 live-dot" />
              )}
              <span className="text-lg font-semibold">
                {ativo ? "Turno em andamento" : "Nenhum turno ativo"}
              </span>
            </div>
            <div className="flex gap-2">
              {!ativo && (
                <button
                  onClick={iniciar}
                  disabled={busy}
                  className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 px-4 py-2 rounded-lg text-sm font-medium"
                >
                  iniciar turno
                </button>
              )}
              {ativo && (
                <button
                  onClick={encerrar}
                  disabled={busy}
                  className="bg-red-600 hover:bg-red-500 disabled:opacity-50 px-4 py-2 rounded-lg text-sm font-medium"
                >
                  encerrar e gerar relatório
                </button>
              )}
            </div>
          </div>
          {t && (
            <div className="text-sm text-zinc-400 mt-2 grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div className="text-xs text-zinc-500">ID</div>
                <div className="font-mono text-zinc-200">{t.id}</div>
              </div>
              <div>
                <div className="text-xs text-zinc-500">Início</div>
                <div className="text-zinc-200">
                  {new Date(t.inicio).toLocaleString("pt-BR")}
                </div>
              </div>
              <div>
                <div className="text-xs text-zinc-500">Frames processados</div>
                <div className="text-zinc-200 tabular-nums">
                  {t.total_frames}
                </div>
              </div>
              <div>
                <div className="text-xs text-zinc-500">Detecções totais</div>
                <div className="text-zinc-200 tabular-nums">
                  {t.total_deteccoes}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Cards grandes por classe */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {CLASSES_RESIDUO.map((classe) => {
            const qtd = contagens[classe] || 0;
            const pesoKg = kg[classe] || 0;
            return (
              <div
                key={classe}
                className="bg-zinc-900 border border-zinc-800 rounded-xl p-5"
                style={{ borderLeftWidth: 4, borderLeftColor: CORES_CLASSE[classe] }}
              >
                <div className="text-xs uppercase tracking-wider text-zinc-500 capitalize">
                  {classe}
                </div>
                <div className="text-4xl font-bold mt-2 tabular-nums">{qtd}</div>
                <div className="text-sm text-zinc-400 mt-1 tabular-nums">
                  {pesoKg.toFixed(2)} kg estimados
                </div>
              </div>
            );
          })}
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <div className="text-sm text-zinc-400 mb-2">Taxa de contaminação</div>
          <div className="flex items-baseline gap-3">
            <span
              className={`text-4xl font-bold tabular-nums ${
                data?.em_alerta ? "text-amber-400" : "text-emerald-400"
              }`}
            >
              {(data?.contaminacao_pct ?? 0).toFixed(1)}%
            </span>
            <span className="text-sm text-zinc-500">
              {data?.em_alerta
                ? "acima do limite (lote pode ser rejeitado)"
                : "dentro do limite — lote saudável"}
            </span>
          </div>
        </div>
      </main>
    </>
  );
}
