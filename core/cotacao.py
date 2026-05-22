"""Cotacao de materiais reciclaveis em tempo real.

Fonte primaria: scraping da tabela publica do CEMPRE (cempre.org.br).
Fallback: cache SQLite local com ultimo valor conhecido.

Funciona offline: se nao houver internet, retorna o ultimo valor salvo
e indica que a cotacao esta defasada. Atualizacao em background a cada
N minutos (configuravel).

Alertas:
- Preco > media 30d em mais de 10% -> "VENDER AGORA" (verde)
- Preco < media 30d em mais de 15% -> "AGUARDAR" (amarelo)
"""
from __future__ import annotations

import logging
import re
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional

log = logging.getLogger(__name__)


# Materiais monitorados (nome canonico usado no banco e na UI).
MATERIAIS = [
    "PET cristal",
    "PET verde",
    "Aluminio",
    "Papelao",
    "Papel branco",
    "PEAD natural",
    "Ferro",
]

# Apelidos para casamento aproximado com a tabela do CEMPRE
# (CEMPRE muda nomenclatura de tempos em tempos, entao mantemos tolerante).
_APELIDOS = {
    "PET cristal":   ["pet cristal", "pet transparente", "pet incolor"],
    "PET verde":     ["pet verde", "pet colorido"],
    "Aluminio":      ["aluminio", "alumínio", "lata de aluminio", "latinha"],
    "Papelao":       ["papelao", "papelão", "papelao ondulado", "kraft"],
    "Papel branco":  ["papel branco", "papel branco i", "papel branco ii", "aparas brancas"],
    "PEAD natural":  ["pead natural", "pead branco", "pead leitoso"],
    "Ferro":         ["ferro", "sucata ferrosa", "sucata de ferro"],
}


@dataclass
class Cotacao:
    """Snapshot de uma cotacao para um material."""
    material: str
    preco_rs_kg: float
    data: str               # ISO 8601
    fonte: str              # "cempre", "manual", "cache"
    defasada: bool = False  # True se veio de cache porque scraping falhou


@dataclass
class AlertaCotacao:
    """Recomendacao automatica de venda/espera."""
    material: str
    tipo: str               # "vender" | "aguardar"
    cor: str                # "verde" | "amarelo"
    mensagem: str
    preco_atual: float
    media_30d: float
    variacao_pct: float


# ============================================================
# Armazenamento (SQLite)
# ============================================================

_DDL = """
CREATE TABLE IF NOT EXISTS cotacoes (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    material     TEXT NOT NULL,
    preco_rs_kg  REAL NOT NULL,
    data         TEXT NOT NULL,
    fonte        TEXT NOT NULL DEFAULT 'cempre'
);
CREATE INDEX IF NOT EXISTS ix_cotacoes_material_data
    ON cotacoes(material, data);
"""


class RepositorioCotacao:
    """Persistencia em SQLite. Pode ser usada offline indefinidamente."""

    def __init__(self, caminho_db: str | Path) -> None:
        self.caminho_db = Path(caminho_db)
        self.caminho_db.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        with self._conn() as cx:
            cx.executescript(_DDL)

    @contextmanager
    def _conn(self):
        cx = sqlite3.connect(self.caminho_db)
        cx.row_factory = sqlite3.Row
        try:
            yield cx
            cx.commit()
        finally:
            cx.close()

    def salvar(self, cot: Cotacao) -> None:
        with self._lock, self._conn() as cx:
            cx.execute(
                "INSERT INTO cotacoes (material, preco_rs_kg, data, fonte) "
                "VALUES (?, ?, ?, ?)",
                (cot.material, cot.preco_rs_kg, cot.data, cot.fonte),
            )

    def ultima(self, material: str) -> Optional[Cotacao]:
        with self._conn() as cx:
            r = cx.execute(
                "SELECT material, preco_rs_kg, data, fonte FROM cotacoes "
                "WHERE material = ? ORDER BY data DESC LIMIT 1",
                (material,),
            ).fetchone()
        if r is None:
            return None
        return Cotacao(r["material"], r["preco_rs_kg"], r["data"], r["fonte"])

    def historico(self, material: str, dias: int = 30) -> List[Cotacao]:
        limite = (datetime.now() - timedelta(days=dias)).isoformat(timespec="seconds")
        with self._conn() as cx:
            rows = cx.execute(
                "SELECT material, preco_rs_kg, data, fonte FROM cotacoes "
                "WHERE material = ? AND data >= ? ORDER BY data ASC",
                (material, limite),
            ).fetchall()
        return [Cotacao(r["material"], r["preco_rs_kg"], r["data"], r["fonte"])
                for r in rows]

    def media(self, material: str, dias: int = 30) -> Optional[float]:
        hist = self.historico(material, dias)
        if not hist:
            return None
        return sum(c.preco_rs_kg for c in hist) / len(hist)


# ============================================================
# Scraper CEMPRE (com fallback gracioso)
# ============================================================

# URL pode mudar; deixamos configuravel via config.yaml.
URL_CEMPRE_PADRAO = "https://cempre.org.br/cempre-informa/precos-do-mercado/"


def _casar_material(linha_texto: str) -> Optional[str]:
    """Retorna o nome canonico se a linha mencionar algum material conhecido."""
    txt = linha_texto.lower()
    for canonico, apelidos in _APELIDOS.items():
        for ap in apelidos:
            if ap in txt:
                return canonico
    return None


def _extrair_preco(texto: str) -> Optional[float]:
    """Le um numero em formato brasileiro (1.234,56) ou ingles (1,234.56)."""
    # Procura R$ X,XX ou apenas X,XX
    m = re.search(r"R?\$?\s*([\d\.\,]+)", texto)
    if not m:
        return None
    raw = m.group(1)
    # Heuristica: se tem virgula como ultimo separador, e BR.
    if "," in raw and (raw.rfind(",") > raw.rfind(".")):
        raw = raw.replace(".", "").replace(",", ".")
    else:
        raw = raw.replace(",", "")
    try:
        valor = float(raw)
    except ValueError:
        return None
    # Filtra valores absurdos (defesa contra falso positivo do parser).
    if not (0.05 <= valor <= 50.0):
        return None
    return valor


def buscar_cempre(url: str = URL_CEMPRE_PADRAO,
                  timeout_seg: int = 10) -> Dict[str, float]:
    """Busca a tabela publica do CEMPRE e devolve {material: preco}.

    Tolerante a mudancas na estrutura: percorre todas as linhas/tabelas
    em busca de nomes conhecidos e um valor monetario na mesma linha.
    Retorna {} se nao conseguir nada (a chamadora cai no cache).
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        log.warning("requests/beautifulsoup4 nao instalados; scraper desativado.")
        return {}

    try:
        resp = requests.get(
            url, timeout=timeout_seg,
            headers={"User-Agent": "residuos-ai/1.0 (+cooperativa local)"},
        )
        resp.raise_for_status()
    except Exception as e:
        log.warning("Falha ao baixar CEMPRE: %s", e)
        return {}

    soup = BeautifulSoup(resp.text, "html.parser")
    encontrados: Dict[str, float] = {}

    # Estrategia 1: linhas de tabela com material + preco na mesma linha.
    for tr in soup.find_all("tr"):
        texto = tr.get_text(" ", strip=True)
        material = _casar_material(texto)
        if material is None:
            continue
        preco = _extrair_preco(texto)
        if preco is None:
            continue
        # Mantem o primeiro casamento (geralmente o mais relevante).
        encontrados.setdefault(material, preco)

    # Estrategia 2: paragrafos / listas (caso a pagina nao use <table>).
    if not encontrados:
        for el in soup.find_all(["li", "p"]):
            texto = el.get_text(" ", strip=True)
            material = _casar_material(texto)
            if material is None:
                continue
            preco = _extrair_preco(texto)
            if preco is None:
                continue
            encontrados.setdefault(material, preco)

    log.info("CEMPRE: %d cotacoes extraidas.", len(encontrados))
    return encontrados


# ============================================================
# Servico de cotacao (orquestra repo + scraper)
# ============================================================

class ServicoCotacao:
    """Orquestra busca, cache e alertas.

    Uso tipico:
        svc = ServicoCotacao("dados/db/cotacoes.sqlite")
        svc.atualizar_agora()           # uma execucao
        svc.iniciar_loop(intervalo_min=30)  # background
        svc.atual()                     # ultimas cotacoes
        svc.alertas()                   # alertas verdes/amarelos
    """

    def __init__(
        self,
        caminho_db: str | Path,
        url_cempre: str = URL_CEMPRE_PADRAO,
        precos_manuais: Optional[Dict[str, float]] = None,
    ) -> None:
        self.repo = RepositorioCotacao(caminho_db)
        self.url_cempre = url_cempre
        self.precos_manuais = precos_manuais or {}
        self._parar = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # ----- atualizacao -----

    def atualizar_agora(self) -> Dict[str, Cotacao]:
        """Tenta CEMPRE; usa precos manuais para os faltantes; senao, cache."""
        agora = datetime.now().isoformat(timespec="seconds")
        do_scraper = buscar_cempre(self.url_cempre)

        resultado: Dict[str, Cotacao] = {}
        for material in MATERIAIS:
            if material in do_scraper:
                cot = Cotacao(material, do_scraper[material], agora, "cempre")
                self.repo.salvar(cot)
                resultado[material] = cot
            elif material in self.precos_manuais:
                cot = Cotacao(material, float(self.precos_manuais[material]),
                              agora, "manual")
                self.repo.salvar(cot)
                resultado[material] = cot
            else:
                ult = self.repo.ultima(material)
                if ult is not None:
                    ult.defasada = True
                    ult.fonte = "cache"
                    resultado[material] = ult
                # Se nunca houve cotacao, simplesmente nao aparece.
        return resultado

    def iniciar_loop(self, intervalo_min: int = 30) -> None:
        """Atualiza em background. Idempotente (nao inicia 2x)."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._parar.clear()
        intervalo_seg = max(60, intervalo_min * 60)

        def loop():
            # Primeira atualizacao imediata, depois espera o intervalo.
            try:
                self.atualizar_agora()
            except Exception:
                log.exception("Erro na atualizacao inicial de cotacao.")
            while not self._parar.wait(intervalo_seg):
                try:
                    self.atualizar_agora()
                except Exception:
                    log.exception("Erro na atualizacao periodica de cotacao.")

        self._thread = threading.Thread(target=loop, daemon=True,
                                        name="cotacao-loop")
        self._thread.start()
        log.info("Loop de cotacao iniciado: intervalo %d min.", intervalo_min)

    def parar(self) -> None:
        self._parar.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    # ----- consulta -----

    def atual(self) -> Dict[str, Cotacao]:
        """Retorna a ultima cotacao conhecida para cada material."""
        out: Dict[str, Cotacao] = {}
        for material in MATERIAIS:
            ult = self.repo.ultima(material)
            if ult is not None:
                # Defasada se for de mais de 2h atras.
                try:
                    dt = datetime.fromisoformat(ult.data)
                    ult.defasada = (datetime.now() - dt) > timedelta(hours=2)
                except ValueError:
                    pass
                out[material] = ult
        return out

    def historico(self, material: str, dias: int = 30) -> List[Cotacao]:
        return self.repo.historico(material, dias)

    def alertas(self, limite_alta_pct: float = 10.0,
                limite_baixa_pct: float = 15.0) -> List[AlertaCotacao]:
        """Compara cotacao atual com media 30d e gera recomendacoes."""
        alertas: List[AlertaCotacao] = []
        for material, atual in self.atual().items():
            media = self.repo.media(material, dias=30)
            if media is None or media <= 0:
                continue
            variacao = 100.0 * (atual.preco_rs_kg - media) / media
            if variacao >= limite_alta_pct:
                alertas.append(AlertaCotacao(
                    material=material,
                    tipo="vender",
                    cor="verde",
                    mensagem=(f"VENDER AGORA — {material} esta "
                              f"{variacao:+.1f}% acima da media 30 dias."),
                    preco_atual=atual.preco_rs_kg,
                    media_30d=round(media, 3),
                    variacao_pct=round(variacao, 2),
                ))
            elif variacao <= -limite_baixa_pct:
                alertas.append(AlertaCotacao(
                    material=material,
                    tipo="aguardar",
                    cor="amarelo",
                    mensagem=(f"AGUARDAR — {material} esta "
                              f"{variacao:+.1f}% abaixo da media 30 dias."),
                    preco_atual=atual.preco_rs_kg,
                    media_30d=round(media, 3),
                    variacao_pct=round(variacao, 2),
                ))
        return alertas

    def recomendacao_para_relatorio(self) -> Dict:
        """Estrutura amigavel para incluir no relatorio de turno."""
        atual = self.atual()
        alertas = self.alertas()
        return {
            "data_consulta": datetime.now().isoformat(timespec="seconds"),
            "precos": {
                m: {
                    "preco_rs_kg": c.preco_rs_kg,
                    "fonte": c.fonte,
                    "data": c.data,
                    "defasada": c.defasada,
                }
                for m, c in atual.items()
            },
            "alertas": [
                {
                    "material": a.material,
                    "tipo": a.tipo,
                    "cor": a.cor,
                    "mensagem": a.mensagem,
                    "variacao_pct": a.variacao_pct,
                }
                for a in alertas
            ],
        }
