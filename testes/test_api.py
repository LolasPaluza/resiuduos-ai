"""Testes da API REST com Flask test client (offline).

Cobre endpoints principais sem subir servidor real:
- /status (publico)
- /turno/* (protegido)
- /cotacao (protegido, com servico injetado)
- /certificados/<hash>/verificar (publico, lendo da pasta)
- /config GET/PUT (sem expor senhas)
- /dados/exportar (ZIP)
"""
from __future__ import annotations

import sys
import tempfile
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.routes import criar_app  # noqa: E402
from core.cotacao import Cotacao, ServicoCotacao  # noqa: E402
from esg.certificado import emitir  # noqa: E402
from esg.rastreabilidade import Lote  # noqa: E402


def _classifier_fake():
    m = MagicMock()
    m.fps_atual.return_value = 9.5
    m.cpu_pct.return_value = 23.1
    m.modelo.caminho = "yolov8n.pt"
    m.perfil.nome = "PC"
    m.degradado = False
    return m


def _turno_fake_vazio():
    m = MagicMock()
    m.turno_atual.return_value = None
    m.listar_historico.return_value = []
    return m


def teste_status_publico():
    app = criar_app(
        classifier=_classifier_fake(),
        turno=_turno_fake_vazio(),
        gerar_relatorio_callback=lambda t: {},
        token_gestor="segredo",
    )
    c = app.test_client()
    r = c.get("/status")
    assert r.status_code == 200
    d = r.get_json()
    assert d["online"] is True and d["fps"] == 9.5
    print("[OK] /status publico")


def teste_auth_bloqueia_sem_token():
    app = criar_app(
        classifier=_classifier_fake(),
        turno=_turno_fake_vazio(),
        gerar_relatorio_callback=lambda t: {},
        token_gestor="segredo",
    )
    c = app.test_client()
    assert c.get("/turno/atual").status_code == 401
    assert c.get("/turno/atual",
                 headers={"Authorization": "Bearer errado"}).status_code == 401
    r = c.get("/turno/atual", headers={"Authorization": "Bearer segredo"})
    assert r.status_code == 200
    print("[OK] auth Bearer protege rotas sensiveis")


def teste_cotacao_endpoint():
    with tempfile.TemporaryDirectory() as tmp:
        svc = ServicoCotacao(caminho_db=Path(tmp) / "cot.sqlite")
        svc.repo.salvar(Cotacao("PET cristal", 2.50,
                                datetime.now().isoformat(timespec="seconds"),
                                "manual"))
        app = criar_app(
            classifier=_classifier_fake(),
            turno=_turno_fake_vazio(),
            gerar_relatorio_callback=lambda t: {},
            cotacao_servico=svc,
            token_gestor="",
        )
        c = app.test_client()
        d = c.get("/cotacao").get_json()
        assert "PET cristal" in d["precos"]
        assert d["precos"]["PET cristal"]["preco_rs_kg"] == 2.50

        r = c.get("/cotacao/historico?material=PET%20cristal&dias=30")
        assert r.status_code == 200
        assert len(r.get_json()) == 1
    print("[OK] /cotacao e /cotacao/historico")


def teste_verificacao_publica_de_certificado():
    with tempfile.TemporaryDirectory() as tmp:
        pasta_cert = Path(tmp)
        lote = Lote(
            material="PET", quantidade_kg=50.0,
            periodo_inicio="2026-05-01T08:00:00",
            periodo_fim="2026-05-15T17:00:00",
            turnos_ids=["T1"], pureza_pct=95.0,
            catadores_envolvidos=4, cooperativa="X", cnpj="0",
        )
        res = emitir(lote, pasta_cert)
        app = criar_app(
            classifier=_classifier_fake(),
            turno=_turno_fake_vazio(),
            gerar_relatorio_callback=lambda t: {},
            pasta_certificados=pasta_cert,
            token_gestor="segredo",
        )
        c = app.test_client()
        r = c.get(f"/certificados/{res['hash']}/verificar")  # SEM auth
        assert r.status_code == 200
        d = r.get_json()
        assert d["verificado"] is True
        assert d["material"] == "PET"
        assert c.get("/certificados").status_code == 401
        r2 = c.get("/certificados", headers={"Authorization": "Bearer segredo"})
        assert r2.status_code == 200 and len(r2.get_json()) == 1
    print("[OK] /certificados/<h>/verificar publico; /certificados protegido")


def teste_verificacao_inexistente_404():
    with tempfile.TemporaryDirectory() as tmp:
        app = criar_app(
            classifier=_classifier_fake(),
            turno=_turno_fake_vazio(),
            gerar_relatorio_callback=lambda t: {},
            pasta_certificados=Path(tmp),
            token_gestor="",
        )
        c = app.test_client()
        r = c.get("/certificados/" + "0" * 64 + "/verificar")
        assert r.status_code == 404
        assert r.get_json()["encontrado"] is False
    print("[OK] hash inexistente devolve 404")


def teste_config_get_omite_senhas():
    with tempfile.TemporaryDirectory() as tmp:
        cfg_path = Path(tmp) / "config.yaml"
        cfg_path.write_text(yaml.safe_dump({
            "cooperativa": {"nome": "Coop X"},
            "relatorio": {"smtp_senha": "TopSecret123"},
            "api": {"token_gestor": "ABCDEF"},
        }), encoding="utf-8")
        app = criar_app(
            classifier=_classifier_fake(),
            turno=_turno_fake_vazio(),
            gerar_relatorio_callback=lambda t: {},
            config_path=cfg_path,
            token_gestor="",
        )
        c = app.test_client()
        d = c.get("/config").get_json()
        assert d["cooperativa"]["nome"] == "Coop X"
        assert d["relatorio"]["smtp_senha"] == "***"
        assert d["api"]["token_gestor"] == "***"
    print("[OK] /config omite senhas e tokens")


def teste_config_put_persiste():
    with tempfile.TemporaryDirectory() as tmp:
        cfg_path = Path(tmp) / "config.yaml"
        cfg_path.write_text(yaml.safe_dump({
            "cooperativa": {"nome": "Antigo"},
        }), encoding="utf-8")
        app = criar_app(
            classifier=_classifier_fake(),
            turno=_turno_fake_vazio(),
            gerar_relatorio_callback=lambda t: {},
            config_path=cfg_path,
            token_gestor="",
        )
        c = app.test_client()
        r = c.put("/config", json={"cooperativa": {"cidade": "Ribeirao Preto"}})
        assert r.status_code == 200
        novo = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        assert novo["cooperativa"]["nome"] == "Antigo"
        assert novo["cooperativa"]["cidade"] == "Ribeirao Preto"
    print("[OK] /config PUT faz merge raso e persiste")


def teste_exportacao_zip():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / "relatorios").mkdir()
        (base / "certificados").mkdir()
        (base / "relatorios" / "relatorio_001.json").write_text(
            '{"id":"001"}', encoding="utf-8")
        (base / "certificados" / "CERT-abc.json").write_text(
            '{"hash":"abc"}', encoding="utf-8")
        app = criar_app(
            classifier=_classifier_fake(),
            turno=_turno_fake_vazio(),
            gerar_relatorio_callback=lambda t: {},
            pasta_dados=base,
            token_gestor="",
        )
        c = app.test_client()
        r = c.get("/dados/exportar")
        assert r.status_code == 200
        with zipfile.ZipFile(BytesIO(r.data)) as zf:
            nomes = zf.namelist()
            assert any("relatorio_001.json" in n for n in nomes)
            assert any("CERT-abc.json" in n for n in nomes)
    print("[OK] /dados/exportar gera ZIP")


def principal():
    teste_status_publico()
    teste_auth_bloqueia_sem_token()
    teste_cotacao_endpoint()
    teste_verificacao_publica_de_certificado()
    teste_verificacao_inexistente_404()
    teste_config_get_omite_senhas()
    teste_config_put_persiste()
    teste_exportacao_zip()
    print("\nTodos os testes da API passaram.")


if __name__ == "__main__":
    principal()
