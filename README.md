# Resíduos AI

> Visão computacional **assistiva** para cooperativas de catadores de materiais recicláveis no Brasil.

![Status](https://img.shields.io/badge/status-funcional-success)
![Hardware](https://img.shields.io/badge/hardware-Raspberry%20Pi%205-c51a4a)
![Modelo](https://img.shields.io/badge/IA-YOLOv8n-blue)
![Backend](https://img.shields.io/badge/backend-Flask-000)
![Licença](https://img.shields.io/badge/licença-MIT-green)

Um sistema que **assiste** o catador de cooperativa a separar materiais recicláveis com mais precisão e gera **rastreabilidade ESG** verificável — sem substituir a pessoa, sem mandar dados pra nuvem, sem monitorar trabalhadores individualmente.

---

## O problema

Cooperativas de catadores no Brasil perdem **R$ 3.000–6.000 por mês** com lotes rejeitados pela indústria por causa de erros de separação. São exploradas por atravessadores que conhecem os preços de mercado em tempo real — elas, não. Os catadores trabalham longas horas sem assistência técnica nenhuma.

## A solução

Uma câmera USB sobre a esteira + um Raspberry Pi 5 + IA local que:

- 🎯 **Classifica em tempo real** cada objeto em PET, PEAD, papel, metal, orgânico ou rejeito
- 📊 **Conta e pesa** o lote do turno automaticamente
- 💰 **Busca cotações reais** no CEMPRE e recomenda quando vender (>10% acima da média → "vender agora")
- 📜 **Emite certificado ESG** com QR Code e hash SHA-256 — comprova quanto CO₂ a cooperativa evitou (vendável pra indústrias com meta ambiental)
- 🛡️ **Roda 100% local** — nenhum dado sai do Pi por padrão
- 👤 **Nunca identifica trabalhadores individualmente** — só conta o lote

## Demo

> 🎥 *Vídeo demo em breve.*

| Antes (modelo COCO base) | Depois (fine-tuned 5800 imagens) |
|---|---|
| Pessoa → "rejeito" 🙃 | Garrafa PET → `PET 81%` ✅ |
| Garrafa → "bottle" (genérico) | Folha de papel → `papel 84%` ✅ |
| 80 classes genéricas | 6 classes do mercado de reciclagem |

## Stack

```
Hardware:    Raspberry Pi 5 + webcam USB + monitor HDMI
IA:          YOLOv8 nano (Ultralytics) com fine-tuning em CPU
Datasets:    TACO (1500 imgs) + TrashNet (2500 imgs) = ~5800 imgs com bbox
Backend:     Python 3.13 + Flask + SQLite
Frontend:    Next.js + Tailwind (dashboard web — em desenvolvimento)
Relatórios:  ReportLab (PDF) + JSON
Cotação:     Scraping CEMPRE + cache SQLite
Certificado: PDF + QR Code + SHA-256 imutável
Auth API:    Bearer token (hmac.compare_digest, timing-safe)
```

## Métricas do modelo (V4 — 100 epochs, CPU i7)

| Classe | mAP50 | Notas |
|---|---|---|
| **PET** | **0.81** 🔥 | Garrafas transparentes — performance forte |
| **papel** | **0.84** 🔥 | Folhas, papelão, livros |
| **metal** | **0.63** ✅ | Latas, tampas metálicas |
| PEAD | 0.22 | Datasets têm poucos exemplos — melhora com correções do operador |
| rejeito | 0.39 | Default razoável |
| orgânico | 0.00 | Dataset não cobre (intencional — cooperativa não compra) |
| **Total (mAP50)** | **0.48** | |

> Performance limitada pela quantidade/diversidade do dataset público. Próximo passo: coletar imagens reais da cooperativa via correções do operador (já implementado — tecla 1-6 corrige e salva pra retreinamento).

## Princípios éticos não-negociáveis

Esse projeto foi pensado **pelos** catadores, não **sobre** eles. Sete regras que valem mais que decisões técnicas:

1. **Assiste, nunca julga** — métricas são do lote, nunca da pessoa
2. **Dados ficam na cooperativa** — `envio_externo: false` é o padrão
3. **Transparência do modelo** — confiança sempre visível (badge amarelo "VERIFICAR" abaixo de 70%)
4. **Modo degradado obrigatório** — IA pode falhar, o trabalho continua
5. **Redistribuição, não eliminação** — sistema não justifica demissões
6. **Acessibilidade real** — operável só com teclado numérico, fontes ≥ 28px
7. **Consentimento informado** — `setup.sh` exibe termo em PT-BR claro antes de instalar

Mais detalhes em [`docs/USO.md`](docs/USO.md#impacto-no-trabalho).

## API REST

16 endpoints (autenticados via Bearer token, exceto verificação pública de certificado):

```
GET  /status                          # publico — saude do sistema
GET  /turno/atual                     # dados do turno em andamento
POST /turno/novo / /encerrar          # ciclo de vida do turno
GET  /historico   /historico/<id>     # relatorios anteriores
GET  /cotacao    /cotacao/historico   # precos do CEMPRE
GET  /certificados                    # lista ESG emitidos
POST /certificados/emitir             # emite ESG novo
GET  /certificados/<hash>/verificar   # PUBLICO — QR Code aponta aqui
POST /modelo/retreinar                # fine-tuning com correcoes locais
GET/PUT /config                       # nunca devolve senhas
GET  /dados/exportar                  # ZIP com tudo
```

## Instalação

```bash
git clone https://github.com/LolasPaluza/residuos-ai.git
cd residuos-ai
bash setup.sh --com-modelo
```

O `setup.sh` cuida de tudo: termo de consentimento em PT-BR, instalação de dependências do sistema (libopenblas, libv4l, etc), criação do virtualenv, download do YOLOv8n base, geração automática de token de gestor, registro do serviço `systemd` pra subir no boot.

Detalhes operacionais em [`docs/USO.md`](docs/USO.md).

## Estrutura

```
residuos-ai/
├── core/         → camera, classifier, turno, alertas, cotacao, modo_degradado
├── ml/           → modelo YOLOv8, preparar dataset, retreinar
├── esg/          → certificado ESG, rastreabilidade (hash SHA-256)
├── api/          → Flask REST + Bearer auth
├── ui/           → dashboard local OpenCV
├── web/          → Next.js (em desenvolvimento)
├── ferramentas/  → exportar / deletar dados (LGPD-friendly)
├── testes/       → 21 testes (5 cotação + 8 certificado + 8 API)
└── docs/         → USO.md (manual operacional completo)
```

## Status do projeto

- [x] Etapas 1–9: câmera, IA, classificador, alertas, dashboard local, turno, relatório PDF, cotação CEMPRE, certificado ESG
- [x] Etapa 10a: API REST completa com 16 endpoints
- [x] Etapa 11: modo degradado + retreinamento
- [x] Etapa 12: setup.sh com consentimento + documentação
- [x] Tracking + dedup robusto por IOU (não conta a mesma garrafa 30x)
- [x] Modelo V4 fine-tuned (TACO + TrashNet, 100 epochs)
- [ ] Etapa 10b: dashboard web Next.js
- [ ] Vídeo demo

## Autor

Lorenzo Papagano — projeto desenvolvido como estudo de visão computacional aplicada a impacto social.

## Licença

MIT — uso comercial e acadêmico permitidos. Crédito apreciado.
