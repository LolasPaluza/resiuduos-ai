"""API Flask local: status, turno, historico, cotacao, certificados, config.

Autenticacao via Bearer token (config.yaml -> api.token_gestor). Rotas
publicas sem token: /status, /certificados/<hash>/verificar (necessario
para que indus tria / orgao externo cheque autenticidade do certificado
sem precisar de credencial).
"""
from __future__ import annotations

import io
import json
import logging
import threading
import zipfile
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

import yaml
from flask import Flask, Response, jsonify, request, send_file

from api.auth import requer_token

log = logging.getLogger(__name__)


def criar_app(
    classifier,
    turno,
    gerar_relatorio_callback: Callable,
    cotacao_servico=None,
    pasta_certificados: Optional[Path] = None,
    pasta_relatorios: Optional[Path] = None,
    config_path: Optional[Path] = None,
    token_gestor: str = "",
    retreinar_callback: Optional[Callable] = None,
    pasta_dados: Optional[Path] = None,
) -> Flask:
    """Constroi a app Flask. `token_gestor=""` desativa auth (dev only)."""
    app = Flask(__name__)
    proteger = requer_token(token_gestor)

    # CORS minimalista para o dashboard web (Next.js em outro host).
    # Permite qualquer origem em rotas publicas e nas autenticadas; o token
    # Bearer continua sendo a unica protecao real.
    @app.after_request
    def _cors(resp):
        origem = request.headers.get("Origin", "*")
        resp.headers["Access-Control-Allow-Origin"] = origem
        resp.headers["Access-Control-Allow-Credentials"] = "true"
        resp.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        return resp

    @app.route("/<path:_>", methods=["OPTIONS"])
    @app.route("/", methods=["OPTIONS"])
    def _cors_preflight(_=None):
        return ("", 204)

    pasta_relatorios = pasta_relatorios or Path("dados/relatorios")
    pasta_certificados = pasta_certificados or Path("dados/certificados")
    pasta_dados = pasta_dados or Path("dados")

    # ============================================================
    # Publicas
    # ============================================================

    @app.get("/status")
    def status():
        info = {
            "online": True,
            "versao_api": "1.0",
            "fps": round(classifier.fps_atual(), 2),
            "modelo": str(getattr(getattr(classifier, "modelo", None), "caminho", "—")),
            "hardware": getattr(getattr(classifier, "perfil", None), "nome", "—"),
            "modo_degradado": getattr(classifier, "degradado", False),
        }
        try:
            info["cpu_pct"] = round(classifier.cpu_pct(), 1)
        except Exception:
            pass
        return jsonify(info)

    @app.get("/certificados/<hash_cert>/verificar")
    def verificar_certificado(hash_cert):
        """Verificacao publica (sem auth) — usada por QR Code do PDF."""
        from esg.certificado import verificar
        d = verificar(hash_cert, pasta_certificados)
        if d is None:
            return jsonify({
                "encontrado": False,
                "mensagem": "Certificado nao encontrado nesta cooperativa.",
            }), 404
        # Exibe apenas o necessario para verificacao publica.
        return jsonify({
            "encontrado": True,
            "verificado": d.get("verificado", False),
            "hash": d.get("hash"),
            "emissao": d.get("emissao"),
            "validade": d.get("validade"),
            "emitente": d.get("emitente"),
            "material": d["lote"]["material"],
            "quantidade_kg": d["lote"]["quantidade_kg"],
            "pureza_pct": d["lote"]["pureza_pct"],
            "impacto": d["lote"].get("impacto"),
        })

    # ============================================================
    # Turno (protegidas)
    # ============================================================

    @app.get("/turno/atual")
    @proteger
    def turno_atual():
        t = turno.turno_atual()
        if t is None:
            return jsonify({"ativo": False}), 200
        return jsonify({
            "ativo": True,
            "turno": asdict(t),
            "contaminacao_pct": round(turno.percentual_contaminacao(), 2),
            "em_alerta": turno.em_alerta_contaminacao(),
            "kg_estimados": turno.kg_estimados(),
            "tempo_decorrido_seg": turno.tempo_decorrido_segundos(),
        })

    @app.post("/turno/novo")
    @proteger
    def turno_novo():
        if turno.turno_atual() is not None:
            return jsonify({"erro": "Turno ja em andamento."}), 409
        t = turno.iniciar()
        return jsonify({"ok": True, "turno": asdict(t)}), 201

    @app.post("/turno/encerrar")
    @proteger
    def turno_encerrar():
        if turno.turno_atual() is None:
            return jsonify({"erro": "Nenhum turno ativo."}), 409
        t = turno.encerrar()
        try:
            relatorio = gerar_relatorio_callback(t)
            return jsonify({"ok": True, "relatorio": relatorio}), 200
        except Exception as e:
            log.exception("Falha ao gerar relatorio.")
            return jsonify({"ok": True, "relatorio_erro": str(e)}), 200

    # ============================================================
    # Historico (protegidas)
    # ============================================================

    @app.get("/historico")
    @proteger
    def historico():
        arquivos = turno.listar_historico()
        resumo = []
        for arq in arquivos:
            try:
                data = json.loads(Path(arq).read_text(encoding="utf-8"))
                resumo.append({
                    "id": data.get("id"),
                    "inicio": data.get("inicio"),
                    "fim": data.get("fim"),
                    "total_deteccoes": data.get("total_deteccoes"),
                    "arquivo": arq.name,
                })
            except Exception:
                continue
        return jsonify(resumo)

    @app.get("/historico/<turno_id>")
    @proteger
    def historico_id(turno_id):
        # Procura o arquivo de turno e o relatorio gerado.
        for arq in turno.listar_historico():
            try:
                d = json.loads(arq.read_text(encoding="utf-8"))
                if d.get("id") == turno_id:
                    rel = pasta_relatorios / f"relatorio_{turno_id}.json"
                    relatorio = None
                    if rel.exists():
                        relatorio = json.loads(rel.read_text(encoding="utf-8"))
                    return jsonify({"turno": d, "relatorio": relatorio})
            except Exception:
                continue
        return jsonify({"erro": "turno nao encontrado"}), 404

    # ============================================================
    # Cotacao (protegidas; servico opcional)
    # ============================================================

    @app.get("/cotacao")
    @proteger
    def cotacao_atual():
        if cotacao_servico is None:
            return jsonify({"erro": "servico de cotacao desativado"}), 503
        atual = cotacao_servico.atual()
        alertas = cotacao_servico.alertas()
        return jsonify({
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
                {"material": a.material, "tipo": a.tipo, "cor": a.cor,
                 "mensagem": a.mensagem, "variacao_pct": a.variacao_pct}
                for a in alertas
            ],
        })

    @app.get("/cotacao/historico")
    @proteger
    def cotacao_historico():
        if cotacao_servico is None:
            return jsonify({"erro": "servico de cotacao desativado"}), 503
        material = request.args.get("material", "")
        try:
            dias = int(request.args.get("dias", 90))
        except ValueError:
            dias = 90
        if not material:
            return jsonify({"erro": "informe ?material=..."}), 400
        hist = cotacao_servico.historico(material, dias=dias)
        return jsonify([
            {"data": c.data, "preco_rs_kg": c.preco_rs_kg, "fonte": c.fonte}
            for c in hist
        ])

    # ============================================================
    # Certificados (protegidas; verificar e publico, ja definido acima)
    # ============================================================

    @app.get("/certificados")
    @proteger
    def listar_certificados():
        pasta_certificados.mkdir(parents=True, exist_ok=True)
        out = []
        for arq in sorted(pasta_certificados.glob("CERT-*.json")):
            try:
                d = json.loads(arq.read_text(encoding="utf-8"))
                out.append({
                    "hash": d.get("hash"),
                    "hash_curto": d.get("hash_curto"),
                    "emissao": d.get("emissao"),
                    "validade": d.get("validade"),
                    "material": d["lote"]["material"],
                    "quantidade_kg": d["lote"]["quantidade_kg"],
                    "arquivo_json": arq.name,
                    "arquivo_pdf": arq.name.replace(".json", ".pdf"),
                })
            except Exception:
                continue
        return jsonify(out)

    @app.get("/certificados/<hash_cert>")
    @proteger
    def obter_certificado(hash_cert):
        from esg.certificado import verificar
        d = verificar(hash_cert, pasta_certificados)
        if d is None:
            return jsonify({"erro": "nao encontrado"}), 404
        return jsonify(d)

    @app.post("/certificados/emitir")
    @proteger
    def emitir_certificado():
        """Emite certificado a partir de uma janela de relatorios.

        Body JSON:
            {
              "material": "PET",
              "desde": "2026-05-01",       # ISO, inclusive
              "ate":   "2026-05-31",       # ISO, inclusive
              "catadores_envolvidos": 8    # opcional
            }
        """
        from esg.certificado import emitir
        from esg.rastreabilidade import montar_lote_de_relatorios

        body = request.get_json(silent=True) or {}
        material = body.get("material")
        if not material:
            return jsonify({"erro": "campo 'material' obrigatorio"}), 400

        desde = body.get("desde", "")
        ate = body.get("ate", "")

        # Filtra relatorios no intervalo.
        relatorios = []
        for arq in sorted(pasta_relatorios.glob("relatorio_*.json")):
            try:
                d = json.loads(arq.read_text(encoding="utf-8"))
                inicio = d.get("inicio", "")
                if desde and inicio[:10] < desde:
                    continue
                if ate and inicio[:10] > ate:
                    continue
                relatorios.append(arq)
            except Exception:
                continue
        if not relatorios:
            return jsonify({"erro": "nenhum relatorio no intervalo"}), 404

        cfg = _ler_config(config_path) if config_path else {}
        coop = cfg.get("cooperativa", {})
        esg_cfg = cfg.get("esg", {})

        lote = montar_lote_de_relatorios(
            relatorios, material=material,
            cooperativa=coop.get("nome", ""),
            cnpj=coop.get("cnpj", ""),
            catadores_envolvidos=int(body.get("catadores_envolvidos", 0)),
            pesos_kg=cfg.get("turno", {}).get("peso_medio_kg"),
        )
        if lote is None:
            return jsonify({"erro": "nao foi possivel montar lote"}), 400
        if not lote.aprovado():
            return jsonify({
                "erro": "lote reprovado",
                "motivo": f"pureza {lote.pureza_pct:.1f}% (rejeito > 10%)",
                "lote": asdict(lote),
            }), 422

        url_base = f"http://{request.host}/certificados"
        resultado = emitir(
            lote, pasta_certificados,
            cidade=coop.get("cidade", ""),
            estado=coop.get("estado", ""),
            responsavel=coop.get("responsavel", ""),
            url_verificacao_base=url_base,
            logo_path=esg_cfg.get("logo_cooperativa") or None,
            validade_dias=int(esg_cfg.get("validade_dias", 365)),
        )
        return jsonify({"ok": True, **resultado}), 201

    # ============================================================
    # Modelo (retreinamento)
    # ============================================================

    @app.post("/modelo/retreinar")
    @proteger
    def retreinar_modelo():
        if retreinar_callback is None:
            return jsonify({"erro": "retreinamento nao configurado"}), 503
        # Roda em background para nao bloquear o request.
        threading.Thread(target=retreinar_callback, daemon=True,
                         name="retreinar").start()
        return jsonify({"ok": True, "mensagem": "retreinamento iniciado"}), 202

    # ============================================================
    # Config (protegidas; nunca devolve senhas)
    # ============================================================

    @app.get("/config")
    @proteger
    def get_config():
        if not config_path:
            return jsonify({"erro": "config nao disponivel"}), 503
        cfg = _ler_config(config_path)
        return jsonify(_remover_segredos(cfg))

    @app.put("/config")
    @proteger
    def put_config():
        if not config_path:
            return jsonify({"erro": "config nao disponivel"}), 503
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return jsonify({"erro": "body deve ser objeto JSON"}), 400
        atual = _ler_config(config_path)
        # Merge raso por secao (nao sobrescreve tudo).
        for secao, valores in body.items():
            if isinstance(valores, dict) and isinstance(atual.get(secao), dict):
                atual[secao].update(valores)
            else:
                atual[secao] = valores
        config_path.write_text(
            yaml.safe_dump(atual, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        return jsonify({"ok": True, "config": _remover_segredos(atual)})

    # ============================================================
    # Exportacao
    # ============================================================

    @app.get("/dados/exportar")
    @proteger
    def exportar_dados():
        """Devolve ZIP com relatorios + certificados (sem frames brutos)."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for sub in ["relatorios", "certificados"]:
                pasta = pasta_dados / sub
                if not pasta.exists():
                    continue
                for arq in pasta.rglob("*"):
                    if arq.is_file():
                        zf.write(arq, arcname=str(arq.relative_to(pasta_dados)))
        buf.seek(0)
        nome = f"residuos-ai-export-{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        return send_file(buf, mimetype="application/zip",
                         as_attachment=True, download_name=nome)

    return app


# ============================================================
# Helpers
# ============================================================

def _ler_config(caminho: Path) -> Dict:
    try:
        return yaml.safe_load(caminho.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


_CHAVES_SECRETAS = ("senha", "token", "password", "secret")


def _remover_segredos(cfg: Dict) -> Dict:
    """Remove campos sensiveis antes de devolver via API."""
    if not isinstance(cfg, dict):
        return cfg
    limpo = {}
    for k, v in cfg.items():
        if any(s in k.lower() for s in _CHAVES_SECRETAS):
            limpo[k] = "***"
        elif isinstance(v, dict):
            limpo[k] = _remover_segredos(v)
        else:
            limpo[k] = v
    return limpo


def iniciar_api_em_thread(app: Flask, host: str, porta: int) -> threading.Thread:
    """Sobe a API em thread daemon, sem bloquear o dashboard."""
    def alvo():
        app.run(host=host, port=porta, debug=False, use_reloader=False)
    t = threading.Thread(target=alvo, daemon=True, name="api-flask")
    t.start()
    log.info("API REST iniciada em http://%s:%s", host, porta)
    return t
