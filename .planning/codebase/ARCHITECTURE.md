# Architecture

**Analysis Date:** 2026-03-30

## System Overview

mvp.gg is a League of Legends AI coaching platform with three distinct runtime environments:

1. **Cloud API** (`ProjectB/main.py` served on Render) — FastAPI backend consumed by the website. Handles summoner lookups, match history, scoreboard data, AI analysis cache (read/write via Supabase), and coaching delivery to the frontend.
2. **Web Frontend** (`ProjectB-frontend/`) — React SPA deployed on Vercel. Lets users search summoners, browse match history, and read AI coaching reports.
3. **Local Desktop App** (`ProjectB/coach_app.py` compiled to `CoachApp.exe`) — Windows tray app that runs on the player's machine during live games. Monitors the Riot Live Client API, captures minimap screenshots, and uploads post-game event data to the cloud API for AI analysis.

The three components are loosely coupled: the desktop app produces analysis; the cloud API stores and exposes it; the web frontend displays it. No real-time channel exists between the desktop app and the frontend — communication is asynchronous through Supabase as the shared data store.

## Components

**FastAPI Cloud Backend (`ProjectB/main.py`)**
- Central HTTP API, title "LoL Coach API v2.0"
- Owns all Riot API interactions for the web flow
- Holds in-memory live session state (`_live_session`, `_auto_monitor_task`, `_last_postgame_result`, `_local_jobs`, `_upload_counts`)
- Enforces `X-App-Token` auth on sensitive endpoints
- Daily upload rate limit per `riot_id` (20/day, set in `ProjectB/settings.py`)
- Auto-starts a background game monitor loop on startup (`_lifespan`)

**RiotMatchClient (`ProjectB/riot_client.py`)**
- Async HTTP wrapper around Riot Match-V5 API (region: `americas`, platform: `br1`)
- Disk-based JSON cache under `.cache/` with per-resource TTLs (match: 7 days, rank: 15 min, history: 5 min)
- Provides: summoner lookup, match history, full match data, timeline, item names from DDragon

**ContextBuilder (`ProjectB/context_builder.py`)**
- Transforms raw Riot API `MatchData` + `MatchTimeline` into a rich typed `MatchContext` Pydantic model
- Computes: death context, kill events, ward coverage, CS benchmarks, teamfight detection, gold deficit, objective proximity, recall analysis, buy decisions
- Output fed directly to Gemini as structured JSON

**CoachAI (`ProjectB/coach_ai.py`)**
- Wraps Google Gemini 2.5 Flash (`google-genai` SDK)
- Reads/writes an `ai_cache` table in Supabase to avoid redundant AI calls
- Produces structured `insights` (list of categorised events with severity/timestamp) and `feedback_geral` (prose coaching text)
- System prompt enforces output format constraints (no markdown headers in `feedback_geral`, actionable language, etc.)

**LiveCoachSession (`ProjectB/live_coach.py`)**
- Async polling orchestrator running on the local machine or cloud backend
- Polls Riot Live Client Data API every 300 ms for deaths/kills/multikills
- Every 3 ticks (~900 ms) checks objectives (Baron, Dragon, Herald, turrets)
- On each notable event: captures minimap via `ProjectB/minimap_capture.py` (uses `mss` for screen capture, `Pillow` for image processing) and saves to disk
- Accumulates `LiveEvent` objects in `event_history` and `events_queue` (asyncio Queue for SSE streaming)

**LiveGameClient (`ProjectB/live_game_client.py`)**
- Async HTTP client for Riot Live Client Data API at `https://127.0.0.1:2999`
- Uses `httpx` with `verify=False` (Riot uses a self-signed cert)
- Provides: active player info, player list, game stats, event log, game clock

**PostgameAnalyzer (`ProjectB/postgame_analyzer.py`)**
- Assembles a batch prompt from event list + minimap image paths + Riot API context
- Calls Google Gemini with multimodal input (text + images) in a single batch request
- Returns a structured coaching text (markdown sections)

**Desktop App Entry Point (`ProjectB/coach_app.py`)**
- PyInstaller-compiled Windows `.exe`
- Runs `pystray` (system tray icon) on the main thread and asyncio loop on a background thread
- States: waiting → recording → uploading → ready, shown via color-coded tray icon (gray/gold/blue/green)
- Uploads post-game data to `POST /local/upload` on the cloud backend with `X-App-Token` auth
- Polls `GET /local/status` every 10 s until analysis is ready (max 10 min / 60 attempts)

**Database Layer (`ProjectB/db.py`)**
- Single `ai_cache` Supabase table used for: AI result caching (insights + feedback_geral), coaching analysis storage (coaching_analysis), per-player riot_id association
- Async `supabase-py` client, lazy-initialized singleton

**Pydantic Schemas (`ProjectB/schemas.py`)**
- Request/response contracts for all API endpoints
- Key models: `MatchHistoryResponse`, `AnalyzeResponse`, `ScoreboardResponse`, `CoachingAnalysisResponse`, `LiveUploadRequest/Response`, `LocalUploadRequest/Response`

**React Frontend (`ProjectB-frontend/src/`)**
- SPA, no server-side rendering
- All API calls go through `ProjectB-frontend/src/services/api.js` — fetch wrapper over `VITE_API_URL`
- No client-side state management library; local `useState`/`useEffect` per screen
- Score computation (`calcScore`) is done entirely in the browser (`src/services/utils.js`)

## Data Flow

**Web — Summoner Search Flow:**

1. User types `Nick#TAG` in `SearchScreen` → `navigate('/summoner/:name/:tag')`
2. `SummonerProfileScreen` calls `fetchMatches(nick)` → `GET /summoner/{game_name}/{tag_line}`
3. Backend: `RiotMatchClient` resolves PUUID, fetches rank + last 10 match IDs, hydrates each match in parallel via `asyncio.gather`
4. Returns `MatchHistoryResponse` (summoner info + array of `MatchHistoryItem`)
5. Frontend computes `calcScore` per match, displays history with `ScoreBadge` components
6. Simultaneously calls `fetchCoachingStatus(matchIds)` → `GET /coaching/status?ids=...` to know which matches have AI analysis ready
7. User clicks a match → navigates to `/match/:matchId`

**Web — Match Details / Coaching Flow:**

1. `ResultsScreen` calls `fetchMatchDetails(matchId)` → `GET /match/{match_id}` (Supabase read)
2. Calls `fetchScoreboard(matchId, puuid)` → `GET /match/{match_id}/scoreboard` (Riot API + live calculation)
3. Calls `fetchCoachingAnalysis(matchId, riotId)` → `GET /coaching/{match_id}` (Supabase read)
4. If analysis exists: `CoachingSection` renders `UnlockedCoaching` with tabbed markdown sections
5. If not: `LockedCoaching` placeholder shown (prompts user to download the desktop app)

**Desktop App — Live Game Flow:**

1. `coach_app.py` starts → asyncio loop monitors Riot Live Client API via `LiveGameClient`
2. When `is_game_active()` returns true: `LiveCoachSession.start()` begins polling
3. Per event detected: minimap captured via `minimap_capture.py` (screen region calculated from resolution), saved to temp disk path
4. Game ends: `coach_app.py` calls `session.get_postgame_payload()`, serializes events with base64 minimap images
5. Posts `LocalUploadRequest` to `POST /local/upload` on cloud backend with `X-App-Token`
6. Cloud backend receives events, calls `analyze_postgame()` (Gemini multimodal batch), saves result to Supabase `ai_cache`
7. Desktop app polls `GET /local/status` every 10 s; on `ready`, tray icon turns green

**AI Analysis Flow (Cloud Backend — Legacy `/analyze` endpoint):**

1. `POST /analyze` or `GET /analyze/{game_name}/{tag_line}`
2. `RiotMatchClient` fetches match + timeline
3. `ContextBuilder.build()` produces `MatchContext`
4. `_get_ai_cache(match_id)` checks Supabase — cache hit returns immediately
5. Cache miss: `CoachAI.run_full_analysis()` sends context JSON to Gemini, receives structured response
6. `_set_ai_cache()` saves to Supabase; response returned to caller

## Communication Patterns

**REST (primary):**
- Frontend → Cloud Backend: standard `fetch()` over HTTPS, no auth headers
- Desktop App → Cloud Backend: `httpx` POST/GET with `X-App-Token` header (shared secret)
- Cloud Backend → Riot API: `httpx` async with `X-Riot-Token` header
- Cloud Backend → Supabase: `supabase-py` async client (PostgreSQL under the hood)
- Cloud Backend → Make.com: fire-and-forget `httpx` POST (feedback webhook)

**Server-Sent Events (SSE):**
- `GET /analyze/stream/{game_name}/{tag_line}/{match_index}` — streams `meta` event then `done`; AI streaming was removed, endpoint now only emits metadata
- `GET /live/events` — streams `LiveEvent` objects from `_live_session.events_queue` with `: heartbeat` keepalive every 5 s

**Local IPC (desktop app only):**
- `LiveGameClient` connects to `https://127.0.0.1:2999` (Riot Live Client Data API process)
- `minimap_capture.py` uses `mss` for direct screen capture — no IPC, direct OS calls

**Webhook (outgoing):**
- Feedback ratings (`POST /feedback`) forwarded to Make.com webhook (`MAKE_FEEDBACK_WEBHOOK_URL`)

## State Management

**Backend (in-memory, per-process):**
- `_live_session: Optional[LiveCoachSession]` — single active live session
- `_auto_monitor_task: Optional[asyncio.Task]` — background game monitor
- `_last_postgame_result: Optional[dict]` — last completed post-game analysis
- `_local_jobs: dict[str, str | None]` — riot_id → match_id mapping for local upload jobs
- `_upload_counts: dict[str, list]` — rate limit tracking (timestamps per riot_id)
- All state is lost on process restart; no distributed cache

**Backend (persistent, Supabase):**
- `ai_cache` table: primary persistent store for AI results and coaching analyses
- `RiotMatchClient` disk cache (`.cache/*.json`): TTL-based local file cache for Riot API responses

**Frontend (React local state):**
- No global state manager (no Redux, Zustand, Context API for app state)
- Each screen manages its own data via `useState` + `useEffect` + API calls on mount
- Navigation state passed via React Router `useLocation().state` (e.g., error messages from `SearchScreen` to itself)
- Score computation is pure function (`calcScore` in `utils.js`) — no caching

---

*Architecture analysis: 2026-03-30*
