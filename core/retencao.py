"""Retencao automatica de dados — apaga arquivos antigos.

Principio etico (P2): a cooperativa controla seus dados, e o sistema
nao acumula imagens indefinidamente. A retencao e configuravel em
config.yaml > privacidade.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

log = logging.getLogger(__name__)


def aplicar_retencao(
    pasta_frames: Path, pasta_relatorios: Path,
    dias_frames: int = 30, dias_relatorios: int = 365,
) -> dict:
    """Apaga arquivos mais velhos que N dias. Retorna {removidos_frames, removidos_relatorios}."""
    removidos = {"frames": 0, "relatorios": 0}
    agora = time.time()

    if dias_frames > 0 and pasta_frames.exists():
        limite = agora - dias_frames * 86400
        for p in list(pasta_frames.glob("*")):
            if not p.is_file():
                continue
            try:
                if p.stat().st_mtime < limite:
                    p.unlink()
                    removidos["frames"] += 1
            except OSError:
                continue

    if dias_relatorios > 0 and pasta_relatorios.exists():
        limite = agora - dias_relatorios * 86400
        for p in list(pasta_relatorios.glob("relatorio_*")):
            try:
                if p.stat().st_mtime < limite:
                    p.unlink()
                    removidos["relatorios"] += 1
            except OSError:
                continue

    if removidos["frames"] or removidos["relatorios"]:
        log.info("Retencao aplicada: %s", removidos)
    return removidos
