# Design: Integração Site — Coaching IA Gateado (P5)

**Data:** 2026-03-27
**Status:** Aprovado

---

## Visão Geral

Redesenhar o frontend (mvpgg.vercel.app) e integrar a análise pós-game gerada pelo app local. Apenas usuários com o CoachApp instalado terão acesso à análise IA — os demais veem a seção bloqueada como CTA de conversão.

O backend para de gerar análise IA ao abrir uma partida (removendo a chamada Gemini/game_rules). A análise agora vem exclusivamente do app local, que captura prints do minimapa durante a partida.

---

## Arquitetura

```
App Local (ProjectB)
  └── analyze_postgame() gera análise
  └── POST /coaching/save → Backend Render
          └── Salva coaching_analysis no Supabase

Frontend (Vercel)
  └── GET /summoner/:nick → lista partidas (existente)
  └── GET /coaching/:match_id → coaching_analysis ou null
          └── Com análise → seção desbloqueada (abas)
          └── Sem análise → seção bloqueada (blur + CTA)
```

---

## Supabase

Adicionar coluna à tabela existente:

```sql
ALTER TABLE matches ADD COLUMN coaching_analysis TEXT;
```

- `match_id` — chave existente
- `insights` — JSON Riot API (existente, mantido)
- `feedback_geral` — análise antiga (existente, para de ser populado)
- `coaching_analysis` — novo texto gerado pelo app local
- `timestamp` — existente

---

## Backend Render (ProjectB — main.py)

### Novos endpoints

**`POST /coaching/save`**

Recebido do app local após `analyze_postgame`. Salva no Supabase.

```
Request:
{
  "match_id": "BR1_123456",
  "puuid": "abc123...",
  "analysis": "texto da análise..."
}

Response:
{ "status": "saved", "match_id": "BR1_123456" }
```

**`GET /coaching/{match_id}`**

Consultado pelo frontend ao abrir uma partida.

```
Response (com análise):
{ "match_id": "BR1_123456", "analysis": "texto...", "has_analysis": true }

Response (sem análise):
{ "match_id": "BR1_123456", "analysis": null, "has_analysis": false }
```

### Remoção

Remover a chamada de IA (Gemini + game_rules) do endpoint `/analyze` e `/analyze/stream`. Manter apenas os dados brutos da Riot API (insights já existentes no contexto).

---

## App Local (ProjectB — live_coach.py + main.py)

Após `analyze_postgame` concluir no `_auto_monitor_loop`, POST automático para o Render:

```python
async def _upload_coaching_result(match_id: str, puuid: str, analysis: str):
    render_url = os.getenv("RENDER_BACKEND_URL", "https://lol-coach-backend-z4b7.onrender.com")
    async with httpx.AsyncClient() as client:
        await client.post(f"{render_url}/coaching/save", json={
            "match_id": match_id,
            "puuid": puuid,
            "analysis": analysis,
        }, timeout=15)
```

---

## Frontend (ProjectB-frontend)

### Homepage — redesign

Layout Opção C: hero com tagline + busca central + cards de campeões populares.

**Estrutura:**
- Navbar: logo + link Tierlist (desabilitado, fase 2) + link Campeões (desabilitado, fase 2)
- Hero: tagline "EVOLUA. ANALISE. VENÇA." + input nick#TAG + botão buscar + seletor de região
- Seção campeões: cards horizontais com imagem de splash + nome + "Descubra a build de {nome}" (estáticos por agora, sem funcionalidade)

### Perfil do jogador — match card

Badge `🤖 IA` inline no card de partida quando `has_analysis: true`:

```jsx
{hasAnalysis && (
  <span className="badge-ia">🤖 IA</span>
)}
```

O badge aparece ao lado do resultado (VITÓRIA/DERROTA), dourado, apenas nas partidas com análise disponível.

### Página da partida — seção coaching

**Variante A — sem análise (app não instalado ou partida anterior ao app):**

Preview borrado com overlay:
- Texto fictício de análise com `filter: blur(4px)`
- Overlay semi-transparente com cadeado + "Coaching IA disponível"
- Subtexto: "Instale o CoachApp e jogue uma partida"
- Botão: "Baixar CoachApp — grátis"

**Variante B — com análise (app instalado, partida capturada):**

Seção com abas:
- **Mortes** — cards por evento com timestamp, análise do minimapa
- **Kills** — cards por kill com contexto
- **Objetivos** — dragons, barons, torres com contexto
- **Resumo** — padrões identificados + conselho final

O texto da análise (gerado pelo `analyze_postgame`) é parseado por seção usando marcadores do prompt (`## 1.`, `## 2.`, etc.).

---

## Fluxo de dados completo

```
1. Usuário joga partida com app ativo
2. App captura prints → analyze_postgame() → texto de análise
3. App POST /coaching/save → Render → Supabase (coaching_analysis)
4. Usuário abre mvpgg.vercel.app → busca nick
5. Frontend GET /summoner/:nick → lista partidas com match_ids
6. Frontend GET /coaching/:match_id → { has_analysis: true, analysis: "..." }
7. Página da partida mostra seção desbloqueada com abas
```

---

## Parsing da análise no frontend

A IA gera seções com headers `## N. Título` (confirmado em testes). O frontend divide o texto nesses marcadores e cria uma aba por seção encontrada:

```js
function parseAnalysisSections(text) {
  // Divide em seções pelo padrão "## N."
  const parts = text.split(/(?=##\s+\d+\.)/);
  return parts
    .filter(p => p.trim())
    .map(p => {
      const titleMatch = p.match(/##\s+\d+\.\s+(.+)/);
      return {
        title: titleMatch ? titleMatch[1].trim() : 'Análise',
        content: p.replace(/##\s+\d+\.\s+.+\n/, '').trim(),
      };
    });
}
```

Se o texto não tiver `## N.` (modo degraded), cria uma única aba "Resumo" com o texto completo.

---

## O que NÃO entra nesta fase

- Tierlist, página de campeão, notícias, leaderboard (Fase 2 / P7)
- Builds de campeões (cards na homepage são estáticos)
- Login / autenticação de usuário
- Histórico de análises do jogador (apenas partida a partida)
- Notificações push quando análise fica pronta

---

## Prioridades de implementação

| # | O que | Onde |
|---|---|---|
| 1 | Coluna `coaching_analysis` no Supabase | SQL migration |
| 2 | `POST /coaching/save` + `GET /coaching/{match_id}` | ProjectB/main.py |
| 3 | Upload automático no `_auto_monitor_loop` | ProjectB/main.py |
| 4 | Remover chamada IA do `/analyze/stream` | ProjectB/main.py |
| 5 | Homepage redesign (hero + campeões) | ProjectB-frontend |
| 6 | Badge `🤖 IA` no match card do perfil | ProjectB-frontend |
| 7 | Seção coaching na página da partida (locked + unlocked) | ProjectB-frontend |
