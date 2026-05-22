"""Integra camera + modelo: pipeline completo de classificacao em tempo real.

Aplica frame-skipping quando CPU > 80% e mantem media movel de FPS.
Salva frames para retreinamento (todos ou apenas baixa confianca).
"""
from __future__ import annotations

import logging
import time
import uuid
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

import cv2
import psutil

from core.camera import Camera, PerfilHardware, detectar_hardware
from ml.modelo import Deteccao, Modelo

log = logging.getLogger(__name__)


class Classifier:
    """Orquestra captura -> inferencia -> persistencia para retreinamento."""

    def __init__(
        self,
        camera: Camera,
        modelo: Modelo,
        pasta_frames: str,
        salvar_todos: bool = False,
        salvar_baixa_confianca: bool = True,
        limite_baixa_confianca: float = 0.65,
        perfil: Optional[PerfilHardware] = None,
    ) -> None:
        self.camera = camera
        self.modelo = modelo
        self.pasta_frames = Path(pasta_frames)
        self.pasta_frames.mkdir(parents=True, exist_ok=True)
        self.salvar_todos = salvar_todos
        self.salvar_baixa_confianca = salvar_baixa_confianca
        self.limite_baixa_confianca = limite_baixa_confianca
        self.perfil = perfil or detectar_hardware()

        self._fps_window: deque = deque(maxlen=30)
        self._frame_skip = 0
        self._cpu_check_ts = 0.0
        self._cpu_pct = 0.0

    def fps_atual(self) -> float:
        """Media movel do FPS efetivo."""
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
            # Frame skip dinamico: a cada 80%+ CPU pula 1 frame extra.
            if self._cpu_pct > 80:
                self._frame_skip = min(self._frame_skip + 1, 3)
            elif self._cpu_pct < 60 and self._frame_skip > 0:
                self._frame_skip = max(self._frame_skip - 1, 0)

    def _salvar_frame_se_preciso(
        self, frame, deteccoes: List[Deteccao]
    ) -> Optional[Path]:
        if not deteccoes:
            return None
        baixa_conf = any(d.confianca < self.limite_baixa_confianca for d in deteccoes)
        if not (self.salvar_todos or (self.salvar_baixa_confianca and baixa_conf)):
            return None
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        uid = uuid.uuid4().hex[:6]
        nome = f"{ts}_{uid}.jpg"
        caminho = self.pasta_frames / nome
        cv2.imwrite(str(caminho), frame)
        # Salva tambem o label em formato YOLO (normalizado).
        h, w = frame.shape[:2]
        label_path = caminho.with_suffix(".txt")
        with label_path.open("w", encoding="utf-8") as f:
            for d in deteccoes:
                x1, y1, x2, y2 = d.bbox
                cx = ((x1 + x2) / 2) / w
                cy = ((y1 + y2) / 2) / h
                bw = (x2 - x1) / w
                bh = (y2 - y1) / h
                f.write(f"{d.classe_id} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}\n")
        return caminho

    def stream(self) -> Iterable:
        """Gera tuplas (frame, deteccoes) para o dashboard consumir."""
        log.info("Iniciando classificador. Hardware: %s", self.perfil.nome)
        contador = 0
        for frame in self.camera.frames():
            self._atualizar_cpu()
            contador += 1
            if self._frame_skip > 0 and (contador % (self._frame_skip + 1) != 0):
                # Skip: ainda passa o frame pro dashboard, sem deteccoes novas.
                yield frame, []
                continue

            t0 = time.time()
            try:
                deteccoes = self.modelo.inferir(frame)
            except Exception:
                # Principio etico: o sistema nao pode travar a cooperativa.
                # Falhas pontuais da IA sao toleradas; sucessivas viram modo degradado
                # (tratado em main.py com fallback global).
                log.exception("Falha na inferencia; frame ignorado.")
                deteccoes = []
            dt = time.time() - t0
            if dt > 0:
                self._fps_window.append(1.0 / dt)
            self._salvar_frame_se_preciso(frame, deteccoes)
            yield frame, deteccoes
