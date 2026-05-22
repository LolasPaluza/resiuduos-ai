# Plano de Contingência — Quando o Sistema Falha

> Este documento foi escrito para o caso de **algo dar errado**. A cooperativa nunca deve parar de trabalhar porque um computador caiu.

---

## Princípio

A cooperativa funcionava **antes** desse sistema existir, e continua funcionando **sem ele**. O sistema é um **assistente**, não uma muleta. Toda decisão importante segue sendo da pessoa.

---

## 1. O sistema está rodando mas a IA falhou (não detecta nada)

**Sinal:** banner laranja na tela "MODO MANUAL — IA temporariamente indisponível".

**O que fazer:**
- Continuar trabalhando normalmente.
- Use o teclado numérico para registrar manualmente cada item separado:
  - `1` = PET, `2` = PEAD, `3` = papel, `4` = metal, `5` = orgânico, `6` = rejeito
- Os relatórios de turno continuam sendo gerados normalmente.
- Avisar o suporte técnico, sem pressa — não é urgente.

## 2. O programa fechou sozinho

**Sinal:** tela preta ou voltou para a área de trabalho.

**O que fazer:**

1. Abrir o terminal (ícone com `>_`).
2. Digitar:
   ```bash
   sudo systemctl restart residuos-ai
   ```
3. Esperar 30 segundos. Se a tela do sistema voltar, ótimo.
4. Se não voltar, vá para o item 4.

## 3. A câmera parou de mostrar imagem

**O que fazer:**

1. Verificar se o cabo USB da webcam está conectado.
2. Desconectar e reconectar o cabo.
3. Reiniciar o sistema:
   ```bash
   sudo systemctl restart residuos-ai
   ```
4. Se mesmo assim não voltar, **trabalhar sem o sistema** — separação manual como antes. Anotar no papel o que processou.

## 4. O computador (Raspberry Pi) não liga

**O que fazer:**

1. Verificar se está na tomada e se a luz vermelha do Pi acende.
2. Testar outra tomada.
3. Se a luz vermelha acende mas a tela fica preta:
   - Trocar o cabo HDMI.
   - Trocar o cartão SD pelo de backup (a cooperativa deve ter um).
4. Se nada funcionar: **trabalhar sem o sistema** até suporte técnico.

## 5. Como continuar **sem o sistema** (qualquer cenário)

A operação que existia antes do sistema continua funcionando:

- **Separação manual** pelos catadores na esteira.
- **Anotação em papel** das quantidades por categoria, por turno.
- **Pesagem manual** ao final do dia para registro.
- **Sem alertas automáticos** de rejeito — atenção redobrada do líder do turno.

Quando o sistema voltar, **digite manualmente** no relatório os totais do período em que ficou fora — entre em contato com o suporte para ajuda.

## 6. Como pedir ajuda técnica

1. Exportar os dados existentes antes de qualquer reparo:
   ```bash
   python -m ferramentas.exportar_meus_dados
   ```
2. Guardar o arquivo `meus-dados-AAAA-MM-DD.zip` em um pendrive.
3. Anotar:
   - **Quando** o problema começou (data e hora).
   - **O que** apareceu na tela (foto com o celular ajuda muito).
   - **O que** você tentou fazer.
4. Contato:
   - E-mail / WhatsApp do suporte: **(preencher na instalação)**

## 7. Backup mensal recomendado

Uma vez por mês, copie a pasta `dados/` inteira para um **HD externo ou pendrive**. Use o script:

```bash
python -m ferramentas.exportar_meus_dados
```

Guarde os ZIPs em local seguro. **Não dependa só de um único computador.**

---

## Lembrete final

Esse sistema deve ajudar, não atrapalhar. Se ele estiver atrapalhando — desligue:

```bash
sudo systemctl stop residuos-ai
```

E volte ao trabalho normal. **A cooperativa funciona sem ele.**
