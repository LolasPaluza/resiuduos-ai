# Resíduos AI — Dashboard Web

Painel de gestão em Next.js 16 (App Router) que conversa com a API REST Flask rodando no Raspberry Pi.

## Setup

```bash
cd web
npm install
cp .env.local.example .env.local
# Edita NEXT_PUBLIC_API_URL com o IP do seu Pi
npm run dev
```

Abre <http://localhost:3000>. Na primeira vez, vai em **Configuração** e cola o token Bearer (no Pi: `grep token_gestor config.yaml`).

## Páginas

| Rota | Função |
|---|---|
| `/` | Dashboard com KPIs do turno, sistema, distribuição |
| `/turno` | Turno ao vivo, contadores grandes, iniciar/encerrar |
| `/historico` | Lista de turnos encerrados |
| `/certificados` | Lista + emissão de certificado ESG |
| `/cotacao` | Preços CEMPRE + alertas de venda |
| `/configuracao` | Token Bearer, info de privacidade |

## Stack

- **Next.js 16.2** com App Router
- **React 19**
- **Tailwind CSS v4**
- **TypeScript**
- Sem biblioteca de gráficos pesada — barras CSS puras
- PWA básico (manifest + icon SVG)
