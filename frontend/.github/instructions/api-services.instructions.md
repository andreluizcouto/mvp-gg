---
description: "Use when working with API calls, backend integration, fetch functions, or data services in src/services/. Covers API patterns, error handling, and data constants for mvp.gg."
applyTo: "src/services/**"
---
# Padrões de Serviços API — mvp.gg

## Arquitetura
- TODA comunicação com o backend passa por `src/services/api.js`
- Nunca usar `fetch()` diretamente em componentes ou telas
- Backend: FastAPI em `VITE_API_URL` (fallback: Render.com)

## Endpoints Existentes

```js
BASE_URL = import.meta.env.VITE_API_URL || "https://lol-coach-backend-z4b7.onrender.com"

// Busca summoner + 20 partidas recentes + stats
fetchMatches(nick)              → GET /summoner/{name}/{tag}

// Força refresh do histórico
refreshMatches(nick)            → GET /summoner/{name}/{tag}/refresh

// Análise de coaching IA para uma partida
fetchCoachingAnalysis(matchId)  → GET /coaching/{matchId}

// Batch: verifica quais partidas têm coaching disponível
fetchCoachingStatus(matchIds)   → GET /coaching/status?ids={id1,id2,...}

// Scoreboard completo da partida
fetchScoreboard(matchId, puuid) → GET /match/{matchId}/scoreboard?puuid={puuid}
```

## Padrão de Função no api.js
```js
export async function fetchAlgo(param) {
  const response = await fetch(`${BASE_URL}/endpoint/${param}`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || 'Erro ao buscar dados');
  }
  return response.json();
}
```

## Regras
- Sempre verificar `response.ok`
- Parse de erro: tentar `response.json()` com `.catch(() => null)`
- Mensagem de erro padrão em português
- Retornar sempre o `.json()` parseado
- Nunca logar dados sensíveis no console em produção

## Constantes (constants.js)
- `DDV` = versão do Data Dragon (ex: "14.24.1")
- URLs de assets: `https://ddragon.leagueoflegends.com/cdn/${DDV}/img/...`
- Maps de posição: JUNGLE, TOP, MID, ADC, SUPPORT

## Utilitários (utils.js)
- `calculateScore()` — Score de 0-100 baseado em KDA, CS/min, vision, etc.
- `formatKDA()` — Formata ratio como string
- `buildChampionPool()` — Agrega stats por campeão
- Nunca duplicar lógica de utils — reutilizar funções existentes
