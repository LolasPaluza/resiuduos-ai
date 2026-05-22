"""Alertas sonoros e visuais para o operador.

Acessibilidade (P6): cada classe tem uma FREQUENCIA distinta de beep,
nao apenas volume diferente. Operador identifica a categoria pelo som.

Mensagens (P1): nunca dizem "operador errou". Sao neutras, sobre o LOTE.
"""
from __future__ import annotations

import logging
import platform
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Dict, Optional

log = logging.getLogger(__name__)


# Frequencias distintas por classe (Hz). Tons graves = orgânico/papel;
# agudos = metal; mais alto e duplo = rejeito (mais urgente).
FREQUENCIAS_HZ: Dict[str, tuple[int, int]] = {
    "PET":      (800, 150),
    "PEAD":     (900, 150),
    "papel":    (500, 150),
    "metal":    (1400, 150),
    "organico": (400, 150),
    "rejeito":  (1200, 250),  # mais longo e medio-agudo
}


class GerenciadorAlertas:
    """Beeps distintos por categoria, com throttle anti-spam."""

    def __init__(self, intervalo_minimo_seg: float = 1.5,
                 caminho_som: Optional[str] = None) -> None:
        self.intervalo = intervalo_minimo_seg
        self.caminho_som = caminho_som
        self._ultimo_por_classe: Dict[str, float] = {}
        self._lock = threading.Lock()

    def alertar_classe(self, classe: str) -> None:
        """Beep distinto por classe. Rejeito sempre toca; outras com throttle."""
        agora = time.time()
        with self._lock:
            ultimo = self._ultimo_por_classe.get(classe, 0.0)
            # Rejeito tem intervalo menor (mais urgente).
            intervalo = self.intervalo if classe != "rejeito" else 1.0
            if agora - ultimo < intervalo:
                return
            self._ultimo_por_classe[classe] = agora
        freq, dur = FREQUENCIAS_HZ.get(classe, (1000, 150))
        threading.Thread(
            target=self._beep, args=(freq, dur), daemon=True,
        ).start()

    def alertar_rejeito(self) -> None:
        """Atalho retrocompativel — equivalente a alertar_classe('rejeito')."""
        self.alertar_classe("rejeito")

    def _beep(self, freq: int, duracao_ms: int) -> None:
        try:
            if self.caminho_som and Path(self.caminho_som).exists():
                self._tocar_arquivo(self.caminho_som)
                return
            sistema = platform.system()
            if sistema == "Windows":
                import winsound  # type: ignore
                winsound.Beep(freq, duracao_ms)
            elif sistema == "Linux":
                # Tenta `beep` real; se nao tiver, usa speaker-test em BG; senao bell.
                if self._comando_existe("beep"):
                    subprocess.Popen(
                        ["beep", "-f", str(freq), "-l", str(duracao_ms)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    )
                else:
                    sys.stdout.write("\a")
                    sys.stdout.flush()
            else:
                sys.stdout.write("\a")
                sys.stdout.flush()
        except Exception as e:
            log.debug("Falha no beep: %s", e)

    @staticmethod
    def _comando_existe(nome: str) -> bool:
        from shutil import which
        return which(nome) is not None

    @staticmethod
    def _tocar_arquivo(caminho: str) -> None:
        sistema = platform.system()
        try:
            if sistema == "Linux":
                subprocess.Popen(
                    ["aplay", "-q", caminho],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            elif sistema == "Darwin":
                subprocess.Popen(["afplay", caminho])
            elif sistema == "Windows":
                import winsound  # type: ignore
                winsound.PlaySound(caminho, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception as e:
            log.debug("Falha ao tocar arquivo de som: %s", e)
