# Phase 2: Evidence Pipeline and Analysis Contracts - Research

**Researched:** 2026-04-01
**Domain:** FastAPI/Pydantic evidence normalization, stage verification, and analysis gating
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
### Verification checkpoints
- **D-01:** The evidence pipeline must use strong, formal checkpoints between stages rather than relying only on logs or ad hoc exceptions.
- **D-02:** Each major stage in the pipeline must validate both its input and its output before the next stage can proceed.
- **D-03:** The pipeline must fail closed by default when a checkpoint does not pass.

### Status model
- **D-04:** Each checkpoint must produce a structured machine-readable status, not just a boolean pass/fail.
- **D-05:** Checkpoint status must include a structured reason when a stage is rejected, blocked, or degraded.
- **D-06:** The status model should support distinctions such as accepted, invalid input, incomplete evidence, degraded-safe, ready, and blocked, or equivalent explicit categories.

### Internal versus external visibility
- **D-07:** The backend must keep detailed internal pipeline statuses for verification, debugging, and deterministic behavior.
- **D-08:** The frontend and user-facing product should consume only a summarized and safe external status model.
- **D-09:** External statuses should stay simple and product-oriented, such as ready, pending, insufficient_data, or failed, while detailed internal causes remain backend-only.

### the agent's Discretion
- Exact stage boundaries and naming for the checkpoint model
- Exact schema shape for internal versus external status payloads
- Whether checkpoint reasons are represented as enums, typed codes, structured objects, or a combination, as long as they stay machine-readable and deterministic

### Deferred Ideas (OUT OF SCOPE)
None - discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DATA-01 | System can assemble a complete post-game evidence bundle from Riot data and localhost-derived context before AI analysis runs | Standard stack, bundle contract, stage boundaries, and evidence completeness rules define how Riot + localhost inputs become one normalized bundle |
| DATA-02 | System rejects, flags, or safely degrades when the evidence bundle is incomplete, corrupt, or insufficient for trustworthy coaching | Status model, checkpoint reasons, degradation rules, and common pitfalls define fail-closed vs degraded-safe behavior |
| QUAL-02 | System performs explicit verification between ingestion, context building, AI output validation, and frontend delivery | Verification hooks, internal/external status split, and validation architecture map the required checks and tests |
</phase_requirements>

## Summary

The current backend already has the raw building blocks for this phase, but the evidence pipeline is split across two incompatible paths. The Riot-driven `/analyze` path builds a typed `MatchContext` through `ContextBuilder`, while the localhost upload path sends loose event data and champion names into `analyze_postgame()` as plain strings. That means the system validates request shapes, but it does not yet define a single analysis-ready evidence bundle or preserve stage-level verification between ingestion, normalization, analysis, persistence, and delivery.

Phase 2 should not introduce a new architecture. It should formalize the existing one around a single internal `AnalysisEvidenceBundle` contract, a strict checkpoint/status model, and explicit gate functions between stages. The planner should treat this as backend contract hardening, not prompt tuning. The highest-leverage change is to move from "analysis succeeded or failed" to "every stage emits a typed result with status, reasons, and sanitized external visibility."

**Primary recommendation:** Standardize both analysis entry points on one Pydantic evidence-bundle contract plus one internal checkpoint/result model, and make every downstream action consume that contract instead of ad hoc dicts and strings.

## Project Constraints (from CLAUDE.md)

- Improve the existing brownfield backend, frontend, localhost integration, and analysis flow instead of replacing them.
- Backend must own critical trust decisions and never rely on frontend logic for security or business-critical behavior.
- Important flows should include verification between stages plus test coverage.
- Web browser is the primary product surface; mobile is out of scope.
- Keep v1 simple and focused on trust, consistency, and safety.
- Riot public APIs and localhost-derived context must remain viable data sources.
- Use GSD workflow entry points before repo edits; research output still needs to be written even when `commit_docs` is false.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | Repo: `0.115.0`; PyPI current: `0.135.2` published 2026-03-23 | Route orchestration and response filtering | Already owns backend API flow; official `response_model` filtering is the right mechanism for safe external status payloads |
| Pydantic | Repo: `>=2.8.0`; PyPI current: `2.12.5` published 2025-11-26 | Evidence bundle contracts, stage results, and validators | Already codebase standard; `ConfigDict`, `field_validator`, and `model_validator` fit bundle validation and cross-field completeness checks |
| Python `enum.StrEnum` | Stdlib, Python `3.11+` | Deterministic machine-readable status/reason codes | Best fit for internal stage statuses and external summarized states without hand-rolled string constants |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `httpx` | Repo: `>=0.28.1,<1.0.0`; PyPI current: `0.28.1` published 2024-12-06 | Riot/local HTTP fetches already used by pipeline | Keep existing client; no new transport layer is needed for this phase |
| `supabase` | Repo: `>=2.11.0`; PyPI current: `2.28.0` published 2026-02-10 | Persisting bundle-derived outputs and status snapshots | Use for persisted analysis/status records once the internal contract exists |
| `google-genai` | Repo: `1.10.0`; PyPI current: `1.66.0` published 2026-03-04 | Existing AI execution path | Keep current SDK for this phase; contract hardening matters more than SDK upgrade |
| `pytest` / `pytest-asyncio` / `pytest-timeout` | Repo: `>=8.0.0`, `>=0.23.0`, `>=2.3.0`; PyPI current seen: `pytest-asyncio 1.3.0` on 2025-11-10, `pytest-timeout 2.4.0` on 2025-05-05 | Verification hooks and regression tests | Extend current backend tests around stage gates and failure states |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pydantic models for bundle + stage results | Plain dicts + helper functions | Faster to start, but repeats the current problem: no single trusted contract and weak cross-stage verification |
| Enum-based reason/status codes | Freeform strings | Easier initially, but harder to test, summarize, and keep deterministic across stages |
| One normalized bundle for all analysis paths | Separate Riot and localhost contracts | Preserves current divergence and makes later UX/status work much harder |

**Installation:**
```bash
py -m pip install -r ProjectB/requirements.txt
```

**Version verification:** Current upstream package versions were verified from PyPI package pages on 2026-04-01. The phase should remain on the repo's existing versions unless a later implementation task proves an upgrade is required.

## Architecture Patterns

### Recommended Project Structure
```text
ProjectB/
├── schemas.py                  # Public API request/response models
├── analysis_contracts.py       # New internal bundle, checkpoint, and status models
├── evidence_pipeline.py        # New bundle builder + gate functions
├── context_builder.py          # Riot normalization into MatchContext
├── coach_ai.py                 # Analysis execution + AI output validation
├── postgame_analyzer.py        # Localhost-derived multimodal analysis runner
└── main.py                     # Route orchestration only
```

### Pattern 1: Single Internal Evidence Bundle
**What:** Introduce one internal Pydantic model that represents the analysis-ready evidence payload regardless of entry path.
**When to use:** For any step after request/auth validation and before AI execution.
**Example:**
```python
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field, model_validator


class EvidenceSource(StrEnum):
    RIOT_ONLY = "riot_only"
    RIOT_PLUS_LOCAL = "riot_plus_local"


class ExternalAnalysisStatus(StrEnum):
    READY = "ready"
    PENDING = "pending"
    INSUFFICIENT_DATA = "insufficient_data"
    FAILED = "failed"


class AnalysisEvidenceBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    match_id: str = Field(min_length=3, max_length=80)
    riot_id: str = Field(min_length=3, max_length=64)
    source: EvidenceSource
    match_context: dict
    local_events: list[dict] = Field(default_factory=list)
    images_present: int = 0

    @model_validator(mode="after")
    def verify_completeness(self):
        if self.source == EvidenceSource.RIOT_PLUS_LOCAL and not self.local_events:
            raise ValueError("local evidence required for riot_plus_local bundle")
        return self
```
Source basis: Pydantic model config and model validators support strict contracts and whole-model checks.

### Pattern 2: Every Stage Returns a Typed Checkpoint Result
**What:** Replace ad hoc booleans/logging with one internal result object per stage.
**When to use:** Ingestion, evidence normalization, AI execution, AI output validation, persistence, and delivery.
**Example:**
```python
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field


class StageStatus(StrEnum):
    ACCEPTED = "accepted"
    INVALID_INPUT = "invalid_input"
    INCOMPLETE_EVIDENCE = "incomplete_evidence"
    DEGRADED_SAFE = "degraded_safe"
    READY = "ready"
    BLOCKED = "blocked"


class StageResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage: str
    status: StageStatus
    reason_codes: list[str] = Field(default_factory=list)
    details: dict = Field(default_factory=dict)
```

### Pattern 3: Internal Status, External Summary
**What:** Persist detailed backend-only checkpoint results, but expose only summarized product-safe status values.
**When to use:** Any route that returns readiness or coaching availability to the frontend.
**Example:**
```python
from fastapi import APIRouter
from pydantic import BaseModel


class PublicCoachingState(BaseModel):
    match_id: str
    status: ExternalAnalysisStatus


@router.get("/coaching/{match_id}", response_model=PublicCoachingState)
async def get_coaching_state(match_id: str):
    internal = await load_internal_pipeline_status(match_id)
    return PublicCoachingState(match_id=match_id, status=internal.external_status)
```
Source basis: FastAPI `response_model` validates and filters output to the declared public schema.

### Anti-Patterns to Avoid
- **Route-owned pipeline logic:** `main.py` already orchestrates too much. Do not keep adding normalization, gating, and persistence logic inline in route handlers.
- **String-only match context:** `_process_local_upload()` currently builds `match_context` as freeform text from `player_map`; that is not a trusted evidence contract.
- **Success-by-side-effect:** `_local_jobs[riot_id] = None` and later checking Supabase is not enough verification state for this phase.
- **Fallback analysis as success:** `CoachAI` fallback text and empty `save_coaching_analysis()` rows must not be treated as the same state as verified-ready analysis.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Schema validation | Manual dict key checks spread across routes | Pydantic models + validators | Cross-field completeness rules are exactly what Pydantic is for |
| Stage statuses | Freeform status strings in many files | Shared `StrEnum` + `StageResult` models | Keeps backend deterministic and testable |
| Public payload filtering | Manual dict pruning in each route | FastAPI `response_model` | Prevents accidental leakage and keeps frontend contract stable |
| Evidence readiness | Implicit meaning from cache rows and `None` sentinels | Explicit internal checkpoint objects | Current implicit state is ambiguous and brittle |

**Key insight:** This phase is mostly about removing ambiguity. Custom, untyped glue code will recreate the exact trust problem the phase is supposed to solve.

## Common Pitfalls

### Pitfall 1: Treating Riot-only and localhost uploads as equivalent inputs
**What goes wrong:** The system analyzes two different evidence shapes under one product concept of "coaching".
**Why it happens:** `/analyze` produces typed `MatchContext`; `/local/upload` feeds `analyze_postgame()` loose event dicts plus a text blob.
**How to avoid:** Normalize both paths into one internal bundle model with a declared `source` and completeness rules.
**Warning signs:** Prompt-building functions accept raw strings or dicts instead of typed bundle objects.

### Pitfall 2: Conflating degraded-safe with ready
**What goes wrong:** Users can see analysis that looks complete when some evidence was missing or AI output fell back.
**Why it happens:** Current code often checks only truthiness of saved analysis text.
**How to avoid:** Keep separate internal statuses for `degraded_safe` and `ready`; map both carefully to external states.
**Warning signs:** Any code path where fallback text, empty insights, or missing local evidence still returns as normal success.

### Pitfall 3: Verifying only inputs, not outputs
**What goes wrong:** A route accepts valid JSON, but downstream stages still emit incomplete or misleading artifacts.
**Why it happens:** Request validation exists today, but stage output contracts do not.
**How to avoid:** Add output verification after bundle build, after AI response parse, and before persistence/delivery.
**Warning signs:** Functions return raw `dict`/`str` without a typed stage result.

### Pitfall 4: Leaking internal failure detail into public product states
**What goes wrong:** Frontend becomes coupled to backend internals or exposes sensitive/debug-only reasons.
**Why it happens:** Public and private status payloads are not currently separated.
**How to avoid:** Define one internal checkpoint schema and one external summarized schema up front.
**Warning signs:** Frontend starts branching on backend-specific reason strings.

## Code Examples

Verified patterns from official sources and current codebase:

### Strict Request/Contract Base
```python
from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
```
Use this as the base for internal bundle and checkpoint models, not only public request models.

### Whole-Model Completeness Validation
```python
from pydantic import BaseModel, model_validator


class Bundle(BaseModel):
    match_id: str
    local_events: list[dict]
    source: str

    @model_validator(mode="after")
    def require_local_events_for_local_source(self):
        if self.source == "riot_plus_local" and not self.local_events:
            raise ValueError("missing local evidence")
        return self
```
Source basis: Pydantic model validators support checks across the entire validated model.

### Output Filtering for Safe External States
```python
from typing import Any
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class PublicState(BaseModel):
    match_id: str
    status: str


@app.get("/coaching/{match_id}", response_model=PublicState)
async def get_state(match_id: str) -> Any:
    internal = {"match_id": match_id, "status": "ready", "debug": {"reason_codes": ["AI_OK"]}}
    return internal
```
The public response excludes undeclared internal debug fields.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Request validation only | Request validation plus explicit stage output contracts | Current best practice in Pydantic v2/FastAPI era | Better fit for multi-stage pipelines where "valid input" is not enough |
| Freeform strings for internal state | Enum-like machine-readable codes with schema-backed payloads | Mature backend/API practice | Easier tests, safer frontend mapping, less drift |
| Route handlers doing orchestration and transformation | Thin routes calling pipeline services | Long-standing FastAPI service-layer pattern | Cleaner verification and smaller regression surface |

**Deprecated/outdated:**
- Treating a populated DB row as equivalent to a verified analysis result.
- Treating AI fallback prose as a normal success state.
- Building analysis context from prompt-ready strings instead of typed contracts.

## Open Questions

1. **Should Phase 2 persist internal checkpoint history or only latest status?**
   - What we know: The phase requires explicit verification between stages, and current persistence only stores final analysis-ish fields in `ai_cache`.
   - What's unclear: Whether planner should add a new column/JSON blob/table for internal stage results now, or keep it transient in code plus logs.
   - Recommendation: Persist at least the latest internal checkpoint snapshot per match; full history is optional.

2. **How far should localhost-derived evidence be required for "ready" status?**
   - What we know: Product requirement says analysis runs from Riot and localhost-derived context, but current web endpoints can analyze Riot-only.
   - What's unclear: Whether Riot-only analysis becomes blocked in Phase 2 or marked degraded-safe.
   - Recommendation: Keep Riot-only path possible internally, but do not surface it as equivalent to a verified full evidence analysis.

3. **Should postgame analysis text be normalized into structured insights in this phase?**
   - What we know: `/local/upload` currently stores plain `coaching_analysis` text, while `/analyze` produces `insights` plus `feedback`.
   - What's unclear: Whether Phase 2 should unify output shape or only unify input/verification shape.
   - Recommendation: Unify input and stage statuses now; leave deeper output-shape convergence to Phase 3 unless required for public status delivery.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Frontend/package tooling, helper scripts | Yes | `v24.14.0` | — |
| `npm.cmd` | Frontend commands under PowerShell | Yes | `11.9.0` | Use `npm.cmd` instead of `npm` in this shell |
| Python runtime (`python` / `py`) | Backend implementation and tests | No | — | None |
| `pytest` | Backend verification | No | — | None until Python is installed |
| Supabase service | Persisted analysis/status checks | Not probed from local shell | — | Mock in tests |
| Riot API access | Live/local evidence completion | Not probed from local shell | — | Mock in tests |
| Gemini/Anthropic API access | Analysis execution | Not probed from local shell | — | Mock in tests |

**Missing dependencies with no fallback:**
- A callable local Python runtime. Planning can proceed, but backend implementation and test execution on this machine are blocked until Python is installed or exposed on `PATH`.

**Missing dependencies with fallback:**
- `npm` PowerShell shim is blocked by execution policy, but `npm.cmd` works.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `pytest` + `fastapi.testclient` + `pytest-asyncio` |
| Config file | none detected |
| Quick run command | `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests/test_public_read_only_mode.py ProjectB/tests/test_security_hardening.py -x` |
| Full suite command | `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests -x` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-01 | Build one normalized evidence bundle from Riot and localhost-derived evidence | unit | `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests/test_evidence_pipeline.py::test_builds_normalized_bundle_from_riot_and_local -x` | No, Wave 0 |
| DATA-02 | Reject invalid/incomplete evidence and distinguish degraded-safe from blocked | unit | `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests/test_evidence_pipeline.py::test_incomplete_bundle_returns_checkpoint_reason -x` | No, Wave 0 |
| QUAL-02 | Verify each pipeline stage between ingestion, context build, analysis, and delivery | unit/integration | `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests/test_evidence_pipeline.py::test_stage_results_gate_downstream_execution -x` | No, Wave 0 |
| QUAL-02 | Public routes expose only summarized safe status | integration | `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests/test_public_read_only_mode.py -k coaching -x` | Yes |

### Sampling Rate
- **Per task commit:** `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests/test_evidence_pipeline.py -x`
- **Per wave merge:** `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests/test_public_read_only_mode.py ProjectB/tests/test_security_hardening.py ProjectB/tests/test_coach_ai_cache.py -x`
- **Phase gate:** `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests -x`

### Wave 0 Gaps
- [ ] `ProjectB/tests/test_evidence_pipeline.py` — bundle contract, checkpoint status, and failure-state coverage for DATA-01/DATA-02/QUAL-02
- [ ] Internal pipeline helper extraction (`analysis_contracts.py` / `evidence_pipeline.py`) so tests target functions instead of route internals
- [ ] Local Python runtime available on this machine so automated verification can actually run

## Sources

### Primary (HIGH confidence)
- Pydantic models docs: https://docs.pydantic.dev/latest/concepts/models/ - strict model config and handling of extra data
- Pydantic validators docs: https://docs.pydantic.dev/latest/concepts/validators/ - `field_validator` and `model_validator` behavior
- FastAPI response model docs: https://fastapi.tiangolo.com/tutorial/response-model/ - response filtering and validation for public payloads
- Python enum docs: https://docs.python.org/3/library/enum.html - `StrEnum` for deterministic string-backed status codes
- FastAPI PyPI page: https://pypi.org/project/fastapi/ - current upstream version and publish date
- Pydantic PyPI page: https://pypi.org/project/pydantic/ - current upstream version and publish date
- HTTPX PyPI page: https://pypi.org/project/httpx/ - current upstream version and publish date
- Supabase PyPI page: https://pypi.org/project/supabase/ - current upstream version and publish date
- Google Gen AI PyPI page: https://pypi.org/project/google-genai/ - current upstream version and publish date
- Repo sources: `ProjectB/main.py`, `ProjectB/schemas.py`, `ProjectB/context_builder.py`, `ProjectB/coach_ai.py`, `ProjectB/postgame_analyzer.py`, `ProjectB/db.py`, `ProjectB/live_coach.py`

### Secondary (MEDIUM confidence)
- `ProjectB/tests/test_public_read_only_mode.py` and `ProjectB/tests/test_security_hardening.py` - existing verification patterns and route protection expectations
- `.planning/codebase/ARCHITECTURE.md` and `.planning/codebase/CONCERNS.md` - current architecture summary and fragile-area context

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - existing repo stack plus official docs/PyPI pages are aligned
- Architecture: HIGH - recommendations are derived directly from current code paths and locked phase decisions
- Pitfalls: HIGH - they map to concrete gaps visible in `main.py`, `db.py`, and the split analysis flows

**Research date:** 2026-04-01
**Valid until:** 2026-05-01
