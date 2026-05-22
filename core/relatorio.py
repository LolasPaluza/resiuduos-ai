"""Geracao de relatorio de turno em JSON + PDF e envio opcional por email."""
from __future__ import annotations

import json
import logging
import smtplib
from dataclasses import asdict
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Dict, List, Optional

from ml import CLASSES

log = logging.getLogger(__name__)


def gerar_relatorio_json(
    turno_gerenciador, turno, pasta_saida: Path,
) -> Path:
    """Salva relatorio detalhado em JSON."""
    pasta_saida.mkdir(parents=True, exist_ok=True)
    dados = {
        "turno_id": turno.id,
        "inicio": turno.inicio,
        "fim": turno.fim,
        "contagens": turno.contagens,
        "kg_estimados": turno_gerenciador.kg_estimados(),
        "total_deteccoes": turno.total_deteccoes,
        "total_frames": turno.total_frames,
        "contaminacao_pct": round(turno_gerenciador.percentual_contaminacao(), 2),
        "horarios_pico_rejeito": turno_gerenciador.horarios_pico_rejeito(),
        "comparativo": comparar_com_anteriores(turno, pasta_saida),
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
    }
    caminho = pasta_saida / f"relatorio_{turno.id}.json"
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    log.info("Relatorio JSON salvo em %s", caminho)
    return caminho


def comparar_com_anteriores(turno_atual, pasta: Path,
                            n: int = 3) -> Dict:
    """Compara contaminacao e total com ultimos N relatorios."""
    anteriores = sorted(pasta.glob("relatorio_*.json"))[-n:]
    historico = []
    for arq in anteriores:
        try:
            d = json.loads(arq.read_text(encoding="utf-8"))
            if d.get("turno_id") == turno_atual.id:
                continue
            historico.append({
                "turno_id": d.get("turno_id"),
                "total_deteccoes": d.get("total_deteccoes"),
                "contaminacao_pct": d.get("contaminacao_pct"),
            })
        except Exception:
            continue
    return {"ultimos": historico}


def gerar_relatorio_pdf(
    turno_gerenciador, turno, pasta_saida: Path,
) -> Optional[Path]:
    """Gera PDF simples com reportlab. Retorna None se reportlab nao disponivel."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
    except ImportError:
        log.warning("reportlab nao instalado; pulando PDF.")
        return None

    pasta_saida.mkdir(parents=True, exist_ok=True)
    caminho = pasta_saida / f"relatorio_{turno.id}.pdf"
    doc = SimpleDocTemplate(str(caminho), pagesize=A4)
    estilos = getSampleStyleSheet()
    historia = []

    historia.append(Paragraph(
        f"Relatório de Turno — {turno.id}", estilos["Title"],
    ))
    historia.append(Paragraph(
        f"Início: {turno.inicio} &nbsp;&nbsp; Fim: {turno.fim or '—'}",
        estilos["Normal"],
    ))
    historia.append(Spacer(1, 12))

    kg = turno_gerenciador.kg_estimados()
    linhas = [["Categoria", "Contagem", "Peso estimado (kg)"]]
    for c in CLASSES:
        linhas.append([c, turno.contagens.get(c, 0), kg.get(c, 0.0)])
    tabela = Table(linhas, hAlign="LEFT")
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    historia.append(tabela)
    historia.append(Spacer(1, 12))

    pct = turno_gerenciador.percentual_contaminacao()
    historia.append(Paragraph(
        f"<b>Taxa de contaminação:</b> {pct:.1f}%", estilos["Normal"],
    ))

    pico = turno_gerenciador.horarios_pico_rejeito()
    if pico:
        historia.append(Paragraph("<b>Horários com mais rejeito:</b>",
                                  estilos["Normal"]))
        for hora, qtd in list(pico.items())[:5]:
            historia.append(Paragraph(f"• {hora} — {qtd} rejeitos",
                                      estilos["Normal"]))

    historia.append(Spacer(1, 12))
    historia.append(Paragraph(
        f"Total de detecções: {turno.total_deteccoes}", estilos["Normal"],
    ))
    historia.append(Paragraph(
        f"Total de frames processados: {turno.total_frames}", estilos["Normal"],
    ))

    doc.build(historia)
    log.info("Relatorio PDF salvo em %s", caminho)
    return caminho


def enviar_email(
    destino: str, smtp_servidor: str, smtp_porta: int,
    usuario: str, senha: str, arquivos: List[Path], assunto: str,
) -> bool:
    """Envia relatorio por SMTP. Silencia falha mas loga."""
    try:
        msg = EmailMessage()
        msg["Subject"] = assunto
        msg["From"] = usuario or "residuos-ai@localhost"
        msg["To"] = destino
        msg.set_content(
            "Em anexo, o relatorio de turno gerado automaticamente.\n"
            "Sistema Residuos AI."
        )
        for arq in arquivos:
            if not arq.exists():
                continue
            with arq.open("rb") as f:
                msg.add_attachment(
                    f.read(),
                    maintype="application",
                    subtype="octet-stream",
                    filename=arq.name,
                )
        with smtplib.SMTP(smtp_servidor, smtp_porta) as s:
            s.starttls()
            if usuario and senha:
                s.login(usuario, senha)
            s.send_message(msg)
        log.info("Email enviado para %s", destino)
        return True
    except Exception as e:
        log.warning("Falha ao enviar email: %s", e)
        return False


def gerar_completo(
    turno_gerenciador, turno, pasta_saida: Path,
    config_email: Optional[dict] = None,
) -> Dict[str, Optional[str]]:
    """Gera JSON + PDF e opcionalmente envia por email. Retorna caminhos."""
    json_path = gerar_relatorio_json(turno_gerenciador, turno, pasta_saida)
    pdf_path = gerar_relatorio_pdf(turno_gerenciador, turno, pasta_saida)
    resultado = {
        "json": str(json_path) if json_path else None,
        "pdf": str(pdf_path) if pdf_path else None,
        "email_enviado": False,
    }
    if config_email and config_email.get("email_destino"):
        enviado = enviar_email(
            destino=config_email["email_destino"],
            smtp_servidor=config_email.get("smtp_servidor", ""),
            smtp_porta=int(config_email.get("smtp_porta", 587)),
            usuario=config_email.get("smtp_usuario", ""),
            senha=config_email.get("smtp_senha", ""),
            arquivos=[p for p in [json_path, pdf_path] if p],
            assunto=f"Relatorio de turno {turno.id}",
        )
        resultado["email_enviado"] = enviado
    return resultado
