"""Coleta de metricas de saude do hardware para o endpoint /health.

Funciona em qualquer Linux (Pi 3/4/5 ou PC). Em Windows so retorna o que
da pra ler. Tudo opcional — falha individual nao quebra o endpoint.
"""
from __future__ import annotations

import logging
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

log = logging.getLogger(__name__)

_INICIO = time.time()


def temperatura_cpu() -> Optional[float]:
    """Temperatura da CPU em graus Celsius. Pi expoe via thermal_zone."""
    try:
        f = Path("/sys/class/thermal/thermal_zone0/temp")
        if f.exists():
            return round(int(f.read_text().strip()) / 1000.0, 1)
    except Exception:
        pass
    return None


def cpu_pct() -> Optional[float]:
    """Uso geral de CPU (0-100). Usa psutil se disponivel."""
    try:
        import psutil
        return round(psutil.cpu_percent(interval=0.5), 1)
    except Exception:
        return None


def memoria_pct() -> Optional[Dict[str, float]]:
    """Uso de RAM."""
    try:
        import psutil
        m = psutil.virtual_memory()
        return {
            "total_mb": round(m.total / (1024 * 1024)),
            "usado_mb": round(m.used / (1024 * 1024)),
            "pct": round(m.percent, 1),
        }
    except Exception:
        return None


def disco_dados(pasta_dados: Path) -> Optional[Dict[str, float]]:
    """Espaco livre na particao onde ficam os dados (frames, modelos, etc)."""
    try:
        total, usado, livre = shutil.disk_usage(pasta_dados)
        pct = round(100 * usado / total, 1) if total else 0
        return {
            "total_gb": round(total / (1024**3), 1),
            "livre_gb": round(livre / (1024**3), 1),
            "pct_usado": pct,
            "alerta": pct > 90,
        }
    except Exception:
        return None


def uptime_seg() -> int:
    """Quanto tempo o main.py esta rodando."""
    return int(time.time() - _INICIO)


def uptime_pi_seg() -> Optional[int]:
    """Quanto tempo o Pi esta ligado."""
    try:
        f = Path("/proc/uptime")
        if f.exists():
            return int(float(f.read_text().split()[0]))
    except Exception:
        pass
    return None


def coletar(pasta_dados: Path) -> Dict:
    """Snapshot completo de saude pra endpoint /health."""
    temp = temperatura_cpu()
    disco = disco_dados(pasta_dados)
    alerta_temp = temp is not None and temp > 75.0
    alerta_disco = bool(disco and disco.get("alerta"))
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "uptime_processo_seg": uptime_seg(),
        "uptime_pi_seg": uptime_pi_seg(),
        "cpu": {
            "pct": cpu_pct(),
            "temperatura_c": temp,
            "alerta_temperatura": alerta_temp,
        },
        "memoria": memoria_pct(),
        "disco": disco,
        "alertas": [
            *(["temperatura_alta"] if alerta_temp else []),
            *(["disco_quase_cheio"] if alerta_disco else []),
        ],
    }
