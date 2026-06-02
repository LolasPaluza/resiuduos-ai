const COUNTERS = [
  { label: "PET", val: "47", color: "var(--c-pet)" },
  { label: "PEAD", val: "23", color: "var(--c-pead)" },
  { label: "Papel", val: "61", color: "var(--c-papel)" },
  { label: "Metal", val: "12", color: "var(--c-metal)" },
  { label: "Orgânico", val: "8", color: "var(--c-org)" },
  { label: "Rejeito", val: "4,2%", color: "var(--c-rej)" },
];

export function HeroSection() {
  return (
    <header
      id="top"
      className="relative pt-32 pb-20 lg:pt-40 lg:pb-32 overflow-hidden"
    >
      {/* Glow verde no canto */}
      <div
        className="absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full pointer-events-none"
        style={{
          background:
            "radial-gradient(circle, rgba(25,226,126,0.15) 0%, transparent 60%)",
        }}
      />

      <div
        className="relative mx-auto"
        style={{ maxWidth: "var(--max-w)", padding: "0 var(--gutter)" }}
      >
        <div className="grid lg:grid-cols-[1.15fr_1fr] gap-10 lg:gap-20 items-center">
          {/* Coluna texto */}
          <div>
            <span className="inline-block text-xs uppercase tracking-[0.14em] font-mono text-[var(--text-mute)] mb-5">
              Sistema em desenvolvimento · 2026
            </span>
            <h1
              className="font-medium leading-[1.04] mb-6"
              style={{ fontSize: "clamp(40px, 6.4vw, 84px)" }}
            >
              Câmera com IA
              <br />
              na esteira
              <br />
              que{" "}
              <span className="text-[var(--green)]">não se cansa</span>.
            </h1>
            <p className="text-base lg:text-lg text-[var(--text-dim)] leading-relaxed max-w-xl mb-8">
              O operador erra{" "}
              <span className="font-mono text-[var(--red)]">5%</span> na hora 1
              e <span className="font-mono text-[var(--red)]">22%</span> na
              hora 8. A câmera erra{" "}
              <span className="font-mono text-[var(--green)]">3%</span> o turno
              inteiro. ReciclaIA avisa em tempo real quando o material está
              indo para o bin errado — e constrói o histórico que leva a
              cooperativa ao crédito e ao mercado ESG.
            </p>
            <div className="flex flex-wrap gap-3 mb-10">
              <a
                href="#como-funciona"
                className="inline-flex items-center gap-2 px-5 py-3 text-sm font-medium rounded-full bg-[var(--green)] text-zinc-950 hover:-translate-y-px transition hover:shadow-[0_16px_40px_-16px_var(--green-glow)]"
              >
                Ver como funciona <span>→</span>
              </a>
              <a
                href="#problema"
                className="inline-flex items-center gap-2 px-5 py-3 text-sm font-medium rounded-full border border-white/10 text-[var(--text)] hover:bg-white/5 transition"
              >
                Entender o problema
              </a>
            </div>
            <div className="grid grid-cols-3 gap-4 pt-6 border-t border-white/10">
              {[
                { v: "800 mil", l: "catadores no Brasil" },
                { v: "R$ 600", l: "hardware total" },
                { v: "~1 mês", l: "payback médio" },
              ].map((s) => (
                <div key={s.v}>
                  <div className="font-mono text-xl lg:text-2xl">{s.v}</div>
                  <div className="text-xs text-[var(--text-mute)] mt-1">
                    {s.l}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Mockup do dashboard */}
          <div
            className="rounded-[var(--r-xl)] border border-white/10 overflow-hidden bg-[var(--surface)] shadow-[0_40px_80px_-40px_rgba(0,0,0,0.6)]"
            style={{
              boxShadow:
                "0 40px 80px -40px rgba(0,0,0,0.6), inset 0 0 0 1px rgba(25,226,126,0.04)",
            }}
          >
            {/* Toolbar */}
            <div className="flex items-center gap-3 px-4 py-3 border-b border-white/10 bg-black/30">
              <div className="flex gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[var(--red)]/70" />
                <span className="w-2.5 h-2.5 rounded-full bg-[var(--amber)]/70" />
                <span className="w-2.5 h-2.5 rounded-full bg-[var(--green)]/70" />
              </div>
              <span className="text-xs font-mono text-[var(--text-mute)] truncate">
                reciclaia · esteira-01 · turno T2
              </span>
              <span className="ml-auto text-xs font-mono text-[var(--green)] flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--green)] live-dot" />
                AO VIVO
              </span>
            </div>

            {/* Canvas com esteira animada e bbox */}
            <div
              className="relative aspect-[4/2.4] overflow-hidden"
              style={{
                background:
                  "linear-gradient(180deg, #0d100c 0%, #161a13 100%)",
              }}
            >
              {/* Esteira */}
              <div
                className="absolute inset-x-0 bottom-8 h-20 belt-anim"
                style={{
                  background:
                    "repeating-linear-gradient(90deg, rgba(255,255,255,0.04) 0 16px, rgba(255,255,255,0.08) 16px 32px)",
                  borderTop: "1px solid rgba(255,255,255,0.08)",
                  borderBottom: "1px solid rgba(255,255,255,0.08)",
                }}
              />
              {/* Garrafa PET (simulada) */}
              <div
                className="absolute"
                style={{ left: "42%", bottom: "30px" }}
              >
                <div
                  className="w-8 h-16 rounded-t-full rounded-b-md relative"
                  style={{
                    background:
                      "linear-gradient(180deg, rgba(107,182,255,0.2), rgba(107,182,255,0.05))",
                    border: "1px solid rgba(107,182,255,0.4)",
                  }}
                >
                  <div
                    className="absolute -top-2 left-1/2 -translate-x-1/2 w-3 h-2 rounded-sm"
                    style={{ background: "rgba(107,182,255,0.6)" }}
                  />
                </div>
              </div>
              {/* Bounding box */}
              <div
                className="absolute bbox-anim"
                style={{
                  left: "38%",
                  bottom: "20px",
                  width: "56px",
                  height: "92px",
                }}
              >
                {/* Cantos */}
                {(["tl", "tr", "bl", "br"] as const).map((c) => (
                  <span
                    key={c}
                    className="absolute w-3 h-3 border-[var(--green)]"
                    style={{
                      borderStyle: "solid",
                      ...(c.includes("t") ? { top: 0 } : { bottom: 0 }),
                      ...(c.includes("l") ? { left: 0 } : { right: 0 }),
                      borderTopWidth: c.startsWith("t") ? "2px" : 0,
                      borderBottomWidth: c.startsWith("b") ? "2px" : 0,
                      borderLeftWidth: c.endsWith("l") ? "2px" : 0,
                      borderRightWidth: c.endsWith("r") ? "2px" : 0,
                    }}
                  />
                ))}
                <span
                  className="absolute -top-7 left-0 text-xs font-mono px-2 py-1 rounded"
                  style={{
                    background: "var(--green)",
                    color: "#0a0c0a",
                  }}
                >
                  PET · 94%
                </span>
              </div>
            </div>

            {/* Contadores */}
            <div className="grid grid-cols-3 gap-px bg-white/5">
              {COUNTERS.map((c) => (
                <div
                  key={c.label}
                  className="bg-[var(--surface)] px-3 py-2.5 flex items-center justify-between"
                >
                  <span
                    className="text-[10px] uppercase tracking-wider"
                    style={{ color: c.color }}
                  >
                    {c.label}
                  </span>
                  <span className="font-mono text-sm">{c.val}</span>
                </div>
              ))}
            </div>

            {/* Footer com barra de contaminação */}
            <div className="flex items-center gap-3 px-4 py-3 border-t border-white/10 text-xs">
              <span className="text-[var(--text-mute)]">Contaminação</span>
              <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full"
                  style={{
                    width: "4.2%",
                    background: "var(--green)",
                  }}
                />
              </div>
              <span className="font-mono text-[var(--green)]">4,2% · OK</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
