# Tech Stack

**Analysis Date:** 2026-03-30

## Languages

**Primary:**
- Python 3.11.0 — Backend (`ProjectB/`) — all server-side logic, API, AI integration, desktop app
- JavaScript (ES2020+) — Frontend (`ProjectB-frontend/`) — React SPA, JSX, no TypeScript

## Runtime

**Backend Environment:**
- Python 3.11.0 (pinned via `ProjectB/.python-version`)
- Runs on Render (cloud, free tier — cold starts expected) or locally via `uvicorn`
- Desktop app variant compiled to Windows `.exe` via PyInstaller 6.x

**Frontend Environment:**
- Node.js (version not pinned — no `.nvmrc`)
- Package manager: npm (lockfile `package-lock.json` present)

## Frameworks

**Backend:**
- FastAPI `0.115.0` — REST API server (`ProjectB/main.py`)
- Uvicorn `0.30.0` — ASGI server (runs FastAPI)
- Pydantic `>=2.8.0` — request/response schemas (`ProjectB/schemas.py`)
- python-dotenv `1.0.1` — env var loading (`ProjectB/settings.py`)

**Frontend:**
- React `^19.2.4` — UI framework (`ProjectB-frontend/src/`)
- React Router DOM `^7.13.1` — client-side routing (`ProjectB-frontend/src/App.jsx`)
- Tailwind CSS `^3.4.19` — utility-first CSS (`ProjectB-frontend/tailwind.config.js`)
- Vite `^8.0.1` — build tool and dev server (`ProjectB-frontend/vite.config.js`)
- PostCSS `^8.5.8` — CSS processing (`ProjectB-frontend/postcss.config.js`)
- Autoprefixer `^10.4.27` — CSS vendor prefixes

**Desktop App (MVPApp):**
- pystray `>=0.19.0` — system tray icon on Windows (`ProjectB/tray_icon.py`)
- mss `>=9.0.0` — cross-platform screen capture / minimap capture (`ProjectB/minimap_capture.py`)
- Pillow `>=10.0.0` — image processing (minimap screenshots to base64)
- PyInstaller — packages `coach_app.py` into `dist/MVPApp/MVPApp.exe` (one-dir mode)

**AI / LLM:**
- google-genai `1.10.0` — Gemini 2.5 Flash SDK (`ProjectB/coach_ai.py`)
- anthropic `>=0.40.0` — Anthropic Claude SDK (available in requirements, referenced in `.env.example`)

**Database Client:**
- supabase `>=2.11.0` — async Supabase client (`ProjectB/db.py`)

**HTTP Client:**
- httpx `>=0.28.1,<1.0.0` — async HTTP for Riot API calls, internal backend calls, and MVPApp uploads

**Testing:**
- pytest `>=8.0.0`
- pytest-asyncio `>=0.23.0`
- pytest-timeout `>=2.3.0`
- Tests located in `ProjectB/tests/`

## Build & Tooling

**Backend:**
- `ProjectB/build.bat` — builds Windows `.exe` via PyInstaller
- `ProjectB/coach.spec` — PyInstaller spec (one-dir, windowed/no console, UPX compression)
- Output: `ProjectB/dist/MVPApp/MVPApp.exe`

**Frontend:**
- `vite build` — production bundle to `ProjectB-frontend/dist/`
- `vite` — dev server with HMR
- ESLint `^9.39.4` with flat config (`ProjectB-frontend/eslint.config.js`)
  - Plugins: `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh`
  - Rule override: `no-unused-vars` ignores `^[A-Z_]` pattern (constants)
- No Prettier config detected

## Database & Storage

**Primary Database:**
- Supabase (PostgreSQL-backed) — hosted cloud instance
  - Table `ai_cache`: stores AI coaching analysis keyed by `match_id` + `riot_id`
  - Async client initialized lazily in `ProjectB/db.py`

**Local Cache:**
- Disk-based JSON cache in `ProjectB/.cache/` directory
  - Used for Riot API responses: match data, timelines, summoner info, rank, item names
  - TTL per key type: matches/timelines 7 days, history 5 min, rank 15 min, summoner 1 hour
  - Implemented in `ProjectB/riot_client.py`

**File Storage:**
- No dedicated file storage service — minimap screenshots encoded as base64 and sent inline in JSON payloads

## Platform Requirements

**Development:**
- Python 3.11.0 + pip/venv
- Node.js + npm (version unspecified)
- `.env` file with: `RIOT_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, `APP_TOKEN`

**Production:**
- Backend: Render (free tier, `https://lol-coach-backend-z4b7.onrender.com`)
  - Cold start delay of 30–60s acknowledged in `ProjectB/coach_app.py`
- Frontend: Vercel (`https://mvpgg.vercel.app`)
  - SPA rewrites configured via `ProjectB-frontend/vercel.json`
- Desktop app: Windows-only `.exe` distributed directly (no installer)

---

*Stack analysis: 2026-03-30*
