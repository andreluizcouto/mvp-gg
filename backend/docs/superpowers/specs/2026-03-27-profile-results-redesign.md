# Design: Redesign de Perfil e Resultados (P6)

**Data:** 2026-03-27
**Status:** Aprovado

---

## Visão Geral

Redesenhar SummonerProfileScreen e ResultsScreen para ficarem mais próximas visualmente de dpm.lol e u.gg: cards de partida com itens e barra de dano, scoreboard completo dos dois times na página da partida, sinergia expandida e layout mais denso.

---

## Arquitetura

```
Backend (ProjectB/main.py)
  └── GET /match/{match_id}/scoreboard  ← novo
  └── GET /summoner/:nick (existente)   ← adicionar items + total_damage no MatchHistoryItem

Frontend (ProjectB-frontend)
  └── SummonerProfileScreen.jsx         ← redesenho: header + cards + abas
  └── ResultsScreen.jsx                 ← redesenho: scoreboard + sinergia
  └── src/services/api.js               ← adicionar fetchScoreboard
```

---

## Backend

### Modificar MatchHistoryItem

Adicionar ao schema existente:

```python
items: list[int] = []          # [item0, item1, item2, item3, item4, item5, item6]
total_damage: int = 0          # totalDamageDealtToChampions
```

Preencher em `fetch_match_details`:

```python
items = [
    participant.get(f"item{i}", 0)
    for i in range(7)
]
total_damage = participant.get("totalDamageDealtToChampions", 0)
```

### Novo endpoint GET /match/{match_id}/scoreboard

Busca dados completos de todos os 10 participantes de uma partida.

**Request:** `GET /match/BR1_123456/scoreboard`

**Response:**
```json
{
  "match_id": "BR1_123456",
  "duration_min": 32,
  "teams": [
    {
      "side": "blue",
      "win": true,
      "players": [
        {
          "puuid": "abc...",
          "summoner_name": "natus vincere",
          "champion": "Viktor",
          "position": "MIDDLE",
          "kills": 8,
          "deaths": 3,
          "assists": 11,
          "cs": 231,
          "cs_per_min": 7.2,
          "total_damage": 34521,
          "damage_share_pct": 28.4,
          "gold_earned": 14200,
          "vision_score": 34,
          "items": [3152, 3157, 3135, 3145, 3089, 3020, 3364],
          "summoner1_id": 4,
          "summoner2_id": 14,
          "is_target": true
        }
      ]
    },
    {
      "side": "red",
      "win": false,
      "players": [...]
    }
  ]
}
```

Parâmetro opcional `?puuid=abc...` para marcar `is_target` no jogador correto. Se não enviado, nenhum jogador é marcado como target.

---

## Frontend — SummonerProfileScreen

### Header
Mantém o layout atual (emblema + nome + rank) mas compacta para liberar espaço. Adicionar:
- LP explícito (ex: "Gold IV — 67 LP")
- Win rate em % com W/L numérico

### Abas
Duas abas acima da lista de partidas:
- **Partidas** — lista existente (padrão)
- **Campeões** — champion pool (seção que já existe, só muda para aba)

### Match Cards — novo layout

Layout em duas linhas compactas:

**Linha 1:**
- Ícone do campeão (44px) + nome do campeão + badge posição
- K/D/A em destaque
- Resultado VITÓRIA/DERROTA + duração
- ScoreBadge dourado (existente)
- Badge 🤖 IA (existente)

**Linha 2:**
- 7 ícones de itens (24px cada, slots vazios mostram fundo escuro)
- Barra de dano relativo ao time (damage_share_pct como largura)
- CS/min · Visão
- Mini-time: 5 ícones de campeão aliados (20px)

Ícones de itens via DDragon:
```
https://ddragon.leagueoflegends.com/cdn/14.24.1/img/item/{itemId}.png
```
Item 0 = slot vazio (não renderiza imagem).

---

## Frontend — ResultsScreen

### Scoreboard completo

Substitui o bloco de header atual (champion icon + player name). Mostra os dois times.

Cada time em uma seção com label "Time Azul" / "Time Vermelho". Cada linha de jogador:

```
[Ícone campeão] [Nome]    K/D/A    CS   [Barra dano] [7 itens]
```

O jogador target (`is_target: true`) tem fundo levemente destacado (borda dourada ou fundo diferente).

Em mobile: layout compacto, itens menores (18px), nome truncado.

### Sinergia expandida

Substituir o bloco "jogou com" atual por uma seção "Sinergia da Partida":
- Mostra o aliado de maior sinergia pela posição (lógica existente: COMBO_ROLE)
- Ícone do campeão + nome + posição
- Label descritivo: "Duo de {posição}" ou "Carry + Suporte"

Se não houver combo identificado, seção não aparece.

### Stats do jogador

Mantém as StatPills existentes (KDA, CS/min, Visão, Kill Part., Dano, Tempo Morto).

`time_dead_pct` ainda é `null` no nav state — mostrar `—` em vez de `null%`.

### CoachingSection

Mantém abaixo das stats, sem mudanças.

---

## api.js

Adicionar:

```js
export async function fetchScoreboard(matchId, puuid = "") {
  const params = puuid ? `?puuid=${encodeURIComponent(puuid)}` : ""
  const response = await fetch(`${BASE_URL}/match/${encodeURIComponent(matchId)}/scoreboard${params}`)
  if (!response.ok) return null
  return response.json()
}
```

---

## DDragon — Versão

Usar `14.24.1` (constante DDV já existente nos componentes).

---

## O que NÃO entra nesta fase

- Score de sinergia numérico (só visual/descritivo)
- Histórico de itens por minuto
- Comparação com médias de rank
- Página de campeão individual
- Notificações ou live stats

---

## Prioridades de implementação

| # | O que | Onde |
|---|---|---|
| 1 | Adicionar `items` e `total_damage` ao `MatchHistoryItem` | `ProjectB/main.py` |
| 2 | Novo endpoint `GET /match/{match_id}/scoreboard` | `ProjectB/main.py` |
| 3 | `fetchScoreboard` em api.js | `ProjectB-frontend/src/services/api.js` |
| 4 | Redesenho do match card no SummonerProfileScreen | `SummonerProfileScreen.jsx` |
| 5 | Abas Partidas / Campeões no SummonerProfileScreen | `SummonerProfileScreen.jsx` |
| 6 | Scoreboard completo no ResultsScreen | `ResultsScreen.jsx` |
| 7 | Sinergia expandida + fix `null%` no ResultsScreen | `ResultsScreen.jsx` |
| 8 | Deploy + teste e2e | Render + Vercel |
