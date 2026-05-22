"use client";

import { useEffect, useState } from "react";

import { Topbar } from "@/components/topbar";
import { apiFetch, ApiError, getToken, setToken } from "@/lib/api";
import { API_URL } from "@/lib/config";

export default function ConfiguracaoPage() {
  const [tokenInput, setTokenInput] = useState("");
  const [mensagem, setMensagem] = useState<string | null>(null);
  const [testando, setTestando] = useState(false);

  useEffect(() => {
    setTokenInput(getToken());
  }, []);

  function salvar() {
    setToken(tokenInput.trim());
    setMensagem("Token salvo no navegador.");
  }

  async function testar() {
    setTestando(true);
    setMensagem(null);
    try {
      const r = await apiFetch<{ ok: boolean }>("/turno/atual");
      void r;
      setMensagem("Conexão OK e token funcionando.");
    } catch (e) {
      const err = e as ApiError;
      if (err.status === 401) {
        setMensagem("Conectou mas token inválido. Confira o valor.");
      } else {
        setMensagem(`Falhou: ${err.message}`);
      }
    } finally {
      setTestando(false);
    }
  }

  return (
    <>
      <Topbar title="Configuração" />
      <main className="flex-1 p-6 space-y-6 max-w-3xl">
        <section className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-base font-semibold mb-1">Conexão com o Pi</h2>
          <p className="text-sm text-zinc-400 mb-4">
            URL da API:{" "}
            <code className="bg-zinc-800 px-2 py-0.5 rounded">{API_URL}</code>{" "}
            <span className="text-xs text-zinc-500">
              (configure em <code>web/.env.local</code> com{" "}
              <code>NEXT_PUBLIC_API_URL</code>)
            </span>
          </p>

          <div className="space-y-3">
            <label className="block">
              <span className="text-xs text-zinc-400 block mb-1">
                Token de gestor (Bearer)
              </span>
              <input
                type="password"
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
                placeholder="ghp_xxx... (config.yaml &gt; api.token_gestor)"
                className="w-full bg-zinc-800 rounded px-3 py-2 text-sm font-mono"
              />
            </label>
            <p className="text-xs text-zinc-500">
              No Pi, descubra com:{" "}
              <code className="bg-zinc-800 px-1 rounded">
                grep token_gestor ~/projetos/residuos-ai/config.yaml
              </code>
            </p>
            <div className="flex gap-2">
              <button
                onClick={salvar}
                className="bg-emerald-600 hover:bg-emerald-500 px-4 py-2 rounded-lg text-sm"
              >
                salvar token
              </button>
              <button
                onClick={testar}
                disabled={testando}
                className="bg-zinc-700 hover:bg-zinc-600 disabled:opacity-50 px-4 py-2 rounded-lg text-sm"
              >
                {testando ? "testando..." : "testar conexão"}
              </button>
            </div>
            {mensagem && (
              <div className="text-sm text-zinc-300 mt-2">{mensagem}</div>
            )}
          </div>
        </section>

        <section className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-base font-semibold mb-2">Privacidade & Ética</h2>
          <p className="text-sm text-zinc-400 leading-relaxed">
            Os dados deste sistema nunca identificam catadores individualmente.
            Nenhum dado sai do Pi por padrão. Para exportar tudo a qualquer
            momento, use o endpoint{" "}
            <code className="bg-zinc-800 px-1 rounded">/dados/exportar</code> ou
            o script{" "}
            <code className="bg-zinc-800 px-1 rounded">
              python -m ferramentas.exportar_meus_dados
            </code>{" "}
            no Pi.
          </p>
        </section>
      </main>
    </>
  );
}
