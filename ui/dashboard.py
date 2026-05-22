"""Dashboard visual usando OpenCV.

Principios eticos aplicados:
- Linguagem simples: "Certeza" no lugar de "Confiança/Inferência".
- Badges VERIFICAR (amarelo, <70%) e INCERTO (vermelho, <50%).
- Modo degradado claramente sinalizado quando IA cai.
- Sem qualquer mencao a operador individual.
- Alto contraste opcional.
- Acessivel apenas com teclado numerico + algumas letras.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np

from core.alertas import GerenciadorAlertas
from core.classifier import Classifier
from core.turno import GerenciadorTurno
from ml import CLASSES, CORES_CLASSES, ICONES_CLASSES
from ml.modelo import Deteccao

log = logging.getLogger(__name__)


TECLA_PARA_CLASSE: Dict[int, str] = {
    ord("1"): "PET",
    ord("2"): "PEAD",
    ord("3"): "papel",
    ord("4"): "metal",
    ord("5"): "organico",
    ord("6"): "rejeito",
}


class Dashboard:
    """Janela OpenCV em fullscreen com video + painel lateral."""

    LARGURA = 1280
    ALTURA = 720
    PAINEL_W = 420

    def __init__(
        self,
        classifier,  # Classifier ou ClassifierDegradado
        turno: GerenciadorTurno,
        alertas: GerenciadorAlertas,
        tema: str = "escuro",
        fonte_tamanho: int = 28,
        alto_contraste: bool = False,
        limite_verificar: float = 0.70,
        limite_incerto: float = 0.50,
        nome_janela: str = "Residuos AI - Cooperativa",
    ) -> None:
        self.classifier = classifier
        self.turno = turno
        self.alertas = alertas
        self.tema = tema
        self.fonte_tamanho = fonte_tamanho
        self.alto_contraste = alto_contraste
        self.limite_verificar = limite_verificar
        self.limite_incerto = limite_incerto
        self.nome_janela = nome_janela
        self._ultimas_deteccoes: List[Deteccao] = []
        self._ultimo_frame: Optional[np.ndarray] = None
        self._fechar = False
        # Modo degradado: detectado pelo atributo do classifier.
        self.modo_degradado = getattr(classifier, "degradado", False)

    # ----- cores -----

    def _cor_fundo(self):
        if self.alto_contraste:
            return (0, 0, 0)
        return (30, 30, 30) if self.tema == "escuro" else (240, 240, 240)

    def _cor_texto(self):
        if self.alto_contraste:
            return (255, 255, 255)
        return (240, 240, 240) if self.tema == "escuro" else (20, 20, 20)

    # ----- desenho -----

    def _badge_certeza(self, conf: float) -> tuple[str, tuple[int, int, int]]:
        """Retorna (rotulo, cor BGR) baseado no nivel de certeza."""
        if conf < self.limite_incerto:
            return "INCERTO", (0, 0, 255)
        if conf < self.limite_verificar:
            return "VERIFICAR", (0, 200, 255)
        return "OK", (0, 200, 0)

    def _desenhar_deteccoes(self, frame: np.ndarray, dets: List[Deteccao]) -> None:
        for d in dets:
            cor = CORES_CLASSES.get(d.classe, (255, 255, 255))
            badge_txt, badge_cor = self._badge_certeza(d.confianca)
            x1, y1, x2, y2 = d.bbox

            # Box: traco mais grosso para alta certeza, tracejado simulado para baixa.
            if d.confianca < self.limite_incerto:
                # "Tracejado" usando linhas curtas — sinaliza incerteza visualmente.
                for i in range(x1, x2, 14):
                    cv2.line(frame, (i, y1), (min(i+7, x2), y1), badge_cor, 3)
                    cv2.line(frame, (i, y2), (min(i+7, x2), y2), badge_cor, 3)
                for j in range(y1, y2, 14):
                    cv2.line(frame, (x1, j), (x1, min(j+7, y2)), badge_cor, 3)
                    cv2.line(frame, (x2, j), (x2, min(j+7, y2)), badge_cor, 3)
            else:
                cv2.rectangle(frame, (x1, y1), (x2, y2), cor, 3)

            icone = ICONES_CLASSES.get(d.classe, "")
            label = f"{icone} {d.classe} - Certeza: {d.confianca*100:.0f}%"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
            cv2.rectangle(frame, (x1, y1 - th - 10), (x1 + tw + 10, y1), cor, -1)
            cv2.putText(
                frame, label, (x1 + 5, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2,
            )
            # Badge VERIFICAR/INCERTO acima da box.
            if d.confianca < self.limite_verificar:
                cv2.rectangle(frame, (x1, y2), (x1 + 140, y2 + 30), badge_cor, -1)
                cv2.putText(frame, badge_txt, (x1 + 8, y2 + 22),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

    def _desenhar_painel(self, canvas: np.ndarray) -> None:
        x0 = self.LARGURA - self.PAINEL_W
        cv2.rectangle(canvas, (x0, 0), (self.LARGURA, self.ALTURA),
                      self._cor_fundo(), -1)

        t = self.turno.turno_atual()
        y = 40
        cv2.putText(canvas, "TURNO", (x0 + 20, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, self._cor_texto(), 3)
        y += 40
        if t:
            inicio = t.inicio.split("T")[1][:5]
            decorrido = self.turno.tempo_decorrido_segundos()
            h, rem = divmod(decorrido, 3600)
            m, _ = divmod(rem, 60)
            cv2.putText(canvas, f"Inicio: {inicio}", (x0 + 20, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, self._cor_texto(), 2)
            y += 30
            cv2.putText(canvas, f"Tempo: {h:02d}h{m:02d}m", (x0 + 20, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, self._cor_texto(), 2)
        else:
            cv2.putText(canvas, "Sem turno ativo", (x0 + 20, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        y += 40

        # Percentual de contaminacao + alerta. Texto NEUTRO: fala do LOTE, nunca da pessoa.
        pct = self.turno.percentual_contaminacao()
        cor_pct = (0, 0, 255) if self.turno.em_alerta_contaminacao() else self._cor_texto()
        cv2.putText(canvas, f"Lote - Rejeito: {pct:.1f}%", (x0 + 20, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, cor_pct, 2)
        y += 40

        # Barras por classe.
        contagens = t.contagens if t else {c: 0 for c in CLASSES}
        max_v = max(contagens.values()) if contagens else 1
        max_v = max(max_v, 1)
        largura_max = self.PAINEL_W - 200
        for classe in CLASSES:
            v = contagens.get(classe, 0)
            cor = CORES_CLASSES[classe]
            cv2.putText(canvas, classe, (x0 + 20, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, self._cor_texto(), 2)
            barra = int(largura_max * v / max_v)
            cv2.rectangle(canvas,
                          (x0 + 140, y - 18),
                          (x0 + 140 + barra, y),
                          cor, -1)
            cv2.putText(canvas, str(v), (x0 + self.PAINEL_W - 50, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, self._cor_texto(), 2)
            y += 35

        # FPS + CPU. (FPS e medido do LOTE/sistema, nao de pessoa.)
        y = self.ALTURA - 80
        cv2.putText(canvas, f"Imagens/s: {self.classifier.fps_atual():.1f}",
                    (x0 + 20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    self._cor_texto(), 2)
        y += 30
        cv2.putText(canvas, f"CPU: {self.classifier.cpu_pct():.0f}%",
                    (x0 + 20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    self._cor_texto(), 2)

    def _desenhar_atalhos(self, canvas: np.ndarray) -> None:
        if self.modo_degradado:
            texto = "MODO MANUAL: aperte 1-6 para classificar cada item | Q=sair"
        else:
            texto = ("1=PET 2=PEAD 3=papel 4=metal 5=organico 6=rejeito  "
                     "| A=aceitar  R=rejeitar  Q=sair")
        cv2.putText(canvas, texto, (10, self.ALTURA - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

    def _desenhar_banner_degradado(self, canvas: np.ndarray) -> None:
        """Banner GRANDE quando opera sem IA. Operador precisa ver de longe."""
        if not self.modo_degradado:
            return
        cv2.rectangle(canvas, (0, 0), (self.LARGURA - self.PAINEL_W, 60),
                      (0, 165, 255), -1)
        cv2.putText(canvas,
                    "MODO MANUAL - IA temporariamente indisponivel",
                    (15, 42), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 3)

    def _desenhar_aviso_coleta(self, canvas: np.ndarray) -> None:
        """Aviso permanente, em letras pequenas, sobre o que e coletado."""
        texto = "Imagens da esteira sao salvas neste computador para melhorar o sistema."
        cv2.putText(canvas, texto, (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 150, 150), 1)

    def _registrar_manual(self, classe: str) -> None:
        """Operador classificou manualmente: cria uma deteccao 'sintetica' com 100%."""
        if self._ultimo_frame is None:
            return
        h, w = self._ultimo_frame.shape[:2]
        cls_id = CLASSES.index(classe)
        det = Deteccao(
            classe=classe, classe_id=cls_id, confianca=1.0,
            bbox=(0, 0, w, h),
        )
        self.turno.registrar([det])
        log.info("Classificacao manual registrada (lote): %s", classe)
        # Tambem salva como amostra rotulada para futuro retreinamento.
        from datetime import datetime
        import uuid
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        uid = uuid.uuid4().hex[:6]
        pasta = self.classifier.pasta_frames
        img = pasta / f"manual_{ts}_{uid}.jpg"
        cv2.imwrite(str(img), self._ultimo_frame)
        lbl = img.with_suffix(".txt")
        lbl.write_text(f"{cls_id} 0.5 0.5 1.0 1.0\n", encoding="utf-8")

    def _corrigir_ultima(self, nova_classe: str) -> None:
        if not self._ultimas_deteccoes or self._ultimo_frame is None:
            return self._registrar_manual(nova_classe)
        cls_id = CLASSES.index(nova_classe)
        log.info("Operador corrigiu classificacao do LOTE para: %s", nova_classe)
        from datetime import datetime
        import uuid
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        uid = uuid.uuid4().hex[:6]
        pasta = self.classifier.pasta_frames
        caminho_img = pasta / f"correcao_{ts}_{uid}.jpg"
        cv2.imwrite(str(caminho_img), self._ultimo_frame)
        label = caminho_img.with_suffix(".txt")
        h, w = self._ultimo_frame.shape[:2]
        with label.open("w", encoding="utf-8") as f:
            for d in self._ultimas_deteccoes:
                x1, y1, x2, y2 = d.bbox
                cx = ((x1 + x2) / 2) / w
                cy = ((y1 + y2) / 2) / h
                bw = (x2 - x1) / w
                bh = (y2 - y1) / h
                f.write(f"{cls_id} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}\n")

    # ----- loop -----

    def executar(self) -> None:
        cv2.namedWindow(self.nome_janela, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.nome_janela, self.LARGURA, self.ALTURA)

        try:
            for frame, deteccoes in self.classifier.stream():
                self._ultimo_frame = frame.copy()
                if deteccoes:
                    self._ultimas_deteccoes = deteccoes
                    self.turno.registrar(deteccoes)
                    # Alerta por classe — sons distintos (P6: nao depender so de volume).
                    for d in deteccoes:
                        if d.confianca >= self.limite_incerto:
                            self.alertas.alertar_classe(d.classe)

                canvas = np.full(
                    (self.ALTURA, self.LARGURA, 3),
                    self._cor_fundo(), dtype=np.uint8,
                )
                video_w = self.LARGURA - self.PAINEL_W
                video_h = self.ALTURA
                redim = cv2.resize(frame, (video_w, video_h))
                fx = video_w / frame.shape[1]
                fy = video_h / frame.shape[0]
                dets_redim = [
                    Deteccao(
                        d.classe, d.classe_id, d.confianca,
                        (int(d.bbox[0]*fx), int(d.bbox[1]*fy),
                         int(d.bbox[2]*fx), int(d.bbox[3]*fy)),
                    )
                    for d in deteccoes
                ]
                self._desenhar_deteccoes(redim, dets_redim)
                canvas[0:video_h, 0:video_w] = redim

                self._desenhar_painel(canvas)
                self._desenhar_banner_degradado(canvas)
                self._desenhar_atalhos(canvas)
                self._desenhar_aviso_coleta(canvas)

                if self.turno.em_alerta_contaminacao():
                    cv2.rectangle(canvas, (0, 0),
                                  (self.LARGURA, self.ALTURA),
                                  (0, 0, 255), 8)

                cv2.imshow(self.nome_janela, canvas)
                tecla = cv2.waitKey(1) & 0xFF
                if tecla == ord("q") or tecla == 27:
                    self._fechar = True
                    break
                if tecla in TECLA_PARA_CLASSE:
                    self._corrigir_ultima(TECLA_PARA_CLASSE[tecla])
                elif tecla == ord("a"):
                    # Aceitar: ja contabilizado, so confirma — registra como amostra positiva.
                    if self._ultimas_deteccoes and self._ultimo_frame is not None:
                        log.info("Operador ACEITOU classificacao do lote.")
                elif tecla == ord("r"):
                    # Rejeitar: tira do turno se foi contabilizado (acima do limite).
                    if self._ultimas_deteccoes:
                        log.info("Operador REJEITOU classificacao do lote — descontando.")
                        for d in self._ultimas_deteccoes:
                            if d.confianca >= self.turno.limite_incerto:
                                self.turno.descontar(d.classe)
                        self._ultimas_deteccoes = []
        finally:
            cv2.destroyAllWindows()
