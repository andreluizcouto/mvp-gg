# Coding Conventions

**Analysis Date:** 2026-03-30

---

## Naming Conventions

### Python (ProjectB/)

**Files:** `snake_case` — `coach_ai.py`, `context_builder.py`, `postgame_analyzer.py`, `app_config.py`

**Functions:** `snake_case` — `get_config()`, `save_config()`, `build_batch_prompt()`, `_cache_path()`

**Private helpers:** Prefixed with `_` — `_default_dir()`, `_cache_get()`, `_cache_path()`, `_bounty_for_streak()`, `_dist()`

**Constants:** `UPPER_SNAKE_CASE` — `CACHE_DIR`, `CACHE_TTL`, `REWRITE_PROMPT`, `_REWRITE_TRIGGERS`

**Classes:** `PascalCase` — `MatchContext`, `DeathContext`, `PlayerPosition`, `FeedbackRequest`

**Private module-level sets/dicts:** Prefixed with `_` — `_REWRITE_TRIGGERS`, `_WARD_PROPS`, `_DEFAULTS`

### JavaScript/JSX (ProjectB-frontend/)

**Files:** `PascalCase` for components — `SearchScreen.jsx`, `CoachingSection.jsx`, `SummonerProfileScreen.jsx`

**Files:** `camelCase` for services/utilities — `api.js`, `utils.js`, `constants.js`

**Functions/variables:** `camelCase` — `fetchMatches()`, `fetchCoachingAnalysis()`, `calcScore()`, `buildChampionPool()`

**React components:** `PascalCase` — `ScoreBadge`, `StatCard`, `InlineScoreboard`, `LockedCoaching`, `UnlockedCoaching`

**Constants:** `UPPER_SNAKE_CASE` — `BASE_URL`, `TIERLIST_PREVIEW`, `LEADERBOARD_PREVIEW`, `POPULAR_CHAMPIONS`

**ESLint rule:** `no-unused-vars` allows uppercase/underscore-prefixed names (`varsIgnorePattern: '^[A-Z_]'`)

---

## Code Patterns

### Python — Module Header Pattern

Every Python file opens with a module-level docstring describing its purpose:

```python
"""
coach_guardrails.py — Linter + Rewrite + Sanitização pós-LLM
...
"""
```

### Python — Section Separators

Long modules use visual separators to divide logical sections:

```python
# ─────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────
```

### Python — Pydantic for Data Contracts

All data contracts use Pydantic `BaseModel`. Both request/response schemas (`schemas.py`) and internal computation models (`context_builder.py`) follow this pattern:

```python
class DeathContext(BaseModel):
    timestamp_sec: float
    game_phase: str
    death_type: str = "UNKNOWN"
    had_vision_of_killer: bool = False
    enemies_count: int = 0
```

Optional fields use `Optional[T]` with a default of `None`. Lists use `Field(default_factory=list)`.

### Python — Settings via Environment Variables

All configuration is centralized in `ProjectB/settings.py`. Modules import named constants from there — never call `os.getenv()` directly in business logic:

```python
from settings import GEMINI_API_KEY, SUPABASE_URL, RIOT_API_KEY
```

### Python — Logging Pattern

Every module defines a module-level logger using `__name__`:

```python
logger = logging.getLogger(__name__)
```

Log calls follow severity:
- `logger.debug()` for cache hits and trace info
- `logger.warning()` for non-fatal misconfigurations
- `logger.error()` for caught exceptions

### Python — Guard Patterns for External Dependencies

Imports of OS-level packages (`mss`, `pystray`) are not at module top-level in test contexts. Tests insert the parent path manually:

```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
```

### JavaScript — Screen Structure Pattern

Each screen file exports a single default function component. Internal sub-components (not reusable) are defined as private functions in the same file above the default export:

```jsx
function ScoreBadge({ score }) { ... }     // private sub-component
function StatCard({ label, value }) { ... } // private sub-component

export default function SummonerProfileScreen() { ... }
```

### JavaScript — API Calls Pattern

All HTTP calls go through `ProjectB-frontend/src/services/api.js`. Functions use `fetch()` directly (no axios). Errors are thrown and caught by the calling screen:

```js
const response = await fetch(`${BASE_URL}/summoner/...`)
if (!response.ok) {
  const error = await response.json().catch(() => ({}))
  throw new Error(error.detail || `Erro ${response.status}`)
}
return response.json()
```

Fallback-safe endpoints (non-critical) return `null` or `{}` instead of throwing:

```js
if (!response.ok) return null
```

### JavaScript — Navigation Pattern

All navigation uses React Router's `useNavigate`. Routes are defined centrally in `ProjectB-frontend/src/App.jsx`. Screens use `useParams` to extract URL parameters.

---

## Style & Formatting

### Python

- No formatter config detected (no `black`, `ruff`, `isort` config files)
- Style is consistent: 4-space indentation, single blank lines between functions, double blank lines between top-level sections
- Type hints used throughout — return types, parameter types, and `Optional[T]` annotations
- f-strings used for all string interpolation: `f"Erro ao ler cache para {match_id}: {e}"`

### JavaScript/JSX

**Linter:** ESLint 9 with flat config — `ProjectB-frontend/eslint.config.js`

**Plugins active:**
- `eslint-plugin-react-hooks` (hooks rules enforced)
- `eslint-plugin-react-refresh` (Vite HMR compatibility)

**Key rules:**
- `no-unused-vars: error` with exception for `^[A-Z_]` pattern (constants and intentional ignores)
- `react-hooks/set-state-in-effect: off` (explicitly disabled)
- `ecmaVersion: 2020`, JSX enabled, `sourceType: module`

**No Prettier config detected.** Indentation is 2 spaces throughout JSX files.

**Tailwind CSS** is the styling system. No CSS modules or styled-components. Class names are applied inline on JSX elements. Custom utility classes defined in `src/index.css`: `.shimmer-bg`, `.glow-purple`, `.scoreGlow`, `.text-premium`.

---

## Error Handling

### Python

**try/except for I/O and external calls:**

```python
try:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    ...
except (json.JSONDecodeError, OSError):
    return dict(_DEFAULTS)
```

Exceptions from external services (Supabase, AI APIs) are caught with broad `except Exception as e:` and logged. Functions return `None` on failure rather than propagating:

```python
except Exception as e:
    logger.error(f"Erro ao ler cache para {match_id}: {e}")
return None
```

**HTTP error handling in FastAPI:** `HTTPException` is raised with appropriate status codes. Rate limit checks raise `429` explicitly.

### JavaScript

**API functions throw on non-ok status** for critical paths. Callers in screens handle errors with `try/catch` and set local error state.

**Non-critical API calls return safe defaults** (null/empty object) rather than throwing, so the UI can degrade gracefully.

---

## Documentation

### Python

- **Module docstrings** on every file (triple-quoted `"""..."""`)
- **Function docstrings** on public functions and complex private helpers:

```python
def get_config(config_dir: str | None = None) -> dict:
    """Retorna configuração atual. Usa defaults se config.json não existir."""
```

- **Inline comments** for non-obvious logic, especially in `context_builder.py` and `game_rules.py`
- **Section header comments** using the `# ─────` divider pattern for visual organization

### JavaScript

- **No JSDoc** found in any frontend files
- **Inline comments** are minimal and only for non-obvious logic
- The `CLAUDE.md` file at `ProjectB-frontend/CLAUDE.md` serves as the primary developer guide (design tokens, screen flow, file structure)

---

*Convention analysis: 2026-03-30*
