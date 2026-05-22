"""Wrapper do modelo YOLOv8 para classificacao de residuos.

Carrega o modelo .pt ou .onnx (mais leve em CPU), aplica inferencia
com filtragem por confianca e retorna deteccoes estruturadas.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

from ml import CLASSES

log = logging.getLogger(__name__)


@dataclass
class Deteccao:
    """Uma deteccao no frame."""
    classe: str
    classe_id: int
    confianca: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    track_id: Optional[int] = None   # ID persistente do tracker (se disponivel)


class Modelo:
    """Carrega YOLOv8 (Ultralytics) e expoe um metodo `inferir`."""

    def __init__(
        self,
        caminho: str,
        confianca_minima: float = 0.5,
        iou_threshold: float = 0.45,
        usar_onnx: bool = False,
        caminho_onnx: Optional[str] = None,
        imgsz: int = 640,
    ) -> None:
        self.caminho = caminho
        self.confianca_minima = confianca_minima
        self.iou_threshold = iou_threshold
        self.usar_onnx = usar_onnx
        self.caminho_onnx = caminho_onnx
        self.imgsz = imgsz
        self._modelo = None
        self._classes_modelo: List[str] = []
        self._tempo_ultima_inferencia: float = 0.0

    def carregar(self) -> None:
        """Carrega os pesos do modelo (ONNX se solicitado, senao .pt)."""
        from ultralytics import YOLO

        if self.usar_onnx and self.caminho_onnx and Path(self.caminho_onnx).exists():
            log.info("Carregando modelo ONNX: %s", self.caminho_onnx)
            self._modelo = YOLO(self.caminho_onnx, task="detect")
        else:
            caminho = self.caminho
            if not Path(caminho).exists():
                # Fallback para o modelo base se nao houver fine-tune.
                base = Path(self.caminho).parent / "yolov8n.pt"
                if base.exists():
                    log.warning(
                        "Modelo fine-tuned nao encontrado em %s, usando base %s.",
                        caminho, base,
                    )
                    caminho = str(base)
                else:
                    log.warning(
                        "Nenhum modelo local encontrado. Baixando yolov8n.pt..."
                    )
                    caminho = "yolov8n.pt"
            log.info("Carregando modelo PyTorch: %s", caminho)
            self._modelo = YOLO(caminho)

        # Tenta extrair nomes de classe do proprio modelo; cai para CLASSES padrao.
        nomes = getattr(self._modelo, "names", None)
        if isinstance(nomes, dict):
            self._classes_modelo = [nomes[i] for i in sorted(nomes)]
        elif isinstance(nomes, list):
            self._classes_modelo = list(nomes)
        else:
            self._classes_modelo = list(CLASSES)
        log.info("Classes do modelo: %s", self._classes_modelo)

    def exportar_onnx(self, saida: Optional[str] = None) -> str:
        """Exporta o modelo carregado para ONNX (melhor inferencia em CPU)."""
        if self._modelo is None:
            raise RuntimeError("Modelo nao carregado antes de exportar.")
        saida_final = saida or str(Path(self.caminho).with_suffix(".onnx"))
        log.info("Exportando modelo para ONNX em %s", saida_final)
        self._modelo.export(format="onnx", imgsz=self.imgsz, opset=12)
        return saida_final

    def inferir(self, frame: np.ndarray) -> List[Deteccao]:
        """Roda inferencia + tracking sobre um frame BGR e retorna deteccoes.

        Usa o tracker ByteTrack do Ultralytics com persist=True, que mantem
        IDs estaveis entre frames consecutivos. O ID e' fundamental para o
        turno contar cada objeto fisico UMA vez, mesmo aparecendo em 30 frames.
        """
        if self._modelo is None:
            raise RuntimeError("Modelo nao carregado. Chame .carregar() antes.")
        t0 = time.time()
        # Tracker customizado: track_buffer maior para nao perder objetos
        # que somem por alguns frames (mao do operador, sobreposicao).
        cfg_tracker = Path(__file__).parent / "bytetrack_residuos.yaml"
        tracker_path = str(cfg_tracker) if cfg_tracker.exists() else "bytetrack.yaml"
        # IMPORTANTE: conf baixo aqui (0.25) deixa o tracker ver mais deteccoes
        # e fazer matching consistente. A filtragem real por confianca_minima
        # acontece DEPOIS, na contagem do turno (turno.py).
        resultados = self._modelo.track(
            source=frame,
            imgsz=self.imgsz,
            conf=0.25,
            iou=self.iou_threshold,
            persist=True,
            tracker=tracker_path,
            verbose=False,
        )
        self._tempo_ultima_inferencia = time.time() - t0

        deteccoes: List[Deteccao] = []
        if not resultados:
            return deteccoes
        r = resultados[0]
        if r.boxes is None:
            return deteccoes
        # IDs vem em r.boxes.id (pode ser None se tracker ainda nao estabilizou).
        ids = r.boxes.id
        for idx, box in enumerate(r.boxes):
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            xyxy = box.xyxy[0].tolist()
            x1, y1, x2, y2 = (int(v) for v in xyxy)
            track_id = None
            if ids is not None and idx < len(ids):
                track_id = int(ids[idx])
            nome = (
                self._classes_modelo[cls_id]
                if cls_id < len(self._classes_modelo)
                else f"classe_{cls_id}"
            )
            # Normaliza nome para nossas categorias quando possivel.
            nome_norm = self._mapear_classe(nome)
            deteccoes.append(Deteccao(
                classe=nome_norm,
                classe_id=cls_id,
                confianca=conf,
                bbox=(x1, y1, x2, y2),
                track_id=track_id,
            ))
        return deteccoes

    @staticmethod
    def _mapear_classe(nome: str) -> str:
        """Aproxima nomes do dataset base (TrashNet/TACO) para nossas 6 classes."""
        n = nome.lower()
        if "pet" in n or "plastic_bottle" in n or "bottle" in n:
            return "PET"
        if "hdpe" in n or "pead" in n or "plastic" in n:
            return "PEAD"
        if "paper" in n or "cardboard" in n or "papel" in n:
            return "papel"
        if "metal" in n or "can" in n or "alumin" in n:
            return "metal"
        if "organic" in n or "food" in n or "organico" in n:
            return "organico"
        if nome in CLASSES:
            return nome
        return "rejeito"

    @property
    def tempo_ultima_inferencia(self) -> float:
        return self._tempo_ultima_inferencia
