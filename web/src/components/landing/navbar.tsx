"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const LINKS = [
  { href: "#problema", label: "Problema" },
  { href: "#solucao", label: "Solução" },
  { href: "#como-funciona", label: "Como funciona" },
  { href: "#financeiro", label: "Financeiro" },
  { href: "#industria", label: "Indústria" },
  { href: "#contato", label: "Contato" },
];

export function LandingNavbar() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 14);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <>
      <nav
        className={`fixed top-0 inset-x-0 z-50 transition-all ${
          scrolled
            ? "bg-[rgba(10,12,10,0.7)] backdrop-blur-lg border-b border-white/5 py-3"
            : "py-4"
        }`}
        aria-label="Navegação principal"
      >
        <div
          className="mx-auto flex items-center justify-between"
          style={{ maxWidth: "var(--max-w)", padding: "0 var(--gutter)" }}
        >
          <Link href="#top" className="flex items-center gap-2 font-semibold">
            <span className="brand-dot inline-block w-2 h-2 rounded-full bg-[var(--green)]" />
            <span>ReciclaIA</span>
          </Link>

          <div className="hidden lg:flex items-center gap-1">
            {LINKS.map((l) => (
              <a
                key={l.href}
                href={l.href}
                className="px-3 py-2 text-sm text-[var(--text-dim)] rounded-full hover:bg-white/5 hover:text-[var(--text)] transition"
              >
                {l.label}
              </a>
            ))}
          </div>

          <div className="hidden lg:flex items-center gap-3">
            <Link
              href="/painel"
              className="px-4 py-2 text-sm text-[var(--text-dim)] hover:text-[var(--text)] transition"
            >
              Painel da cooperativa →
            </Link>
            <a
              href="#contato"
              className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-full bg-[var(--green)] text-zinc-950 hover:-translate-y-px transition hover:shadow-[0_16px_40px_-16px_var(--green-glow)]"
            >
              Começar agora <span>→</span>
            </a>
          </div>

          <button
            className="lg:hidden p-2 text-zinc-300"
            onClick={() => setOpen((v) => !v)}
            aria-label="Menu"
          >
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
              <path d={open ? "M6 6l12 12M6 18L18 6" : "M4 6h16M4 12h16M4 18h16"} />
            </svg>
          </button>
        </div>
      </nav>

      {/* Drawer mobile */}
      {open && (
        <div className="lg:hidden fixed inset-x-0 top-14 z-40 bg-[rgba(10,12,10,0.95)] backdrop-blur-lg border-b border-white/5 p-4 space-y-2">
          {LINKS.map((l) => (
            <a
              key={l.href}
              href={l.href}
              onClick={() => setOpen(false)}
              className="block px-3 py-2 text-sm text-[var(--text-dim)] hover:bg-white/5 rounded"
            >
              {l.label}
            </a>
          ))}
          <Link
            href="/painel"
            className="block px-3 py-2 text-sm text-[var(--green)]"
          >
            Painel →
          </Link>
        </div>
      )}
    </>
  );
}
