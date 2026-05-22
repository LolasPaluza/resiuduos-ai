"""Exporta TODOS os dados da cooperativa em um arquivo ZIP.

Uso simples (qualquer pessoa, sem ajuda tecnica):
    python -m ferramentas.exportar_meus_dados

Cria um arquivo na area de trabalho ou na pasta atual com:
- Todos os relatorios (JSON + PDF)
- Todas as imagens coletadas (frames)
- Logs do sistema
- Arquivo CONSENTIMENTO.txt
- Um README explicando o que e cada coisa, em portugues simples
"""
from __future__ import annotations

import argparse
import logging
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

log = logging.getLogger(__name__)


LEIA_ME = """
SEUS DADOS - COOPERATIVA
=========================

Esse arquivo ZIP contem TODOS os dados que o sistema guardou
sobre o trabalho da cooperativa. Eles pertencem a voces.

O que tem aqui dentro:

1. relatorios/
   - Arquivos .json e .pdf com o resumo de cada turno (quanto de
     cada material foi separado, % de rejeito, horarios de pico).
   - Use os PDFs para impressao ou para mostrar a parceiros e
     orgaos publicos.

2. frames/
   - Imagens da esteira que o sistema salvou para aprender.
   - Cada imagem tem um arquivo .txt do mesmo nome com a
     classificacao que o sistema deu (formato YOLO).
   - Voces podem deletar essa pasta a qualquer momento sem
     prejudicar o sistema.

3. logs/
   - Registro tecnico do que o programa fez. Util se algo deu
     errado e voce precisa pedir ajuda para o suporte tecnico.

4. CONSENTIMENTO.txt
   - Comprovante de quando o sistema foi instalado e que a
     instalacao foi autorizada.

5. config.yaml
   - Configuracoes atuais do sistema.

LEMBRETE
========

- O sistema NAO envia nada para fora do computador da cooperativa
  (a nao ser que voces tenham mudado isso na configuracao).
- O sistema NAO identifica pessoas individualmente. Os relatorios
  sao do LOTE e do TURNO, nunca de uma pessoa especifica.
- Voces podem apagar todos os dados a qualquer momento com:
      python -m ferramentas.deletar_meus_dados
"""


def construir_zip(raiz: Path, destino: Path) -> Path:
    pastas = {
        "relatorios": raiz / "dados" / "relatorios",
        "frames":     raiz / "dados" / "frames",
        "logs":       raiz / "dados" / "logs",
    }
    arquivos_extras = [
        raiz / "dados" / "CONSENTIMENTO.txt",
        raiz / "config.yaml",
    ]

    destino.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destino, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("LEIA-ME.txt", LEIA_ME.strip() + "\n")
        for nome, pasta in pastas.items():
            if not pasta.exists():
                continue
            for arq in pasta.rglob("*"):
                if arq.is_file():
                    zf.write(arq, arcname=f"{nome}/{arq.relative_to(pasta)}")
        for arq in arquivos_extras:
            if arq.exists():
                zf.write(arq, arcname=arq.name)
    return destino


def principal():
    parser = argparse.ArgumentParser(
        description="Exporta todos os dados da cooperativa em um arquivo ZIP.",
    )
    parser.add_argument("--saida", type=Path, default=None,
                        help="Arquivo ZIP de saida. Padrao: meus-dados-<data>.zip")
    parser.add_argument("--raiz", type=Path, default=Path("."),
                        help="Pasta raiz do projeto.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    saida = args.saida or (args.raiz / f"meus-dados-{timestamp}.zip")
    print(f"Empacotando seus dados em {saida} ...")
    construir_zip(args.raiz.resolve(), saida.resolve())

    tam_mb = saida.stat().st_size / 1024 / 1024
    print(f"")
    print(f"Pronto! Arquivo gerado: {saida}")
    print(f"Tamanho: {tam_mb:.1f} MB")
    print(f"")
    print("Voce pode copiar esse arquivo para um pendrive ou enviar por email.")
    print("Para apagar todos os dados do sistema:")
    print("    python -m ferramentas.deletar_meus_dados")


if __name__ == "__main__":
    principal()
