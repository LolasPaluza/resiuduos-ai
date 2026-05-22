"""Testa inferencia do modelo com uma imagem estatica.

Uso:
    python -m testes.test_modelo --imagem caminho/foto.jpg
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

from ml.modelo import Modelo


def principal():
    parser = argparse.ArgumentParser()
    parser.add_argument("--modelo", type=str,
                        default="dados/modelos/yolov8n_residuos.pt")
    parser.add_argument("--imagem", type=str, default=None,
                        help="Imagem de teste. Se vazio, gera uma sintetica.")
    parser.add_argument("--conf", type=float, default=0.25)
    args = parser.parse_args()

    m = Modelo(caminho=args.modelo, confianca_minima=args.conf)
    try:
        m.carregar()
    except Exception as e:
        print(f"[FALHA] Nao foi possivel carregar o modelo: {e}")
        sys.exit(1)

    if args.imagem and Path(args.imagem).exists():
        frame = cv2.imread(args.imagem)
        if frame is None:
            print(f"[FALHA] Nao foi possivel ler imagem: {args.imagem}")
            sys.exit(1)
    else:
        print("[INFO] Sem imagem; usando frame sintetico 640x480.")
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

    dets = m.inferir(frame)
    print(f"[OK] Inferencia completou em {m.tempo_ultima_inferencia*1000:.1f}ms")
    print(f"[OK] {len(dets)} deteccoes:")
    for d in dets:
        print(f"   - {d.classe} ({d.confianca*100:.1f}%) bbox={d.bbox}")
    if not dets:
        print("[INFO] Sem deteccoes — normal em imagem aleatoria/sem objetos conhecidos.")


if __name__ == "__main__":
    principal()
