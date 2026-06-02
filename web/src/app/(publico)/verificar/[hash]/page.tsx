"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";
import type { CertificadoVerificacao } from "@/lib/types";

interface PageProps {
  params: Promise<{ hash: string }>;
}

export default function VerificarPage(props: PageProps) {
  const { hash } = use(props.params);
  const [data, setData] = useState<CertificadoVerificacao | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        // Endpoint publico — nao precisa token.
        const r = await apiFetch<CertificadoVerificacao>(
          `/certificados/${hash}/verificar`,
        );
        if (!cancelled) {
          setData(r);
          setLoading(false);
        }
      } catch (e) {
        if (!cancelled) {
          setError((e as Error).message);
          setLoading(false);
        }
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [hash]);

  return (
    <main className="min-h-screen bg-zinc-950 flex items-center justify-center p-6">
      <div className="max-w-2xl w-full">
        <header className="text-center mb-8">
          <div className="inline-flex items-center gap-2 text-emerald-400 text-sm font-mono">
            <span>♻</span> RESÍDUOS AI · VERIFICAÇÃO PÚBLICA
          </div>
          <p className="text-zinc-500 text-xs mt-2">
            Esta página é acessível sem login. Qualquer pessoa pode
            verificar a autenticidade de um certificado emitido.
          </p>
        </header>

        {loading && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-10 text-center text-zinc-400">
            Verificando hash do certificado...
          </div>
        )}

        {error && !data && (
          <div className="bg-red-950/30 border border-red-900 rounded-xl p-8 text-center">
            <div className="text-3xl mb-3">⚠</div>
            <h2 className="text-lg font-semibold text-red-200">
              Não foi possível verificar
            </h2>
            <p className="text-sm text-red-300/70 mt-2">{error}</p>
          </div>
        )}

        {data && !data.encontrado && (
          <div className="bg-amber-950/30 border border-amber-900 rounded-xl p-8 text-center">
            <div className="text-3xl mb-3">❌</div>
            <h2 className="text-lg font-semibold text-amber-200">
              Certificado não encontrado
            </h2>
            <p className="text-sm text-amber-300/70 mt-2">
              {data.mensagem ||
                "O hash fornecido não corresponde a nenhum certificado nesta cooperativa."}
            </p>
            <code className="text-xs text-zinc-500 mt-4 inline-block font-mono">
              hash: {hash}
            </code>
          </div>
        )}

        {data && data.encontrado && data.verificado && (
          <article className="bg-zinc-900 border border-emerald-700/50 rounded-xl overflow-hidden">
            <div className="bg-emerald-950/40 px-8 py-6 border-b border-emerald-700/30">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-emerald-500 flex items-center justify-center text-xl">
                  ✓
                </div>
                <div>
                  <h2 className="text-xl font-bold text-emerald-200">
                    CERTIFICADO AUTÊNTICO
                  </h2>
                  <p className="text-xs text-emerald-300/70 mt-0.5">
                    Hash SHA-256 verificado com sucesso
                  </p>
                </div>
              </div>
            </div>

            <div className="px-8 py-6 space-y-6 text-sm">
              <Section title="Emitente">
                <KV k="Cooperativa" v={data.emitente?.cooperativa || "—"} />
                <KV k="CNPJ" v={data.emitente?.cnpj || "—"} />
                <KV
                  k="Localização"
                  v={`${data.emitente?.cidade || ""}/${data.emitente?.estado || ""}`}
                />
                <KV k="Responsável" v={data.emitente?.responsavel || "—"} />
              </Section>

              <Section title="Material certificado">
                <KV k="Tipo" v={data.material || "—"} />
                <KV
                  k="Quantidade"
                  v={`${data.quantidade_kg?.toFixed(2) || 0} kg`}
                />
                <KV
                  k="Pureza"
                  v={`${data.pureza_pct?.toFixed(1) || 0}%`}
                />
              </Section>

              {data.impacto && (
                <Section title="Impacto ambiental estimado">
                  <KV
                    k="CO₂ evitado"
                    v={`${data.impacto.co2_evitado_kg.toFixed(1)} kg`}
                  />
                  <KV
                    k="Equivalente"
                    v={`${data.impacto.arvores_equivalente.toFixed(1)} árvores sequestrando por 1 ano`}
                  />
                  <KV
                    k="Água economizada"
                    v={`${data.impacto.agua_economizada_l.toFixed(0)} litros`}
                  />
                  <KV
                    k="Energia economizada"
                    v={`${data.impacto.energia_kwh.toFixed(1)} kWh`}
                  />
                </Section>
              )}

              <Section title="Validade">
                <KV
                  k="Emissão"
                  v={
                    data.emissao
                      ? new Date(data.emissao).toLocaleDateString("pt-BR")
                      : "—"
                  }
                />
                <KV
                  k="Vence em"
                  v={
                    data.validade
                      ? new Date(data.validade).toLocaleDateString("pt-BR")
                      : "—"
                  }
                />
                <KV
                  k="Hash"
                  v={
                    <code className="text-xs font-mono text-emerald-300 break-all">
                      {data.hash}
                    </code>
                  }
                />
              </Section>

              <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-4">
                <p className="text-xs text-zinc-400 leading-relaxed">
                  <strong className="text-zinc-200">
                    Sobre esta verificação:
                  </strong>{" "}
                  o hash SHA-256 acima foi calculado sobre os dados canônicos
                  do lote (material, quantidade, datas, turnos, cooperativa).
                  Qualquer alteração posterior invalidaria a verificação.
                  Nenhum dado pessoal de catadores individuais foi
                  armazenado.
                </p>
              </div>
            </div>
          </article>
        )}

        {data && data.encontrado && !data.verificado && (
          <div className="bg-red-950/30 border border-red-900 rounded-xl p-8 text-center">
            <div className="text-3xl mb-3">⚠</div>
            <h2 className="text-lg font-semibold text-red-200">
              Certificado adulterado
            </h2>
            <p className="text-sm text-red-300/70 mt-2">
              O hash não bate com o conteúdo registrado. Não confiar.
            </p>
          </div>
        )}

        <footer className="text-center mt-8 text-xs text-zinc-600">
          <Link href="/" className="hover:text-zinc-400">
            ir para o painel da cooperativa →
          </Link>
        </footer>
      </div>
    </main>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <h3 className="text-xs uppercase tracking-wider text-emerald-400 mb-3">
        {title}
      </h3>
      <dl className="space-y-2">{children}</dl>
    </div>
  );
}

function KV({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div className="flex justify-between items-baseline gap-4">
      <dt className="text-zinc-500">{k}</dt>
      <dd className="text-zinc-100 text-right">{v}</dd>
    </div>
  );
}
