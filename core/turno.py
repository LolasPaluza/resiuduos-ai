"""Logica de turno: contagem por classe, persistencia, historico.

Salva estado a cada N minutos para sobreviver a quedas de energia.

Principio etico: este modulo agrega SOMENTE por turno e por categoria.
Nao existe campo de identificacao de operador, ID de catador, ou
qualquer rastro que permita atribuir um erro a uma pessoa especifica.
O sistema mede o LOTE, nunca a pessoa.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Deque, Dict, List, Optional, Tuple

from ml import CLASSES


def _iou(a: Tuple[int, int, int, int], b: Tuple[int, int, int, int]) -> float:
    """Intersection-over-Union entre duas bboxes (x1,y1,x2,y2)."""
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
    inter = iw * ih
    if inter == 0:
        return 0.0
    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0

log = logging.getLogger(__name__)


@dataclass
class Turno:
    """Estado de um turno em andamento."""
    id: str
    inicio: str
    fim: Optional[str] = None
    contagens: Dict[str, int] = field(default_factory=lambda: {c: 0 for c in CLASSES})
    # Para detectar horarios de pico de rejeito: lista de (timestamp, classe).
    eventos_rejeito: List[str] = field(default_factory=list)
    total_frames: int = 0
    total_deteccoes: int = 0
    # IDs do tracker ja contados (evita contar o mesmo objeto fisico
    # multiplas vezes quando aparece em frames consecutivos).
    track_ids_vistos: List[int] = field(default_factory=list)


class GerenciadorTurno:
    """Mantem turno atual, persiste e calcula metricas."""

    def __init__(
        self,
        pasta_estado: str,
        intervalo_salvar_seg: int = 300,
        alerta_contaminacao_pct: float = 10.0,
        pesos_kg: Optional[Dict[str, float]] = None,
        limite_incerto: float = 0.50,
    ) -> None:
        self.pasta_estado = Path(pasta_estado)
        self.pasta_estado.mkdir(parents=True, exist_ok=True)
        self.intervalo_salvar = intervalo_salvar_seg
        self.alerta_contaminacao_pct = alerta_contaminacao_pct
        self.pesos_kg = pesos_kg or {c: 0.1 for c in CLASSES}
        # Deteccoes abaixo deste limite NAO sao contadas automaticamente.
        # O operador precisa confirmar manualmente (transparencia do modelo).
        self.limite_incerto = limite_incerto
        # Dedup robusto: lista de (classe, bbox, timestamp) das ultimas
        # deteccoes contabilizadas. Se uma nova deteccao tem IOU >= limiar
        # com objeto da MESMA classe vista nos ultimos N segundos, NAO conta.
        # Isso evita contar a mesma garrafa 30 vezes quando o tracker falha.
        self._dedup_recentes: Deque[Tuple[str, Tuple[int,int,int,int], float]] = deque(maxlen=200)
        self._dedup_janela_seg: float = 3.0   # janela de comparacao
        self._dedup_iou_min: float = 0.30     # IOU minimo para considerar mesmo objeto
        self._turno: Optional[Turno] = None
        self._lock = threading.Lock()
        self._thread_save: Optional[threading.Thread] = None
        self._parar = threading.Event()
        self._restaurar_se_existir()

    # ----- ciclo de vida -----

    def iniciar(self) -> Turno:
        with self._lock:
            self._turno = Turno(
                id=datetime.now().strftime("%Y%m%d_%H%M%S"),
                inicio=datetime.now().isoformat(timespec="seconds"),
            )
            self._salvar()
        self._iniciar_autosave()
        log.info("Turno iniciado: %s", self._turno.id)
        return self._turno

    def encerrar(self) -> Turno:
        with self._lock:
            if self._turno is None:
                raise RuntimeError("Nenhum turno em andamento.")
            self._turno.fim = datetime.now().isoformat(timespec="seconds")
            self._salvar()
            turno_finalizado = self._turno
            # Move arquivo "atual" para arquivo final.
            atual = self.pasta_estado / "turno_atual.json"
            final = self.pasta_estado / f"turno_{turno_finalizado.id}.json"
            if atual.exists():
                atual.replace(final)
            self._turno = None
        self._parar.set()
        log.info("Turno encerrado: %s", turno_finalizado.id)
        return turno_finalizado

    def turno_atual(self) -> Optional[Turno]:
        return self._turno

    # ----- atualizacao -----

    def registrar(self, deteccoes) -> None:
        """Atualiza contagens com deteccoes de um frame.

        Dois niveis de dedup para evitar contar o mesmo objeto fisico 2x:
        1. Por track_id (do tracker ByteTrack) — rapido quando funciona.
        2. Por IOU + classe + janela temporal — robusto a falhas do tracker.

        Conta apenas se:
        - confianca >= limite_incerto
        - track_id ainda nao foi visto
        - bbox nao tem IOU >= 0.3 com objeto da mesma classe visto nos
          ultimos 3 segundos
        """
        if self._turno is None:
            return
        with self._lock:
            self._turno.total_frames += 1
            vistos_track = set(self._turno.track_ids_vistos)
            agora = time.time()

            # Limpa dedup_recentes da janela
            while self._dedup_recentes and (agora - self._dedup_recentes[0][2]) > self._dedup_janela_seg:
                self._dedup_recentes.popleft()

            for d in deteccoes:
                if d.confianca < self.limite_incerto:
                    continue
                if d.classe not in self._turno.contagens:
                    continue

                # Camada 1: dedup por track_id (rapido)
                tid = getattr(d, "track_id", None)
                if tid is not None and tid in vistos_track:
                    # Mesmo track ja contado: so atualiza dedup_recentes pra
                    # manter a posicao mais recente desse objeto.
                    self._dedup_recentes.append((d.classe, d.bbox, agora))
                    continue

                # Camada 2: dedup por IOU + classe + tempo
                duplicado_iou = False
                for cls_r, bbox_r, ts_r in self._dedup_recentes:
                    if cls_r != d.classe:
                        continue
                    if (agora - ts_r) > self._dedup_janela_seg:
                        continue
                    if _iou(d.bbox, bbox_r) >= self._dedup_iou_min:
                        duplicado_iou = True
                        break

                if duplicado_iou:
                    # Atualiza posicao do "mesmo" objeto, mas NAO conta.
                    self._dedup_recentes.append((d.classe, d.bbox, agora))
                    # Se vier com track_id novo (o tracker recriou), registra
                    # o track_id pra acelerar dedup futuro.
                    if tid is not None:
                        vistos_track.add(tid)
                        self._turno.track_ids_vistos.append(tid)
                    continue

                # Novo objeto: conta.
                self._turno.contagens[d.classe] += 1
                self._turno.total_deteccoes += 1
                self._dedup_recentes.append((d.classe, d.bbox, agora))
                if tid is not None:
                    vistos_track.add(tid)
                    self._turno.track_ids_vistos.append(tid)
                if d.classe == "rejeito":
                    self._turno.eventos_rejeito.append(
                        datetime.now().isoformat(timespec="seconds")
                    )

    def descontar(self, classe: str) -> None:
        """Operador rejeitou uma classificacao; tira do turno se houver."""
        if self._turno is None:
            return
        with self._lock:
            if self._turno.contagens.get(classe, 0) > 0:
                self._turno.contagens[classe] -= 1
                self._turno.total_deteccoes = max(
                    0, self._turno.total_deteccoes - 1,
                )

    # ----- metricas -----

    def percentual_contaminacao(self) -> float:
        if self._turno is None or self._turno.total_deteccoes == 0:
            return 0.0
        rejeito = self._turno.contagens.get("rejeito", 0)
        return 100.0 * rejeito / self._turno.total_deteccoes

    def em_alerta_contaminacao(self) -> bool:
        return self.percentual_contaminacao() > self.alerta_contaminacao_pct

    def kg_estimados(self) -> Dict[str, float]:
        if self._turno is None:
            return {}
        return {
            c: round(self._turno.contagens.get(c, 0) * self.pesos_kg.get(c, 0.1), 3)
            for c in CLASSES
        }

    def tempo_decorrido_segundos(self) -> int:
        if self._turno is None:
            return 0
        inicio = datetime.fromisoformat(self._turno.inicio)
        return int((datetime.now() - inicio).total_seconds())

    def horarios_pico_rejeito(self, bucket_min: int = 30) -> Dict[str, int]:
        """Agrupa eventos de rejeito em janelas de N minutos."""
        if self._turno is None:
            return {}
        baldes: Counter = Counter()
        for ev in self._turno.eventos_rejeito:
            dt = datetime.fromisoformat(ev)
            minuto_arred = (dt.minute // bucket_min) * bucket_min
            chave = dt.strftime(f"%H:{minuto_arred:02d}")
            baldes[chave] += 1
        return dict(baldes.most_common())

    # ----- persistencia -----

    def _salvar(self) -> None:
        if self._turno is None:
            return
        caminho = self.pasta_estado / "turno_atual.json"
        with caminho.open("w", encoding="utf-8") as f:
            json.dump(asdict(self._turno), f, ensure_ascii=False, indent=2)

    def _restaurar_se_existir(self) -> None:
        atual = self.pasta_estado / "turno_atual.json"
        if not atual.exists():
            return
        try:
            data = json.loads(atual.read_text(encoding="utf-8"))
            # Se nao foi encerrado, restaura.
            if data.get("fim") is None:
                self._turno = Turno(**data)
                log.info("Turno anterior restaurado: %s", self._turno.id)
                self._iniciar_autosave()
        except Exception:
            log.exception("Falha ao restaurar turno anterior.")

    def _iniciar_autosave(self) -> None:
        self._parar.clear()
        def loop():
            while not self._parar.wait(self.intervalo_salvar):
                with self._lock:
                    self._salvar()
        self._thread_save = threading.Thread(target=loop, daemon=True)
        self._thread_save.start()

    def listar_historico(self) -> List[Path]:
        return sorted(self.pasta_estado.glob("turno_*.json"))
