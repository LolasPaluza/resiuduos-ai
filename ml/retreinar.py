"""Fine-tuning do YOLOv8 nano com dados publicos + correcoes locais.

Uso:
    python -m ml.retreinar --data dados/datasets/yolo/data.yaml --epochs 30
"""
from __future__ import annotations

import argparse
import logging
import shutil
from pathlib import Path

from ml import CLASSES

log = logging.getLogger(__name__)


def juntar_frames_locais(pasta_frames: Path, data_yaml: Path) -> int:
    """Copia frames corrigidos pelo operador para o conjunto de treino."""
    if not pasta_frames.exists():
        return 0
    base = data_yaml.parent
    dst_img = base / "images" / "train"
    dst_lbl = base / "labels" / "train"
    dst_img.mkdir(parents=True, exist_ok=True)
    dst_lbl.mkdir(parents=True, exist_ok=True)
    contador = 0
    for img in pasta_frames.glob("*.jpg"):
        lbl = img.with_suffix(".txt")
        if not lbl.exists():
            continue
        shutil.copy(img, dst_img / f"local_{img.name}")
        shutil.copy(lbl, dst_lbl / f"local_{lbl.name}")
        contador += 1
    log.info("Frames locais adicionados ao treino: %s", contador)
    return contador


def treinar(data_yaml: Path, epochs: int, imgsz: int,
            modelo_base: str, saida: Path) -> Path:
    from ultralytics import YOLO
    log.info("Iniciando treino: base=%s epochs=%s imgsz=%s",
             modelo_base, epochs, imgsz)
    modelo = YOLO(modelo_base)
    # Ultralytics usa caminhos absolutos para project/name; usamos absolutos
    # para evitar que ele combine com seu cwd default (runs/detect/...).
    saida_abs = saida.resolve()
    saida_abs.parent.mkdir(parents=True, exist_ok=True)
    modelo.train(
        data=str(data_yaml.resolve()),
        epochs=epochs,
        imgsz=imgsz,
        batch=8,
        project=str(saida_abs.parent),
        name=saida_abs.name,
        exist_ok=True,
    )
    best = saida_abs / "weights" / "best.pt"
    log.info("Treino concluido. Melhor modelo: %s", best)
    return best


def principal():
    parser = argparse.ArgumentParser(description="Fine-tune YOLOv8 nano para residuos.")
    parser.add_argument("--data", type=Path, default=Path("dados/datasets/yolo/data.yaml"))
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--base", type=str, default="yolov8n.pt")
    parser.add_argument("--frames-locais", type=Path,
                        default=Path("dados/frames"))
    parser.add_argument("--saida", type=Path,
                        default=Path("dados/modelos/runs/finetune"))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if not args.data.exists():
        log.error(
            "data.yaml nao encontrado em %s. "
            "Rode primeiro: python -m ml.preparar_dataset",
            args.data,
        )
        return

    juntar_frames_locais(args.frames_locais, args.data)
    best = treinar(args.data, args.epochs, args.imgsz, args.base, args.saida)

    # Copia o melhor modelo para o local padrao usado em producao.
    destino = Path("dados/modelos/yolov8n_residuos.pt")
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(best, destino)
    log.info("Modelo final copiado para %s", destino)
    log.info(
        "Para usar imediatamente, reinicie o sistema. "
        "Classes treinadas: %s", CLASSES,
    )


if __name__ == "__main__":
    principal()
