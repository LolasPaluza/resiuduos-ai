"""Captura e gerenciamento da webcam USB via OpenCV.

Reconecta automaticamente se a camera cair e detecta o hardware
(Raspberry Pi 3/4/5 ou PC comum) para ajustar resolucao e FPS.
"""
from __future__ import annotations

import logging
import platform
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

log = logging.getLogger(__name__)


@dataclass
class PerfilHardware:
    """Perfil de performance ajustado ao hardware detectado."""
    nome: str
    resolucao_inferencia: int  # lado do quadrado para o modelo
    fps_max: int


def detectar_hardware() -> PerfilHardware:
    """Detecta se esta rodando em Raspberry Pi e retorna perfil adequado."""
    modelo_path = Path("/proc/device-tree/model")
    if modelo_path.exists():
        try:
            modelo = modelo_path.read_text(errors="ignore").strip("\x00").strip()
        except OSError:
            modelo = ""
        if "Raspberry Pi 5" in modelo:
            return PerfilHardware("Raspberry Pi 5", 640, 15)
        if "Raspberry Pi 4" in modelo:
            return PerfilHardware("Raspberry Pi 4", 416, 10)
        if "Raspberry Pi 3" in modelo:
            return PerfilHardware("Raspberry Pi 3B", 320, 5)
        if "Raspberry Pi" in modelo:
            return PerfilHardware(modelo, 416, 8)
    return PerfilHardware(f"PC/{platform.machine()}", 640, 30)


class Camera:
    """Wrapper sobre cv2.VideoCapture com reconexao automatica.

    Uso:
        with Camera(indice=0, resolucao=(640, 480)) as cam:
            for frame in cam.frames():
                processar(frame)
    """

    def __init__(
        self,
        indice: int = 0,
        resolucao: Tuple[int, int] = (640, 480),
        fps_alvo: int = 10,
        tentativas_reconexao: int = 5,
    ) -> None:
        self.indice = indice
        self.resolucao = resolucao
        self.fps_alvo = max(1, fps_alvo)
        self.tentativas_reconexao = tentativas_reconexao
        self._cap: Optional[cv2.VideoCapture] = None
        self._intervalo_frame = 1.0 / self.fps_alvo
        self._ultimo_frame_ts = 0.0

    def abrir(self) -> None:
        """Abre a webcam e configura resolucao e FPS desejados."""
        self._cap = cv2.VideoCapture(self.indice, cv2.CAP_ANY)
        if not self._cap.isOpened():
            raise RuntimeError(
                f"Nao foi possivel abrir a camera no indice {self.indice}. "
                "Verifique se a webcam esta conectada."
            )
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolucao[0])
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolucao[1])
        self._cap.set(cv2.CAP_PROP_FPS, self.fps_alvo)
        log.info(
            "Camera aberta: indice=%s resolucao=%sx%s fps=%s",
            self.indice, self.resolucao[0], self.resolucao[1], self.fps_alvo,
        )

    def fechar(self) -> None:
        """Libera o recurso da camera."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def __enter__(self) -> "Camera":
        self.abrir()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.fechar()

    def _reconectar(self) -> bool:
        """Tenta reabrir a camera apos uma queda."""
        log.warning("Tentando reconectar camera...")
        self.fechar()
        for tentativa in range(1, self.tentativas_reconexao + 1):
            try:
                self.abrir()
                log.info("Camera reconectada na tentativa %s.", tentativa)
                return True
            except RuntimeError:
                log.warning("Tentativa %s falhou.", tentativa)
                time.sleep(min(2 ** tentativa, 10))
        log.error("Nao foi possivel reconectar a camera.")
        return False

    def ler_frame(self) -> Optional[np.ndarray]:
        """Le um unico frame, respeitando o FPS alvo. Reconecta em falha."""
        agora = time.time()
        delta = agora - self._ultimo_frame_ts
        if delta < self._intervalo_frame:
            time.sleep(self._intervalo_frame - delta)

        if self._cap is None or not self._cap.isOpened():
            if not self._reconectar():
                return None

        assert self._cap is not None
        ok, frame = self._cap.read()
        self._ultimo_frame_ts = time.time()
        if not ok or frame is None:
            log.warning("Falha ao ler frame, tentando reconectar...")
            if not self._reconectar():
                return None
            ok, frame = self._cap.read()
            if not ok:
                return None
        return frame

    def frames(self):
        """Gerador infinito de frames. Encerra apenas se a camera nao reconectar."""
        while True:
            frame = self.ler_frame()
            if frame is None:
                log.error("Camera indisponivel, encerrando gerador.")
                break
            yield frame


class CameraVideo(Camera):
    """Substitui webcam por um video pre-gravado (modo --demo)."""

    def __init__(self, caminho_video: str, fps_alvo: int = 10) -> None:
        super().__init__(indice=0, fps_alvo=fps_alvo)
        self.caminho_video = caminho_video

    def abrir(self) -> None:
        self._cap = cv2.VideoCapture(self.caminho_video)
        if not self._cap.isOpened():
            raise RuntimeError(f"Nao foi possivel abrir video: {self.caminho_video}")
        log.info("Video de demonstracao aberto: %s", self.caminho_video)

    def _reconectar(self) -> bool:
        # No modo demo, ao acabar o video, reinicia do comeco.
        if self._cap is not None:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return True
        return False
