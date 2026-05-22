"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", label: "Dashboard", icon: "▦" },
  { href: "/turno", label: "Turno ao vivo", icon: "▶" },
  { href: "/historico", label: "Histórico", icon: "≡" },
  { href: "/certificados", label: "Certificados ESG", icon: "✓" },
  { href: "/cotacao", label: "Cotação", icon: "R$" },
  { href: "/configuracao", label: "Configuração", icon: "⚙" },
];

export function Sidebar() {
  const path = usePathname();
  return (
    <aside className="hidden md:flex md:flex-col md:w-64 bg-zinc-900 text-zinc-100 border-r border-zinc-800 min-h-screen">
      <div className="px-6 py-6 border-b border-zinc-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-700 flex items-center justify-center font-bold text-lg">
            ♻
          </div>
          <div>
            <div className="font-bold leading-tight">Resíduos AI</div>
            <div className="text-xs text-zinc-400">Cooperativa</div>
          </div>
        </div>
      </div>
      <nav className="flex-1 py-4">
        {NAV.map((item) => {
          const active =
            item.href === "/" ? path === "/" : path.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-6 py-3 text-sm transition-colors ${
                active
                  ? "bg-emerald-950 text-emerald-300 border-l-2 border-emerald-500"
                  : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100 border-l-2 border-transparent"
              }`}
            >
              <span className="text-base w-5 text-center">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="px-6 py-4 text-xs text-zinc-500 border-t border-zinc-800">
        v1.0 · open source
      </div>
    </aside>
  );
}
