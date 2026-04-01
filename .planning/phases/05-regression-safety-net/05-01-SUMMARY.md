---
phase: 05-regression-safety-net
plan: "01"
subsystem: backend
tags: [testing, regression, fixtures, coaching, ownership]
dependency_graph:
  requires: []
  provides: [backend-regression-suite, coaching-fixtures, ownership-tests, pagination-tests]
  affects: [backend/tests]
tech_stack:
  added: [pytest, pytest-asyncio, pytest-timeout]
  patterns: [fixture-factories, contract-testing, mocking]
key_files:
  created:
    - backend/tests/fixtures/__init__.py
    - backend/tests/fixtures/coaching_contracts.py
  modified:
    - backend/tests/test_public_read_only_mode.py
    - backend/tests/test_match_history_pagination.py
    - backend/run_tests.py
decisions:
  - "Use shared fixture factories (ready/pending/insufficient/failed snapshots) to reduce test duplication across suites"
  - "run_tests.py uses Path(__file__).resolve().parent for project-relative cwd instead of hardcoded absolute path"
  - "Fixed _missing_local_evidence() bug: localhost_only should map to pending, not insufficient_data (only riot_only has no local evidence)"
metrics:
  duration: ~60min
  completed: "2026-04-01"
---

# Phase 05 Plan 01: Backend Critical Regression Coverage + Fixtures

## One-liner

Created reusable coaching contract fixtures, extended ownership/privacy regression matrix (19 tests), fixed `_missing_local_evidence` bug (`localhost_only` → `pending`), and added pagination regression suite — 28/28 tests passing.

## Tasks Completed

| # | Task | Status | Files |
|---|------|--------|-------|
| 1 | Create fixture factories (ready/pending/insufficient/failed snapshots) | ✅ Done | fixtures/coaching_contracts.py |
| 2 | Extend ownership/shared-link/no-evidence regression matrix | ✅ Done | test_public_read_only_mode.py |
| 3 | Fix _missing_local_evidence(): localhost_only → pending | ✅ Done | backend/main.py |
| 4 | Stabilize pipeline/status checks + portable run_tests.py | ✅ Done | run_tests.py |
| 5 | Expand search/pagination regression (summoner endpoints) | ✅ Done | test_match_history_pagination.py |

## Changes Made

### coaching_contracts.py — fixture factories
Created `ready_snapshot()`, `pending_snapshot()`, `insufficient_snapshot()`, `failed_snapshot()` returning canonical payload dictionaries aligned to current public response schema.

### test_public_read_only_mode.py — 19 tests
Added explicit contract tests for:
- Ownership mismatch: correct match_id + wrong riot_id → safe non-ready state, no analysis payload
- Shared-link: missing/incompatible ownership → no analysis text leaked
- Valid ownership + valid local evidence → only path that exposes ready analysis
- `BR1_PENDING` (localhost_only source) → `pending` (not `insufficient_data`)

### backend/main.py — _missing_local_evidence() bug fix
Changed `if source in {"riot_only", "localhost_only"}` to `if source == "riot_only"`.
`localhost_only` = desktop app has events, Riot context pending → correct status is `pending`.
`riot_only` = only Riot API data, no local events → `insufficient_data`.

### run_tests.py — portable entrypoint
Replaced hardcoded absolute cwd with `Path(__file__).resolve().parent` for project-relative path.

### test_match_history_pagination.py — 9 tests
Added regression tests for `/summoner/{game_name}/{tag_line}` and `/summoner/{game_name}/{tag_line}/refresh` covering pagination fields (`has_more`, `next_offset`), match item shape, and malformed params.

## Deviations from Plan

None — all tasks executed as planned. One bonus bug found and fixed: `_missing_local_evidence()` incorrectly treated `localhost_only` as missing evidence.

## Known Stubs

None.

## Self-Check: PASSED

- ✅ 28/28 backend tests passing: `python -m pytest tests/ -v --tb=short --timeout=30`
- ✅ Fixture factories confirmed via grep: ready/pending/insufficient/failed snapshots exist
- ✅ `_missing_local_evidence` fix verified by `test_coaching_status_exposes_safe_external_states`
- ✅ run_tests.py uses project-relative path
