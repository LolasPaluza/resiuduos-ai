"""Backup automatico de dados criticos para pendrive USB externo.

Procura pendrive em /media/<usuario>/<rotulo>/ ou /mnt/usb/. Se nao houver,
loga aviso e termina. Copia incremental — so leva o que e novo.

Uso (cron diario as 23h):
    0 23 * * * /home/lorenzo/projetos/residuos-ai/.venv/bin/python \
               -m ferramentas.backup
"""
from __future__ import annotations

import argparse
import logging
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional

log = logging.getLogger(__name__)


def achar_pendrives() -> List[Path]:
    """Procura pontos de montagem de pendrives no Linux."""
    candidatos: List[Path] = []
    # /media/<user>/<label>/
    media = Path("/media")
    if media.exists():
        for u in media.iterdir():
            if u.is_dir():
                for d in u.iterdir():
                    if d.is_mount() or any(d.iterdir()):
                        candidatos.append(d)
    # /mnt/usb/
    mnt = Path("/mnt/usb")
    if mnt.exists() and (mnt.is_mount() or any(mnt.iterdir())):
        candidatos.append(mnt)
    # /run/media/<user>/<label>/
    run_media = Path("/run/media")
    if run_media.exists():
        for u in run_media.iterdir():
            for d in u.iterdir():
                if d.is_dir():
                    candidatos.append(d)
    return [c for c in candidatos if c.exists() and os.access(c, os.W_OK)]


def copiar_incremental(origem: Path, destino: Path) -> int:
    """Copia arquivos novos. Pula os que ja existem com mesmo tamanho."""
    if not origem.exists():
        return 0
    destino.mkdir(parents=True, exist_ok=True)
    copiados = 0
    for arq in origem.rglob("*"):
        if not arq.is_file():
            continue
        rel = arq.relative_to(origem)
        dst = destino / rel
        # Pula se ja existe com mesmo tamanho
        if dst.exists() and dst.stat().st_size == arq.stat().st_size:
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(arq, dst)
        copiados += 1
    return copiados


def fazer_backup(pasta_dados: Path, pendrive: Optional[Path] = None) -> dict:
    """Faz backup pra um pendrive especifico ou o primeiro encontrado."""
    if pendrive is None:
        candidatos = achar_pendrives()
        if not candidatos:
            log.warning("Nenhum pendrive USB encontrado. Backup pulado.")
            return {"ok": False, "motivo": "nenhum_pendrive"}
        pendrive = candidatos[0]
        log.info("Pendrive detectado em %s", pendrive)

    data = datetime.now().strftime("%Y-%m-%d")
    destino_raiz = pendrive / "residuos-ai-backup" / data

    sub_relatorios = pasta_dados / "relatorios"
    sub_certificados = pasta_dados / "certificados"
    sub_db = pasta_dados / "db"

    n_relatorios = copiar_incremental(sub_relatorios, destino_raiz / "relatorios")
    n_certificados = copiar_incremental(sub_certificados, destino_raiz / "certificados")
    n_db = copiar_incremental(sub_db, destino_raiz / "db")

    # Cria um manifesto legivel
    manifesto = destino_raiz / "MANIFESTO.txt"
    manifesto.write_text(
        f"Backup ReciclaIA — {datetime.now().isoformat(timespec='seconds')}\n"
        f"================================\n"
        f"Relatorios copiados:   {n_relatorios}\n"
        f"Certificados copiados: {n_certificados}\n"
        f"DB copiados:           {n_db}\n"
        f"\n"
        f"Para restaurar: copie esta pasta de volta pra ~/projetos/residuos-ai/dados/\n",
        encoding="utf-8",
    )

    total = n_relatorios + n_certificados + n_db
    log.info(
        "Backup OK: %d arquivos novos em %s "
        "(relatorios=%d, certificados=%d, db=%d)",
        total, destino_raiz, n_relatorios, n_certificados, n_db,
    )
    return {
        "ok": True,
        "destino": str(destino_raiz),
        "total": total,
        "relatorios": n_relatorios,
        "certificados": n_certificados,
        "db": n_db,
    }


def principal():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pasta-dados", type=Path, default=Path("dados"))
    parser.add_argument("--pendrive", type=Path,
                        help="Forca um pendrive especifico (default: descoberta automatica)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s: %(message)s")
    r = fazer_backup(args.pasta_dados, args.pendrive)
    if not r["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    principal()
