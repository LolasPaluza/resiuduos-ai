"""Emissao de certificado ESG de material reciclavel.

Gera:
- PDF com cabecalho, dados do emitente, dados do lote, impacto ambiental,
  hash imutavel e QR Code para verificacao publica.
- JSON espelho (mesmo conteudo, util para API e auditoria).

A verificacao publica e feita por GET /certificados/{hash}/verificar
(definido em api/routes.py, sem autenticacao).
"""
from __future__ import annotations

import io
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

from esg.rastreabilidade import Lote, lote_para_dict

log = logging.getLogger(__name__)


def _gerar_qr_code(conteudo: str) -> Optional[bytes]:
    """Gera PNG do QR. Retorna None se a lib nao estiver disponivel."""
    try:
        import qrcode
    except ImportError:
        log.warning("qrcode nao instalado; certificado sai sem QR.")
        return None
    img = qrcode.make(conteudo)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def gerar_certificado_pdf(
    lote: Lote,
    pasta_saida: Path,
    cidade: str = "",
    estado: str = "",
    responsavel: str = "",
    url_verificacao_base: str = "http://localhost:5000/certificados",
    logo_path: Optional[str] = None,
    validade_dias: int = 365,
) -> Optional[Path]:
    """Gera o PDF do certificado. Retorna None se reportlab indisponivel."""
    if not lote.aprovado():
        raise ValueError(
            f"Lote nao aprovado para certificacao: pureza {lote.pureza_pct:.1f}% "
            "(precisa de >= 90%)."
        )
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
        )
    except ImportError:
        log.warning("reportlab nao instalado; certificado nao foi gerado.")
        return None

    pasta_saida.mkdir(parents=True, exist_ok=True)
    hash_lote = lote.hash_canonico()
    hash_curto = hash_lote[:12].upper()
    emissao = datetime.now()
    validade = emissao + timedelta(days=validade_dias)
    nome_arq = f"CERT-{hash_curto}-{emissao.strftime('%Y%m%d')}.pdf"
    caminho = pasta_saida / nome_arq

    doc = SimpleDocTemplate(
        str(caminho),
        pagesize=A4,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
        title=f"Certificado ESG {hash_curto}",
        author="Residuos AI",
    )
    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle(
        "TituloCert", parent=estilos["Title"],
        fontSize=18, alignment=1, textColor=colors.HexColor("#1b5e20"),
        spaceAfter=6,
    )
    subtitulo = ParagraphStyle(
        "Sub", parent=estilos["Normal"],
        fontSize=10, alignment=1, textColor=colors.grey,
        spaceAfter=14,
    )
    h_secao = ParagraphStyle(
        "Secao", parent=estilos["Heading4"],
        textColor=colors.HexColor("#1b5e20"), spaceBefore=10,
    )

    historia = []

    # Cabecalho com logo opcional
    if logo_path and Path(logo_path).exists():
        try:
            historia.append(Image(logo_path, width=4 * cm, height=4 * cm))
        except Exception:
            log.warning("Falha ao incluir logo %s", logo_path)

    historia.append(Paragraph(
        "CERTIFICADO DE ORIGEM DE MATERIAL RECICLAVEL", titulo,
    ))
    historia.append(Paragraph(
        f"Numero: <b>{hash_curto}</b> &nbsp;&nbsp; "
        f"Emissao: {emissao.strftime('%d/%m/%Y')} &nbsp;&nbsp; "
        f"Validade: {validade.strftime('%d/%m/%Y')}",
        subtitulo,
    ))

    # Emitente
    historia.append(Paragraph("EMITENTE", h_secao))
    linhas_emitente = [
        ["Cooperativa:", lote.cooperativa or "-"],
        ["CNPJ:",        lote.cnpj or "-"],
        ["Cidade/UF:",   f"{cidade}/{estado}" if cidade or estado else "-"],
        ["Responsavel:", responsavel or "-"],
    ]
    historia.append(_tabela_chave_valor(linhas_emitente))

    # Material
    impacto = lote.impacto_ambiental()
    historia.append(Paragraph("MATERIAL CERTIFICADO", h_secao))
    linhas_material = [
        ["Tipo:",                 lote.material],
        ["Quantidade:",           f"{lote.quantidade_kg:.3f} kg"],
        ["Pureza do lote:",       f"{lote.pureza_pct:.1f}% "
                                  f"(rejeito {100 - lote.pureza_pct:.1f}%)"],
        ["Periodo de coleta:",    f"{_data_curta(lote.periodo_inicio)} a "
                                  f"{_data_curta(lote.periodo_fim)}"],
        ["Catadores envolvidos:", f"{lote.catadores_envolvidos} cooperados "
                                  "(sem identificacao individual)"],
    ]
    historia.append(_tabela_chave_valor(linhas_material))

    # Rastreabilidade
    historia.append(Paragraph("RASTREABILIDADE", h_secao))
    linhas_rast = [
        ["Hash do lote:", hash_lote],
        ["Turnos:",       ", ".join(lote.turnos_ids) or "-"],
        ["Verificar em:", f"{url_verificacao_base}/{hash_lote}/verificar"],
    ]
    historia.append(_tabela_chave_valor(linhas_rast))

    # Impacto ambiental
    historia.append(Paragraph("IMPACTO AMBIENTAL ESTIMADO", h_secao))
    linhas_impacto = [
        ["CO2 evitado:",        f"{impacto['co2_evitado_kg']:.1f} kg"],
        ["Equivalente arvores:", f"{impacto['arvores_equivalente']:.1f} "
                                 "arvores sequestrando CO2 por 1 ano"],
        ["Agua economizada:",    f"{impacto['agua_economizada_l']:.0f} litros"],
        ["Energia economizada:", f"{impacto['energia_kwh']:.1f} kWh"],
    ]
    historia.append(_tabela_chave_valor(linhas_impacto))

    historia.append(Spacer(1, 16))

    # QR Code de verificacao
    url_verif = f"{url_verificacao_base}/{hash_lote}/verificar"
    qr_bytes = _gerar_qr_code(url_verif)
    if qr_bytes:
        historia.append(Paragraph(
            "Escaneie para verificar a autenticidade deste certificado:",
            estilos["Normal"],
        ))
        historia.append(Image(io.BytesIO(qr_bytes),
                              width=3.5 * cm, height=3.5 * cm))
        historia.append(Paragraph(
            f"<font size=7 color='grey'>{url_verif}</font>",
            estilos["Normal"],
        ))

    historia.append(Spacer(1, 18))
    historia.append(Paragraph(
        "<font size=8 color='grey'>"
        "Este certificado e assinado pelo hash SHA256 do conteudo. "
        "Qualquer alteracao posterior invalida a verificacao. "
        "Os dados de impacto sao estimativas baseadas em coeficientes "
        "publicos (EPA, CEMPRE, MMA). Nenhum dado pessoal de catadores "
        "individuais foi armazenado ou divulgado."
        "</font>",
        estilos["Normal"],
    ))

    doc.build(historia)
    log.info("Certificado PDF salvo em %s", caminho)
    return caminho


def _data_curta(iso: str) -> str:
    if not iso:
        return "-"
    try:
        return datetime.fromisoformat(iso).strftime("%d/%m/%Y")
    except ValueError:
        return iso[:10]


def _tabela_chave_valor(linhas):
    """Cria uma tabela 2 colunas padronizada (chave a esquerda, valor a direita)."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import Table, TableStyle
    except ImportError:
        return None
    t = Table(linhas, colWidths=[5 * cm, 11 * cm], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#37474f")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def gerar_certificado_json(
    lote: Lote,
    pasta_saida: Path,
    cidade: str = "",
    estado: str = "",
    responsavel: str = "",
    validade_dias: int = 365,
) -> Path:
    """Salva espelho JSON do certificado (para API e auditoria)."""
    pasta_saida.mkdir(parents=True, exist_ok=True)
    emissao = datetime.now()
    validade = emissao + timedelta(days=validade_dias)
    hash_lote = lote.hash_canonico()

    payload = {
        "tipo": "certificado_esg_residuos",
        "versao": 1,
        "hash": hash_lote,
        "hash_curto": hash_lote[:12].upper(),
        "emissao": emissao.isoformat(timespec="seconds"),
        "validade": validade.isoformat(timespec="seconds"),
        "emitente": {
            "cooperativa": lote.cooperativa,
            "cnpj": lote.cnpj,
            "cidade": cidade,
            "estado": estado,
            "responsavel": responsavel,
        },
        "lote": lote_para_dict(lote),
    }
    caminho = pasta_saida / f"CERT-{hash_lote[:12].upper()}-{emissao.strftime('%Y%m%d')}.json"
    caminho.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    log.info("Certificado JSON salvo em %s", caminho)
    return caminho


def emitir(
    lote: Lote,
    pasta_saida: Path,
    cidade: str = "",
    estado: str = "",
    responsavel: str = "",
    url_verificacao_base: str = "http://localhost:5000/certificados",
    logo_path: Optional[str] = None,
    validade_dias: int = 365,
) -> Dict[str, Optional[str]]:
    """Atalho: gera PDF + JSON e retorna caminhos."""
    json_path = gerar_certificado_json(
        lote, pasta_saida, cidade, estado, responsavel, validade_dias,
    )
    pdf_path = gerar_certificado_pdf(
        lote, pasta_saida, cidade, estado, responsavel,
        url_verificacao_base, logo_path, validade_dias,
    )
    return {
        "hash": lote.hash_canonico(),
        "json": str(json_path),
        "pdf": str(pdf_path) if pdf_path else None,
    }


def verificar(hash_consulta: str, pasta_certificados: Path) -> Optional[Dict]:
    """Procura o certificado pelo hash e devolve o JSON espelho (ou None)."""
    if not pasta_certificados.exists():
        return None
    hash_consulta = hash_consulta.lower()
    for arq in pasta_certificados.glob("CERT-*.json"):
        try:
            d = json.loads(arq.read_text(encoding="utf-8"))
        except Exception:
            continue
        if d.get("hash", "").lower() == hash_consulta:
            # Recalcula o hash a partir do conteudo do lote e compara.
            from esg.rastreabilidade import Lote
            lote_dict = {k: v for k, v in d["lote"].items()
                         if k in Lote.__dataclass_fields__}
            try:
                lote_obj = Lote(**lote_dict)
            except TypeError:
                d["verificado"] = False
                d["motivo"] = "campos do lote nao reconstituiveis"
                return d
            d["verificado"] = lote_obj.hash_canonico() == d["hash"]
            return d
    return None
