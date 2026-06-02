"use client";

import { Topbar } from "@/components/topbar";
import { apiFetch } from "@/lib/api";
import type { CotacaoResponse } from "@/lib/types";
import { usePolling } from "@/lib/use-polling";

export default function CotacaoPage() {
  const { data, error } = usePolling<CotacaoResponse>(
    () => apiFetch<CotacaoResponse>("/cotacao"),
    60000,
  );

  return (
    <>
      <Topbar title="Cotação de mercado" />
      <main className="flex-1 p-6 space-y-6">
        {error && (
          <div className="bg-red-950/30 border border-red-900 text-red-300 rounded-xl p-4 text-sm">
            {error.message}
          </div>
        )}

        {data?.alertas && data.alertas.length > 0 && (
          <section className="space-y-2">
            {data.alertas.map((a, i) => (
              <div
                key={i}
                className={`rounded-xl border p-4 ${
                  a.cor === "verde"
                    ? "bg-emerald-950/30 border-emerald-900 text-emerald-200"
                    : "bg-amber-950/30 border-amber-900 text-amber-200"
                }`}
              >
                <div className="font-semibold">
                  {a.tipo === "vender" ? "🟢 VENDER AGORA" : "🟡 AGUARDAR"}
                </div>
                <div className="text-sm mt-1">{a.mensagem}</div>
              </div>
            ))}
          </section>
        )}

        <section className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-base font-semibold mb-4">Preços atuais (CEMPRE)</h2>
          {!data && !error && (
            <div className="text-zinc-500 text-sm">carregando...</div>
          )}
          {data && Object.keys(data.precos).length === 0 && (
            <div className="text-zinc-500 text-sm">
              Nenhuma cotação disponível ainda. O scraper roda a cada 30 min.
            </div>
          )}
          {data && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {Object.entries(data.precos).map(([material, info]) => (
                <div
                  key={material}
                  className="bg-zinc-950 border border-zinc-800 rounded-lg p-4"
                >
                  <div className="text-sm text-zinc-400">{material}</div>
                  <div className="text-3xl font-bold mt-2 tabular-nums">
                    R$ {info.preco_rs_kg.toFixed(2)}
                    <span className="text-sm font-normal text-zinc-500"> /kg</span>
                  </div>
                  <div className="text-xs text-zinc-500 mt-2 flex justify-between">
                    <span>fonte: {info.fonte}</span>
                    {info.defasada && (
                      <span className="text-amber-400">defasada</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </>
  );
}
