# Design: Port do Design System dpm.lol → mvp.gg

**Data:** 2026-03-29
**Status:** Implementado

---

## Objetivo

Replicar o design system do dpm.lol (Next.js + Tailwind) no frontend mvp.gg (React 19 + Vite + Tailwind), mantendo identidade visual idêntica e substituindo branding "CoachApp / Coach IA" por "mvp.gg App".

---

## Design System dpm.lol Extraído

### Paleta de Cores (Tailwind custom scale)

| Token | Hex | Uso |
|---|---|---|
| `black-900` | `#060708` | Fundo absoluto |
| `black-800` | `#0D0F10` | Navbar + cards principais |
| `black-700` | `#131619` | **Fundo principal da página** |
| `black-600` | `#1A1D21` | Cards secundários |
| `black-500` | `#363A3D` | Bordas, divisores |
| `black-400` | `#686B6E` | Texto desabilitado |
| `black-300` | `#9B9C9E` | Texto secundário |
| `black-200` | `#CDCECF` | Texto padrão |
| `black-100` | `#E8E8E8` | Texto semi-destaque |
| `black-0` | `#FFFFFF` | Texto principal |
| `blue-400` | `#7989EC` | **Accent principal** |
| `blue-500` | `#4D62E5` | Accent forte (botões) |
| `blue-600` | `#3045C9` | Hover botões |
| `purple-200` | `#DECCFB` | Premium / coaching desbloqueado |
| `purple-500` | `#7C35F1` | Accent secundário |
| `green-600` | `#4AC97E` | Vitória |
| `red-600` | `#F03A38` | Derrota |
| `yellow-400` | `#FFD147` | Win rate neutro (50-60%) |

### Tipografia

- **Fonte:** Plus Jakarta Sans (variável, pesos 200–800)
- **Escala:** `bxs` 10px / `bs` 12px / `bm` 14px / `bxl` 18px / `hxs` 20px / `hxl` 32px

### Efeitos visuais

- Shadow navbar/profile header: `0 8px 9px 0px rgba(121,137,236,0.10)`
- Shadow search bar: `0 0px 10px 0px rgba(121,137,236,0.10)`
- Bordas: `border-white/5` a `border-white/10` (branco com baixa opacidade)
- Profile header: `rounded-b-[32px]`
- Search bar: `rounded-full`

---

## Arquivos Alterados

### `tailwind.config.js`
- Substituição completa da paleta `black-*`, `blue-*`, `purple-*`
- Adição de `green-600`, `red-600`, `yellow-400`, `cyan-400`
- `accent.green`: `#22C55E` → `#4AC97E`
- `accent.red`: `#EF4444` → `#F03A38`

### `src/index.css`
- `background-color`: `#0f0f23` → `#131619`
- Scrollbar: thumb azul `#7989EC` (era purple `#7C3AED`)
- `.shimmer-bg`: cores neutras escuras (era purple-tinted)
- `.scoreGlow`: glow azul (era gold)
- `.text-premium`: gradiente purple-200 → purple-500

### `src/components/Navbar.jsx`
- Header: `border-b` removido, shadow azul adicionado
- "Coach IA" → "mvp.gg App" (estilo blue-400)

### `src/screens/SummonerProfileScreen.jsx`
- `ScoreBadge`: cores gold (`#c89b3c`) → blue-400 (`#7989EC`)
- `ChampionPoolCard` win%: verde/gold/vermelho → `#4AC97E` / `#FFD147` / `#F03A38`

### `src/components/CoachingSection.jsx`
- Header accent: gold → blue-400
- Badge "CoachApp" → "mvp.gg App"
- Texto locked: "CoachApp" → "mvp.gg App", "Baixar CoachApp" → "Baixar mvp.gg App"
- Botão CTA: gradiente gold → `#4D62E5` (blue-500)
- Fonte conteúdo: DM Sans → `inherit` (Plus Jakarta Sans)

### `src/screens/LoadingScreen.jsx`
- Spinner/barra: gold (`#c89b3c`) → blue (`#7989EC` / `#4D62E5`)
- "Finalizando relatório do coach..." → "Finalizando relatório de análise..."

### `src/screens/SearchScreen.jsx`
- Subtitle: "Seu Coach de League of Legends com IA" → "Estatísticas e análise IA para League of Legends"
- Botão buscar: `bg-purple-300` → `bg-blue-500`
- Background blob: cores aleatórias → blue/purple do dpm

---

## O que NÃO mudou

- Estrutura de componentes e roteamento (sem alterações)
- Lógica de dados e API calls
- Animações `fade-up`, `fade-in`, `pulse-dot`
- Layout grid do perfil (`grid-cols-4`, `max-w-5xl`)
- Badge `🤖 IA` nos match cards
