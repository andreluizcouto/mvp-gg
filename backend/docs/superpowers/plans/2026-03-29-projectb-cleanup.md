# ProjectB Cleanup & Reorganization — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganizar o ProjectB para parecer profissional no GitHub — limpar dead code, extrair responsabilidades do main.py, e consolidar duplicacoes.

**Architecture:** Estrutura flat com 3 novos modulos utilitarios (`settings.py`, `db.py`, `schemas.py`) extraidos do main.py. Sem subpastas desnecessarias.

**Tech Stack:** Python 3.14, FastAPI, Pydantic, Supabase, Google Genai

---

### Task 1: Deletar artefatos gerados e mover live_debug.html

**Files:**
- Delete: `build/`, `dist/`, `__pycache__/`, `.pytest_cache/`, `.cache/`, `pyarmor_runtime_000000/`, `coach_app.log`
- Move: `live_debug.html` -> `debug/live_debug.html`

- [ ] **Step 1: Deletar artefatos**

```bash
cd C:/Users/andre/Desktop/Coach-AI-Project/ProjectB
rm -rf build/ dist/ __pycache__/ .pytest_cache/ .cache/ pyarmor_runtime_000000/
rm -f coach_app.log
```

- [ ] **Step 2: Mover live_debug.html para debug/**

```bash
mv live_debug.html debug/live_debug.html
```

- [ ] **Step 3: Verificar que .gitignore ja cobre tudo**

O `.gitignore` atual ja ignora: `build/`, `dist/`, `__pycache__/`, `.cache/`, `pyarmor_runtime_000000/`, `*.log`, `debug/`, `live_debug.html`. Nenhuma alteracao necessaria.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: delete generated artifacts + move live_debug.html to debug/"
```

---

### Task 2: Criar settings.py — env vars centralizadas

**Files:**
- Create: `settings.py`

- [ ] **Step 1: Criar settings.py**

```python
"""
Configuracoes centralizadas — todas as env vars do projeto.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# === Riot API ===
RIOT_API_KEY = os.getenv("RIOT_API_KEY", "")

# === AI ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# === Supabase ===
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# === Backend ===
APP_TOKEN = os.getenv("APP_TOKEN", "")
RENDER_BACKEND_URL = os.getenv("RENDER_BACKEND_URL", "https://lol-coach-backend-z4b7.onrender.com")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "https://mvpgg.vercel.app,https://lol-coach-frontend.vercel.app,http://localhost:5173").split(",")

# === Webhooks ===
MAKE_FEEDBACK_WEBHOOK_URL = os.getenv("MAKE_FEEDBACK_WEBHOOK_URL", "")

# === Limites ===
DAILY_LIMIT = 20
```

- [ ] **Step 2: Commit**

```bash
git add settings.py
git commit -m "feat: create settings.py with centralized env vars"
```

---

### Task 3: Criar db.py — Supabase client unificado

**Files:**
- Create: `db.py`

- [ ] **Step 1: Criar db.py**

```python
"""
Cliente Supabase unificado + funcoes de persistencia.
"""
import logging
from typing import Optional
from supabase import create_async_client
from settings import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)

_client = None


async def get_supabase():
    """Retorna o cliente Supabase (lazy init). None se nao configurado."""
    global _client
    if _client is None and SUPABASE_URL and SUPABASE_KEY:
        _client = await create_async_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


async def get_coaching_analysis(match_id: str) -> Optional[str]:
    """Busca analise de coaching salva no Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        sb = await get_supabase()
        if sb is None:
            return None
        resp = await sb.table("ai_cache").select("coaching_analysis,feedback_geral").eq("match_id", match_id).execute()
        if resp.data:
            row = resp.data[0]
            return row.get("coaching_analysis") or row.get("feedback_geral") or None
    except Exception as e:
        logger.error(f"Erro ao buscar coaching {match_id}: {e}")
    return None


async def save_coaching_analysis(match_id: str, analysis: str) -> None:
    """Salva analise de coaching no Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("SUPABASE_URL/KEY nao configurados — analise NAO foi salva!")
        return
    try:
        sb = await get_supabase()
        if sb is None:
            logger.error("Cliente Supabase retornou None — analise NAO foi salva!")
            return
        await sb.table("ai_cache").upsert({
            "match_id": match_id,
            "coaching_analysis": analysis,
            "insights": [],
            "feedback_geral": "",
        }).execute()
        logger.info(f"Analise de coaching salva no Supabase para {match_id}")
    except Exception as e:
        logger.error(f"Erro ao salvar coaching {match_id} no Supabase: {e}")
```

- [ ] **Step 2: Commit**

```bash
git add db.py
git commit -m "feat: create db.py with unified Supabase client"
```

---

### Task 4: Criar schemas.py — Pydantic models extraidos do main.py

**Files:**
- Create: `schemas.py`

- [ ] **Step 1: Criar schemas.py com todos os BaseModel do main.py**

```python
"""
Schemas Pydantic — request/response models da API.
"""
from pydantic import BaseModel
from typing import Optional


# ── Feedback ──

class FeedbackRequest(BaseModel):
    match_id: str
    player: str
    rating: int
    comment: str = ""


# ── Live events (SSE debug) ──

class LiveEventUpload(BaseModel):
    event_type: str
    game_time_sec: float
    champion: str
    detail: str = ""
    killer: Optional[str] = None
    victim: Optional[str] = None
    assisters: list[str] = []
    objective_stolen: bool = False
    minimap_base64: str


class LiveUploadRequest(BaseModel):
    puuid: str
    match_id: str
    events: list[LiveEventUpload]


class LiveUploadResponse(BaseModel):
    match_id: str
    analysis: str
    event_count: int


# ── Coaching ──

class CoachingSaveRequest(BaseModel):
    match_id: str
    puuid: str
    analysis: str


class CoachingAnalysisResponse(BaseModel):
    match_id: str
    has_analysis: bool
    analysis: Optional[str] = None


# ── Scoreboard ──

class ScoreboardPlayer(BaseModel):
    puuid: str
    summoner_name: str
    champion: str
    position: str
    kills: int
    deaths: int
    assists: int
    cs: int
    cs_per_min: float
    total_damage: int
    damage_share_pct: float
    gold_earned: int
    vision_score: int
    items: list[int]
    summoner1_id: int
    summoner2_id: int
    is_target: bool


class ScoreboardTeam(BaseModel):
    side: str
    win: bool
    players: list[ScoreboardPlayer]


class ScoreboardResponse(BaseModel):
    match_id: str
    duration_min: float
    teams: list[ScoreboardTeam]


# ── Local app ──

class LocalEventUpload(BaseModel):
    event_type: str
    game_time: str = ""
    champion: str = ""
    killer: Optional[str] = None
    victim: Optional[str] = None
    detail: str = ""
    assisters: list[str] = []
    minimap_base64: str = ""


class LocalUploadRequest(BaseModel):
    riot_id: str
    events: list[LocalEventUpload]
    match_id: str = ""


class LocalUploadResponse(BaseModel):
    accepted: bool
    job_id: str


# ── Analyze ──

class AnalyzeRequest(BaseModel):
    game_name: str
    tag_line: str
    match_index: int = 0


class InsightResponse(BaseModel):
    category: str
    severity: str
    timestamp: float
    title: str
    detail: str
    suggestion: str


class AnalyzeResponse(BaseModel):
    match_id: str
    player: str
    champion: str
    position: str
    win: bool
    duration_min: float
    kda: str
    cs_per_min: float
    vision_score: int
    kill_participation_pct: float
    damage_share_pct: float
    time_dead_pct: float
    rank: str
    insights: list[InsightResponse]
    feedback: str


# ── Match history ──

class MatchHistoryItem(BaseModel):
    match_id: str
    index: int
    champion: str
    kills: int
    deaths: int
    assists: int
    win: bool
    duration_min: int
    position: str
    wards_placed: Optional[int] = None
    wards_killed: Optional[int] = None
    summoner1_id: Optional[int] = None
    summoner2_id: Optional[int] = None
    cs: int = 0
    cs_per_min: float = 0.0
    vision_score: int = 0
    kill_participation_pct: float = 0.0
    damage_share_pct: float = 0.0
    doubles: int = 0
    triples: int = 0
    quadras: int = 0
    pentas: int = 0
    allies: list[dict] = []
    items: list[int] = []
    total_damage: int = 0


class MatchHistoryResponse(BaseModel):
    summoner: str
    puuid: str
    rank: str
    matches: list[MatchHistoryItem]
    wins: int = 0
    losses: int = 0
```

- [ ] **Step 2: Commit**

```bash
git add schemas.py
git commit -m "feat: create schemas.py with all Pydantic models extracted from main.py"
```

---

### Task 5: Limpar main.py — remover schemas, Supabase, env vars, dead code, webhook

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Substituir bloco de imports e env vars (linhas 1-67)**

Substituir o bloco inteiro de imports e env vars por:

```python
"""
LoL Coach API - Backend FastAPI
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import Optional
import asyncio
import base64
import httpx
import json
import logging
import os
import secrets

from contextlib import asynccontextmanager

from coach_ai import run_full_analysis, CoachAI, _get_ai_cache, _set_ai_cache, _is_valid_ai_result
from context_builder import ContextBuilder
from riot_client import RiotMatchClient, get_item_names, cache_invalidate
from live_coach import LiveCoachSession
from postgame_analyzer import analyze_postgame
from schemas import (
    FeedbackRequest, LiveEventUpload, LiveUploadRequest, LiveUploadResponse,
    CoachingSaveRequest, CoachingAnalysisResponse,
    ScoreboardPlayer, ScoreboardTeam, ScoreboardResponse,
    LocalEventUpload, LocalUploadRequest, LocalUploadResponse,
    AnalyzeRequest, InsightResponse, AnalyzeResponse,
    MatchHistoryItem, MatchHistoryResponse,
)
from settings import (
    RIOT_API_KEY as RIOT_KEY,
    GEMINI_API_KEY as GEMINI_KEY,
    SUPABASE_URL, SUPABASE_KEY,
    APP_TOKEN, RENDER_BACKEND_URL,
    CORS_ORIGINS, MAKE_FEEDBACK_WEBHOOK_URL,
    DAILY_LIMIT,
)
from db import get_supabase, get_coaching_analysis, save_coaching_analysis

logger = logging.getLogger(__name__)

app = FastAPI(title="LoL Coach API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in CORS_ORIGINS],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Validacao de configuracao na inicializacao
_missing = []
if not RIOT_KEY:
    _missing.append("RIOT_API_KEY")
if not SUPABASE_URL:
    _missing.append("SUPABASE_URL")
if not SUPABASE_KEY:
    _missing.append("SUPABASE_KEY")
if not APP_TOKEN:
    _missing.append("APP_TOKEN")
if _missing:
    logger.warning(f"Variaveis de ambiente ausentes: {', '.join(_missing)}")
if RIOT_KEY and RIOT_KEY.startswith("RGAPI-"):
    logger.warning("RIOT_API_KEY e uma chave de desenvolvimento (RGAPI-*) — expira a cada 24h!")
```

- [ ] **Step 2: Remover todas as classes BaseModel (linhas 69-240)**

Deletar todo o bloco de `class FeedbackRequest` ate `class MatchHistoryResponse` — agora vem de `schemas.py`.

- [ ] **Step 3: Remover Supabase client duplicado e funcoes de coaching (linhas 286-329)**

Deletar:
- `_supabase_client = None`
- `async def _get_supabase_client():`
- `async def _get_coaching_analysis():`
- `async def _save_coaching_analysis():`

Substituir todas as chamadas:
- `_get_supabase_client()` -> `get_supabase()` (de db.py)
- `_get_coaching_analysis(match_id)` -> `get_coaching_analysis(match_id)` (de db.py)
- `_save_coaching_analysis(match_id, analysis)` -> `save_coaching_analysis(match_id, analysis)` (de db.py)

- [ ] **Step 4: Remover MAKE_WEBHOOK_URL e seu uso**

Deletar a linha:
```python
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL", "")
```

Deletar a linha 548:
```python
asyncio.create_task(send_to_make(response.model_dump(), MAKE_WEBHOOK_URL))
```

Manter o `send_to_make` no endpoint `/feedback` (linha 628) que usa `MAKE_FEEDBACK_WEBHOOK_URL`.

- [ ] **Step 5: Remover dead code**

Deletar:
```python
DEBUG_MODE = os.getenv("DEBUG_MODE", "").lower() in ("1", "true", "yes")
```

Remover imports nao usados:
```python
import shutil
import tempfile
```

- [ ] **Step 6: Substituir _DAILY_LIMIT por DAILY_LIMIT de settings**

Na funcao `_check_rate_limit`, trocar `_DAILY_LIMIT` por `DAILY_LIMIT` (importado de settings).
Remover a linha:
```python
_DAILY_LIMIT = 20
```

- [ ] **Step 7: Adicionar try/except no _upload_coaching_to_render**

A funcao ja tem try/except com log — verificar que esta ok. (Ja esta, nenhuma mudanca necessaria.)

- [ ] **Step 8: Commit**

```bash
git add main.py
git commit -m "refactor: extract schemas, db, settings from main.py + remove dead code"
```

---

### Task 6: Limpar coach_ai.py — remover Supabase duplicado e env vars

**Files:**
- Modify: `coach_ai.py`

- [ ] **Step 1: Substituir imports e Supabase local**

Remover:
```python
import os
from supabase import create_async_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

_supabase_client = None

async def _get_supabase():
    global _supabase_client
    if _supabase_client is None and SUPABASE_URL and SUPABASE_KEY:
        _supabase_client = await create_async_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client
```

Adicionar no topo:
```python
from db import get_supabase
from settings import GEMINI_API_KEY
```

- [ ] **Step 2: Atualizar todas as chamadas `_get_supabase()` para `get_supabase()`**

Nas funcoes `_get_ai_cache` e `_set_ai_cache`, trocar:
```python
sb = await _get_supabase()
```
por:
```python
sb = await get_supabase()
```

- [ ] **Step 3: Atualizar `run_full_analysis` para usar settings**

Se a funcao usa `os.getenv("GEMINI_API_KEY")` internamente, trocar para usar `GEMINI_API_KEY` de settings. (Verificar — pode ja receber como parametro.)

- [ ] **Step 4: Commit**

```bash
git add coach_ai.py
git commit -m "refactor: use shared db.py and settings.py in coach_ai"
```

---

### Task 7: Limpar postgame_analyzer.py — remover dead code

**Files:**
- Modify: `postgame_analyzer.py`

- [ ] **Step 1: Remover funcao `_format_time` nao usada**

Deletar linhas 12-16:
```python
def _format_time(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"
```

- [ ] **Step 2: Remover import `io` se nao usado**

Verificar se `io` esta sendo usado em algum lugar do arquivo. Se nao, remover. (O import nao apareceu no topo — ja pode ter sido removido anteriormente. Verificar.)

- [ ] **Step 3: Commit**

```bash
git add postgame_analyzer.py
git commit -m "refactor: remove dead code from postgame_analyzer"
```

---

### Task 8: Atualizar .env.example

**Files:**
- Modify: `.env.example`

- [ ] **Step 1: Atualizar .env.example**

```
# Renomeie esse arquivo para .env e preencha suas chaves

# === Obrigatorios (backend) ===
RIOT_API_KEY=sua_chave_riot_aqui
GEMINI_API_KEY=sua_chave_gemini_aqui
ANTHROPIC_API_KEY=sua_chave_anthropic_aqui
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua_anon_key_aqui
APP_TOKEN=seu_token_app_aqui

# === Opcionais ===
# CORS_ORIGINS=https://mvpgg.vercel.app,http://localhost:5173
# MAKE_FEEDBACK_WEBHOOK_URL=
# RENDER_BACKEND_URL=https://lol-coach-backend-z4b7.onrender.com
# BACKEND_URL=http://localhost:8000
```

Removido: `MAKE_WEBHOOK_URL` e `DEBUG_MODE`.

- [ ] **Step 2: Commit**

```bash
git add .env.example
git commit -m "chore: update .env.example — remove unused vars"
```

---

### Task 9: Atualizar coach.spec — adicionar novos modulos

**Files:**
- Modify: `coach.spec`

- [ ] **Step 1: Adicionar settings, db, schemas aos hiddenimports**

No array `hiddenimports`, adicionar:
```python
"settings",
"db",
"schemas",
```

Lista completa fica:
```python
hiddenimports=[
    "pystray._win32",
    "PIL._imagingtk",
    "PIL.Image",
    "PIL.ImageDraw",
    "mss.windows",
    "httpx",
    "app_config",
    "tray_icon",
    "live_coach",
    "live_game_client",
    "minimap_capture",
    "settings",
    "db",
    "schemas",
],
```

- [ ] **Step 2: Commit**

```bash
git add coach.spec
git commit -m "chore: add new modules to PyInstaller hiddenimports"
```

---

### Task 10: Rodar testes e verificar

**Files:**
- None (verification only)

- [ ] **Step 1: Rodar testes**

```bash
cd C:/Users/andre/Desktop/Coach-AI-Project/ProjectB
python -m pytest tests/ -v --tb=short --timeout=30
```

Expected: Todos os testes passam.

- [ ] **Step 2: Verificar imports com dry-run**

```bash
python -c "from settings import RIOT_API_KEY; print('settings OK')"
python -c "from db import get_supabase; print('db OK')"
python -c "from schemas import AnalyzeResponse; print('schemas OK')"
python -c "import main; print('main OK')"
```

Expected: Todos imprimem OK sem erros.

- [ ] **Step 3: Se algo falhar, corrigir e commitar**

---

### Task 11: Commit final consolidado (se necessario)

- [ ] **Step 1: Verificar estado do repo**

```bash
git status
git log --oneline -10
```

- [ ] **Step 2: Se houver algo pendente, commitar**

```bash
git add -A
git commit -m "refactor: ProjectB cleanup complete — settings, db, schemas extracted"
```
