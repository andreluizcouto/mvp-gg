# mvp.gg — Coach de LoL com IA

## Projeto
Frontend React do mvp.gg, um coach de LoL com IA que analisa partidas e dá feedback personalizado.

**Stack:** React 19 + Vite + React Router v7 + Tailwind CSS
**Backend:** FastAPI (URL via env var `VITE_API_URL`)
**Deploy:** Vercel

## Estrutura
```
src/
  screens/
    SearchScreen.jsx              ← tela inicial, busca por summoner
    SummonerProfileScreen.jsx     ← perfil com partidas e campeões
    ResultsScreen.jsx             ← detalhes da partida + scoreboard + coaching
    LoadingScreen.jsx             ← loading animado
  components/
    CoachingSection.jsx           ← seção de coaching IA (locked/unlocked)
  services/
    api.js                        ← wrapper da API (fetchMatches, BASE_URL)
    constants.js                  ← constantes compartilhadas (DDV)
```

## Visual / Design
Design baseado no dpm.lol — Next.js + Tailwind CSS (portado para Vite + React).

- Fundo principal: `black-700` (#131619)
- Navbar/cards: `black-800` (#0D0F10) com shadow `rgba(121,137,236,0.10)`
- Accent principal: `blue-400` (#7989EC) — barras de progresso, hover, badges
- Vitória: `green-600` (#4AC97E) | Derrota: `red-600` (#F03A38)
- Destaque premium/coaching: `purple-200` (#DECCFB)
- Fonte: Plus Jakarta Sans (variável, peso 200–800)
- Classes utilitárias: `.shimmer-bg`, `.glow-purple`, `.scoreGlow`, `.text-premium`

## Fluxo do usuário
1. SearchScreen → usuário digita Nick#TAG
2. SummonerProfileScreen → perfil com rank, partidas e campeões
3. ResultsScreen → detalhes da partida, scoreboard, coaching IA

## Conta de teste
- Summoner: **natus vincere#navi1** (servidor BR)
