"""Cadeia de custodia: agrega turnos em lotes certificaveis.

Um lote = conjunto de turnos do mesmo material em uma janela de datas,
com taxa de rejeito agregada abaixo de um limite (default 10%).
Hash SHA256 sobre os campos canonicos torna o lote imutavel apos
emissao do certificado.

Etica: nenhum dos campos identifica catador individual.
Apenas contagem agregada de cooperados envolvidos no periodo.
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger(__name__)


# Fatores aproximados de impacto ambiental por kg reciclado.
# Fontes: EPA WARM, CEMPRE, MMA (valores conservadores).
# Manter em modulo para serem citaveis no certificado.
FATORES_IMPACTO = {
    # material: (kg CO2 evitado, litros agua economizada, kWh energia)
    "PET":      (2.50, 28.0, 6.0),
    "PEAD":     (1.80, 22.0, 5.5),
    "papel":    (1.10, 26.0, 4.1),
    "metal":    (1.50, 40.0, 4.0),
    "Aluminio": (9.10, 1000.0, 14.0),   # aluminio tem impacto altissimo
    "organico": (0.30, 2.0, 0.4),
    "rejeito":  (0.00, 0.0, 0.0),
}

# Quantas arvores equivalem a 1 kg de CO2 evitado por ano.
# Uma arvore adulta sequestra ~22 kg CO2/ano (FAO/IPCC).
ARVORE_KG_CO2_ANO = 22.0


@dataclass
class Lote:
    """Lote de material reciclavel pronto para certificacao."""
    material: str
    quantidade_kg: float
    periodo_inicio: str         # ISO date
    periodo_fim: str            # ISO date
    turnos_ids: List[str] = field(default_factory=list)
    pureza_pct: float = 100.0   # 100 - taxa de rejeito media
    catadores_envolvidos: int = 0
    cooperativa: str = ""
    cnpj: str = ""

    def aprovado(self, limite_rejeito_pct: float = 10.0) -> bool:
        """Lote so pode virar certificado se taxa de rejeito <= limite."""
        return (100.0 - self.pureza_pct) <= limite_rejeito_pct

    def hash_canonico(self) -> str:
        """SHA256 sobre representacao canonica (ordenada). Imutavel."""
        canonico = {
            "material": self.material,
            "quantidade_kg": round(self.quantidade_kg, 4),
            "periodo_inicio": self.periodo_inicio,
            "periodo_fim": self.periodo_fim,
            "turnos_ids": sorted(self.turnos_ids),
            "pureza_pct": round(self.pureza_pct, 2),
            "catadores_envolvidos": self.catadores_envolvidos,
            "cooperativa": self.cooperativa,
            "cnpj": self.cnpj,
        }
        bruto = json.dumps(canonico, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(bruto.encode("utf-8")).hexdigest()

    def impacto_ambiental(self) -> Dict[str, float]:
        """Calcula CO2/agua/energia/arvores equivalentes."""
        co2, agua, energia = FATORES_IMPACTO.get(
            self.material, (0.0, 0.0, 0.0),
        )
        co2_total = co2 * self.quantidade_kg
        return {
            "co2_evitado_kg":     round(co2_total, 2),
            "agua_economizada_l": round(agua * self.quantidade_kg, 1),
            "energia_kwh":        round(energia * self.quantidade_kg, 2),
            "arvores_equivalente": round(co2_total / ARVORE_KG_CO2_ANO, 1),
        }


def montar_lote_de_relatorios(
    relatorios_json: List[Path],
    material: str,
    cooperativa: str = "",
    cnpj: str = "",
    catadores_envolvidos: int = 0,
    pesos_kg: Optional[Dict[str, float]] = None,
) -> Optional[Lote]:
    """Le relatorios de turno (JSON) e agrega em um lote do material dado.

    Cada relatorio JSON deve ter as chaves geradas por core/relatorio.py:
    turno_id, inicio, fim, contagens, kg_estimados, contaminacao_pct.

    Se houver relatorios sem o material, sao ignorados. Se nenhum
    relatorio contribuir, retorna None.
    """
    pesos_kg = pesos_kg or {}
    total_kg = 0.0
    soma_contaminacao = 0.0
    n = 0
    turnos = []
    inicios: List[str] = []
    fins: List[str] = []

    for arq in relatorios_json:
        try:
            d = json.loads(arq.read_text(encoding="utf-8"))
        except Exception:
            log.warning("Relatorio invalido: %s", arq)
            continue
        kg_dict = d.get("kg_estimados", {})
        kg_material = float(kg_dict.get(material, 0.0))
        if kg_material <= 0:
            # Tenta pelo contagem * peso medio se kg_estimados nao tem.
            contagens = d.get("contagens", {})
            kg_material = float(contagens.get(material, 0)) * pesos_kg.get(material, 0.0)
        if kg_material <= 0:
            continue
        total_kg += kg_material
        soma_contaminacao += float(d.get("contaminacao_pct", 0.0))
        n += 1
        turnos.append(d.get("turno_id", arq.stem))
        if d.get("inicio"):
            inicios.append(d["inicio"])
        if d.get("fim"):
            fins.append(d["fim"])

    if n == 0:
        return None

    pureza = max(0.0, 100.0 - (soma_contaminacao / n))
    return Lote(
        material=material,
        quantidade_kg=round(total_kg, 3),
        periodo_inicio=min(inicios) if inicios else "",
        periodo_fim=max(fins) if fins else "",
        turnos_ids=turnos,
        pureza_pct=round(pureza, 2),
        catadores_envolvidos=catadores_envolvidos,
        cooperativa=cooperativa,
        cnpj=cnpj,
    )


def lote_para_dict(lote: Lote) -> Dict:
    """Serializa lote + impacto + hash para uso em PDF/JSON/API."""
    d = asdict(lote)
    d["hash"] = lote.hash_canonico()
    d["impacto"] = lote.impacto_ambiental()
    d["aprovado"] = lote.aprovado()
    return d
