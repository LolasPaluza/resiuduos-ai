"use client";

import { useState } from "react";

import { Topbar } from "@/components/topbar";
import { apiFetch, ApiError } from "@/lib/api";
import { CLASSES_RESIDUO } from "@/lib/config";
import type { CertificadoItem } from "@/lib/types";
import { usePolling } from "@/lib/use-polling";

export default function CertificadosPage() {
  const { data, error } = usePolling<CertificadoItem[]>(
    () => apiFetch<CertificadoItem[]>("/certificados"),
    15000,
  );

  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [material, setMaterial] = useState<string>("PET");
  const [desde, setDesde] = useState("");
  const [ate, setAte] = useState("");
  const [catadores, setCatadores] = useState("0");

  async function emitir() {
    setBusy(true);
    setMsg(null);
    try {
      const r = await apiFetch<{ hash: string; pdf: string }>(
        "/certificados/emitir",
        {
          method: "POST",
          body: {
            material,
            desde,
            ate,
            catadores_envolvidos: Number(catadores) || 0,
          },
        },
      );
      setMsg(`Certificado emitido: ${r.hash.slice(0, 12).toUpperCase()}`);
    } catch (e) {
      setMsg(`Falhou: ${(e as ApiError).message}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Topbar title="Certificados ESG" />
      <main className="flex-1 p-6 space-y-6">
        <section className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-base font-semibold mb-1">Emitir novo</h2>
          <p className="text-sm text-zinc-400 mb-4">
            Cria um certificado de origem para a quantidade de material
            processada no período. PDF + JSON + QR Code com verificação pública.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            <Field label="Material">
              <select
                className="bg-zinc-800 rounded px-2 py-2 text-sm"
                value={material}
                onChange={(e) => setMaterial(e.target.value)}
              >
                {CLASSES_RESIDUO.filter(
                  (c) => c !== "rejeito" && c !== "organico",
                ).map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Desde">
              <input
                type="date"
                className="bg-zinc-800 rounded px-2 py-2 text-sm"
                value={desde}
                onChange={(e) => setDesde(e.target.value)}
              />
            </Field>
            <Field label="Até">
              <input
                type="date"
                className="bg-zinc-800 rounded px-2 py-2 text-sm"
                value={ate}
                onChange={(e) => setAte(e.target.value)}
              />
            </Field>
            <Field label="Nº catadores">
              <input
                type="number"
                className="bg-zinc-800 rounded px-2 py-2 text-sm"
                value={catadores}
                onChange={(e) => setCatadores(e.target.value)}
              />
            </Field>
            <div className="flex items-end">
              <button
                onClick={emitir}
                disabled={busy}
                className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 px-4 py-2 rounded-lg text-sm font-medium w-full"
              >
                {busy ? "emitindo..." : "emitir"}
              </button>
            </div>
          </div>
          {msg && (
            <div className="text-sm mt-3 text-zinc-300">{msg}</div>
          )}
        </section>

        <section className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-base font-semibold mb-4">Certificados emitidos</h2>
          {error && (
            <div className="text-sm text-red-400">{error.message}</div>
          )}
          {data && data.length === 0 && (
            <div className="text-zinc-500 text-sm py-8 text-center">
              Nenhum certificado emitido ainda.
            </div>
          )}
          {data && data.length > 0 && (
            <div className="space-y-3">
              {data.map((c) => (
                <div
                  key={c.hash}
                  className="bg-zinc-950 border border-zinc-800 rounded-lg p-4 flex flex-col md:flex-row md:items-center gap-3"
                >
                  <div className="flex-1">
                    <div className="font-mono text-emerald-400 text-sm">
                      {c.hash_curto}
                    </div>
                    <div className="text-xs text-zinc-500 mt-1">
                      {c.material} · {c.quantidade_kg.toFixed(2)} kg · emitido em{" "}
                      {new Date(c.emissao).toLocaleDateString("pt-BR")}
                    </div>
                  </div>
                  <div className="text-xs text-zinc-400">
                    válido até {new Date(c.validade).toLocaleDateString("pt-BR")}
                  </div>
                  <code className="text-xs bg-zinc-800 px-2 py-1 rounded text-zinc-300">
                    {c.arquivo_pdf}
                  </code>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-xs text-zinc-400">{label}</span>
      {children}
    </label>
  );
}
