"""Unifica TACO + TrashNet + Roboflow datasets em formato YOLO com nossas 6 classes.

Cada dataset de origem tem suas proprias classes; remapeamos pra:
    PET, PEAD, papel, metal, organico, rejeito
"""
from __future__ import annotations

import argparse
import logging
import random
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from ml import CLASSES
from ml.preparar_dataset import (
    escrever_data_yaml,
    preparar_taco,
    preparar_trashnet,
)

log = logging.getLogger(__name__)


# Mapeamento ecosift (5 classes) -> nossas 6
MAP_ECOSIFT = {
    "Can":             "metal",
    "HDPE":            "PEAD",
    "PET_Bottle":      "PET",
    "Plastic_wrapper": "rejeito",  # filme plastico mole nao tem mercado
    "Tetrapak":        "papel",    # tetrapak vai pra cooperativas que processam papel
}

# Mapeamento htl (6 classes) -> nossas 6
MAP_HTL = {
    "BIODEGRADABLE": "organico",
    "CARDBOARD":     "papel",
    "GLASS":         "rejeito",   # cooperativa nao compra vidro
    "METAL":         "metal",
    "PAPER":         "papel",
    "PLASTIC":       "PEAD",       # plastic generico vai pra PEAD (rigido)
}


def preparar_roboflow(
    origem: Path,
    saida: Path,
    classes_origem: List[str],
    mapeamento: Dict[str, str],
    prefixo: str,
) -> int:
    """Copia imagens e remapeia labels de um dataset Roboflow YOLOv8 para nossas classes."""
    if not origem.exists():
        log.warning("Dataset %s nao encontrado em %s", prefixo, origem)
        return 0

    contador = 0
    for subset_src, subset_dst in [("train", "train"), ("valid", "val"), ("test", "train")]:
        # test vira train (aumenta dado)
        img_dir = origem / subset_src / "images"
        lbl_dir = origem / subset_src / "labels"
        if not img_dir.exists() or not lbl_dir.exists():
            continue
        for img in img_dir.glob("*.jpg"):
            lbl = lbl_dir / (img.stem + ".txt")
            if not lbl.exists():
                continue
            # Le labels e remapeia
            linhas_novas = []
            for ln in lbl.read_text(encoding="utf-8").splitlines():
                ln = ln.strip()
                if not ln:
                    continue
                partes = ln.split()
                if len(partes) < 5:
                    continue
                cls_idx = int(partes[0])
                if cls_idx >= len(classes_origem):
                    continue
                nome_orig = classes_origem[cls_idx]
                nome_destino = mapeamento.get(nome_orig)
                if nome_destino is None:
                    continue
                novo_idx = CLASSES.index(nome_destino)
                linhas_novas.append(f"{novo_idx} {' '.join(partes[1:5])}")
            if not linhas_novas:
                continue
            # Copia para saida com prefixo unico
            dst_img = saida / "images" / subset_dst / f"{prefixo}_{img.name}"
            dst_lbl = saida / "labels" / subset_dst / f"{prefixo}_{img.stem}.txt"
            dst_img.parent.mkdir(parents=True, exist_ok=True)
            dst_lbl.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(img, dst_img)
            dst_lbl.write_text("\n".join(linhas_novas) + "\n", encoding="utf-8")
            contador += 1
    log.info("%s: %s imagens preparadas.", prefixo, contador)
    return contador


def principal():
    parser = argparse.ArgumentParser(description="Unifica todos os datasets em formato YOLO.")
    parser.add_argument("--saida", type=Path, default=Path("dados/datasets/yolo"))
    parser.add_argument("--trashnet", type=Path, default=Path("dados/datasets/trashnet/dataset-resized"))
    parser.add_argument("--taco", type=Path, default=Path("dados/datasets/TACO"))
    parser.add_argument("--ecosift", type=Path, default=Path("dados/datasets/ecosift"))
    parser.add_argument("--htl", type=Path, default=Path("dados/datasets/htl"))
    parser.add_argument("--split", type=float, default=0.85)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Limpa saida
    if args.saida.exists():
        log.info("Removendo saida existente: %s", args.saida)
        shutil.rmtree(args.saida)
    args.saida.mkdir(parents=True, exist_ok=True)

    total = 0
    total += preparar_trashnet(args.trashnet, args.saida, args.split)
    total += preparar_taco(args.taco, args.saida, args.split)
    total += preparar_roboflow(
        args.ecosift, args.saida,
        ["Can", "HDPE", "PET_Bottle", "Plastic_wrapper", "Tetrapak"],
        MAP_ECOSIFT, "ecosift",
    )
    total += preparar_roboflow(
        args.htl, args.saida,
        ["BIODEGRADABLE", "CARDBOARD", "GLASS", "METAL", "PAPER", "PLASTIC"],
        MAP_HTL, "htl",
    )

    escrever_data_yaml(args.saida)
    log.info("=" * 60)
    log.info("TOTAL UNIFICADO: %s imagens", total)
    log.info("=" * 60)


if __name__ == "__main__":
    principal()
