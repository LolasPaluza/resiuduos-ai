# Guia pra gravar o vídeo demo

> Objetivo: 20–30 segundos mostrando o sistema funcionando.
> Esse vídeo vai no GitHub README, no site institucional e nos slides.

---

## Equipamento mínimo

- **Celular** com câmera (vertical ou horizontal — escolha um e mantenha)
- **Tripé / suporte** ou alguém segurando firme
- **Iluminação:** lâmpada de teto + uma lateral. Sem contraluz.
- **Pi 5 ligado** com `main.py` rodando e janela visível
- **5 objetos** pra mostrar:
  - 🍶 garrafa PET de água transparente
  - 📄 folha de papel ou caixa de papelão
  - 🥫 lata de refrigerante/cerveja
  - 🥤 embalagem de iogurte/shampoo (PEAD)
  - 🍺 garrafa de vidro (vai virar "rejeito" = correto)

---

## Roteiro (20–30s)

### Cena 1 — Abertura (3s)
**Visual:** plano fechado da câmera USB apontada pra superfície clara (mesa branca, fundo limpo). Pi visível atrás (mostra que é hardware real, não simulação).
**Texto sobreposto (legenda):** "Resíduos AI · Triagem assistida por IA"

### Cena 2 — Detecção PET (4s)
**Visual:** mão coloca a garrafa de água em frente à câmera. Foco na **tela do monitor do Pi** mostrando bounding box verde com `PET 80%+`.
**Texto sobreposto:** "PET detectado em tempo real"

### Cena 3 — Detecção Papel (4s)
**Visual:** troca pelo papel. Tela mostra `papel 80%+`.
**Texto sobreposto:** "Papel · Metal · PEAD"

### Cena 4 — Detecção Metal (3s)
**Visual:** lata. `metal XX%`.

### Cena 5 — Garrafa de vidro = rejeito (4s)
**Visual:** garrafa de cerveja. Sistema marca como `rejeito` ou ignora.
**Texto sobreposto:** "Diferencia o que a cooperativa compra do que descarta"

### Cena 6 — Dashboard web (5s)
**Visual:** corte pro **celular** mostrando `http://localhost:3000` ou `http://10.0.1.121:3000` (dashboard Next.js) com os contadores em tempo real.
**Texto sobreposto:** "Painel acessível pelo celular do gestor"

### Cena 7 — Encerramento (3s)
**Visual:** plano aberto: cooperativa, esteira (foto ilustrativa) ou tela final com texto.
**Texto sobreposto:** "100% local · sem nuvem · sem rastreamento individual"
**Logo no canto:** Resíduos AI

---

## Captura da tela do Pi (se quiser usar screen recording em vez de filmar o monitor)

No SSH do Pi, instala e roda:

```bash
sudo apt install -y ffmpeg
# Captura o que está no DISPLAY do Pi (precisa estar logado no desktop)
DISPLAY=:0 ffmpeg -f x11grab -video_size 1920x1080 -i :0.0 -r 25 -t 30 demo-pi.mp4
```

Isso grava 30s do que está aparecendo no monitor. Salva em `demo-pi.mp4`. Depois copia pro PC com:

```bash
scp lorenzo@10.0.1.121:~/projetos/residuos-ai/demo-pi.mp4 .
```

---

## Edição (rápida, em qualquer ferramenta)

### Ferramentas grátis recomendadas
- **CapCut** (PC e celular) — mais simples e tem efeitos prontos
- **DaVinci Resolve** (PC) — gratuito, qualidade profissional
- **Clipchamp** (já vem com Windows 11) — bom o suficiente

### Estrutura mínima
1. Importa os clipes na ordem do roteiro
2. Corta para que cada cena tenha 2-5 segundos
3. Adiciona **legendas grandes** com tipografia limpa (sans-serif tipo Inter ou Geist)
4. Música discreta de fundo (volume baixo) — sugestões:
   - YouTube Audio Library (filtra por "no copyright")
   - Pixabay Music (gratis, sem direitos)
   - Buscar: "calm ambient", "minimal tech", "uplifting indie"
5. Exporta 1080p MP4

---

## Onde publicar

1. **Sobre o GitHub** — sobe direto no README via tag `<video>` ou converte pra GIF (max 10MB pra hospedar no GitHub):
   ```bash
   ffmpeg -i demo.mp4 -vf "fps=15,scale=720:-1:flags=lanczos" -loop 0 demo.gif
   ```
2. **YouTube unlisted** + embed no site institucional
3. **Slides:** exporta um GIF curto e embed direto

---

## Frases que valorizam o projeto (pra usar em legenda/slide)

- "Detecta PET com **81% de precisão** em hardware de **R$ 600**"
- "Roda **100% local** — nenhum dado sai do Pi"
- "Certificado ESG **verificável** com QR Code e SHA-256"
- "Não identifica trabalhadores individualmente — apenas o lote"
- "Funciona **sem internet** depois da instalação"

---

## Antes de gravar — checklist

- [ ] Sistema rodando, modelo V4 ativo, FPS estável
- [ ] Janela do dashboard local visível e em foco
- [ ] Dashboard web acessível em outro dispositivo
- [ ] Mesa/superfície limpa
- [ ] Iluminação boa
- [ ] Objetos limpos (sem rótulos rasgados que confundem o modelo)
- [ ] Celular com bateria
- [ ] Modo "não perturbe" no celular (sem notificação aparecendo)
