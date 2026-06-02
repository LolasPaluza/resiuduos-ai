# Manual do operador — Resíduos AI

> Este manual é pra quem **opera o sistema na esteira**. Linguagem direta, sem jargão.

---

## 1. Como ligar o sistema

1. **Plugue o Pi na tomada.**
2. **Espere 1 minuto.** Os primeiros logs aparecem na tela.
3. **Confira:**
   - Câmera mostra a esteira na tela
   - Topo da tela mostra `TURNO INICIADO`
   - Não tem nenhuma mensagem vermelha grande

Se algo não bate, vá para **Seção 7 — Quando algo dá errado**.

---

## 2. O que aparece na tela

```
┌──────────────────────────────────────────────────┐
│  TURNO INICIADO — 14:32        FPS: 12  ●ON     │
├──────────────────────────────────────────────────┤
│                                                  │
│   [vídeo da esteira ao vivo com retângulos]     │
│                                                  │
├──────────────────────────────────────────────────┤
│ PET: 47   PEAD: 23   Papel: 61                  │
│ Metal: 12  Orgânico: 8   Rejeito: 4,2%          │
└──────────────────────────────────────────────────┘
```

- **Retângulos coloridos** em volta dos objetos = o que a IA viu
- **Contadores** mostram quanto foi separado neste turno
- **Rejeito** mostra a porcentagem do lote que foi como lixo

---

## 3. As 6 categorias

| Cor | Categoria | Tecla |
|---|---|---|
| 🟦 Azul | **PET** — garrafas transparentes | `1` |
| 🟧 Laranja | **PEAD** — frascos opacos, sacos | `2` |
| 🟨 Amarelo | **Papel** — caixas, papelão | `3` |
| ⬜ Cinza | **Metal** — latas | `4` |
| 🟩 Verde | **Orgânico** — restos de comida | `5` |
| 🟥 Vermelho | **Rejeito** — não vende | `6` |

---

## 4. Quando o sistema mostrar **VERIFICAR** (amarelo)

Quer dizer: "Acho que é isso, mas não tenho certeza."

**O que fazer:**
1. Olha o objeto
2. **Aperta a tecla** da categoria certa (1 a 6)
3. Pronto. Sistema aprende com você.

> Se ignorar, sistema **não conta** o objeto. Por isso vale apertar.

---

## 5. Quando o sistema mostrar **REJEITO** (vermelho piscando)

Quer dizer: "Algo errado no lote."

**O que fazer:**
1. Olha o que está passando
2. Se for **realmente rejeito** (lixo de banheiro, vidro, etc), tira da esteira
3. Se a IA errou (era papel sujo, por exemplo), aperta `3`

> Se a **tela inteira fica vermelha**: o lote está com mais de 10% de rejeito. **Para a esteira e revisa o que está entrando.**

---

## 6. Como fechar o turno

**Aperta `0`** no teclado.

Aparece a pergunta:
```
Encerrar turno? (0 = sim · qualquer outra = cancelar)
```

**Aperta `0` de novo** pra confirmar.

O sistema:
- Salva tudo
- Gera **relatório em PDF** automaticamente
- Mostra os totais do dia

---

## 7. Quando algo dá errado

### "Tela preta"
- Confira o cabo do monitor
- Espere mais 30 segundos (sistema pode estar carregando)

### "Câmera não mostra imagem"
- Desplugue e replugue o cabo USB da webcam
- Aguarde 5 segundos. Sistema reconecta sozinho.

### "MODO MANUAL apareceu em laranja"
- A IA falhou, mas o sistema continua
- Aperte 1–6 manualmente pra cada material que separar
- Avise o suporte (sem pressa, dá pra trabalhar assim)

### "Sistema travou"
- Desliga da tomada por 10 segundos
- Liga de novo
- Aguarda 1 minuto

### "Nada funciona"
- Olha o arquivo **CONTINGÊNCIA** (na pasta) — tem instruções pra trabalhar sem o sistema
- A cooperativa funcionava antes do sistema. Continua funcionando sem ele.

---

## 8. O que o sistema **não** vê

- **Não te identifica** — não sabe quem é você
- **Não conta** quem fez o quê
- **Não manda** nada pra internet (a não ser que vocês mudem isso)
- **Não vai** justificar demissão (isso contradiz o propósito)

Os dados são da **cooperativa**, ficam no computador da cooperativa.

---

## 9. Para o gestor

**Modo gestor:** aperta `*` no teclado e digita o PIN de 4 dígitos.

Aparece:
- Histórico dos últimos 30 dias
- Comparativo entre semanas
- Receita estimada
- Lista de certificados ESG emitidos
- Configurações

> PIN padrão é **0000**. Mude no `config.yaml` antes de usar de verdade.

**Pelo celular** (na mesma Wi-Fi):
- Abre o navegador
- Vai em `http://[IP-DO-PI]:3000/painel`
- Senha = token do gestor (no `config.yaml`)

---

## 10. Cuidados diários

- **Limpe a lente da webcam** uma vez por semana (pano seco)
- **Não desligue da tomada** sem encerrar o turno antes
- **Backup automático** roda toda noite às 23h se houver pendrive plugado
- **Atualizações** quem cuida é o suporte técnico — você não precisa fazer nada

---

## Em caso de dúvida

Se você tem dúvida que este manual não responde:
- **Não tente adivinhar** — pode confundir o sistema
- Anota a dúvida no caderno
- Pergunta no suporte na próxima oportunidade

O sistema é assistente, não chefe. Você decide.
