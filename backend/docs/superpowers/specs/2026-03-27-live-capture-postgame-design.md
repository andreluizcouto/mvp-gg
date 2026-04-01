# Design: Captura de Minimapa ao Vivo + Análise Pós-Game

**Data:** 2026-03-27
**Status:** Aprovado

---

## Visão Geral

Expandir o sistema de coaching para capturar prints do minimapa durante partidas ao vivo e usar todas as capturas em uma análise batch pós-game. O sistema se divide em duas experiências:

- **Sem app (site):** Dashboard estilo op.gg com dados crus da Riot API (KDA, build, vision, dano, CS). Zero IA.
- **Com app (site + app local):** Tudo acima + coaching IA completo com prints do minimapa como evidência visual.

O app local funciona como "booster" — captura dados que a API não fornece (estado real do minimapa com fog of war) e envia pro backend no fim da partida para análise consolidada.

---

## Arquitetura

```
SEM APP (site = op.gg)              COM APP (site + coaching IA)
        |                                      |
        v                                      v
   Site (frontend)                        Site (frontend)
        |                                      |
        v                                      |
  Backend (nuvem)                         App Local (background)
   - Riot API                              - Live Client API (localhost:2999)
   - Dados crus                            - Captura minimapa (mss)
   - KDA, build, CS,                       - Salva prints locais
     vision, dano                          |
   - Zero IA                               v (fim da partida)
                                      Upload prints + match data
                                           |
                                           v
                                      Backend (nuvem)
                                       - Riot API (complementa)
                                       - Analise IA batch (1 chamada)
                                       - Salva resultado texto
                                       - Descarta imagens (TTL 48h)
                                           |
                                           v
                                      Site mostra:
                                       - Dashboard (igual)
                                       - + Coaching IA com prints
                                       - + Tag "analise premium"
```

---

## Sistema de Captura (App Local)

### Eventos capturados

| Evento | Fonte de detecção | Polling |
|---|---|---|
| Morte do jogador | `isDead` flag change | **300ms** |
| Kill do jogador | `ChampionKill` event | 800ms |
| Multi-kill (double+) | `Multikill` event | 800ms |
| Dragon (aliado/inimigo) | `DragonKill` event | 800ms |
| Baron (aliado/inimigo) | `BaronKill` event | 800ms |
| Herald | `HeraldKill` event | 800ms |
| Torre destruida | `TurretKilled` event | 800ms |

**Principio:** captura tudo, a IA decide o peso no pos-game. O sistema nao tenta ser inteligente sobre relevancia — um dragon "givado" vs. um dragon contestado e decidido pela IA, nao pelo capturador.

### Dados salvos por evento

```json
{
  "event_type": "death",
  "game_time_sec": 945.0,
  "champion": "Viktor",
  "killer": "Zed",
  "assisters": ["LeeSin"],
  "minimap_png": "prints/match_BR1_123456/death_0945.png",
  "metadata": {}
}
```

### Armazenamento local

- Prints salvos em pasta temporaria por partida
- ~20KB por print, estimativa 20-40 prints/jogo = ~400-800KB
- Apos upload pro backend, pasta local pode ser limpa

### Sem analise individual durante o jogo

Nenhuma chamada de IA durante a partida. Apenas captura e salva localmente. A IA so entra no pos-game.

---

## Detecção de Fim de Partida

Nao usar timeout da Live Client API (pode ser queda de internet, alt+F4, crash).

**Metodo:** Riot API como fonte de verdade.
1. App detecta que a Live Client API parou de responder
2. Busca match IDs recentes via Riot API (`/match/v5/matches/by-puuid/{puuid}/ids`)
3. Se encontra match ID novo (nao existia antes do jogo) -> partida acabou, inicia upload
4. Se nao encontra -> jogo crashou/saiu, nao faz upload

---

## Upload e Analise Pos-Game

### Upload (app local -> backend)

```
POST /live/upload
{
  "puuid": "abc123...",
  "match_id": "BR1_123456",
  "events": [
    {
      "event_type": "death",
      "game_time_sec": 245.0,
      "killer": "Zed",
      "assisters": ["LeeSin"],
      "minimap_base64": "iVBOR..."
    },
    ...
  ]
}
```

### Backend processa

1. Recebe prints + dados dos eventos
2. Puxa dados complementares da Riot API (Timeline + match data)
3. Monta prompt unico com:
   - Dados da API (KDA, CS, wards, posicoes, gold diff, etc.)
   - Todos os prints em ordem cronologica
   - Contexto de cada evento
4. **1 chamada de IA** — a IA ve o jogo inteiro e gera:
   - Analise de cada morte (com print como evidencia)
   - Padroes identificados ("3 das 4 mortes foram por falta de visao no rio")
   - Momentos positivos relevantes
   - Feedback consolidado
5. Salva texto da analise no Supabase
6. Descarta imagens (ou TTL de 48h)

### Custo estimado por partida

- ~20-40 prints de ~20KB = ~400-800KB de imagens
- 1 chamada IA com visao = ~$0.01-0.03
- Muito mais barato que analise individual por evento

---

## Experiencia no Site

### Sem app (op.gg)
- Historico de partidas com KDA, build, CS/min, vision, dano
- Dados crus da Riot API, sem IA
- Gratuito, sem login necessario

### Com app (coaching IA)
- Tudo acima +
- Secao "Coaching IA" na pagina da partida
- Tag visivel: "Analise disponivel porque voce usa o CoachApp"
- Conteudo:
  - Analise de cada morte com contexto
  - Padroes identificados entre mortes
  - Momentos positivos relevantes
  - Feedback consolidado do jogo
- Pra quem nao tem o app: secao aparece como preview/bloqueada com CTA para instalar

### Loop de conversao
```
Jogador entra no site -> ve seus dados (op.gg)
    -> ve secao coaching bloqueada
    -> "O que e isso?" -> instala o app
    -> joga uma partida -> analise aparece
    -> volta pro site sempre
```

---

## Decisoes Tecnicas

- **Polling de morte:** 300ms (mais agressivo para precisao do minimapa)
- **Polling de outros eventos:** 800ms
- **Analise:** batch no pos-game, zero IA durante o jogo
- **Upload:** hibrido — prints sobem pro backend, analise gera texto, imagens descartadas apos TTL
- **Fim de partida:** detectado via Riot API, nao por timeout da Live Client
- **IA:** Anthropic (Haiku) por enquanto, Gemini Flash quando quota resolver
- **Fallback:** Gemini Flash (gratis) -> Claude Haiku (pago, ~$0.001/chamada)
- **Site:** mvpgg.vercel.app (redesign planejado para depois)

---

## Prioridades de Implementacao

| Prioridade | O que | Descricao |
|---|---|---|
| P1 | Refatorar captura para salvar local | Prints em disco sem analise individual, polling morte 300ms |
| P2 | Deteccao de fim de partida via Riot API | Busca match ID novo ao perder conexao com Live Client |
| P3 | Endpoint `/live/upload` | Recebe batch de prints + eventos, puxa Timeline API |
| P4 | Analise batch pos-game | 1 chamada IA com todos os prints + dados API |
| P5 | Integracao site | Secao coaching na pagina da partida, tag de app, preview bloqueado |
| P6 | App desktop (background) | Empacotar processo local como .exe instalavel |
| P7 | Redesign do site | Visual novo pro mvpgg.vercel.app |
