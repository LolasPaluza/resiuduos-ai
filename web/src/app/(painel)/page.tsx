"use client";

import Link from "next/link";

import { Topbar } from "@/components/topbar";
import { apiFetch } from "@/lib/api";
import { CORES_CLASSE } from "@/lib/config";
import type {
  CotacaoResponse,
  StatusResponse,
  TurnoResponse,
} from "@/lib/types";
import { usePolling } from "@/lib/use-polling";

export default function HomePage() {
  const status = usePolling<StatusResponse>(
    () => apiFetch<StatusResponse>("/status"),
    5000,
  );
  const turno = usePolling<TurnoResponse>(
    () => apiFetch<TurnoResponse>("/turno/atual"),
    3000,
  );
  const cotacao = usePolling<CotacaoResponse>(
    () => apiFetch<CotacaoResponse>("/cotacao"),
    60000,
  );

  const t = turno.data;
  const contagens = t?.turno?.contagens || {};
  const kg = t?.kg_estimados || {};
  const totalKg = Object.values(kg).reduce((a, b) => a + b, 0);
  const alertaCount = cotacao.data?.alertas?.length ?? 0;

  return (
    <>
      <Topbar title="Dashboard" />
      <main className="flex-1 p-6 space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard
            label="Turno ativo"
            value={t?.ativo ? "sim" : "não"}
            sub={t?.ativo ? `iniciado ${formatTempo(t.tempo_decorrido_seg)}` : "—"}
            highlight={t?.ativo}
          />
          <KpiCard
            label="Peso total estimado"
            value={`${totalKg.toFixed(2)} kg`}
            sub="lote do turno"
          />
          <KpiCard
            label="Taxa de rejeito"
            value={`${(t?.contaminacao_pct ?? 0).toFixed(1)}%`}
            sub={t?.em_alerta ? "acima do limite" : "dentro do esperado"}
            warning={t?.em_alerta}
          />
          <KpiCard
            label="Alertas de cotação"
            value={`${alertaCount}`}
            sub={alertaCount > 0 ? "há oportunidade!" : "sem novidades"}
            highlight={alertaCount > 0}
          />
        </div>

        <section className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-zinc-100">
              Distribuição do turno
            </h2>
            <Link
              href="/turno"
              className="text-sm text-emerald-400 hover:text-emerald-300"
            >
              ver detalhes →
            </Link>
          </div>
          {Object.values(contagens).every((v) => v === 0) ? (
            <div className="text-zinc-500 text-sm py-8 text-center">
              Aguardando primeiras detecções do turno...
            </div>
          ) : (
            <div className="space-y-3">
              {Object.entries(contagens).map(([classe, qtd]) => {
                const total =
                  Object.values(contagens).reduce((a, b) => a + b, 0) || 1;
                const pct = (qtd / total) * 100;
                return (
                  <div key={classe}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="capitalize">{classe}</span>
                      <span className="text-zinc-400 tabular-nums">
                        {qtd} · {(kg[classe] || 0).toFixed(2)} kg
                      </span>
                    </div>
                    <div className="h-2 bg-zinc-800 rounded overflow-hidden">
                      <div
                        className="h-full rounded transition-all"
                        style={{
                          width: `${pct}%`,
                          background:
                            CORES_CLASSE[
                              classe as keyof typeof CORES_CLASSE
                            ] || "#888",
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        <section className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-base font-semibold text-zinc-100 mb-3">
            Sistema
          </h2>
          {status.error && (
            <div className="text-sm text-red-400">
              Sem conexão com o Pi. Confira se ele está ligado e na mesma Wi-Fi.
            </div>
          )}
          {status.data && (
            <dl className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <Field label="FPS" value={status.data.fps?.toFixed(2)} />
              <Field
                label="CPU"
                value={`${status.data.cpu_pct?.toFixed(1) ?? "?"}%`}
              />
              <Field
                label="Modelo"
                value={status.data.modelo?.split(/[\\/]/).pop()}
              />
              <Field label="Hardware" value={status.data.hardware} />
            </dl>
          )}
        </section>
      </main>
    </>
  );
}

function KpiCard({
  label,
  value,
  sub,
  highlight,
  warning,
}: {
  label: string;
  value: string;
  sub?: string;
  highlight?: boolean;
  warning?: boolean;
}) {
  const borderClass = warning
    ? "border-amber-700/50"
    : highlight
      ? "border-emerald-700/50"
      : "border-zinc-800";
  return (
    <div className={`bg-zinc-900 border ${borderClass} rounded-xl p-5`}>
      <div className="text-xs uppercase tracking-wider text-zinc-500 mb-2">
        {label}
      </div>
      <div className="text-2xl font-bold text-zinc-100">{value}</div>
      {sub && <div className="text-xs text-zinc-500 mt-1">{sub}</div>}
    </div>
  );
}

function Field({ label, value }: { label: string; value?: string }) {
  return (
    <div>
      <div className="text-xs text-zinc-500">{label}</div>
      <div className="text-zinc-100 font-mono text-sm">{value || "—"}</div>
    </div>
  );
}

function formatTempo(seg?: number): string {
  if (!seg) return "agora";
  const h = Math.floor(seg / 3600);
  const m = Math.floor((seg % 3600) / 60);
  if (h > 0) return `há ${h}h${m}m`;
  return `há ${m}m`;
}
