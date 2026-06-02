import { Topbar } from "@/components/topbar";

const PRINCIPIOS = [
  {
    n: "01",
    titulo: "O sistema assiste, nunca julga o trabalhador",
    texto:
      "Todas as métricas são do lote e do turno. Não existe campo de identificação de catador individual. O sistema mede o material, nunca a pessoa.",
  },
  {
    n: "02",
    titulo: "Os dados pertencem à cooperativa",
    texto:
      "Nada sai do Pi por padrão. O modo offline é o normal — internet é opcional, usada só pra cotação CEMPRE e envio de relatório. A cooperativa pode exportar ou apagar tudo a qualquer momento.",
  },
  {
    n: "03",
    titulo: "Transparência do modelo",
    texto:
      "A confiança da IA aparece sempre na tela. Abaixo de 70% o sistema mostra badge amarelo de VERIFICAR. Abaixo de 50%, badge vermelho de INCERTO — e nesse caso, a detecção não é contada automaticamente. O operador tem sempre a palavra final.",
  },
  {
    n: "04",
    titulo: "Modo degradado obrigatório",
    texto:
      "Se a IA falhar, o sistema continua. A esteira não para porque um computador parou. Modo manual com teclado numérico está sempre disponível. CONTINGENCIA.md tem instruções pra operar sem o Pi se ele quebrar.",
  },
  {
    n: "05",
    titulo: "Redistribuição, não eliminação",
    texto:
      "O sistema reduz rejeição de lote e dá ferramentas de gestão pra cooperativa. O ganho de eficiência não deve virar demissão — deve virar mais volume processado, inclusão de mais pessoas, e tempo para gestão estratégica.",
  },
  {
    n: "06",
    titulo: "Acessibilidade real",
    texto:
      "Interface em português claro, sem jargão técnico. Operável só com teclado numérico. Fontes mínimas de 28px. Sons distintos por categoria para ambiente barulhento. Modo alto contraste disponível.",
  },
  {
    n: "07",
    titulo: "Consentimento informado",
    texto:
      "O instalador exibe um termo em linguagem simples antes de qualquer instalação, explicando o que o sistema faz e o que ele NÃO faz. Confirmação explícita é registrada com hash de auditoria em CONSENTIMENTO.txt.",
  },
];

export default function SobrePage() {
  return (
    <>
      <Topbar title="Sobre · Princípios" />
      <main className="flex-1 p-6 space-y-6 max-w-4xl">
        <section className="bg-gradient-to-br from-emerald-950/40 to-zinc-900 border border-emerald-900/50 rounded-xl p-8">
          <h1 className="text-2xl font-bold mb-3">
            Visão computacional pelos catadores, não sobre eles.
          </h1>
          <p className="text-zinc-300 leading-relaxed">
            Esse projeto foi pensado a partir de uma constatação simples:
            tecnologia em ambiente de trabalho geralmente é{" "}
            <strong>vigilância</strong>. Aqui não. Os sete princípios abaixo
            não são preferências — são regras invioláveis. Cada decisão
            técnica do projeto foi testada contra eles antes de ser aceita.
          </p>
        </section>

        <section className="space-y-3">
          {PRINCIPIOS.map((p) => (
            <article
              key={p.n}
              className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 flex gap-5"
            >
              <div className="text-3xl font-mono text-emerald-400/70 leading-none mt-0.5 shrink-0">
                {p.n}
              </div>
              <div>
                <h2 className="text-base font-semibold mb-2">{p.titulo}</h2>
                <p className="text-sm text-zinc-400 leading-relaxed">
                  {p.texto}
                </p>
              </div>
            </article>
          ))}
        </section>

        <section className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-base font-semibold mb-3">
            Aviso explícito sobre o uso
          </h2>
          <p className="text-sm text-zinc-400 leading-relaxed">
            Usar o sistema para <strong>justificar demissões</strong>{" "}
            contradiz frontalmente seu propósito. O ganho de eficiência deve
            virar mais material processado com a mesma equipe (e portanto
            mais renda por pessoa), inclusão de mais cooperados, ou tempo
            para gestão estratégica — não redução de postos.
          </p>
        </section>

        <section className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-base font-semibold mb-3">
            Onde isso está implementado tecnicamente
          </h2>
          <ul className="text-sm text-zinc-400 space-y-2 leading-relaxed">
            <li>
              ✓ <code className="text-zinc-200">core/turno.py</code> só
              armazena contagens por categoria — nenhum identificador
              individual
            </li>
            <li>
              ✓ <code className="text-zinc-200">privacidade.envio_externo: false</code>{" "}
              é o padrão em <code className="text-zinc-200">config.yaml</code>
            </li>
            <li>
              ✓ <code className="text-zinc-200">core/modo_degradado.py</code>{" "}
              assume controle quando a IA falha
            </li>
            <li>
              ✓ <code className="text-zinc-200">setup.sh</code> exibe o termo
              e gera <code className="text-zinc-200">CONSENTIMENTO.txt</code>{" "}
              antes de instalar
            </li>
            <li>
              ✓{" "}
              <code className="text-zinc-200">
                ferramentas/exportar_meus_dados.py
              </code>{" "}
              e <code className="text-zinc-200">deletar_meus_dados.py</code>{" "}
              dão controle pleno à cooperativa (LGPD)
            </li>
          </ul>
        </section>
      </main>
    </>
  );
}
