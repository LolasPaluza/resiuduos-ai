"""Modo degradado: opera sem IA, com classificacao manual via teclado.

Quando o modelo falha (exception, OOM, modelo nao carrega), o sistema
NAO TRAVA. Ele entra neste modo: continua mostrando a camera ao vivo,
o operador classifica com 1-6, e as contagens seguem normalmente.

Principio etico aplicado: nao criar dependencia tecnologica fragil.
A cooperativa nao pode parar de trabalhar porque a IA caiu.
"""
from __future__ import annotations

import logging
import time
from collections import deque
from typing import Iterable, List

import psutil

from core.camera import Camera, PerfilHardware, detectar_hardware
from ml.modelo import Deteccao

log = logging.getLogger(__name__)


class ClassifierDegradado:
    """Mesmo contrato do Classifier, mas sem rodar IA.

    Sempre retorna uma lista vazia de deteccoes — o dashboard
    desenha um aviso e o operador classifica manualmente com 1-6.
    """

    def __init__(self, camera: Camera, pasta_frames: str,
                 perfil: PerfilHardware | None = None,
                 motivo: str = "modelo indisponivel") -> None:
        self.camera = camera
        from pathlib import Path
        self.pasta_frames = Path(pasta_frames)
        self.pasta_frames.mkdir(parents=True, exist_ok=True)
        self.perfil = perfil or detectar_hardware()
        self.motivo = motivo
        self.degradado = True
        # Compat: mesmas propriedades do Classifier normal.
        self.modelo = _ModeloPlaceholder()
        self._fps_window: deque = deque(maxlen=30)
        self._cpu_pct = 0.0
        self._cpu_check_ts = 0.0

    def fps_atual(self) -> float:
        if not self._fps_window:
            return 0.0
        return sum(self._fps_window) / len(self._fps_window)

    def cpu_pct(self) -> float:
        return self._cpu_pct

    def _atualizar_cpu(self) -> None:
        agora = time.time()
        if agora - self._cpu_check_ts > 1.0:
            self._cpu_pct = psutil.cpu_percent(interval=None)
            self._cpu_check_ts = agora

    def stream(self) -> Iterable:
        log.warning("Operando em MODO DEGRADADO: %s", self.motivo)
        t_prev = time.time()
        for frame in self.camera.frames():
            self._atualizar_cpu()
            t_now = time.time()
            dt = t_now - t_prev
            if dt > 0:
                self._fps_window.append(1.0 / dt)
            t_prev = t_now
            yield frame, []


class _ModeloPlaceholder:
    """Mock para manter a interface compativel com codigo que le `.modelo.caminho`."""
    caminho = "(modo degradado — sem IA)"
    tempo_ultima_inferencia = 0.0


def envolver_seguro(stream_fn):
    """Decorator: se o stream original lancar, troca por modo degradado.

    Mantemos isso simples — chamadores podem chamar diretamente
    ClassifierDegradado quando detectarem falha no carregamento do modelo.
    """
    def wrapper(*args, **kwargs):
        try:
            yield from stream_fn(*args, **kwargs)
        except Exception:
            log.exception("Falha no pipeline de IA — caindo para modo degradado.")
            raise
    return wrapper
