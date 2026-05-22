"""Ponto de entrada do sistema de classificacao de residuos.

Uso:
    python main.py                # modo normal, com webcam
    python main.py --demo VIDEO   # usa video gravado em vez de webcam
    python main.py --headless     # sem UI, apenas API + classificacao
    python main.py --config X     # config alternativo
"""
from __future__ import annotations

import argparse
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

import yaml

from core.alertas import GerenciadorAlertas
from core.camera import Camera, CameraVideo, detectar_hardware
from core.classifier import Classifier
from core.cotacao import ServicoCotacao
from core.modo_degradado import ClassifierDegradado
from core.relatorio import gerar_completo
from core.retencao import aplicar_retencao
from core.turno import GerenciadorTurno
from api.routes import criar_app, iniciar_api_em_thread
from ml.modelo import Modelo
from ui.dashboard import Dashboard


def configurar_log(pasta: Path) -> None:
    pasta.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(pasta / "sistema.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def carregar_config(caminho: Path) -> dict:
    with caminho.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def construir_camera(cfg: dict, demo: Optional[str]) -> Camera:
    perfil = detectar_hardware()
    fps_alvo = min(cfg["camera"]["fps_alvo"], perfil.fps_max)
    if demo:
        return CameraVideo(caminho_video=demo, fps_alvo=fps_alvo)
    return Camera(
        indice=cfg["camera"]["indice"],
        resolucao=tuple(cfg["camera"]["resolucao"]),
        fps_alvo=fps_alvo,
    )


def construir_modelo(cfg: dict) -> Modelo:
    perfil = detectar_hardware()
    modelo = Modelo(
        caminho=cfg["modelo"]["caminho"],
        confianca_minima=cfg["modelo"]["confianca_minima"],
        iou_threshold=cfg["modelo"]["iou_threshold"],
        usar_onnx=cfg["modelo"].get("usar_onnx", False),
        caminho_onnx=cfg["modelo"].get("caminho_onnx"),
        imgsz=perfil.resolucao_inferencia,
    )
    modelo.carregar()
    return modelo


def principal():
    parser = argparse.ArgumentParser(description="Sistema de classificacao de residuos")
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    parser.add_argument("--demo", type=str, default=None,
                        help="Caminho para video de demonstracao.")
    parser.add_argument("--headless", action="store_true",
                        help="Roda sem interface grafica (apenas API).")
    parser.add_argument("--sem-api", action="store_true",
                        help="Nao sobe a API REST.")
    args = parser.parse_args()

    cfg = carregar_config(args.config)
    configurar_log(Path("dados") / "logs")
    log = logging.getLogger("main")

    camera = construir_camera(cfg, args.demo)
    camera.abrir()

    interface_cfg = cfg.get("interface", {})
    limite_incerto = interface_cfg.get("limite_incerto", 0.50)
    limite_verificar = interface_cfg.get("limite_verificar", 0.70)

    # Tenta carregar o modelo; se falhar, vai para modo degradado.
    try:
        modelo = construir_modelo(cfg)
        classifier = Classifier(
            camera=camera,
            modelo=modelo,
            pasta_frames=cfg["dados"]["pasta_frames"],
            salvar_todos=cfg["dados"].get("salvar_todos_frames", False),
            salvar_baixa_confianca=cfg["dados"].get("salvar_apenas_baixa_confianca", True),
            limite_baixa_confianca=cfg["dados"].get("limite_baixa_confianca", 0.65),
        )
    except Exception as e:
        log.exception("Falha ao carregar o modelo — entrando em MODO DEGRADADO.")
        classifier = ClassifierDegradado(
            camera=camera,
            pasta_frames=cfg["dados"]["pasta_frames"],
            motivo=f"{type(e).__name__}: {e}",
        )

    turno = GerenciadorTurno(
        pasta_estado=cfg["dados"]["pasta_relatorios"],
        intervalo_salvar_seg=cfg["turno"]["salvar_intervalo_min"] * 60,
        alerta_contaminacao_pct=cfg["turno"]["alerta_contaminacao_pct"],
        pesos_kg=cfg["turno"].get("peso_medio_kg"),
        limite_incerto=limite_incerto,
    )
    if turno.turno_atual() is None:
        turno.iniciar()
    alertas = GerenciadorAlertas()

    # Retencao automatica de dados (P2 — Dados pertencem a cooperativa).
    privacidade = cfg.get("privacidade", {})
    aplicar_retencao(
        pasta_frames=Path(cfg["dados"]["pasta_frames"]),
        pasta_relatorios=Path(cfg["dados"]["pasta_relatorios"]),
        dias_frames=privacidade.get("retencao_frames_dias", 30),
        dias_relatorios=privacidade.get("retencao_relatorios_dias", 365),
    )
    if privacidade.get("envio_externo", False):
        log.warning("ATENCAO: envio_externo=true. Verifique configuracao com a cooperativa.")

    def gerar_relatorio_callback(t):
        return gerar_completo(
            turno_gerenciador=turno,
            turno=t,
            pasta_saida=Path(cfg["dados"]["pasta_relatorios"]),
            config_email=cfg.get("relatorio"),
        )

    # Servico de cotacao (opcional — sobe loop em background se configurado).
    cotacao_cfg = cfg.get("cotacao", {})
    cotacao_servico = None
    if cotacao_cfg.get("ativo", True):
        cotacao_servico = ServicoCotacao(
            caminho_db=Path(cfg["dados"].get("pasta_db", "dados/db")) / "cotacoes.sqlite",
            url_cempre=cotacao_cfg.get("url_cempre", "https://cempre.org.br/cempre-informa/precos-do-mercado/"),
            precos_manuais=cotacao_cfg.get("precos_manuais") or {},
        )
        cotacao_servico.iniciar_loop(
            intervalo_min=int(cotacao_cfg.get("atualizar_intervalo_min", 30)),
        )

    if not args.sem_api:
        app = criar_app(
            classifier=classifier,
            turno=turno,
            gerar_relatorio_callback=gerar_relatorio_callback,
            cotacao_servico=cotacao_servico,
            pasta_certificados=Path(cfg["dados"].get("pasta_certificados",
                                                     "dados/certificados")),
            pasta_relatorios=Path(cfg["dados"]["pasta_relatorios"]),
            pasta_dados=Path("dados"),
            config_path=args.config,
            token_gestor=cfg.get("api", {}).get("token_gestor", "") or "",
        )
        iniciar_api_em_thread(app, cfg["api"]["host"], cfg["api"]["porta"])

    def encerrar(*_):
        log.info("Encerrando sistema...")
        try:
            t = turno.turno_atual()
            if t is not None:
                t_final = turno.encerrar()
                gerar_relatorio_callback(t_final)
        finally:
            camera.fechar()
            sys.exit(0)

    signal.signal(signal.SIGINT, encerrar)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, encerrar)

    if args.headless:
        log.info("Modo headless: pressione Ctrl+C para encerrar.")
        for frame, deteccoes in classifier.stream():
            if deteccoes:
                turno.registrar(deteccoes)
                if any(d.classe == "rejeito" for d in deteccoes):
                    alertas.alertar_rejeito()
    else:
        dashboard = Dashboard(
            classifier=classifier,
            turno=turno,
            alertas=alertas,
            tema=interface_cfg.get("tema", "escuro"),
            fonte_tamanho=interface_cfg.get("fonte_tamanho", 28),
            alto_contraste=interface_cfg.get("alto_contraste", False),
            limite_verificar=limite_verificar,
            limite_incerto=limite_incerto,
        )
        try:
            dashboard.executar()
        finally:
            encerrar()


if __name__ == "__main__":
    principal()
