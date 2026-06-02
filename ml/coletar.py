"""Modo de coleta de dados: aponta o objeto pra camera, sistema salva frames
com a classe correta automaticamente. Usado para enriquecer o dataset com
material especifico da sua cooperativa.

Uso (no Pi):
    python -m ml.coletar --classe PEAD --quantos 100
    python -m ml.coletar --classe organico --quantos 50

Apos coletar, retreine com:
    python -m ml.retreinar --epochs 30

Os frames vao para dados/frames/<data>/, com labels YOLO usando bbox que
pega a regiao central do frame (assume que o objeto enche a tela).
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2

from core.camera import Camera, detectar_hardware
from ml import CLASSES

log = logging.getLogger(__name__)


def coletar(classe: str, quantos: int, pasta_saida: Path,
            intervalo_seg: float = 0.5,
            indice_camera: int = 0) -> int:
    """Coleta N frames da webcam, todos rotulados como `classe`.

    O bbox e a regiao central (60% do frame) — assume que o operador esta
    apontando o objeto principal pra camera.
    """
    if classe not in CLASSES:
        log.error("Classe '%s' invalida. Opcoes: %s", classe, CLASSES)
        return 0

    cls_id = CLASSES.index(classe)
    pasta = pasta_saida / datetime.now().strftime("%Y-%m-%d_coleta_%H%M%S")
    pasta_img = pasta / "images"
    pasta_lbl = pasta / "labels"
    pasta_img.mkdir(parents=True, exist_ok=True)
    pasta_lbl.mkdir(parents=True, exist_ok=True)

    perfil = detectar_hardware()
    log.info("Hardware: %s", perfil.nome)
    log.info("Coletando %d frames como '%s' em %s", quantos, classe, pasta)
    log.info("Aponta o objeto bem em frente da camera!")
    log.info("Inicia em 3s...")
    time.sleep(3)

    salvos = 0
    cam = Camera(indice=indice_camera, fps_alvo=10)
    cam.abrir()
    try:
        ultimo = 0.0
        while salvos < quantos:
            frame = cam.ler_frame()
            if frame is None:
                continue
            agora = time.time()
            if agora - ultimo < intervalo_seg:
                continue
            ultimo = agora

            h, w = frame.shape[:2]
            nome = f"{classe}_{salvos:04d}.jpg"
            cv2.imwrite(str(pasta_img / nome), frame)

            # Label YOLO: classe + bbox central (60% do frame)
            (pasta_lbl / nome.replace(".jpg", ".txt")).write_text(
                f"{cls_id} 0.5 0.5 0.6 0.6\n",
                encoding="utf-8",
            )
            salvos += 1
            print(f"  [{salvos:3d}/{quantos}] {nome}", flush=True)
    finally:
        cam.fechar()

    log.info("Concluido: %d frames salvos em %s", salvos, pasta)
    return salvos


def principal():
    parser = argparse.ArgumentParser(
        description="Coleta frames de uma classe especifica.",
    )
    parser.add_argument("--classe", required=True, choices=CLASSES,
                        help="Classe alvo (PET/PEAD/papel/metal/organico/rejeito)")
    parser.add_argument("--quantos", type=int, default=50,
                        help="Quantos frames coletar (default: 50)")
    parser.add_argument("--intervalo", type=float, default=0.5,
                        help="Segundos entre frames (mover objeto pra variar pose)")
    parser.add_argument("--pasta", type=Path,
                        default=Path("dados/frames"),
                        help="Pasta de saida")
    parser.add_argument("--camera", type=int, default=0)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s: %(message)s")
    coletar(args.classe, args.quantos, args.pasta,
            args.intervalo, args.camera)


if __name__ == "__main__":
    principal()
