# mvp.gg — Regras Globais do Projeto

## Projeto
Frontend React do **mvp.gg**, um coach de LoL com IA que analisa partidas e dá feedback personalizado.

- **Stack**: React 19 + Vite 8 + React Router v7 + Tailwind CSS 3.4
- **Backend**: FastAPI (URL via `VITE_API_URL`)
- **Deploy**: Vercel
- **Idioma da UI**: Português (BR)

## Estrutura de Pastas
```
src/
  screens/          ← Telas/páginas (1 JSX por rota)
  components/       ← Componentes reutilizáveis
  services/
    api.js          ← Wrapper da API (fetchMatches, BASE_URL)
    constants.js    ← Constantes (DDV, position maps)
    utils.js        ← Utilitários (scoring, KDA, champion pool)
```

## Rotas
| Rota | Tela | Descrição |
|------|------|-----------|
| `/` | SearchScreen | Busca por summoner (Nick#TAG) |
| `/summoner/:name/:tag` | SummonerProfileScreen | Perfil, rank, partidas, campeões |
| `/match/:matchId` | ResultsScreen | Scoreboard + coaching IA |

## Convenções de Código

### React
- Componentes funcionais com hooks (useState, useEffect, useNavigate)
- Um componente por arquivo, nome = PascalCase (ex: `CoachingSection.jsx`)
- Props desestruturadas no parâmetro da função
- Estado de loading, error e data em toda tela que faz fetch
- Navegação via `useNavigate()` com state para passar dados entre telas

### Tailwind CSS
- Estilização inline via className (nunca CSS modules)
- Mobile-first: classes base = mobile, `lg:` = desktop
- Usar as cores customizadas do tailwind.config.js (black-700, blue-400, etc.)
- Nunca usar cores hardcoded — sempre referência ao design system

### API
- Todas as chamadas via `src/services/api.js`
- Tratar erros com try/catch e mostrar mensagem ao usuário
- Nunca chamar a API diretamente com fetch() fora do api.js

### Geral
- Sem TypeScript (projeto é JavaScript puro)
- Sem bibliotecas extras de UI (não usar Material UI, Chakra, etc.)
- Animações via classes CSS do index.css (fade-up, fade-in, shimmer-bg)
- Fonte: Plus Jakarta Sans (já configurada)
- Sempre manter responsividade mobile

## Design System — Cores
```
Backgrounds:    black-900 (#060708) → black-700 (#131619) → black-600 (#1A1D21)
Cards/Navbar:   black-800 (#0D0F10) com shadow rgba(121,137,236,0.10)
Texto:          black-0 (#FFF) | black-100 (#E8E8E8) | black-200 (#CDCECF) | black-300 (#9B9C9E)
Accent:         blue-400 (#7989EC) | blue-500 (#4D62E5) | blue-600 (#3045C9)
Premium:        purple-200 (#DECCFB) | purple-500 (#7C35F1)
Vitória:        green-600 (#4AC97E)
Derrota:        red-600 (#F03A38)
Neutro:         yellow-400 (#FFD147)
Coaching IA:    gold-400 (#c89b3c)
```

## Conta de Teste
- Summoner: **natus vincere#navi1** (servidor BR)
