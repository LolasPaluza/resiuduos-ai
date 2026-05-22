"""Apaga TODOS os dados da cooperativa, com confirmacao explicita.

Uso:
    python -m ferramentas.deletar_meus_dados
    python -m ferramentas.deletar_meus_dados --so-frames
    python -m ferramentas.deletar_meus_dados --so-relatorios

O modelo treinado e o config NAO sao apagados (operam o sistema).
Para apagar tambem o modelo, use --com-modelo.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def confirmar(pergunta: str, esperado: str) -> bool:
    print(pergunta)
    print(f'Para confirmar, digite exatamente: {esperado}')
    resp = input("> ").strip()
    return resp == esperado


def apagar_pasta(p: Path) -> int:
    """Apaga conteudo da pasta (mantem a pasta). Retorna n. de arquivos."""
    if not p.exists():
        return 0
    n = 0
    for filho in p.iterdir():
        try:
            if filho.is_file() or filho.is_symlink():
                filho.unlink()
                n += 1
            elif filho.is_dir():
                shutil.rmtree(filho)
                n += 1
        except OSError:
            continue
    return n


def principal():
    parser = argparse.ArgumentParser(
        description="Apaga dados da cooperativa (relatorios, frames, logs).",
    )
    parser.add_argument("--so-frames", action="store_true",
                        help="Apaga somente as imagens coletadas.")
    parser.add_argument("--so-relatorios", action="store_true",
                        help="Apaga somente os relatorios.")
    parser.add_argument("--com-modelo", action="store_true",
                        help="Apaga TAMBEM o modelo treinado.")
    parser.add_argument("--sem-confirmacao", action="store_true",
                        help="Pula a confirmacao interativa (use com cuidado).")
    parser.add_argument("--raiz", type=Path, default=Path("."))
    args = parser.parse_args()

    raiz = args.raiz.resolve()
    frames = raiz / "dados" / "frames"
    relatorios = raiz / "dados" / "relatorios"
    logs = raiz / "dados" / "logs"
    modelos = raiz / "dados" / "modelos"

    alvos = []
    if args.so_frames:
        alvos = [("imagens da esteira", frames)]
    elif args.so_relatorios:
        alvos = [("relatorios de turno", relatorios)]
    else:
        alvos = [
            ("imagens da esteira", frames),
            ("relatorios de turno", relatorios),
            ("logs do sistema", logs),
        ]
        if args.com_modelo:
            alvos.append(("modelo de IA treinado", modelos))

    print("=" * 60)
    print("APAGAR DADOS DA COOPERATIVA")
    print("=" * 60)
    print()
    print("As seguintes pastas serao APAGADAS PERMANENTEMENTE:")
    for nome, p in alvos:
        existe = "(existe)" if p.exists() else "(vazia)"
        print(f"  - {nome}: {p}  {existe}")
    print()
    print("DICA: antes de apagar, exporte uma copia com:")
    print("    python -m ferramentas.exportar_meus_dados")
    print()

    if not args.sem_confirmacao:
        if not confirmar(
            "Tem certeza? Esta acao NAO pode ser desfeita.",
            esperado="APAGAR TUDO",
        ):
            print("Cancelado. Nada foi apagado.")
            sys.exit(0)

    total = 0
    for nome, p in alvos:
        n = apagar_pasta(p)
        print(f"  - {nome}: {n} item(ns) apagado(s).")
        total += n

    print()
    print(f"Concluido. Total: {total} item(ns) apagado(s).")


if __name__ == "__main__":
    principal()
