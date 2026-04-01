# External Integrations

**Analysis Date:** 2026-03-30

## APIs & External Services

**Riot Games API:**
- Riot Account v1 — resolves Riot ID (game_name#tag_line) to PUUID
  - Endpoint: `https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}`
- Riot Summoner v4 — fetches summoner profile by PUUID (level, icon)
  - Endpoint: `https://br1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}`
- Riot League v4 — fetches ranked tier (RANKED_SOLO_5x5)
  - Endpoint: `https://br1.api.riotgames.com/lol/league/v4/entries/by-summoner/{id}`
- Riot Match v5 — fetches match history IDs and full match/timeline data
  - Endpoints: `https://americas.api.riotgames.com/lol/match/v5/matches/...`
- Auth: `X-Riot-Token` header, key sourced from `RIOT_API_KEY` env var
- Platform: `br1` (Brazil), Region: `americas`
- Implemented in: `ProjectB/riot_client.py`

**Riot Live Client Data API (local only):**
- Polls localhost during active League of Legends matches
  - Base URL: `https://127.0.0.1:2999` (self-signed cert, `verify=False`)
  - Endpoints used: `/liveclientdata/gamestats`, `/liveclientdata/activeplayer`, `/liveclientdata/playerlist`, `/liveclientdata/eventdata`
- Used by the MVPApp desktop client during live games
- Implemented in: `ProjectB/live_game_client.py`

**Riot Data Dragon (DDragon):**
- Fetches item name data for match analysis display
  - Versions list: `https://ddragon.leagueoflegends.com/api/versions.json`
  - Items JSON: `https://ddragon.leagueoflegends.com/cdn/{version}/data/pt_BR/item.json`
- Version is matched against the game's patch version (`gameVersion` field)
- Implemented in: `ProjectB/riot_client.py` (`get_item_names`, `_resolve_ddragon_version`)

**Google Gemini:**
- Model: Gemini 2.5 Flash
- Used to generate per-match coaching analysis (insights + narrative feedback)
- SDK: `google-genai 1.10.0` (`from google import genai`)
- Auth: `GEMINI_API_KEY` env var
- System prompt + JSON match context sent per analysis request
- Guardrails layer post-processes output: `ProjectB/coach_guardrails.py`
- Implemented in: `ProjectB/coach_ai.py`

**Anthropic Claude:**
- `anthropic >=0.40.0` listed in `requirements.txt` and `ANTHROPIC_API_KEY` in `.env.example`
- Auth: `ANTHROPIC_API_KEY` env var
- Usage not visible in current source files (may be reserved or used in guardrails rewrite path)

## SDKs & Clients

| SDK | Version | Purpose | File |
|-----|---------|---------|------|
| `google-genai` | 1.10.0 | Gemini LLM coaching analysis | `ProjectB/coach_ai.py` |
| `anthropic` | >=0.40.0 | Claude LLM (secondary/reserved) | `ProjectB/settings.py` |
| `supabase` | >=2.11.0 | Supabase DB async client | `ProjectB/db.py` |
| `httpx` | >=0.28.1 | Async HTTP for all external calls | `ProjectB/riot_client.py`, `coach_app.py`, `main.py` |

## Data Sources

**League of Legends Match Data:**
- Source: Riot Games Match v5 API
- Includes: participant stats (KDA, CS, gold, vision, items, damage), game timeline events (kills, wards, objectives, item purchases), summoner rank
- Cached locally in `ProjectB/.cache/*.json` with per-type TTLs

**Live Game Events:**
- Source: Riot Live Client Data API (localhost:2999)
- Available only while LoL is running on the player's machine
- Captured by MVPApp desktop app; minimap screenshots captured with `mss` and encoded as base64
- Data stored in-memory during session, then uploaded to backend at game end

**AI Coaching Analysis:**
- Source: Gemini 2.5 Flash, given structured match context JSON built by `ProjectB/context_builder.py`
- Results cached in Supabase `ai_cache` table keyed by `(match_id, riot_id)`
- Served to frontend via `/coaching/{match_id}` endpoint

**Item Names / Game Data:**
- Source: Riot Data Dragon CDN (patch-versioned)
- Cached locally for 7 days

## Webhooks & Events

**Outbound — Make.com Webhook:**
- Triggered from backend when feedback data needs to be forwarded
- URL: `MAKE_FEEDBACK_WEBHOOK_URL` env var (optional)
- Called via `send_to_make()` in `ProjectB/main.py`
- Used for feedback/analytics pipeline; no-op if env var is empty

**Outbound — Render Backend (from MVPApp desktop):**
- MVPApp posts game data to: `{BACKEND_URL}/local/upload` (POST)
- MVPApp polls analysis status at: `{BACKEND_URL}/local/status` (GET)
- Auth: `X-App-Token` header (hardcoded default token in `ProjectB/coach_app.py`, overridable via `.env`)
- Backend URL defaults to `https://lol-coach-backend-z4b7.onrender.com`

**Inbound — No webhooks:**
- No inbound webhook endpoints defined
- Frontend communicates with backend over standard REST (no WebSockets, no SSE)

## CI/CD & Deployment

**Backend Hosting:**
- Platform: Render (free tier)
- URL: `https://lol-coach-backend-z4b7.onrender.com`
- Cold start delay: 30–60 seconds (MVPApp has explicit warmup logic in `ProjectB/coach_app.py`)

**Frontend Hosting:**
- Platform: Vercel
- URL: `https://mvpgg.vercel.app`
- SPA rewrite rule in `ProjectB-frontend/vercel.json`
- Backend URL configured via `VITE_API_URL` env var at build time

**GitHub Actions:**
- `ProjectB/.github/workflows/claude.yml` — Claude Code action triggered by `@claude` mentions in issues/PRs
- `ProjectB/.github/workflows/claude-code-review.yml` — automated code review via Claude
- Auth: `CLAUDE_CODE_OAUTH_TOKEN` GitHub secret

## Environment Configuration

**Required backend env vars (`ProjectB/.env`):**
- `RIOT_API_KEY` — Riot Games developer/production API key
- `GEMINI_API_KEY` — Google AI Studio key for Gemini 2.5 Flash
- `ANTHROPIC_API_KEY` — Anthropic API key
- `SUPABASE_URL` — Supabase project URL (e.g. `https://xxx.supabase.co`)
- `SUPABASE_KEY` — Supabase anon key
- `APP_TOKEN` — shared secret between MVPApp desktop client and backend

**Optional backend env vars:**
- `CORS_ORIGINS` — comma-separated allowed origins (default includes Vercel + localhost:5173)
- `MAKE_FEEDBACK_WEBHOOK_URL` — Make.com automation webhook
- `RENDER_BACKEND_URL` — override for backend URL used in coaching upload
- `BACKEND_URL` — override for MVPApp desktop to target local dev backend
- `DEBUG_MODE` — enables debug endpoints when `"true"`

**Frontend env vars:**
- `VITE_API_URL` — backend base URL; falls back to `https://lol-coach-backend-z4b7.onrender.com`

---

*Integration audit: 2026-03-30*
