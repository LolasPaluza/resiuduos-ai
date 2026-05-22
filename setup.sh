#!/usr/bin/env bash
# Setup do sistema Residuos AI para Raspberry Pi (Bullseye/Bookworm) e Ubuntu ARM.
# Uso:  bash setup.sh
# Opcoes:
#   --sem-servico    nao registra o servico systemd
#   --com-modelo     baixa o YOLOv8 nano base
#   --aceito-tudo    pula o prompt de consentimento (auditoria CI/CD)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

SEM_SERVICO=0
COM_MODELO=0
ACEITO_TUDO=0
for arg in "$@"; do
    case "$arg" in
        --sem-servico)  SEM_SERVICO=1 ;;
        --com-modelo)   COM_MODELO=1 ;;
        --aceito-tudo)  ACEITO_TUDO=1 ;;
    esac
done

# ---------------------------------------------------------------------------
# CONSENTIMENTO INFORMADO (Principio 7 — etica)
# ---------------------------------------------------------------------------
PROMPT_CONSENTIMENTO=$(cat <<'EOF'
==============================================
SISTEMA DE CLASSIFICACAO DE RESIDUOS - v1.0
==============================================

Antes de instalar, leia com atencao:

ESTE SISTEMA:
[v] Usa a camera para identificar tipos de material na esteira
[v] Mostra os resultados na tela para ajudar na separacao
[v] Registra quantidades por turno para gerar relatorios
[v] Salva imagens da esteira para melhorar o sistema

ESTE SISTEMA NAO:
[x] Identifica ou monitora trabalhadores individualmente
[x] Envia dados para fora da cooperativa (por padrao)
[x] Toma decisoes sem aprovacao humana
[x] Substitui ou avalia o trabalho de ninguem

Todos os dados ficam salvos neste computador.
A cooperativa tem controle total sobre eles.

Voce pode, a qualquer momento:
- Exportar todos os dados:  python -m ferramentas.exportar_meus_dados
- Apagar todos os dados:    python -m ferramentas.deletar_meus_dados

EOF
)

echo "$PROMPT_CONSENTIMENTO"

if [ "$ACEITO_TUDO" -eq 0 ]; then
    echo -n "Deseja continuar com a instalacao? (s/n): "
    read -r resp
    case "$resp" in
        s|S|sim|SIM|y|Y|yes|YES) ;;
        *)
            echo "Instalacao cancelada pelo usuario."
            exit 1
            ;;
    esac
fi

# Hash do prompt para auditoria.
if command -v sha256sum >/dev/null 2>&1; then
    HASH=$(echo "$PROMPT_CONSENTIMENTO" | sha256sum | cut -d' ' -f1)
else
    HASH="(sha256sum indisponivel)"
fi

mkdir -p dados
CONSENT_FILE="dados/CONSENTIMENTO.txt"
cat > "$CONSENT_FILE" <<EOF
COMPROVANTE DE CONSENTIMENTO - INSTALACAO
==========================================

Data e hora:      $(date "+%Y-%m-%d %H:%M:%S %Z")
Versao do sistema: 1.0
Usuario do sistema: $(id -un)
Maquina:          $(hostname)
Hash do prompt:   $HASH

O instalador confirmou ter lido e aceito o aviso de instalacao
exibido pelo setup.sh, incluindo:
- Sistema usa camera apenas sobre a esteira.
- Sistema nao monitora trabalhadores individualmente.
- Dados nao sao enviados para fora por padrao.
- Cooperativa tem controle total dos dados.

Para auditoria, este arquivo deve ser mantido junto com a
configuracao atual do sistema (config.yaml).
EOF

echo ""
echo "Consentimento registrado em $CONSENT_FILE"
echo ""


echo "==> Atualizando indices apt e instalando dependencias do sistema..."
sudo apt-get update -y
sudo apt-get install -y \
    python3 python3-pip python3-venv \
    libopenblas-dev libopenjp2-7 libtiff6 \
    libavcodec-dev libavformat-dev libswscale-dev \
    libv4l-dev libgtk-3-0 \
    alsa-utils

echo "==> Criando virtualenv em .venv..."
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Instalando dependencias Python..."
pip install --upgrade pip wheel
pip install -r requirements.txt

echo "==> Criando pastas de dados..."
mkdir -p dados/frames dados/relatorios dados/modelos dados/logs \
         dados/certificados dados/db ui/assets/sons

# Gera token_gestor aleatorio se ainda nao houver um no config.yaml.
if grep -qE '^[[:space:]]*token_gestor:[[:space:]]*""[[:space:]]*$' config.yaml 2>/dev/null; then
    TOKEN=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    # Substitui apenas a primeira ocorrencia de token_gestor: "".
    python3 - <<PY
import re, pathlib
p = pathlib.Path("config.yaml")
texto = p.read_text(encoding="utf-8")
novo = re.sub(r'(token_gestor:\s*)""', r'\1"$TOKEN"', texto, count=1)
p.write_text(novo, encoding="utf-8")
print("Token de gestor gerado e gravado em config.yaml")
PY
    echo ""
    echo "==> IMPORTANTE: anote o token de acesso da API do gestor (em config.yaml > api.token_gestor)."
    echo "    Ele eh exigido para acessar o dashboard web e os endpoints administrativos."
    echo ""
fi

if [ "$COM_MODELO" -eq 1 ]; then
    echo "==> Baixando YOLOv8 nano base..."
    python3 - <<'PY'
from ultralytics import YOLO
m = YOLO("yolov8n.pt")
import shutil, pathlib
src = pathlib.Path("yolov8n.pt")
dst = pathlib.Path("dados/modelos/yolov8n.pt")
if src.exists():
    shutil.move(str(src), str(dst))
    print(f"Modelo salvo em {dst}")
PY
fi

if [ "$SEM_SERVICO" -eq 0 ]; then
    echo "==> Registrando servico systemd (residuos-ai.service)..."
    USUARIO_ATUAL="$(id -un)"
    SERVICO=/etc/systemd/system/residuos-ai.service
    sudo tee "$SERVICO" > /dev/null <<EOF
[Unit]
Description=Sistema de Classificacao de Residuos com IA
After=network.target

[Service]
Type=simple
User=$USUARIO_ATUAL
WorkingDirectory=$SCRIPT_DIR
Environment=PYTHONUNBUFFERED=1
ExecStart=$SCRIPT_DIR/.venv/bin/python $SCRIPT_DIR/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    sudo systemctl daemon-reload
    sudo systemctl enable residuos-ai.service
    echo "Servico habilitado. Para iniciar agora:  sudo systemctl start residuos-ai"
fi

echo ""
echo "==> Setup concluido."
echo ""
echo "Proximos passos:"
echo "  1. Teste a camera:       .venv/bin/python -m testes.test_camera"
echo "  2. Teste o modelo:       .venv/bin/python -m testes.test_modelo"
echo "  3. Teste a cotacao:      .venv/bin/python -m testes.test_cotacao"
echo "  4. Teste o certificado:  .venv/bin/python -m testes.test_certificado"
echo "  5. Teste a API:          .venv/bin/python -m testes.test_api"
echo "  6. Rode o sistema:       .venv/bin/python main.py"
echo ""
echo "Acesso da API: http://localhost:5000  (token em config.yaml > api.token_gestor)"
echo "Verificacao publica de certificado: http://localhost:5000/certificados/<hash>/verificar"
echo ""
