"""Testa se a webcam esta funcionando.

Uso:
    python -m testes.test_camera
    python -m testes.test_camera --indice 1 --frames 5
"""
from __future__ import annotations

import argparse
import sys

import cv2

from core.camera import Camera, detectar_hardware


def principal():
    parser = argparse.ArgumentParser()
    parser.add_argument("--indice", type=int, default=0)
    parser.add_argument("--frames", type=int, default=10)
    parser.add_argument("--mostrar", action="store_true",
                        help="Exibe janela com video ao vivo.")
    args = parser.parse_args()

    perfil = detectar_hardware()
    print(f"[OK] Hardware detectado: {perfil.nome} "
          f"(res {perfil.resolucao_inferencia}, fps max {perfil.fps_max})")

    try:
        with Camera(indice=args.indice, fps_alvo=10) as cam:
            for i in range(args.frames):
                frame = cam.ler_frame()
                if frame is None:
                    print(f"[FALHA] Frame {i+1} retornou None.")
                    sys.exit(1)
                h, w = frame.shape[:2]
                print(f"[OK] Frame {i+1}: {w}x{h}")
                if args.mostrar:
                    cv2.imshow("teste-camera", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
            if args.mostrar:
                cv2.destroyAllWindows()
        print("[OK] Camera funcionando corretamente.")
    except RuntimeError as e:
        print(f"[FALHA] {e}")
        sys.exit(1)


if __name__ == "__main__":
    principal()
