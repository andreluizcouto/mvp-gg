# ProjectB — Cleanup & Reorganization Spec

**Date:** 2026-03-29
**Goal:** Reorganizar o codebase para parecer profissional no GitHub sem over-engineering. Limpeza de dead code, consolidacao de duplicacoes, e extracao de responsabilidades do main.py.

---

## 1. Deletar artefatos gerados

Remover tudo que e regeneravel e esta no .gitignore:

| Item | Tamanho | Motivo |
|---|---|---|
| `build/` | 25MB | Artefato intermediario PyInstaller |
| `dist/` | 62MB | Artefato final PyInstaller |
| `__pycache__/` | 644K | Bytecode Python |
| `.pytest_cache/` | 8K | Cache pytest |
| `.cache/` | 1K | Cache Riot API |
| `pyarmor_runtime_000000/` | 634K | PyArmor trial nao usado |
| `coach_app.log` | 652K | Log regenerado automaticamente |

**Total: ~89MB liberados.**

---

## 2. Mover live_debug.html

- De: `ProjectB/live_debug.html`
- Para: `ProjectB/debug/live_debug.html`
- Atualizar `.gitignore` se necessario (ja ignora `debug/`)

---

## 3. Criar `settings.py` — env vars centralizadas

Extrair todas as env vars espalhadas em `main.py` e `coach_app.py` para um unico modulo:

```python
# settings.py
import os
from dotenv import load_dotenv

load_dotenv()

RIOT_API_KEY = os.getenv("RIOT_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
APP_TOKEN = os.getenv("APP_TOKEN", "")
MAKE_FEEDBACK_WEBHOOK_URL = os.getenv("MAKE_FEEDBACK_WEBHOOK_URL", "")
BACKEND_URL = os.getenv("BACKEND_URL", "")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
DAILY_LIMIT = 20
```

Todos os modulos passam a importar de `settings` em vez de chamar `os.getenv()` diretamente.

---

## 4. Criar `db.py` — Supabase client unificado

Consolidar os dois clientes duplicados (`coach_ai._get_supabase` + `main._get_supabase_client`):

```python
# db.py
from supabase import acreate_client
from settings import SUPABASE_URL, SUPABASE_KEY

_client = None

async def get_supabase():
    global _client
    if _client is None:
        _client = await acreate_client(SUPABASE_URL, SUPABASE_KEY)
    return _client
```

Funcoes de coaching analysis (`_get_coaching_analysis`, `_save_coaching_analysis`) tambem migram pra ca.

---

## 5. Criar `schemas.py` — Pydantic models extraidos do main.py

Extrair todas as ~18 classes BaseModel do main.py para `schemas.py`:

**Request models:**
- FeedbackRequest
- LiveEventUpload, LiveUploadRequest
- LocalEventUpload, LocalUploadRequest
- AnalyzeRequest
- CoachingSaveRequest

**Response models:**
- LiveUploadResponse, LocalUploadResponse
- AnalyzeResponse, InsightResponse
- CoachingAnalysisResponse
- ScoreboardPlayer, ScoreboardTeam, ScoreboardResponse
- MatchHistoryItem, MatchHistoryResponse

main.py passa a fazer: `from schemas import AnalyzeRequest, AnalyzeResponse, ...`

---

## 6. Limpar main.py

Apos extracoes:
- Remover todas as classes BaseModel (agora em schemas.py)
- Remover `_get_supabase_client()` (agora em db.py)
- Remover `_get_coaching_analysis()` e `_save_coaching_analysis()` (agora em db.py)
- Remover env vars diretas (agora em settings.py)
- Remover `MAKE_WEBHOOK_URL` e o `create_task(send_to_make(...))` da rota /analyze (L548)
- Remover variavel `DEBUG_MODE` (dead code)
- Remover imports `shutil` e `tempfile` (nao usados)
- Adicionar `try/except` com log no `_upload_coaching_to_render`
- Importar de settings, db, schemas

---

## 7. Limpar coach_ai.py

- Remover `_get_supabase()` duplicado -> importar de `db.py`
- Remover env vars diretas -> importar de `settings.py`

---

## 8. Limpar postgame_analyzer.py

- Remover funcao `_format_time()` (definida, nunca chamada)
- Remover import `io` (nao usado)

---

## 9. Consolidar webhook Make.com

- Remover `MAKE_WEBHOOK_URL` de settings e .env.example
- Manter `MAKE_FEEDBACK_WEBHOOK_URL` para caixinha de feedback
- Remover `asyncio.create_task(send_to_make(...))` da rota /analyze (L548)
- Manter `send_to_make()` no endpoint /feedback (L628)

---

## 10. Atualizar .env.example

Remover `MAKE_WEBHOOK_URL`, garantir que todas as vars de `settings.py` estao documentadas.

---

## 11. Atualizar coach.spec e build.bat

Verificar se os hidden imports no coach.spec incluem os novos modulos (`settings`, `db`, `schemas`).

---

## O que NAO muda

- Estrutura flat (sem subpastas api/, services/, etc.)
- `context_builder.py` — modulo coeso, nao fragmentar
- `game_rules.py` — ja esta bem
- `coach_guardrails.py` — standalone, limpo
- `minimap_capture.py` — utilitario simples
- `app_config.py` — config local do .exe
- `tray_icon.py` — UI do tray
- `live_game_client.py` — wrapper Riot Live API
- `live_coach.py` — orquestrador live
- `riot_client.py` — client + cache
- Testes existentes em tests/
- Docs existentes em docs/

---

## Ordem de execucao

1. Deletar artefatos + mover live_debug.html
2. Criar settings.py
3. Criar db.py
4. Criar schemas.py
5. Limpar main.py (imports, dead code, extrair, consolidar webhook)
6. Limpar coach_ai.py
7. Limpar postgame_analyzer.py
8. Atualizar .env.example
9. Atualizar coach.spec
10. Rodar testes pra garantir que nada quebrou
