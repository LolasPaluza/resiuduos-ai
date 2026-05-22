# Resíduos AI — Classificação Inteligente de Materiais Recicláveis

Sistema de visão computacional para **cooperativas de catadores** no Brasil. Usa uma câmera USB sobre a esteira de triagem e classifica em tempo real cada objeto em **PET, PEAD, papel, metal, orgânico ou rejeito**, ajudando o catador a reduzir a taxa de rejeição do lote sem substituir o trabalho humano.

> Roda em **Raspberry Pi 3, 4 e 5** com webcam comum e display HDMI. Sem nuvem, sem internet obrigatória.

---

## O que o sistema faz

- **Classifica em tempo real** (mínimo 10 FPS no Pi 4) com bounding box, cor e ícone por categoria.
- **Alerta sonoro** quando detecta rejeito/contaminante.
- **Dashboard** com contagens do turno, % de contaminação, FPS, tempo decorrido, gráfico de barras ao vivo.
- **Coleta automática** de frames para retreinamento; operador corrige erros com teclado numérico (1–6).
- **Relatório de turno** em JSON + PDF, opcionalmente enviado por e-mail.
- **API REST local** (`localhost:5000`) para integração futura com ERP.
- **Persistência** do estado a cada 5 min — não perde turno em queda de energia.

## Por que existe

Cooperativas perdem **R$ 3.000–6.000/mês** com lotes rejeitados pela indústria por má separação. Catadores trabalham por longas horas, sem assistência, e cometem erros por fadiga. Esse sistema atua como **assistente** — destaca o que parece errado e registra histórico de produtividade, o que abre portas para crédito, contratos ESG e relatórios para o poder público.

---

## Instalação rápida (Raspberry Pi)

```bash
git clone <seu-fork> residuos-ai
cd residuos-ai
bash setup.sh --com-modelo
```

O `setup.sh` instala dependências do sistema, cria virtualenv, instala pacotes Python, baixa o YOLOv8 nano e registra um serviço `systemd` que sobe o sistema no boot.

Para instalação detalhada, veja [`INSTALL.md`](INSTALL.md).

## Uso no dia a dia

### Iniciar manualmente
```bash
.venv/bin/python main.py
```

### Modos disponíveis
```bash
python main.py                  # normal, com webcam
python main.py --demo video.mp4 # roda sobre vídeo gravado (treino/demonstração)
python main.py --headless       # sem janela, só API + classificação
python main.py --sem-api        # desabilita a API REST
```

### Teclas na interface
| Tecla | Ação                              |
|-------|-----------------------------------|
| `1`   | Corrige última classificação para **PET**       |
| `2`   | Corrige para **PEAD**             |
| `3`   | Corrige para **papel**            |
| `4`   | Corrige para **metal**            |
| `5`   | Corrige para **orgânico**         |
| `6`   | Corrige para **rejeito**          |
| `Q`   | Sair (encerra turno e gera relatório) |

---

## Corrigir erros e retreinar o modelo

1. Durante o turno, o operador usa as teclas 1–6 para corrigir classificações erradas. Os frames corrigidos são salvos em `dados/frames/` com label no formato YOLO.
2. Ao acumular alguns dias de dados, prepare o dataset:
   ```bash
   python -m ml.preparar_dataset
   ```
   Esse script junta TrashNet + TACO + correções locais (baixe os datasets antes — links no script).
3. Rode o fine-tuning:
   ```bash
   python -m ml.retreinar --epochs 30
   ```
4. O novo modelo é copiado automaticamente para `dados/modelos/yolov8n_residuos.pt`. Reinicie o sistema (`sudo systemctl restart residuos-ai`) para usá-lo.

---

## Como interpretar os relatórios

Cada turno gera **dois arquivos** em `dados/relatorios/`:
- `relatorio_<id>.json` — dados estruturados para integração.
- `relatorio_<id>.pdf` — uma página, pronto para imprimir/enviar.

Campos principais:
- **Total processado por categoria** (contagem + peso estimado em kg).
- **Taxa de contaminação** — quantos % das detecções foram rejeito. Se passou de **10%**, aparece em vermelho.
- **Horários de pico de rejeito** — em quais janelas houve mais erro. Útil para ajustar turno, fadiga, troca de catador.
- **Comparativo** com os últimos 3 turnos.

---

## API REST

Base: `http://localhost:5000` &nbsp;&nbsp; Autenticação: header `Authorization: Bearer <token>` (token gerado pelo `setup.sh` em `config.yaml > api.token_gestor`).

| Método | Endpoint                                  | Auth?   | Descrição                                  |
|--------|-------------------------------------------|---------|--------------------------------------------|
| GET    | `/status`                                 | público | Sistema online, FPS, modelo, hardware       |
| GET    | `/turno/atual`                            | sim     | Dados do turno em andamento                 |
| POST   | `/turno/novo`                             | sim     | Inicia novo turno                           |
| POST   | `/turno/encerrar`                         | sim     | Encerra turno e gera relatório              |
| GET    | `/historico`                              | sim     | Lista de relatórios anteriores              |
| GET    | `/historico/<id>`                         | sim     | Relatório específico                        |
| GET    | `/cotacao`                                | sim     | Preços atuais por material + alertas        |
| GET    | `/cotacao/historico?material=&dias=`      | sim     | Histórico de preços (até 90 dias)          |
| GET    | `/certificados`                           | sim     | Lista de certificados ESG emitidos          |
| GET    | `/certificados/<hash>`                    | sim     | Certificado completo                        |
| POST   | `/certificados/emitir`                    | sim     | Emite certificado para um lote/janela       |
| GET    | `/certificados/<hash>/verificar`          | **público** | Verificação pública (usada pelo QR Code) |
| POST   | `/modelo/retreinar`                       | sim     | Dispara fine-tuning em background           |
| GET    | `/config`                                 | sim     | Configurações atuais (omite senhas/tokens)  |
| PUT    | `/config`                                 | sim     | Atualiza seções do config.yaml              |
| GET    | `/dados/exportar`                         | sim     | ZIP com relatórios + certificados           |

> Em ambiente local de desenvolvimento, deixar `api.token_gestor: ""` desativa a autenticação. **Nunca** use isso em produção exposta na rede.

---

## Configuração

Edite `config.yaml`. Campos principais:

```yaml
camera:
  indice: 0                # 0 = primeira webcam USB
  resolucao: [640, 480]
  fps_alvo: 10

modelo:
  caminho: dados/modelos/yolov8n_residuos.pt
  confianca_minima: 0.50
  usar_onnx: false         # true = inferência ONNX em CPU (mais rápida)

turno:
  alerta_contaminacao_pct: 10
  salvar_intervalo_min: 5

relatorio:
  email_destino: ""        # vazio = não envia
  smtp_servidor: ""
  smtp_porta: 587

api:
  porta: 5000
```

O sistema **detecta automaticamente** se está rodando em Pi 3/4/5 e ajusta resolução de inferência e FPS limites.

---

## Seus Dados

**Tudo o que o sistema guarda fica neste computador.** Nada é enviado para a internet (a não ser que vocês mudem isso no `config.yaml`).

### O que é coletado

| O que | Onde fica | Por que existe | Pode apagar? |
|---|---|---|---|
| Imagens da esteira | `dados/frames/` | Para o sistema melhorar com o tempo | Sim, a qualquer momento |
| Relatórios de turno | `dados/relatorios/` | Para mostrar produtividade e gerar provas para parceiros | Sim, mas guarde antes |
| Logs do sistema | `dados/logs/` | Para entender se algo deu errado | Sim, sempre que quiser |
| Modelo de IA | `dados/modelos/` | É o "cérebro" do sistema | Apagar quebra o sistema |

### O sistema **não** guarda:
- Nome, foto ou identificação de quem está trabalhando.
- Horário de chegada/saída de pessoas.
- Qualquer coisa que permita dizer "foi o fulano que errou".

Os relatórios falam do **lote** e do **turno**, nunca de uma pessoa.

### Exportar todos os meus dados

```bash
python -m ferramentas.exportar_meus_dados
```

Isso cria um arquivo `meus-dados-AAAA-MM-DD.zip` que vocês podem copiar para um pendrive ou enviar por e-mail. Dentro do ZIP vem um `LEIA-ME.txt` explicando cada pasta.

### Apagar todos os meus dados

```bash
python -m ferramentas.deletar_meus_dados
```

O programa pede confirmação digitada (`APAGAR TUDO`). Antes de rodar, **exporte uma cópia** se quiser guardar.

### Retenção automática

O sistema apaga sozinho **imagens** com mais de **30 dias** e **relatórios** com mais de **365 dias** (configurável em `config.yaml`):

```yaml
privacidade:
  envio_externo: false
  aviso_coleta: true
  retencao_frames_dias: 30
  retencao_relatorios_dias: 365
```

---

## Limitações do Sistema

Esse sistema **erra**. É importante saber quando confiar nele e quando não confiar.

### Taxa esperada de erro por classe

Os números abaixo são estimativas com base em fine-tuning sobre TrashNet+TACO. Cada cooperativa terá números diferentes — recomenda-se medir nas primeiras semanas:

| Categoria | Precisão esperada | Casos difíceis                                        |
|-----------|-------------------|--------------------------------------------------------|
| PET       | 85–92%            | Garrafas amassadas/coloridas, rótulos enormes          |
| PEAD      | 75–85%            | Embalagens muito sujas ou parecidas com PET            |
| Papel     | 80–90%            | Papel molhado, papelão muito amassado                  |
| Metal     | 88–95%            | Latas amassadas, metal pintado                         |
| Orgânico  | 70–85%            | Mistura de embalagem + restos                          |
| Rejeito   | 65–80%            | Material novo que o modelo nunca viu                   |

### Condições que pioram a precisão

- **Iluminação fraca** ou muito clarão direto na esteira.
- **Material úmido** ou coberto de líquido escuro.
- **Objeto fora de foco** (ajustar foco fixo da webcam ajuda).
- **Esteira muito rápida** — o frame fica borrado.
- **Categorias misturadas** num único item (ex: embalagem com restos de comida).

### Sinais na interface

- **Borda verde sólida** = sistema confia (acima de 70%).
- **Borda amarela "VERIFICAR"** = entre 50–70%, dá uma olhada.
- **Borda vermelha tracejada "INCERTO"** = abaixo de 50%, **não é contado automaticamente**, o operador decide.

### Como reportar erros

Quando o sistema errar, aperte a tecla da categoria correta (1–6). A imagem é salva com o rótulo certo para o próximo retreinamento. Quando juntar muitas correções (≥ 200 itens), rode:

```bash
python -m ml.retreinar --epochs 30
```

Acompanhe se a precisão melhora. Se piorar, restaure o modelo anterior em `dados/modelos/`.

---

## Impacto no Trabalho

**Este sistema NÃO foi feito para substituir catadores.** Ele foi feito para reduzir rejeição de lote, abrir acesso a crédito ESG e dar à cooperativa uma ferramenta de gestão que ela não tinha antes.

### Como os papéis se redistribuem com o sistema

| Antes | Com o sistema |
|---|---|
| Catador separa **e** confere sozinho, com fadiga | Catador separa; sistema confere e avisa quando algo passou errado |
| Final do dia: pesagem manual, anotação em caderno | Final do dia: relatório pronto em PDF, com kg estimado por categoria |
| Sem histórico, sem prova de produtividade | Histórico mensal exportável para bancos, prefeituras, parceiros ESG |
| Erro de classificação não é descoberto até a indústria rejeitar o lote | Erro é apontado em segundos, ainda na esteira |
| Toda a cooperativa depende da memória/atenção dos catadores experientes | Conhecimento dos catadores experientes vira dataset que treina o sistema |

### Onde vai o tempo poupado

O ganho de eficiência **não deve virar demissão**. Deve virar:

- **Mais volume processado** com a mesma equipe → mais renda por pessoa.
- **Inclusão de mais pessoas** (mães, idosos, jovens em primeiro emprego).
- **Tempo para gestão** — alguém da cooperativa pode aprender a usar os relatórios para conversar com prefeitura, parceiros e bancos.
- **Tempo para manutenção** — equipamentos cuidados duram mais.

### Aviso explícito

> Usar o sistema para **justificar demissões** contradiz seu propósito.
> Cooperativas que reduzem postos de trabalho com IA **perdem elegibilidade** a:
> - Financiamento ESG e fundos de impacto social.
> - Contratos públicos baseados em geração de emprego.
> - Programas de incentivo a economia solidária.

A planilha que comprova "preservação de postos antes e depois da IA" é mais valiosa do que qualquer ganho de eficiência.

---

## FAQ

**A câmera não abre.**
Verifique o índice: `python -m testes.test_camera --indice 1`. Em Pi, instale `v4l-utils` e rode `v4l2-ctl --list-devices`.

**O modelo está lento (<5 FPS) no Pi 4.**
Use ONNX: configure `usar_onnx: true` em `config.yaml` e gere o modelo:
```python
from ml.modelo import Modelo
m = Modelo("dados/modelos/yolov8n_residuos.pt"); m.carregar(); m.exportar_onnx()
```

**O alerta sonoro não toca.**
No Linux, garanta que `alsa-utils` está instalado e que há saída de áudio configurada. Você pode trocar pelo seu arquivo `.wav` colocando em `ui/assets/sons/` e referenciando no código.

**Como reseto um turno travado?**
Apague `dados/relatorios/turno_atual.json` e reinicie o sistema.

**O sistema funciona sem internet?**
Sim, depois de instalado. A única etapa que precisa de internet é o `setup.sh` (baixar pacotes) e o download inicial do modelo YOLOv8 nano. Após isso, opera 100% offline.

**Posso usar em outro hardware (não-Pi)?**
Sim. Em Linux/Mac/Windows com Python 3.9+ basta `pip install -r requirements.txt` e `python main.py`. O `setup.sh` é específico de sistemas Debian-like.

---

## Estrutura do código

```
residuos-ai/
├── main.py             # ponto de entrada
├── config.yaml         # configurações
├── core/               # câmera, classifier, turno, relatório, alertas
├── ui/                 # dashboard OpenCV
├── api/                # Flask
├── ml/                 # modelo, fine-tuning, preparação de dataset
├── dados/              # frames, relatórios, modelos, logs
└── testes/             # testes manuais por módulo
```

## Licença

MIT.
