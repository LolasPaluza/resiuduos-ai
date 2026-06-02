"use client";
/* Todas as outras secoes da landing num arquivo compacto. */

export function SectionHead({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: React.ReactNode;
  description?: React.ReactNode;
}) {
  return (
    <div className="max-w-3xl mb-12">
      <span className="inline-block text-xs uppercase tracking-[0.14em] font-mono text-[var(--text-mute)] mb-4">
        {eyebrow}
      </span>
      <h2
        className="font-medium leading-[1.08] mb-4"
        style={{ fontSize: "clamp(34px, 4.6vw, 60px)" }}
      >
        {title}
      </h2>
      {description && (
        <p className="text-base lg:text-lg text-[var(--text-dim)]">
          {description}
        </p>
      )}
    </div>
  );
}

function Container({ children, id }: { children: React.ReactNode; id?: string }) {
  return (
    <section id={id} className="relative" style={{ padding: "var(--section-py) 0" }}>
      <div
        className="relative mx-auto"
        style={{ maxWidth: "var(--max-w)", padding: "0 var(--gutter)" }}
      >
        {children}
      </div>
    </section>
  );
}

/* ========== 3 — PROBLEMA ========== */

const PROBLEMA = [
  {
    cor: "var(--red)",
    icon: "🗑",
    num: "20%",
    title: "Rejeição de lote",
    text: "Operador cansado classifica errado. Lote vai com 15–25% de contaminação. Indústria recusa ou paga metade. Perda de R$ 3–6 mil/mês silenciosa.",
  },
  {
    cor: "var(--amber)",
    icon: "↘",
    num: "40%",
    title: "Preço injusto",
    text: "Sem saber o preço real do alumínio hoje, o gestor aceita o que o atravessador oferece — 30–40% abaixo do valor de mercado.",
  },
  {
    cor: "var(--blue)",
    icon: "⊘",
    num: "R$0",
    title: "Sem histórico",
    text: "Sem dados registrados, banco não empresta. Sem crédito, cooperativa não cresce. A mesma receita, o mesmo volume, para sempre.",
  },
];

export function ProblemaSection() {
  return (
    <Container id="problema">
      <SectionHead
        eyebrow="O Problema"
        title={
          <>
            A cooperativa trabalha muito
            <br />e ganha pouco.
          </>
        }
        description="Não por falta de esforço — por três buracos específicos no processo."
      />
      <div className="grid md:grid-cols-3 gap-4">
        {PROBLEMA.map((p) => (
          <article
            key={p.title}
            className="bg-[var(--surface)] border border-white/5 rounded-[var(--r-lg)] p-6 relative overflow-hidden"
            style={{ borderTop: `3px solid ${p.cor}` }}
          >
            <div
              className="w-10 h-10 rounded-lg flex items-center justify-center text-lg mb-4"
              style={{ background: `${p.cor}22`, color: p.cor }}
            >
              {p.icon}
            </div>
            <div
              className="font-mono text-4xl lg:text-5xl mb-2"
              style={{ color: p.cor }}
            >
              {p.num}
            </div>
            <h3 className="font-medium mb-2">{p.title}</h3>
            <p className="text-sm text-[var(--text-dim)] leading-relaxed">
              {p.text}
            </p>
          </article>
        ))}
      </div>
      <div className="mt-10 bg-[var(--green-glow)] border border-[var(--green)]/30 rounded-[var(--r-lg)] p-5 flex gap-4 items-start">
        <div
          className="w-9 h-9 rounded-full bg-[var(--green)]/15 flex items-center justify-center text-[var(--green)] shrink-0"
          aria-hidden
        >
          ⓘ
        </div>
        <p className="text-sm leading-relaxed">
          Os três problemas têm a mesma causa: ninguém registra o que acontece
          dentro da cooperativa. Sem dado, não tem argumento, não tem crédito,
          não tem poder de negociação.
        </p>
      </div>

      {/* Gráfico de fadiga SVG simples */}
      <FatigueChart />
    </Container>
  );
}

function FatigueChart() {
  // 8 horas de turno
  const erroOp = [5, 7, 9, 12, 14, 17, 20, 22];
  const erroAI = [3, 3, 3, 3, 3, 3, 3, 3];
  const w = 600;
  const h = 200;
  const padX = 30;
  const padY = 24;
  const xs = erroOp.map((_, i) => padX + (i / 7) * (w - padX * 2));
  const yScale = (v: number) => h - padY - (v / 25) * (h - padY * 2);

  const path = (vals: number[]) =>
    vals.map((v, i) => `${i === 0 ? "M" : "L"} ${xs[i]} ${yScale(v)}`).join(" ");

  return (
    <div className="mt-10 bg-[var(--surface)] border border-white/5 rounded-[var(--r-lg)] p-6">
      <div className="flex items-baseline justify-between mb-4 gap-4 flex-wrap">
        <div>
          <span className="text-xs uppercase tracking-[0.14em] font-mono text-[var(--text-mute)]">
            Fadiga do operador
          </span>
          <h3 className="mt-2 text-lg">
            Taxa de erro ao longo do turno (8 horas)
          </h3>
        </div>
        <div className="flex gap-4 text-xs">
          <span className="flex items-center gap-2">
            <span className="w-3 h-0.5 bg-[var(--red)]" /> Sem sistema
          </span>
          <span className="flex items-center gap-2">
            <span className="w-3 h-0.5 bg-[var(--green)]" /> Com ReciclaIA
          </span>
        </div>
      </div>
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full">
        {/* Grid */}
        {[0, 5, 10, 15, 20, 25].map((v) => (
          <g key={v}>
            <line
              x1={padX}
              x2={w - padX}
              y1={yScale(v)}
              y2={yScale(v)}
              stroke="rgba(255,255,255,0.05)"
            />
            <text
              x={5}
              y={yScale(v) + 4}
              fill="var(--text-mute)"
              fontSize="9"
              fontFamily="var(--font-mono)"
            >
              {v}%
            </text>
          </g>
        ))}
        {/* Curva operador (vermelha com area) */}
        <path
          d={`${path(erroOp)} L ${xs[7]} ${h - padY} L ${xs[0]} ${h - padY} Z`}
          fill="rgba(239,68,68,0.1)"
        />
        <path
          d={path(erroOp)}
          fill="none"
          stroke="var(--red)"
          strokeWidth="2"
        />
        {/* Linha AI (verde tracejada) */}
        <path
          d={path(erroAI)}
          fill="none"
          stroke="var(--green)"
          strokeWidth="2"
          strokeDasharray="6 4"
        />
        {/* labels eixo X */}
        {erroOp.map((_, i) => (
          <text
            key={i}
            x={xs[i]}
            y={h - 4}
            textAnchor="middle"
            fill="var(--text-mute)"
            fontSize="9"
            fontFamily="var(--font-mono)"
          >
            H{i + 1}
          </text>
        ))}
      </svg>
    </div>
  );
}

/* ========== 4 — COMO FUNCIONA ========== */

const SCENARIOS = [
  {
    cor: "var(--green)",
    badge: "AUTO",
    title: "✅ Confiança ≥ 70%",
    text: "Sistema classifica automaticamente. Bounding box verde. Som curto. Material contabilizado. Ritmo não para.",
  },
  {
    cor: "var(--amber)",
    badge: "VERIFICAR",
    title: "⚠ Confiança 50–70%",
    text: "Badge amarelo VERIFICAR em fonte grande. Som duplo. Operador pressiona tecla 1–6. Sistema aprende com a correção.",
  },
  {
    cor: "var(--red)",
    badge: "ALERTA",
    title: "🔴 Rejeito detectado",
    text: "Badge vermelho piscando. Som agudo. Se rejeito ultrapassar 10% do lote: tela inteira vermelha.",
  },
];

const PIPELINE = [
  { name: "Webcam", sub: "Captura", cor: "var(--green)" },
  { name: "OpenCV", sub: "Pré-proc.", cor: "var(--blue)" },
  { name: "YOLOv8n", sub: "Inferência", cor: "var(--purple)" },
  { name: "Display", sub: "Exibição", cor: "var(--amber)" },
  { name: "SQLite", sub: "Persistência", cor: "var(--red)" },
  { name: "Relatório", sub: "Exportação", cor: "var(--gray)" },
];

const KEYS = [
  { k: "1", l: "PET", cor: "var(--c-pet)" },
  { k: "2", l: "PEAD", cor: "var(--c-pead)" },
  { k: "3", l: "Papel", cor: "var(--c-papel)" },
  { k: "4", l: "Metal", cor: "var(--c-metal)" },
  { k: "5", l: "Orgânico", cor: "var(--c-org)" },
  { k: "6", l: "Rejeito", cor: "var(--c-rej)" },
  { k: "0", l: "Fechar turno", cor: "var(--text-dim)" },
];

export function ComoFuncionaSection() {
  return (
    <Container id="como-funciona">
      <SectionHead
        eyebrow="Como Funciona"
        title={
          <>
            A câmera fica acima da esteira.
            <br />O operador confirma.
          </>
        }
        description="É onde o dinheiro é ganho ou perdido — e onde o sistema entra."
      />

      <div id="solucao" className="grid lg:grid-cols-[1.3fr_1fr] gap-8">
        {/* Diagrama da esteira */}
        <div className="bg-[var(--surface)] border border-white/5 rounded-[var(--r-lg)] p-6">
          <EsteiraDiagram />
          <div className="flex gap-3 flex-wrap pt-4 border-t border-white/10 mt-3 font-mono text-xs text-[var(--text-mute)]">
            <span>① Captura 1080p</span>
            <span>② Inferência local</span>
            <span>③ Operador confirma</span>
            <span>④ Histórico SQLite</span>
          </div>
        </div>

        {/* 3 cenários */}
        <div className="space-y-3">
          {SCENARIOS.map((s) => (
            <article
              key={s.title}
              className="bg-[var(--surface)] border border-white/5 rounded-[var(--r-lg)] p-5"
              style={{ borderLeft: `4px solid ${s.cor}` }}
            >
              <h4 className="font-medium mb-2 flex items-center gap-2 flex-wrap">
                {s.title}
                <span
                  className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded-full"
                  style={{ background: `${s.cor}22`, color: s.cor }}
                >
                  {s.badge}
                </span>
              </h4>
              <p className="text-sm text-[var(--text-dim)] leading-relaxed">
                {s.text}
              </p>
            </article>
          ))}
        </div>
      </div>

      {/* Pipeline */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2 mt-12">
        {PIPELINE.map((p, i) => (
          <div
            key={p.name}
            className="bg-[var(--surface)] border border-white/5 rounded-md p-3 relative"
            style={{ borderLeft: `3px solid ${p.cor}` }}
          >
            <div className="font-medium text-sm">{p.name}</div>
            <div className="text-xs text-[var(--text-mute)] mt-0.5">{p.sub}</div>
            {i < PIPELINE.length - 1 && (
              <span className="hidden lg:block absolute -right-1.5 top-1/2 -translate-y-1/2 text-[var(--text-mute)]">
                ›
              </span>
            )}
          </div>
        ))}
      </div>

      {/* Mapa de teclas */}
      <div className="mt-12 bg-[var(--surface)] border border-white/5 rounded-[var(--r-lg)] p-6">
        <span className="text-xs uppercase tracking-[0.14em] font-mono text-[var(--text-mute)] block mb-4">
          Mapa de teclas
        </span>
        <div className="grid grid-cols-4 md:grid-cols-7 gap-2">
          {KEYS.map((k) => (
            <div
              key={k.k}
              className="bg-[var(--bg)] border border-white/5 rounded-md p-3 text-center hover:-translate-y-0.5 transition"
              style={{ borderBottom: `3px solid ${k.cor}` }}
            >
              <div className="font-mono text-xl">{k.k}</div>
              <div className="text-[10px] uppercase tracking-wider text-[var(--text-mute)] mt-1">
                {k.l}
              </div>
            </div>
          ))}
        </div>
        <p className="text-xs text-[var(--text-mute)] mt-4">
          Operável apenas com teclado numérico — sem mouse, sem touch, sem
          treinamento técnico.
        </p>
      </div>
    </Container>
  );
}

function EsteiraDiagram() {
  return (
    <svg viewBox="0 0 600 320" className="w-full">
      {/* Camera */}
      <g>
        <rect x="270" y="20" width="60" height="40" rx="6" fill="var(--surface-3)" stroke="rgba(255,255,255,0.1)" />
        <circle cx="300" cy="40" r="10" fill="var(--bg)" stroke="var(--green)" strokeWidth="1.5" />
        <circle cx="300" cy="40" r="4" fill="var(--green)" />
        <text x="300" y="14" textAnchor="middle" fill="var(--text-mute)" fontSize="10" fontFamily="var(--font-mono)">
          Webcam 1080p
        </text>
      </g>
      {/* Cone de visão */}
      <polygon points="270,60 330,60 380,180 220,180" fill="rgba(25,226,126,0.05)" stroke="rgba(25,226,126,0.3)" strokeDasharray="3 3" />
      {/* Esteira */}
      <g>
        <rect x="40" y="180" width="520" height="60" fill="var(--surface-3)" stroke="rgba(255,255,255,0.1)" />
        <pattern id="belt" patternUnits="userSpaceOnUse" width="40" height="60">
          <line x1="0" y1="0" x2="0" y2="60" stroke="rgba(255,255,255,0.06)" />
        </pattern>
        <rect x="40" y="180" width="520" height="60" fill="url(#belt)" />
        <circle cx="50" cy="210" r="14" fill="var(--surface-2)" stroke="rgba(255,255,255,0.1)" />
        <circle cx="550" cy="210" r="14" fill="var(--surface-2)" stroke="rgba(255,255,255,0.1)" />
        {/* Itens na esteira */}
        <circle cx="180" cy="210" r="8" fill="var(--c-pet)" opacity="0.5" />
        <circle cx="240" cy="210" r="9" fill="var(--c-papel)" opacity="0.5" />
        <circle cx="300" cy="210" r="7" fill="var(--c-metal)" opacity="0.7" />
        <circle cx="380" cy="210" r="8" fill="var(--c-pead)" opacity="0.5" />
        <circle cx="460" cy="210" r="9" fill="var(--c-org)" opacity="0.5" />
      </g>
      {/* Pi */}
      <g>
        <rect x="40" y="260" width="80" height="50" rx="4" fill="var(--surface-3)" stroke="rgba(255,255,255,0.1)" />
        <circle cx="55" cy="275" r="2" fill="var(--green)" />
        <text x="80" y="280" textAnchor="middle" fill="var(--text-dim)" fontSize="10" fontFamily="var(--font-mono)">
          Raspberry Pi
        </text>
        <text x="80" y="294" textAnchor="middle" fill="var(--text-mute)" fontSize="9" fontFamily="var(--font-mono)">
          local · offline
        </text>
      </g>
      {/* Display */}
      <g>
        <rect x="160" y="260" width="160" height="50" rx="4" fill="var(--surface-3)" stroke="rgba(255,255,255,0.1)" />
        <rect x="170" y="268" width="50" height="14" fill="var(--green)" opacity="0.2" rx="2" />
        <text x="195" y="278" textAnchor="middle" fill="var(--green)" fontSize="9" fontFamily="var(--font-mono)">
          PET 94%
        </text>
        <text x="240" y="280" fill="var(--text-dim)" fontSize="10" fontFamily="var(--font-mono)">
          PET: 47
        </text>
        <text x="240" y="294" fill="var(--text-dim)" fontSize="10" fontFamily="var(--font-mono)">
          Papel: 61
        </text>
      </g>
      {/* Teclado */}
      <g>
        <rect x="360" y="260" width="100" height="50" rx="4" fill="var(--surface-3)" stroke="rgba(255,255,255,0.1)" />
        {[0, 1, 2].map((row) =>
          [0, 1, 2].map((col) => (
            <rect
              key={`${row}${col}`}
              x={368 + col * 28}
              y={266 + row * 14}
              width="20"
              height="10"
              rx="1"
              fill="var(--bg)"
              stroke="rgba(255,255,255,0.05)"
            />
          )),
        )}
        <text x="410" y="320" textAnchor="middle" fill="var(--text-mute)" fontSize="9" fontFamily="var(--font-mono)">
          teclado numérico
        </text>
      </g>
      {/* Bins */}
      <g>
        <rect x="490" y="260" width="20" height="35" rx="2" fill="var(--c-pet)" opacity="0.4" />
        <rect x="514" y="260" width="20" height="35" rx="2" fill="var(--c-papel)" opacity="0.4" />
        <rect x="538" y="260" width="20" height="35" rx="2" fill="var(--c-metal)" opacity="0.4" />
      </g>
    </svg>
  );
}

/* ========== 5 — MATERIAIS ========== */

const MATERIAIS = [
  { cor: "var(--c-pet)", icon: "💧", name: "PET", k: "1", ex: "Garrafas, embalagens transparentes." },
  { cor: "var(--c-pead)", icon: "🥛", name: "PEAD", k: "2", ex: "Frascos opacos, galões, tampas." },
  { cor: "var(--c-papel)", icon: "📰", name: "Papel", k: "3", ex: "Caixas, jornal, revista, papelão." },
  { cor: "var(--c-metal)", icon: "⬡", name: "Metal", k: "4", ex: "Latas de alumínio, ferro, cobre, aço." },
  { cor: "var(--c-org)", icon: "🌿", name: "Orgânico", k: "5", ex: "Restos de comida, cascas, material úmido." },
  { cor: "var(--c-rej)", icon: "✕", name: "Rejeito", k: "6", ex: "Não reciclável, composto, sujo demais." },
];

export function MateriaisSection() {
  return (
    <Container id="materiais">
      <SectionHead
        eyebrow="Classificação"
        title={
          <>
            6 classes de material.
            <br />
            Classificadas em menos de 100&nbsp;ms.
          </>
        }
      />
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {MATERIAIS.map((m) => (
          <article
            key={m.name}
            className="bg-[var(--surface)] border border-white/5 rounded-[var(--r-lg)] p-6 hover:-translate-y-0.5 transition"
            style={{ borderTop: `3px solid ${m.cor}` }}
          >
            <div className="flex items-start justify-between mb-4">
              <div
                className="w-11 h-11 rounded-lg flex items-center justify-center text-xl"
                style={{ background: `${m.cor}22`, color: m.cor }}
              >
                {m.icon}
              </div>
              <span
                className="font-mono px-2 py-0.5 rounded text-sm"
                style={{ background: "var(--bg)", color: m.cor }}
              >
                {m.k}
              </span>
            </div>
            <h3 className="text-2xl font-medium mb-1">{m.name}</h3>
            <p className="text-sm text-[var(--text-dim)]">{m.ex}</p>
          </article>
        ))}
      </div>
      <div className="flex flex-wrap gap-3 mt-8 text-xs font-mono">
        <span className="px-3 py-1.5 bg-[var(--surface)] border border-white/5 rounded-full">
          Precisão após 1 mês:{" "}
          <strong className="text-[var(--green)]">80–85%</strong>
        </span>
        <span className="px-3 py-1.5 bg-[var(--surface)] border border-white/5 rounded-full">
          Precisão após 3 meses:{" "}
          <strong className="text-[var(--green)]">90%+</strong>
        </span>
      </div>
    </Container>
  );
}

/* ========== 6 — FINANCEIRO ========== */

const KPIS_FIN = [
  { cor: "var(--green)", v: "~1 mês", l: "payback do investimento" },
  { cor: "var(--blue)", v: "+60%", l: "aumento potencial de receita" },
  { cor: "var(--red)", v: "−75%", l: "redução na taxa de rejeição" },
  { cor: "var(--amber)", v: "R$ 600", l: "custo total do hardware" },
];

export function FinanceiroSection() {
  return (
    <Container id="financeiro">
      <SectionHead
        eyebrow="Financeiro"
        title={
          <>
            Payback em aproximadamente
            <br />1&nbsp;mês.
          </>
        }
        description="Hardware de R$ 600. Resultado positivo de R$ 22–31 mil por mês."
      />
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
        {KPIS_FIN.map((k) => (
          <div
            key={k.l}
            className="bg-[var(--surface)] border border-white/5 rounded-[var(--r-lg)] p-5 relative overflow-hidden"
          >
            <div
              className="absolute -top-10 -right-10 w-32 h-32 rounded-full"
              style={{ background: `${k.cor}15` }}
            />
            <div
              className="font-mono mb-1 relative"
              style={{ fontSize: "clamp(34px, 4vw, 48px)", color: k.cor }}
            >
              {k.v}
            </div>
            <div className="text-xs text-[var(--text-mute)] relative">
              {k.l}
            </div>
          </div>
        ))}
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="bg-[var(--surface)] border border-[var(--red)]/30 rounded-[var(--r-lg)] p-6">
          <h3 className="font-medium mb-4 text-[var(--red)]">Sem sistema</h3>
          <dl className="space-y-2 text-sm border-b border-white/5 pb-4 mb-4">
            <Row label="Custo operacional" value="R$ 43.400/mês" />
            <Row label="Perda por rejeição" value="R$ 3–6k/mês" />
            <Row label="Receita mensal" value="R$ 45.000" />
          </dl>
          <div className="flex justify-between items-baseline">
            <span className="text-xs uppercase tracking-wider text-[var(--text-mute)]">
              Resultado
            </span>
            <span className="font-mono text-2xl text-[var(--red)]">
              − R$ 2k
            </span>
          </div>
        </div>

        <div
          className="border border-[var(--green)]/40 rounded-[var(--r-lg)] p-6"
          style={{
            background:
              "linear-gradient(135deg, rgba(25,226,126,0.08) 0%, var(--surface) 60%)",
          }}
        >
          <h3 className="font-medium mb-4 text-[var(--green)]">
            Com ReciclaIA
          </h3>
          <dl className="space-y-2 text-sm border-b border-white/5 pb-4 mb-4">
            <Row label="Custo operacional" value="R$ 32.000/mês" />
            <Row label="Perda por rejeição" value="R$ 800–1.200/mês" />
            <Row label="Receita mensal" value="R$ 72–81k" />
          </dl>
          <div className="flex justify-between items-baseline">
            <span className="text-xs uppercase tracking-wider text-[var(--text-mute)]">
              Resultado
            </span>
            <span className="font-mono text-2xl text-[var(--green)]">
              + R$ 22–31k
            </span>
          </div>
        </div>
      </div>

      <PaybackChart />
    </Container>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <dt className="text-[var(--text-dim)]">{label}</dt>
      <dd className="font-mono">{value}</dd>
    </div>
  );
}

function PaybackChart() {
  // 13 pontos (M0 a M12) — sem sistema cai, com sistema sobe
  const semSis = [-42, -85, -130, -175, -222, -268, -315, -360, -407, -453, -500, -528, -564];
  const comSis = [-18, 22, 60, 95, 130, 162, 192, 218, 240, 250, 256, 252, 246];
  const w = 600;
  const h = 220;
  const padX = 40;
  const padY = 30;
  const xs = semSis.map((_, i) => padX + (i / 12) * (w - padX * 2));
  const minY = -600;
  const maxY = 280;
  const yScale = (v: number) =>
    h - padY - ((v - minY) / (maxY - minY)) * (h - padY * 2);
  const zero = yScale(0);

  const path = (vals: number[]) =>
    vals
      .map((v, i) => `${i === 0 ? "M" : "L"} ${xs[i]} ${yScale(v)}`)
      .join(" ");

  // ponto payback aprox em M1 onde com_sis cruza zero
  const paybackX = xs[1];
  const paybackY = yScale(comSis[1]);

  return (
    <div className="mt-10 bg-[var(--surface)] border border-white/5 rounded-[var(--r-lg)] p-6">
      <div className="flex items-baseline justify-between mb-4 gap-4 flex-wrap">
        <div>
          <span className="text-xs uppercase tracking-[0.14em] font-mono text-[var(--text-mute)]">
            Retorno acumulado
          </span>
          <h3 className="mt-2 text-lg">
            Retorno acumulado — 12 meses (R$ mil)
          </h3>
        </div>
        <div className="flex gap-4 text-xs">
          <span className="flex items-center gap-2">
            <span className="w-3 h-0.5 bg-[var(--text-mute)] border-dashed" /> Sem sistema
          </span>
          <span className="flex items-center gap-2">
            <span className="w-3 h-0.5 bg-[var(--green)]" /> Com ReciclaIA
          </span>
        </div>
      </div>

      <svg viewBox={`0 0 ${w} ${h}`} className="w-full">
        {/* grid horizontal */}
        {[-600, -400, -200, 0, 200].map((v) => (
          <g key={v}>
            <line
              x1={padX}
              x2={w - padX}
              y1={yScale(v)}
              y2={yScale(v)}
              stroke="rgba(255,255,255,0.05)"
            />
            <text
              x={5}
              y={yScale(v) + 4}
              fill="var(--text-mute)"
              fontSize="9"
              fontFamily="var(--font-mono)"
            >
              {v >= 0 ? `+${v}` : v}
            </text>
          </g>
        ))}
        {/* zero destacado */}
        <line
          x1={padX}
          x2={w - padX}
          y1={zero}
          y2={zero}
          stroke="rgba(255,255,255,0.15)"
        />
        {/* Sem sistema (cinza tracejado) */}
        <path
          d={path(semSis)}
          fill="none"
          stroke="var(--text-mute)"
          strokeWidth="1.5"
          strokeDasharray="5 3"
        />
        {/* Com sistema (verde) */}
        <path
          d={`${path(comSis)} L ${xs[12]} ${zero} L ${xs[0]} ${zero} Z`}
          fill="rgba(25,226,126,0.1)"
        />
        <path
          d={path(comSis)}
          fill="none"
          stroke="var(--green)"
          strokeWidth="2.5"
        />
        {/* Payback marker */}
        <circle cx={paybackX} cy={paybackY} r="6" fill="var(--green)" className="pulse-ring" />
        <text
          x={paybackX + 10}
          y={paybackY - 8}
          fill="var(--green)"
          fontSize="11"
          fontFamily="var(--font-mono)"
        >
          payback aqui
        </text>
        {/* labels eixo x */}
        {xs.map((x, i) =>
          i % 2 === 0 ? (
            <text
              key={i}
              x={x}
              y={h - 4}
              textAnchor="middle"
              fill="var(--text-mute)"
              fontSize="9"
              fontFamily="var(--font-mono)"
            >
              M{i}
            </text>
          ) : null,
        )}
      </svg>
    </div>
  );
}

/* ========== 7 — INDÚSTRIA ========== */

const KPIS_IND = [
  { cor: "var(--amber)", v: "20–40%", l: "prêmio por material rastreável" },
  { cor: "var(--green)", v: "R$ 0", l: "custo de implementação" },
  { cor: "var(--blue)", v: "100%", l: "rastreabilidade de origem" },
  { cor: "var(--purple)", v: "CSRD", l: "regulação europeia atendida" },
];

export function IndustriaSection() {
  return (
    <Container id="industria">
      <SectionHead
        eyebrow="Para a Indústria"
        title={
          <>
            A fábrica ganha sem
            <br />
            pagar nada.
          </>
        }
        description="O sistema fica na cooperativa. A indústria recebe material certificado, rastreável e com dados ESG prontos para publicar."
      />
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-10">
        {KPIS_IND.map((k) => (
          <div
            key={k.l}
            className="bg-[var(--surface)] border border-white/5 rounded-[var(--r-lg)] p-5"
          >
            <div className="font-mono text-3xl mb-1" style={{ color: k.cor }}>
              {k.v}
            </div>
            <div className="text-xs text-[var(--text-mute)]">{k.l}</div>
          </div>
        ))}
      </div>
      <div className="grid lg:grid-cols-[1.4fr_1fr] gap-6">
        {/* Tabela */}
        <div className="bg-[var(--surface)] border border-white/5 rounded-[var(--r-lg)] overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-black/30 text-xs uppercase tracking-wider text-[var(--text-mute)]">
              <tr>
                <th className="text-left p-3"></th>
                <th className="text-left p-3">Sem ReciclaIA</th>
                <th className="text-left p-3 text-[var(--green)]">
                  Com ReciclaIA
                </th>
              </tr>
            </thead>
            <tbody>
              {[
                ["Qualidade do lote", "15–25% de rejeito", "< 5% certificado"],
                ["Rastreabilidade ESG", "Inexistente", "QR Code · SHA256"],
                ["Relatório de sustentabilidade", "Sem dados", "CO₂, água, energia auto"],
                ["Regulação europeia", "Não atende", "Documentação completa"],
                ["Preço", "Commoditie", "+20–40% de prêmio"],
              ].map((row, i) => (
                <tr key={i} className="border-t border-white/5">
                  <td className="p-3">{row[0]}</td>
                  <td className="p-3 text-[var(--red)]/80">{row[1]}</td>
                  <td className="p-3 text-[var(--green)]">{row[2]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Certificado mockup */}
        <aside className="bg-[var(--surface)] border border-[var(--green)]/30 rounded-[var(--r-lg)] p-6 text-sm relative">
          <span className="absolute top-4 right-4 text-[10px] font-mono uppercase tracking-wider px-2 py-1 rounded-full bg-[var(--green)] text-zinc-950">
            VÁLIDO
          </span>
          <h3 className="font-medium mb-1">Certificado de Origem</h3>
          <div className="text-xs font-mono text-[var(--green)] mb-4">
            ReciclaIA · CERT-2025-0847
          </div>
          <hr className="border-white/5 mb-3" />
          <KVRow k="Material" v="PET cristal · 320 kg" />
          <KVRow k="Pureza" v="97,2%" />
          <KVRow k="Cooperativa" v="Exemplo — SP" />
          <KVRow k="Catadores" v="28 (anon.)" />
          <hr className="border-white/5 my-3" />
          <KVRow k="CO₂ evitado" v="486 kg" />
          <KVRow k="Água economizada" v="9.600 L" />
          <KVRow k="Energia" v="1.280 kWh" />
          <div className="flex items-center gap-3 mt-4 pt-4 border-t border-white/5">
            <div
              className="w-12 h-12 rounded grid grid-cols-4 grid-rows-4 gap-px overflow-hidden"
              style={{ background: "#fff" }}
              aria-hidden
            >
              {Array.from({ length: 16 }).map((_, i) => (
                <span
                  key={i}
                  style={{
                    background: [0, 1, 4, 5, 8, 11, 14, 15].includes(i)
                      ? "#000"
                      : "#fff",
                  }}
                />
              ))}
            </div>
            <div className="font-mono text-[10px] text-[var(--text-mute)]">
              SHA256:
              <br />
              a3f7b2c1·····d9e4
            </div>
          </div>
        </aside>
      </div>
    </Container>
  );
}

function KVRow({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between py-1 text-xs">
      <span className="text-[var(--text-mute)]">{k}</span>
      <span className="text-[var(--text)]">{v}</span>
    </div>
  );
}

/* ========== 8 — ÉTICA ========== */

const ETICA = [
  { t: "Assiste — nunca julga", d: "Métricas por lote e turno, nunca por indivíduo." },
  { t: "Dados pertencem à cooperativa", d: "Zero envio externo por padrão." },
  { t: "Transparência total", d: "Confiança sempre visível. Abaixo de 70%: VERIFICAR." },
  { t: "Sem dependência frágil", d: "Modo manual obrigatório se IA falhar." },
  { t: "Redistribuição, não demissão", d: "Usar pra cortes contradiz o propósito." },
  { t: "Acessibilidade real", d: "Só teclado numérico. Fonte mínima 28px." },
  { t: "Consentimento na instalação", d: "Setup pede confirmação antes de instalar." },
];

const ETICA_CORES = ["var(--green)", "var(--blue)", "var(--amber)", "var(--purple)", "var(--red)", "var(--c-pet)", "var(--c-papel)"];

export function EticaSection() {
  return (
    <Container id="etica">
      <SectionHead
        eyebrow="Ética"
        title={
          <>
            7 princípios embutidos
            <br />
            no código.
          </>
        }
        description="Não no papel. No código. Se um princípio conflitar com uma decisão técnica, o princípio prevalece."
      />
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {ETICA.map((e, i) => (
          <article
            key={e.t}
            className="bg-[var(--surface)] border border-white/5 rounded-[var(--r-lg)] p-5"
          >
            <span
              className="inline-block font-mono text-xl mb-3 px-2 py-1 rounded"
              style={{
                background: `${ETICA_CORES[i]}18`,
                color: ETICA_CORES[i],
              }}
            >
              {String(i + 1).padStart(2, "0")}
            </span>
            <h4 className="font-medium mb-2 text-sm">{e.t}</h4>
            <p className="text-xs text-[var(--text-dim)] leading-relaxed">
              {e.d}
            </p>
          </article>
        ))}
      </div>
    </Container>
  );
}

/* ========== 9 — HARDWARE ========== */

const HARDWARE = [
  { icon: "🖥", title: "Raspberry Pi 4 ou 5", desc: "Processador ARM. Detecta o modelo e ajusta resolução/FPS.", preco: "R$ 400–700" },
  { icon: "📷", title: "Webcam USB 1080p", desc: "Qualquer webcam USB padrão compatível com OpenCV.", preco: "R$ 150–300" },
  { icon: "📺", title: "Display HDMI", desc: "TV velha ou monitor. Fonte mínima 28px — legível a 3m.", preco: "R$ 0–200" },
  { icon: "⌨", title: "Teclado numérico", desc: "Qualquer USB. Única interface que o operador usa.", preco: "R$ 30–50" },
];

export function HardwareSection() {
  return (
    <Container id="hardware">
      <SectionHead
        eyebrow="Hardware"
        title={
          <>
            R$&nbsp;600. Plug and play.
            <br />
            Funciona offline.
          </>
        }
        description="Tudo que você precisa está disponível em qualquer loja de eletrônicos."
      />
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {HARDWARE.map((h) => (
          <article
            key={h.title}
            className="bg-[var(--surface)] border border-white/5 rounded-[var(--r-lg)] p-5 hover:-translate-y-0.5 transition"
          >
            <div className="text-2xl mb-3">{h.icon}</div>
            <h4 className="font-medium mb-2 text-sm">{h.title}</h4>
            <p className="text-xs text-[var(--text-dim)] leading-relaxed mb-4">
              {h.desc}
            </p>
            <div className="font-mono text-sm text-[var(--green)]">
              {h.preco}
            </div>
          </article>
        ))}
      </div>
      <div className="flex items-baseline gap-4 mt-8 flex-wrap">
        <span className="px-4 py-2 rounded-full bg-[var(--green)] text-zinc-950 font-mono text-sm">
          Total: R$ 600–1.300
        </span>
        <span className="text-sm text-[var(--text-mute)]">
          Payback em aproximadamente 1 mês.
        </span>
      </div>

      <div className="mt-10 bg-[var(--surface)] border border-white/5 rounded-[var(--r-lg)] overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-black/30 text-xs uppercase tracking-wider text-[var(--text-mute)]">
            <tr>
              <th className="text-left p-3">Modelo</th>
              <th className="text-left p-3">Resolução</th>
              <th className="text-left p-3">FPS</th>
              <th className="text-left p-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {[
              ["Raspberry Pi 3B", "320×320", "5 FPS", "✓ Compatível", "var(--text-dim)"],
              ["Raspberry Pi 4", "416×416", "10 FPS", "✓ Recomendado", "var(--green)"],
              ["Raspberry Pi 5", "640×640", "15 FPS", "✓ Ideal", "var(--green)"],
            ].map((r, i) => (
              <tr key={i} className="border-t border-white/5">
                <td className="p-3">{r[0]}</td>
                <td className="p-3 font-mono text-xs">{r[1]}</td>
                <td className="p-3 font-mono text-xs">{r[2]}</td>
                <td className="p-3" style={{ color: r[4] }}>
                  {r[3]}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Container>
  );
}

/* ========== 10 — CONTATO ========== */

export function ContatoSection() {
  return (
    <Container id="contato">
      <SectionHead
        eyebrow="Começar"
        title={
          <>
            Pronto para reduzir
            <br />a rejeição de lote?
          </>
        }
      />

      <div className="grid md:grid-cols-2 gap-4 mb-12">
        <article
          className="border border-[var(--green)]/30 rounded-[var(--r-lg)] p-6"
          style={{
            background:
              "linear-gradient(135deg, rgba(25,226,126,0.08), var(--surface) 60%)",
          }}
        >
          <div className="w-11 h-11 rounded-lg bg-[var(--green)]/20 flex items-center justify-center text-xl mb-4">
            👥
          </div>
          <h3 className="font-medium mb-2">Sou uma cooperativa</h3>
          <p className="text-sm text-[var(--text-dim)] mb-4">
            Quero instalar o sistema e reduzir a rejeição de lote. Hardware de
            R$ 600. Payback em 1 mês.
          </p>
          <a
            href="#contact-form"
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-full bg-[var(--green)] text-zinc-950"
          >
            Entrar em contato →
          </a>
        </article>
        <article
          className="border border-[var(--blue)]/30 rounded-[var(--r-lg)] p-6"
          style={{
            background:
              "linear-gradient(135deg, rgba(59,130,246,0.08), var(--surface) 60%)",
          }}
        >
          <div className="w-11 h-11 rounded-lg bg-[var(--blue)]/20 flex items-center justify-center text-xl mb-4">
            🏭
          </div>
          <h3 className="font-medium mb-2">Sou uma indústria</h3>
          <p className="text-sm text-[var(--text-dim)] mb-4">
            Quero comprar material reciclado certificado com rastreabilidade
            ESG para meu relatório de sustentabilidade.
          </p>
          <a
            href="#contact-form"
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-full bg-[var(--blue)] text-white"
          >
            Falar sobre fornecimento →
          </a>
        </article>
      </div>

      <ContactForm />

      <div className="flex justify-center gap-6 mt-10 flex-wrap text-xs font-mono text-[var(--text-mute)]">
        <span>♻ Open source · código aberto</span>
        <span>🔒 Dados 100% locais · sem cloud</span>
        <span>⚡ Payback em ~1 mês</span>
      </div>
    </Container>
  );
}

function ContactForm() {
  return (
    <form
      id="contact-form"
      onSubmit={(e) => {
        e.preventDefault();
        const btn = e.currentTarget.querySelector("button[type=submit]");
        if (btn) {
          const orig = btn.textContent;
          btn.textContent = "Enviado ✓";
          (e.currentTarget as HTMLFormElement).reset();
          setTimeout(() => {
            if (orig) btn.textContent = orig;
          }, 2400);
        }
      }}
      className="bg-[var(--surface)] border border-white/5 rounded-[var(--r-lg)] p-6 grid md:grid-cols-2 gap-4"
    >
      <Field label="Nome" name="nome" required placeholder="Como devemos te chamar" />
      <Field label="Email" name="email" type="email" required placeholder="nome@empresa.com" />
      <Field label="Tipo" name="tipo" select>
        <option value="cooperativa">Cooperativa</option>
        <option value="industria">Indústria</option>
        <option value="investidor">Investidor</option>
        <option value="outro">Outro</option>
      </Field>
      <Field label="Telefone (opcional)" name="tel" placeholder="(11) 90000-0000" />
      <label className="md:col-span-2 block">
        <span className="text-xs text-[var(--text-mute)] block mb-1">
          Mensagem
        </span>
        <textarea
          name="msg"
          placeholder="Conte um pouco sobre o que você precisa"
          rows={4}
          className="w-full bg-[var(--bg)] border border-white/10 rounded-md p-3 text-sm resize-y focus:outline-none focus:border-[var(--green)]/50"
        />
      </label>
      <div className="md:col-span-2 flex justify-end">
        <button
          type="submit"
          className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium rounded-full bg-[var(--green)] text-zinc-950 hover:-translate-y-px transition"
        >
          Enviar mensagem →
        </button>
      </div>
    </form>
  );
}

function Field({
  label,
  name,
  type = "text",
  placeholder,
  required,
  select,
  children,
}: {
  label: string;
  name: string;
  type?: string;
  placeholder?: string;
  required?: boolean;
  select?: boolean;
  children?: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="text-xs text-[var(--text-mute)] block mb-1">{label}</span>
      {select ? (
        <select
          name={name}
          required={required}
          className="w-full bg-[var(--bg)] border border-white/10 rounded-md p-2.5 text-sm focus:outline-none focus:border-[var(--green)]/50"
        >
          {children}
        </select>
      ) : (
        <input
          name={name}
          type={type}
          required={required}
          placeholder={placeholder}
          className="w-full bg-[var(--bg)] border border-white/10 rounded-md p-2.5 text-sm focus:outline-none focus:border-[var(--green)]/50"
        />
      )}
    </label>
  );
}

/* ========== FOOTER ========== */

export function LandingFooter() {
  return (
    <footer className="border-t border-white/5 mt-20" style={{ padding: "60px 0" }}>
      <div
        className="mx-auto"
        style={{ maxWidth: "var(--max-w)", padding: "0 var(--gutter)" }}
      >
        <div className="grid md:grid-cols-[1.2fr_2fr_1fr] gap-8 pb-10">
          <div>
            <a href="#top" className="flex items-center gap-2 font-semibold mb-3">
              <span className="brand-dot inline-block w-2 h-2 rounded-full bg-[var(--green)]" />
              ReciclaIA
            </a>
            <p className="text-sm text-[var(--text-mute)]">
              Visão computacional para cooperativas de reciclagem. Open
              source. Local-first.
            </p>
          </div>
          <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-[var(--text-dim)]">
            {[
              "Problema",
              "Solução",
              "Financeiro",
              "Ética",
              "Hardware",
              "Contato",
            ].map((l) => (
              <a key={l} href={`#${l.toLowerCase()}`} className="hover:text-[var(--text)]">
                {l}
              </a>
            ))}
          </div>
          <div className="text-sm text-[var(--text-mute)] text-right">
            Projeto social com IA
            <br />
            Brasil · 2026
          </div>
        </div>
        <div className="text-xs text-[var(--text-mute)] pt-6 border-t border-white/5">
          Todos os dados ficam no Raspberry Pi da cooperativa. Nenhum dado é
          enviado para servidores externos por padrão.
        </div>
      </div>
    </footer>
  );
}
