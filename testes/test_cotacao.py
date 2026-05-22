"""Testes do modulo de cotacao.

Nao depende de internet: usa precos manuais e injeta historico fake
para validar as regras de alerta. Para um teste real do scraper:

    python -m testes.test_cotacao --scrape
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# Permite rodar como `python testes/test_cotacao.py`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.cotacao import (  # noqa: E402
    Cotacao,
    MATERIAIS,
    RepositorioCotacao,
    ServicoCotacao,
    _extrair_preco,
    buscar_cempre,
)


def teste_parser_preco():
    casos = [
        ("R$ 1,80", 1.80),
        ("R$ 0,85 / kg", 0.85),
        ("1.234,56", None),       # > 50, filtrado
        ("2,50", 2.50),
        ("texto sem preco", None),
        ("R$ 0,01", None),        # < 0.05, filtrado
    ]
    for entrada, esperado in casos:
        obtido = _extrair_preco(entrada)
        assert obtido == esperado, f"{entrada!r}: esperado {esperado}, obtido {obtido}"
    print("[OK] _extrair_preco")


def teste_repo_persiste_e_le():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "cot.sqlite"
        repo = RepositorioCotacao(db)
        repo.salvar(Cotacao("PET cristal", 2.50, datetime.now().isoformat(), "manual"))
        ult = repo.ultima("PET cristal")
        assert ult is not None and ult.preco_rs_kg == 2.50
        assert repo.ultima("Aluminio") is None
    print("[OK] RepositorioCotacao persiste e le")


def teste_alerta_alta_dispara_vender():
    with tempfile.TemporaryDirectory() as tmp:
        svc = ServicoCotacao(
            caminho_db=Path(tmp) / "cot.sqlite",
            precos_manuais={"PET cristal": 3.00},
        )
        # Injeta historico de 30 dias com media 2.00.
        base = datetime.now() - timedelta(days=15)
        for i in range(30):
            svc.repo.salvar(Cotacao(
                "PET cristal", 2.00,
                (base + timedelta(hours=i)).isoformat(timespec="seconds"),
                "manual",
            ))
        # Cotacao atual = 3.00 (50% acima da media).
        svc.repo.salvar(Cotacao(
            "PET cristal", 3.00,
            datetime.now().isoformat(timespec="seconds"), "manual",
        ))
        alertas = svc.alertas()
        assert any(a.tipo == "vender" and a.material == "PET cristal"
                   for a in alertas), f"esperava alerta vender, recebi {alertas}"
    print("[OK] Alerta de alta gera recomendacao 'vender'")


def teste_alerta_baixa_dispara_aguardar():
    with tempfile.TemporaryDirectory() as tmp:
        svc = ServicoCotacao(caminho_db=Path(tmp) / "cot.sqlite")
        base = datetime.now() - timedelta(days=15)
        for i in range(30):
            svc.repo.salvar(Cotacao(
                "Aluminio", 10.00,
                (base + timedelta(hours=i)).isoformat(timespec="seconds"),
                "manual",
            ))
        svc.repo.salvar(Cotacao(
            "Aluminio", 7.50,
            datetime.now().isoformat(timespec="seconds"), "manual",
        ))
        alertas = svc.alertas()
        assert any(a.tipo == "aguardar" and a.material == "Aluminio"
                   for a in alertas), f"esperava alerta aguardar, recebi {alertas}"
    print("[OK] Alerta de baixa gera recomendacao 'aguardar'")


def teste_atualizar_sem_internet_usa_cache():
    """Quando scraping falha, atual() ainda devolve dados do cache."""
    with tempfile.TemporaryDirectory() as tmp:
        svc = ServicoCotacao(
            caminho_db=Path(tmp) / "cot.sqlite",
            url_cempre="http://localhost:1/inexistente",  # forca falha
            precos_manuais={m: 1.50 for m in MATERIAIS},
        )
        cotacoes = svc.atualizar_agora()
        assert len(cotacoes) == len(MATERIAIS), "deveria preencher via manuais"
        assert all(c.fonte == "manual" for c in cotacoes.values())
    print("[OK] Sem internet usa precos manuais como fallback")


def teste_scraper_real():
    """Tenta CEMPRE de verdade. Apenas informativo."""
    print("Buscando CEMPRE (pode demorar)...")
    cotacoes = buscar_cempre()
    if not cotacoes:
        print("[INFO] CEMPRE nao retornou nenhuma cotacao. "
              "Isso eh esperado se a estrutura da pagina mudou ou nao ha internet.")
        return
    for m, p in cotacoes.items():
        print(f"  - {m}: R$ {p:.2f}/kg")
    print(f"[OK] Scraper extraiu {len(cotacoes)} materiais.")


def principal():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scrape", action="store_true",
                        help="Tambem testa o scraper real do CEMPRE (precisa de internet).")
    args = parser.parse_args()

    teste_parser_preco()
    teste_repo_persiste_e_le()
    teste_alerta_alta_dispara_vender()
    teste_alerta_baixa_dispara_aguardar()
    teste_atualizar_sem_internet_usa_cache()
    if args.scrape:
        teste_scraper_real()
    print("\nTodos os testes passaram.")


if __name__ == "__main__":
    principal()
