"""Testes do modulo de certificado ESG.

Cobertura:
- hash canonico imutavel
- detecao de adulteracao
- aprovacao por taxa de rejeito
- impacto ambiental nao-nulo
- montagem de lote a partir de relatorios JSON
- emissao completa (PDF + JSON) e verificacao
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from esg.certificado import emitir, verificar  # noqa: E402
from esg.rastreabilidade import Lote, montar_lote_de_relatorios  # noqa: E402


def _lote_exemplo(material="PET", kg=120.0, pureza=95.0) -> Lote:
    return Lote(
        material=material,
        quantidade_kg=kg,
        periodo_inicio="2026-05-01T08:00:00",
        periodo_fim="2026-05-15T17:30:00",
        turnos_ids=["20260501_080000", "20260515_080000"],
        pureza_pct=pureza,
        catadores_envolvidos=8,
        cooperativa="Cooperativa Exemplo",
        cnpj="12.345.678/0001-90",
    )


def teste_hash_e_estavel():
    h1 = _lote_exemplo().hash_canonico()
    h2 = _lote_exemplo().hash_canonico()
    assert h1 == h2
    assert len(h1) == 64
    print("[OK] Hash canonico e estavel e tem 64 chars (SHA256)")


def teste_alteracao_muda_hash():
    h1 = _lote_exemplo(kg=120.0).hash_canonico()
    h2 = _lote_exemplo(kg=120.001).hash_canonico()
    assert h1 != h2
    print("[OK] Alteracao de quantidade muda o hash")


def teste_aprovacao_por_rejeito():
    assert _lote_exemplo(pureza=95.0).aprovado() is True
    assert _lote_exemplo(pureza=85.0).aprovado() is False
    print("[OK] Lote com rejeito > 10% nao e aprovado")


def teste_impacto_ambiental_positivo():
    imp = _lote_exemplo(material="PET", kg=100.0).impacto_ambiental()
    assert imp["co2_evitado_kg"] > 0
    assert imp["arvores_equivalente"] > 0
    print(f"[OK] Impacto PET 100 kg: {imp}")


def teste_montagem_de_lote():
    with tempfile.TemporaryDirectory() as tmp:
        pasta = Path(tmp)
        for i, (kg_pet, contam) in enumerate([(40.0, 5.0), (50.0, 8.0)]):
            (pasta / f"relatorio_{i}.json").write_text(json.dumps({
                "turno_id": f"T{i}",
                "inicio": f"2026-05-{i+1:02d}T08:00:00",
                "fim":    f"2026-05-{i+1:02d}T16:00:00",
                "kg_estimados": {"PET": kg_pet},
                "contagens": {"PET": int(kg_pet / 0.04)},
                "contaminacao_pct": contam,
            }), encoding="utf-8")
        relatorios = sorted(pasta.glob("relatorio_*.json"))
        lote = montar_lote_de_relatorios(
            relatorios, material="PET",
            cooperativa="Coop X", cnpj="00.000.000/0001-00",
            catadores_envolvidos=5,
        )
        assert lote is not None
        assert abs(lote.quantidade_kg - 90.0) < 1e-6
        assert abs(lote.pureza_pct - 93.5) < 1e-6  # 100 - (5+8)/2
        assert lote.turnos_ids == ["T0", "T1"]
    print("[OK] Montagem de lote agrega kg e calcula pureza")


def teste_emissao_e_verificacao():
    with tempfile.TemporaryDirectory() as tmp:
        pasta = Path(tmp)
        lote = _lote_exemplo()
        res = emitir(lote, pasta, cidade="Ribeirao Preto", estado="SP",
                     responsavel="Maria")
        assert res["json"] and Path(res["json"]).exists()
        # PDF pode nao existir se reportlab nao estiver instalado.
        if res["pdf"]:
            assert Path(res["pdf"]).exists()
            assert Path(res["pdf"]).stat().st_size > 1000

        verif = verificar(res["hash"], pasta)
        assert verif is not None
        assert verif["verificado"] is True
        assert verif["hash"] == lote.hash_canonico()
    print("[OK] Emissao gera arquivos e verifica autenticidade")


def teste_verificacao_detecta_adulteracao():
    """Se o JSON for editado a mao, verifica deve dar False."""
    with tempfile.TemporaryDirectory() as tmp:
        pasta = Path(tmp)
        lote = _lote_exemplo()
        res = emitir(lote, pasta)
        # Adultera a quantidade no JSON salvo.
        json_path = Path(res["json"])
        d = json.loads(json_path.read_text(encoding="utf-8"))
        d["lote"]["quantidade_kg"] = 999999.0
        json_path.write_text(json.dumps(d), encoding="utf-8")
        verif = verificar(res["hash"], pasta)
        assert verif is not None
        assert verif["verificado"] is False
    print("[OK] Adulteracao do JSON quebra a verificacao")


def teste_lote_reprovado_nao_emite_pdf():
    with tempfile.TemporaryDirectory() as tmp:
        lote = _lote_exemplo(pureza=80.0)  # 20% de rejeito
        try:
            emitir(lote, Path(tmp))
        except ValueError:
            print("[OK] Lote reprovado gera ValueError")
            return
        # Algumas implementacoes podem gerar so JSON; e ok desde que o PDF
        # nao saia. Aqui exigimos exception por seguranca.
        raise AssertionError("Esperava ValueError para lote reprovado.")


def principal():
    teste_hash_e_estavel()
    teste_alteracao_muda_hash()
    teste_aprovacao_por_rejeito()
    teste_impacto_ambiental_positivo()
    teste_montagem_de_lote()
    teste_emissao_e_verificacao()
    teste_verificacao_detecta_adulteracao()
    teste_lote_reprovado_nao_emite_pdf()
    print("\nTodos os testes passaram.")


if __name__ == "__main__":
    principal()
