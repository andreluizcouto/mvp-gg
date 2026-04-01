# Phase 5: Regression Safety Net - Research

**Researched:** 2026-04-01  
**Domain:** Regression test strategy for coaching ownership/privacy and frontend status rendering  
**Confidence:** MEDIUM

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
### Cobertura backend crítica (prioridade da fase)
- **D-01:** A primeira frente da Fase 5 será cobertura de regressão para os endpoints públicos de coaching e status.
- **D-02:** Regra não-negociável: nunca expor conteúdo de análise quando faltar evidência local válida.
- **D-03:** Em acesso sem ownership/contexto correto, a API deve responder com estado seguro (`private` no frontend derivado de contexto ausente, ou `insufficient_data`/indisponível no backend), sem texto de análise.

### Fluxo de ownership e privacidade (app desktop + web)
- **D-04:** O app desktop é somente sinalizador de prontidão e direcionamento: avisa que a análise ficou pronta e leva para o link direto da partida.
- **D-05:** O usuário deve conseguir ver apenas a própria análise (riot_id + match_id corretos); visualização de terceiros não deve liberar conteúdo.
- **D-06:** Testes devem validar explicitamente que link compartilhado sem identidade compatível nunca retorna análise.

### the agent's Discretion
- Seleção exata dos casos de teste complementares (rate-limit, schema shape e compatibilidade de payload) desde que não despriorize D-01..D-06.
- Organização dos testes entre arquivos existentes (`test_public_read_only_mode.py` e correlatos) ou novos módulos de regressão, mantendo padrão atual do backend.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| QUAL-01 | Automated tests cover the critical search, ingestion, analysis, and rendering paths most likely to regress | Backend matrix for `/coaching/status`, `/coaching/{match_id}`, ownership/privacy, and evidence gating; frontend smoke/render checks for SummonerProfile/Results status and safe fallbacks |
</phase_requirements>

## Summary

Backend already has strong pytest + `TestClient` regression style (heavy monkeypatch + fake Supabase/Riot clients) and already covers many safe-state contracts in `test_public_read_only_mode.py` and pipeline contracts in `test_evidence_pipeline.py`. This is the right base to extend rather than redesign.

Main remaining risk for D-01..D-06 is not core pipeline logic but **cross-surface ownership/privacy regressions**: mismatched `riot_id` access, direct-link behavior, and frontend status rendering drift when API contracts evolve. Frontend currently has no test framework configured and no test files, so critical rendering paths are unprotected.

**Primary recommendation:** Keep backend testing in current pytest pattern, and add a minimal frontend test harness focused only on high-risk status/ownership states (`ready/pending/failed/insufficient_data/private`) plus direct-link privacy behavior.

## Standard Stack

### Core
| Library | Version in repo | Purpose | Why Standard |
|---------|------------------|---------|--------------|
| pytest | `>=8.0.0` (backend requirements) | Backend regression tests | Already used across backend tests; fastest path for Phase 5 |
| fastapi.testclient | via FastAPI `0.115.0` | Endpoint contract tests | Existing tests already validate API behavior with this stack |
| monkeypatch fixture | pytest built-in | Isolate Supabase/Riot/network deps | Current test suite uses it extensively and consistently |

### Supporting
| Library | Version in repo | Purpose | When to Use |
|---------|------------------|---------|-------------|
| pytest-asyncio | `>=0.23.0` | Async unit tests (cache/pipeline functions) | For direct async function tests (`coach_ai`, `db`) |
| pytest-timeout | `>=2.3.0` | Prevent hanging tests | Keep on integration-like tests with async/gather |
| React + Vite app stack | React `^19.2.4`, Vite `^8.0.1` | Frontend rendering under test | Add lightweight component/screen smoke tests |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Extending pytest suites | New backend framework | Unnecessary migration cost/risk for this phase |
| Minimal frontend smoke tests | Full E2E suite first | Higher setup cost; slower feedback loop for immediate regression net |

**Installation (current backend test deps already present in `backend/requirements.txt`):**
```bash
pip install -r backend/requirements.txt
```

## Architecture Patterns

### Recommended Project Structure
```text
backend/tests/
├── test_public_read_only_mode.py      # extend ownership/privacy endpoint matrix
├── test_evidence_pipeline.py          # keep evidence/pipeline status contracts
├── test_*_security*.py                # validation/rate-limit helper coverage
└── fixtures/
   └── coaching_contracts.py           # new shared factories for snapshots/rows (recommended)

frontend/src/
├── screens/                           # ResultsScreen + SummonerProfileScreen
├── services/api.js                    # fetch + fallback behavior contracts
└── __tests__/                         # new smoke/render tests (recommended)
```

### Pattern 1: Contract-first backend endpoint tests
**What:** Assert public response shape + safe status + analysis redaction, not internal implementation details.  
**When to use:** `/coaching/status`, `/coaching/{match_id}`, regenerate, and ownership checks.  
**Existing example source:** `backend/tests/test_public_read_only_mode.py`.

### Pattern 2: Pipeline status gating tests
**What:** Assert source/status normalization (`riot_plus_local` vs `riot_only`) maps to safe external status.  
**When to use:** Any change in `coach_ai.py`, `db.py`, or status derivation helpers.  
**Existing example source:** `backend/tests/test_evidence_pipeline.py`.

### Pattern 3: Frontend status derivation tests (new)
**What:** Verify `ResultsScreen` and `SummonerProfileScreen` render expected trust/status signals from API states, including safe fallbacks.  
**When to use:** Any UI/status copy or status mapping changes.

### Anti-Patterns to Avoid
- **Testing only happy-path `ready`:** misses the highest-risk privacy/status regressions.
- **Mocking too deep into implementation internals:** brittle tests; prefer endpoint-level contract assertions.
- **Relying on manual browser checks for status rendering:** not repeatable for QUAL-01.

## Biggest Regression Gaps (Current)

1. **No explicit backend test for mismatched ownership on shared links (`match_id` correct, `riot_id` wrong).**  
   Risk: accidental analysis leakage (D-05/D-06).
2. **No frontend automated tests for `ResultsScreen` status mapping and direct-link privacy rendering.**  
   Risk: UI could mislabel/show content after refactors.
3. **No frontend tests for IA badge gating in `SummonerProfileScreen` (`status === "ready"` only).**  
   Risk: false trust signal.
4. **`api.js` swallows errors for coaching endpoints (`catch` fallback), but behavior is untested.**  
   Risk: regressions silently masked in prod UX.
5. **`backend/run_tests.py` uses stale hardcoded cwd (`Coach-AI-Project\\ProjectB`).**  
   Risk: non-repeatable local verification if teams depend on script.

## Concrete Test Strategy (Backend + Frontend, aligned to D-01..D-06)

### Backend (Plan 05-01 focus)
- Extend `test_public_read_only_mode.py` with a compact ownership matrix:
  - correct `match_id` + wrong `riot_id` => `status=insufficient_data`, `has_analysis=false`, `analysis=null`
  - no `riot_id` (if required enabled) => 422 (safe failure)
  - valid local-evidence snapshot + matching `riot_id` => only then `ready` with analysis
- Add explicit shared-link regression case for D-06:
  - simulate third-party viewer (no owner context) and assert no analysis exposure.
- Keep message contract assertions for unavailable/private-safe flows:
  - `"Coach indisponivel, baixe o app e jogue uma partida."`
- Add schema-shape regression assertion:
  - ensure `/coaching/{match_id}` response keys remain exactly safe public keys (already done in one case; extend to ownership mismatch case too).

### Frontend (Plan 05-02 focus)
- Add smoke/render tests for `ResultsScreen` and `SummonerProfileScreen`:
  - `coachingApiStatus=ready + hasAnalysis=true` => render coaching content
  - `pending|failed|insufficient_data|private` => correct status block copy and no analysis text leak
  - direct-link/no owner context path => private-safe presentation (or explicit intentional hidden coaching block behavior, locked in tests)
  - IA badge appears only when `status === "ready"` on match rows
- Add `api.js` behavior tests:
  - `fetchCoachingAnalysis` network error => safe fallback object
  - `fetchCoachingStatus` error => `{}`
  - invalid riotId normalization => omitted query param (safe default)

## Fixtures / Mocks Approach (stable, low maintenance)

### Recommended
- Create shared fixture factories for:
  - pipeline snapshot payloads (`ready/pending/insufficient_data/failed`)
  - coaching DB row payloads (`coaching_analysis`, `feedback_geral`, `external_status`)
  - common match/riot identifiers
- Keep monkeypatch boundaries at service edges only:
  - `get_supabase`, `get_pipeline_snapshot`, `get_pending_local_evidence`, Riot client methods

### Avoid
- Per-test ad-hoc payload dict duplication (already growing in `test_public_read_only_mode.py`).
- Mocking internal helper internals when endpoint contract assertions are enough.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| API endpoint test transport | Custom HTTP harness | `fastapi.testclient.TestClient` | Already proven in suite, less boilerplate |
| Async test runner | Manual event-loop wiring | `pytest-asyncio` | Stable async test semantics |
| Ownership/state fixtures | Inline dicts in every test | Shared factory fixtures | Reduces drift and maintenance cost |

**Key insight:** Phase 5 should optimize confidence-per-test, not build new infrastructure.

## Common Pitfalls

### Pitfall 1: False “ready” state leakage
**What goes wrong:** analysis shown even when source is `riot_only` or owner mismatch.  
**Why it happens:** status derivation or ownership query changes without regression coverage.  
**How to avoid:** enforce matrix tests for source + riot_id combinations.  
**Warning signs:** `has_analysis=true` with `insufficient_data` scenarios.

### Pitfall 2: Frontend trust-signal drift
**What goes wrong:** IA badge or status text appears for non-ready states.  
**Why it happens:** UI refactors without rendering tests.  
**How to avoid:** snapshot/assertion tests for state labels and badge gating.  
**Warning signs:** badge displayed for `pending/failed`.

### Pitfall 3: Silent fallback masking regressions
**What goes wrong:** API errors hidden by `catch` fallback cause unnoticed behavior changes.  
**Why it happens:** no direct tests around fallback contracts in `api.js`.  
**How to avoid:** explicit tests for fallback return shapes.

## Code Examples

### Backend contract assertion pattern
```python
resp = client.get("/coaching/BR1_X", params={"riot_id": "wrong#BR1"})
assert resp.status_code == 200
payload = resp.json()
assert payload["status"] == "insufficient_data"
assert payload["has_analysis"] is False
assert payload["analysis"] is None
```
Source: `backend/tests/test_public_read_only_mode.py` pattern.

### Frontend status gate pattern
```jsx
const hasCoaching = coachingStatus[match.match_id]?.status === "ready"
```
Source: `frontend/src/screens/SummonerProfileScreen.jsx`.

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Ad-hoc manual checks | Contract-focused pytest suites + deterministic status states | Better regression detection for trust/privacy paths |
| Single “has analysis” boolean UX | Explicit status model (`ready/pending/failed/insufficient_data/private`) | Safer user trust signaling |

**Deprecated/outdated in this repo context:**
- Hardcoded `backend/run_tests.py` cwd path (not portable/reliable for this phase).

## Open Questions

1. **Should direct-link mode render explicit `private` UI block or hide coaching section entirely?**
   - What we know: `ResultsScreen` derives `private`, but also gates coaching UI behind `!isDirectLink`.
   - What's unclear: expected visible UX for D-03/D-06 in final product behavior.
   - Recommendation: lock expected behavior in Phase 5 tests before implementation changes.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| PowerShell 6+ (`pwsh`) | Running automated shell verification in this environment | ✗ | — | Manual command execution outside agent session |
| Python/Node/npm local runtime | Backend/frontend test execution | Unknown (probe blocked by missing `pwsh`) | — | Human local verification |

**Missing dependencies with no fallback:**
- None for research itself.

**Missing dependencies with fallback:**
- `pwsh` missing in agent runtime; use manual local verification commands.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Backend: pytest (`>=8`), pytest-asyncio; Frontend: none detected (Wave 0 gap) |
| Config file | Backend: none detected (defaults); Frontend: none detected |
| Quick run command | `python -m pytest backend/tests/test_public_read_only_mode.py -v --tb=short` |
| Full suite command | `python -m pytest backend/tests -v --tb=short --timeout=30` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| QUAL-01 | Coaching ownership/privacy safe responses | backend integration | `python -m pytest backend/tests/test_public_read_only_mode.py -k "coaching and (status or blocks or hides)" -v` | ✅ |
| QUAL-01 | Evidence gating prevents unsafe ready/exposure | backend unit/integration | `python -m pytest backend/tests/test_evidence_pipeline.py -v` | ✅ |
| QUAL-01 | Frontend status rendering and IA badge trust signals | frontend component/screen smoke | `npm run test -- ResultsScreen SummonerProfileScreen` | ❌ Wave 0 |
| QUAL-01 | API service safe fallback behavior (`api.js`) | frontend unit | `npm run test -- api` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** backend targeted pytest file(s) relevant to changed contracts.
- **Per wave merge:** backend full suite + frontend smoke subset.
- **Phase gate:** backend full suite green + new frontend smoke suite green before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] Frontend test framework/config not present (add Vitest + React Testing Library, or equivalent minimal harness).
- [ ] `frontend/src/__tests__/ResultsScreen.test.*` — ownership/private/status rendering.
- [ ] `frontend/src/__tests__/SummonerProfileScreen.test.*` — IA badge gating.
- [ ] `frontend/src/services/__tests__/api.test.*` — fallback and query-param safety behavior.

## Sources

### Primary (HIGH confidence)
- `.planning/phases/05-regression-safety-net/05-CONTEXT.md` — D-01..D-06 decisions and scope.
- `backend/main.py` — `/coaching/status`, `/coaching/{match_id}`, `/coaching/{match_id}/regenerate`, status normalization and safe responses.
- `backend/coach_ai.py` — evidence gating, snapshot persistence, safe external status control.
- `backend/db.py` — snapshot normalization and external status derivation.
- `backend/tests/test_public_read_only_mode.py` — existing regression contracts for public read-only behavior.
- `backend/tests/test_evidence_pipeline.py` — pipeline/evidence status contract coverage.
- `frontend/src/services/api.js` — coaching fetch behavior and error fallbacks.
- `frontend/src/screens/ResultsScreen.jsx` — status derivation and direct-link behavior.
- `frontend/src/screens/SummonerProfileScreen.jsx` — IA badge gating and status consumption.
- `frontend/src/components/CoachingSection.jsx`, `frontend/src/components/AnalysisStatusBlock.jsx` — frontend trust/status rendering.

### Secondary (MEDIUM confidence)
- `backend/tests/test_security_hardening.py`, `backend/tests/test_match_history_pagination.py` — broader backend testing style consistency.
- `backend/requirements.txt`, `frontend/package.json`, `frontend/package-lock.json` — in-repo dependency versions.

### Tertiary (LOW confidence)
- None (no external web sources used in this research run).

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM — based on in-repo versions; registry verification unavailable in this environment.
- Architecture: HIGH — directly derived from current code and tests.
- Pitfalls: MEDIUM — inferred from code/test gaps and current behavior.

**Research date:** 2026-04-01  
**Valid until:** 2026-04-08 (fast-moving phase with pending frontend test-infra decisions)

