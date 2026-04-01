# Testing

**Analysis Date:** 2026-03-30

---

## Test Setup

### Python (ProjectB/)

**Framework:** pytest

**Key packages (from `ProjectB/requirements.txt`):**
- `pytest >= 8.0.0`
- `pytest-asyncio >= 0.23.0` — async test support
- `pytest-timeout >= 2.3.0` — per-test timeout enforcement

**No pytest.ini, setup.cfg, or pyproject.toml found.** Configuration is passed via CLI flags in the test runner.

**Test runner script:** `ProjectB/run_tests.py`

```python
subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "--timeout=30"],
    cwd=r"c:\Users\andre\Desktop\Coach-AI-Project\ProjectB"
)
```

**Default timeout:** 30 seconds per test (via `--timeout=30`).

### JavaScript (ProjectB-frontend/)

**No test framework configured.** No Vitest, Jest, or any test runner found in `package.json`. No test files exist in the frontend codebase. The `package.json` scripts are: `dev`, `build`, `lint`, `preview` — no `test` script.

---

## Test Types

### Python

**Unit tests — primary type.** All 5 test files target individual functions/modules in isolation.

| Test file | Module under test | Focus |
|---|---|---|
| `tests/test_app_config.py` | `app_config.py` | Config read/write/defaults/corruption |
| `tests/test_guardrails.py` | `coach_guardrails.py` | AI output linting, violation detection, sanitization |
| `tests/test_postgame.py` | `postgame_analyzer.py` | Prompt building, AI dispatch with mocked providers |
| `tests/test_live_capture.py` | `minimap_capture.py` | File save logic, collision handling |
| `tests/test_minimap_capture.py` | `minimap_capture.py` | Screen capture region calculations |

**Integration tests:** One async integration-style test in `test_postgame.py` patches multiple AI provider calls and verifies fallback behavior across providers.

**No E2E tests** for either project.

---

## Test Patterns

### Path Setup

Every test file manually inserts the parent directory into `sys.path` to allow imports without installing the package:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
```

### Test Function Naming

All tests use `test_<what_it_tests>` naming — descriptive and action-oriented:

```python
def test_get_config_returns_defaults_when_no_file(...)
def test_save_and_reload_config(...)
def test_get_config_returns_defaults_for_corrupted_json(...)
def test_paragraph_missing_timestamp()
def test_good_output_no_violations()
```

### Temporary Directories (Filesystem Tests)

File I/O tests use pytest's `tmp_path` fixture exclusively. No hardcoded temp paths:

```python
def test_save_and_reload_config(tmp_path):
    from app_config import get_config, save_config
    save_config({"minimap_left": True, "minimap_large": False}, config_dir=str(tmp_path))
    cfg = get_config(config_dir=str(tmp_path))
    assert cfg["minimap_left"] is True
```

For non-pytest tests (`test_live_capture.py`), `tempfile.TemporaryDirectory()` context managers are used:

```python
with tempfile.TemporaryDirectory() as tmpdir:
    path = save_minimap_to_disk(img, tmpdir, "death", 945.0)
    assert os.path.exists(path)
```

### Fixtures for Complex Test Data

`test_guardrails.py` defines module-level dict fixtures (`BASE_INPUT`, `GOOD_OUTPUT`) that serve as reusable base state. Tests mutate copies via `dict(GOOD_OUTPUT)` rather than modifying the originals:

```python
BASE_INPUT = {
    "match_id": "TEST_001",
    "kda": "13/5/11",
    "deaths": [...],
    ...
}

def test_paragraph_missing_timestamp():
    output = dict(GOOD_OUTPUT)            # copy, not mutate
    output["feedback_geral"] = "..."      # override specific field
    violations = lint(BASE_INPUT, output)
    assert len([v for v in violations if "MISSING_TIMESTAMP" in v]) >= 1
```

### Mocking Pattern

External dependencies are patched with `unittest.mock.patch` and `AsyncMock`:

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_analyze_postgame_calls_ai_with_images():
    with patch("postgame_analyzer._call_haiku_batch", new_callable=AsyncMock, return_value="Analise mock") as mock_haiku, \
         patch("postgame_analyzer._call_gemini_batch", new_callable=AsyncMock, side_effect=Exception("quota")), \
         patch("postgame_analyzer._load_image_bytes", return_value=b"fake_png_bytes"):
        result = await analyze_postgame(events, image_paths, match_context)
    assert result == "Analise mock"
    mock_haiku.assert_called_once()
```

For hardware/screen capture mocks (`test_minimap_capture.py`), `MagicMock` is used to simulate `mss` context managers:

```python
def _make_mock_screenshot(w, h):
    mock = MagicMock()
    mock.size = (w, h)
    mock.bgra = b"\x00\x00\x00\xff" * (w * h)
    return mock

def test_capture_default_is_bottom_right():
    with patch("mss.mss") as mock_mss:
        ctx = mock_mss.return_value.__enter__.return_value
        ctx.grab.return_value = _make_mock_screenshot(200, 200)
        minimap_capture.capture_minimap(1920, 1080)
        region = ctx.grab.call_args[0][0]
        assert region["left"] > 960
```

### Async Tests

Async tests use `@pytest.mark.asyncio` decorator. No `asyncio_mode = "auto"` config detected, so the decorator is applied per-test.

### Assert Style

Plain `assert` statements throughout. Failure messages are included for complex assertions:

```python
assert violations == [], f"Output OK gerou violações inesperadas: {violations}"
assert "VIOL_GLOBAL_MAP_VISION_CLAIM" in violations, (
    f"Esperado VIOL_GLOBAL_MAP_VISION_CLAIM, obtido: {violations}"
)
```

---

## Test Coverage

### Covered Areas

- `ProjectB/app_config.py` — fully covered: defaults, save/reload, unknown keys, corrupted JSON
- `ProjectB/coach_guardrails.py` — well covered: all major violation types (7 violation tests), `needs_rewrite()`, `sanitize_minimally()`, and the "no violations" happy path
- `ProjectB/postgame_analyzer.py` — prompt construction and AI provider fallback covered
- `ProjectB/minimap_capture.py` — file save with collision detection, region calculation for left/right/large/normal minimap

### Uncovered Areas

- `ProjectB/main.py` — FastAPI route handlers have no tests
- `ProjectB/coach_ai.py` — AI prompt building, Gemini API calls, cache logic (`_get_ai_cache`, `_set_ai_cache`) have no tests
- `ProjectB/context_builder.py` — core match analysis logic (death classification, vision analysis, CS benchmark computation) has no tests
- `ProjectB/riot_client.py` — Riot API client, disk cache layer have no tests
- `ProjectB/db.py` — Supabase persistence layer has no tests
- `ProjectB/live_coach.py`, `ProjectB/live_game_client.py` — live game session logic has no tests
- `ProjectB-frontend/` — zero test coverage (no test framework configured)

---

## Running Tests

```bash
# Run all Python tests (from ProjectB/ directory)
cd ProjectB
python -m pytest tests/ -v --tb=short --timeout=30

# Alternatively use the runner script
cd ProjectB
python run_tests.py

# Run a single test file
cd ProjectB
python -m pytest tests/test_guardrails.py -v

# Run a single test by name
cd ProjectB
python -m pytest tests/test_guardrails.py::test_good_output_no_violations -v

# Frontend — lint only (no test runner configured)
cd ProjectB-frontend
npm run lint
```

---

*Testing analysis: 2026-03-30*
