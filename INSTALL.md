# Guia de Instalação — Passo a Passo

Este guia foi escrito para uma pessoa **sem experiência técnica**. Siga em ordem. Não pule passos.

## O que você precisa

1. **Raspberry Pi 4 ou 5** (funciona em Pi 3, mas fica lento). Cartão SD de 32 GB ou mais.
2. **Webcam USB** comum (qualquer uma que apareça como `/dev/video0`).
3. **Monitor ou TV** com cabo HDMI.
4. **Teclado USB** (mouse não é necessário).
5. **Acesso à internet** apenas para a instalação inicial. Depois funciona sem.

---

## Passo 1 — Instalar o Raspberry Pi OS

1. Baixe o **Raspberry Pi Imager**: https://www.raspberrypi.com/software/
2. Grave a versão **Raspberry Pi OS (64-bit) — Bookworm** no cartão SD.
3. Coloque o cartão no Pi, ligue na TV/monitor e na tomada.
4. Siga o assistente inicial (idioma, Wi-Fi, senha).

## Passo 2 — Abrir o Terminal

No menu da barra superior, clique no ícone preto com `>_`. Vai abrir uma janela onde você digita comandos.

## Passo 3 — Baixar o sistema

Cole o comando abaixo no terminal (botão direito > Colar):

```bash
git clone https://github.com/SEU-USUARIO/residuos-ai.git
cd residuos-ai
```

Se você não tem o repositório no GitHub ainda, copie os arquivos por pendrive para a pasta `/home/SEU-USUARIO/residuos-ai`.

## Passo 4 — Rodar o instalador

```bash
bash setup.sh --com-modelo
```

Esse comando demora **15–30 minutos**. Ele vai:
- Instalar bibliotecas do sistema (`apt-get`).
- Criar um ambiente Python isolado (`.venv`).
- Instalar todas as dependências Python.
- Baixar o modelo de IA YOLOv8 nano.
- Registrar o sistema para iniciar **automaticamente quando o Pi liga**.

Se aparecer pergunta `[Y/n]`, aperte **Enter**.

## Passo 5 — Testar a câmera

Plug a webcam USB. Depois rode:

```bash
.venv/bin/python -m testes.test_camera --mostrar
```

Vai abrir uma janela com o vídeo. Se aparecer, **sua câmera está OK**. Aperte `Q` para fechar.

Se aparecer erro:
- Confira se a webcam está conectada.
- Tente `--indice 1` (talvez seja a segunda câmera).
- Rode `v4l2-ctl --list-devices` para ver as câmeras disponíveis (instale com `sudo apt install v4l-utils` se preciso).

## Passo 6 — Testar o modelo

```bash
.venv/bin/python -m testes.test_modelo
```

Vai imprimir `[OK] Inferencia completou em XXms`. Se aparecer isso, **a IA carrega e funciona**.

## Passo 7 — Rodar o sistema completo

```bash
.venv/bin/python main.py
```

Uma janela em tela cheia aparece com:
- O vídeo da câmera com bounding boxes coloridos.
- Painel à direita com contagens, % de contaminação, FPS.
- Atalhos no rodapé.

Para encerrar: aperte **Q**.

## Passo 8 — Fazer iniciar sozinho no boot

Como o `setup.sh` já registrou o serviço, basta:

```bash
sudo systemctl start residuos-ai
```

Para conferir se está rodando:

```bash
sudo systemctl status residuos-ai
```

E para reiniciar o Pi:

```bash
sudo reboot
```

Quando ligar de novo, o sistema sobe sozinho.

---

## Problemas comuns

### "Permission denied" ao rodar `setup.sh`
```bash
chmod +x setup.sh
bash setup.sh --com-modelo
```

### A tela fica preta ao iniciar o sistema
A interface gráfica precisa de uma sessão de usuário ativa. Não rode o sistema via SSH puro — ou use `--headless`, ou ative `XDG_SESSION_TYPE=x11` no serviço.

### A câmera é detectada mas o vídeo trava
- Pode ser USB 2.0 com pouca banda. Tente reduzir resolução em `config.yaml`:
  ```yaml
  camera:
    resolucao: [320, 240]
  ```

### O modelo está muito lento
- Em Pi 3 ou 4, exporte para ONNX e ative no config:
  ```python
  from ml.modelo import Modelo
  m = Modelo("dados/modelos/yolov8n.pt"); m.carregar(); m.exportar_onnx()
  ```
  E em `config.yaml`:
  ```yaml
  modelo:
    usar_onnx: true
  ```

### Quero atualizar o sistema com novo modelo treinado
```bash
git pull
.venv/bin/pip install -r requirements.txt
sudo systemctl restart residuos-ai
```

---

## Checklist final

- [ ] Pi liga e mostra a tela.
- [ ] Webcam abre em `testes.test_camera`.
- [ ] Modelo carrega em `testes.test_modelo`.
- [ ] `main.py` exibe a interface com câmera ao vivo.
- [ ] `sudo systemctl status residuos-ai` mostra `active (running)`.
- [ ] Após `sudo reboot`, o sistema sobe sozinho.

Se algum item falhar, veja a seção FAQ do `README.md`.
