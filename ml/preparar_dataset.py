"""Download e preparacao dos datasets publicos TrashNet e TACO.

Gera estrutura YOLOv8:
    dataset/
      images/{train,val}/
      labels/{train,val}/
      data.yaml

Os datasets sao opcionais; o script avisa o que falta baixar manualmente.
"""
from __future__ import annotations

import argparse
import json
import logging
import random
import shutil
import urllib.request
from pathlib import Path
from typing import Dict, List

from ml import CLASSES

log = logging.getLogger(__name__)

# Mapeamento das classes originais para nossas 6 classes.
# TrashNet nao distingue PET de PEAD — mapeia "plastic" para PET (mais comum
# em mercado). O modelo aprende formas genericas de plastico que ajudam tambem
# na deteccao de PEAD.
MAP_TRASHNET = {
    "plastic":   "PET",
    "glass":     "rejeito",   # cooperativa nao compra vidro neste sistema
    "metal":     "metal",
    "paper":     "papel",
    "cardboard": "papel",
    "trash":     "rejeito",
}

# TACO: mapeamento baseado no NOME especifico da categoria (mais preciso).
# A supercategoria do TACO eh muito genericagrupa "Bottle" sem distinguir
# vidro/plastico. Por isso casamos pelo `name` da categoria.
def mapear_taco(supercategoria: str, nome_categoria: str = "") -> str:
    s = (nome_categoria or supercategoria).lower()

    # PET — plastico transparente/garrafas
    if "clear plastic bottle" in s:
        return "PET"
    if "other plastic bottle" in s:
        return "PET"

    # PEAD — plastico rigido opaco
    if "plastic bottle cap" in s:
        return "PEAD"
    if "plastic lid" in s:
        return "PEAD"
    if "disposable food container" in s and "foam" not in s:
        return "PEAD"
    if "plastic utensils" in s:
        return "PEAD"

    # Papel e papelao
    if "paper cup" in s or "paper bag" in s:
        return "papel"
    if "normal paper" in s or "magazine paper" in s or "wrapping paper" in s:
        return "papel"
    if "tissues" in s:
        return "papel"
    if "carton" in s:  # corrugated, drink, meal, egg, other carton
        return "papel"

    # Metal
    if "drink can" in s or "food can" in s:
        return "metal"
    if "metal bottle cap" in s:
        return "metal"
    if "pop tab" in s:
        return "metal"
    if "aluminium foil" in s or "aluminum foil" in s:
        return "metal"
    if "scrap metal" in s:
        return "metal"
    if "aerosol" in s:
        return "metal"

    # Organico
    if "food waste" in s:
        return "organico"

    # Tudo o que sobra vai pra rejeito:
    # - cigarettes, unlabeled litter, broken glass, styrofoam,
    #   glass bottle (cooperativa nao compra), plastic film/wrapper,
    #   straws, plastic cups descartaveis, ropes, etc.
    return "rejeito"


def baixar(url: str, destino: Path) -> None:
    if destino.exists():
        log.info("Ja existe: %s", destino)
        return
    destino.parent.mkdir(parents=True, exist_ok=True)
    log.info("Baixando %s -> %s", url, destino)
    urllib.request.urlretrieve(url, destino)


def preparar_trashnet(origem: Path, saida: Path, split: float = 0.8) -> int:
    """Recebe pasta TrashNet ja extraida e organiza para YOLO."""
    if not origem.exists():
        log.warning(
            "TrashNet nao encontrado em %s. "
            "Baixe manualmente: https://github.com/garythung/trashnet",
            origem,
        )
        return 0
    contador = 0
    for classe_origem, classe_destino in MAP_TRASHNET.items():
        pasta = origem / classe_origem
        if not pasta.exists():
            continue
        imagens = list(pasta.glob("*.jpg")) + list(pasta.glob("*.png"))
        random.shuffle(imagens)
        n_train = int(len(imagens) * split)
        for i, img in enumerate(imagens):
            subset = "train" if i < n_train else "val"
            destino_img = saida / "images" / subset / f"{classe_origem}_{i}.jpg"
            destino_lbl = saida / "labels" / subset / f"{classe_origem}_{i}.txt"
            destino_img.parent.mkdir(parents=True, exist_ok=True)
            destino_lbl.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(img, destino_img)
            # TrashNet nao tem bbox, entao usa imagem inteira (classificacao).
            cls_id = CLASSES.index(classe_destino)
            destino_lbl.write_text(f"{cls_id} 0.5 0.5 1.0 1.0\n", encoding="utf-8")
            contador += 1
    log.info("TrashNet: %s imagens preparadas.", contador)
    return contador


def preparar_taco(origem: Path, saida: Path, split: float = 0.8) -> int:
    """Recebe pasta TACO clonada (com annotations.json) e organiza para YOLO."""
    anotacoes = origem / "data" / "annotations.json"
    if not anotacoes.exists():
        log.warning(
            "TACO nao encontrado em %s. "
            "Clone: https://github.com/pedropro/TACO",
            origem,
        )
        return 0
    coco = json.loads(anotacoes.read_text(encoding="utf-8"))
    imagens = {img["id"]: img for img in coco["images"]}
    cats = {c["id"]: c for c in coco["categories"]}
    contador = 0
    por_imagem: Dict[int, List] = {}
    for ann in coco["annotations"]:
        por_imagem.setdefault(ann["image_id"], []).append(ann)

    items = list(por_imagem.items())
    random.shuffle(items)
    n_train = int(len(items) * split)
    for i, (img_id, anns) in enumerate(items):
        info = imagens[img_id]
        src = origem / "data" / info["file_name"]
        if not src.exists():
            continue
        subset = "train" if i < n_train else "val"
        dst_img = saida / "images" / subset / f"taco_{img_id}.jpg"
        dst_lbl = saida / "labels" / subset / f"taco_{img_id}.txt"
        dst_img.parent.mkdir(parents=True, exist_ok=True)
        dst_lbl.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst_img)
        W, H = info["width"], info["height"]
        with dst_lbl.open("w", encoding="utf-8") as f:
            for a in anns:
                cat = cats[a["category_id"]]
                supercat = cat.get("supercategory", "")
                nome = cat.get("name", "")
                classe = mapear_taco(supercat, nome)
                cls_id = CLASSES.index(classe)
                x, y, w, h = a["bbox"]
                cx = (x + w / 2) / W
                cy = (y + h / 2) / H
                f.write(f"{cls_id} {cx:.6f} {cy:.6f} {w/W:.6f} {h/H:.6f}\n")
        contador += 1
    log.info("TACO: %s imagens preparadas.", contador)
    return contador


def escrever_data_yaml(saida: Path) -> Path:
    yaml = saida / "data.yaml"
    linhas = [
        f"path: {saida.resolve()}",
        "train: images/train",
        "val: images/val",
        f"nc: {len(CLASSES)}",
        f"names: {CLASSES}",
    ]
    yaml.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    log.info("data.yaml escrito em %s", yaml)
    return yaml


def principal():
    parser = argparse.ArgumentParser(description="Prepara TrashNet + TACO para YOLOv8.")
    parser.add_argument("--trashnet", type=Path, default=Path("dados/datasets/trashnet"))
    parser.add_argument("--taco", type=Path, default=Path("dados/datasets/TACO"))
    parser.add_argument("--saida", type=Path, default=Path("dados/datasets/yolo"))
    parser.add_argument("--split", type=float, default=0.8)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    total = 0
    total += preparar_trashnet(args.trashnet, args.saida, args.split)
    total += preparar_taco(args.taco, args.saida, args.split)
    escrever_data_yaml(args.saida)
    log.info("Total de imagens preparadas: %s", total)
    if total == 0:
        log.warning(
            "Nenhuma imagem foi preparada. Baixe ao menos um dos datasets:\n"
            "  - TrashNet: https://github.com/garythung/trashnet\n"
            "  - TACO:     https://github.com/pedropro/TACO"
        )


if __name__ == "__main__":
    principal()
