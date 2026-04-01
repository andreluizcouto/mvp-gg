---
phase: 02-evidence-pipeline-and-analysis-contracts
plan: 02
subsystem: api
tags: [fastapi, pydantic, pytest, evidence-pipeline]
requires:
  - phase: 02-evidence-pipeline-and-analysis-contracts
    provides: strict evidence bundle contracts and stage gates from 02-01
provides:
  - Riot and localhost entry points wired to one shared evidence pipeline contract
  - localhost-only uploads persisted as pending artifacts with explicit blocked/degraded-safe handling
  - route-level regression tests proving analyze/local upload rewiring and riot+local join behavior
affects: [analyze-route, local-upload, postgame-analysis]
key-files:
  modified:
    - ProjectB/coach_ai.py
    - ProjectB/main.py
    - ProjectB/postgame_analyzer.py
    - ProjectB/tests/test_public_read_only_mode.py
completed: 2026-04-01
---

# Phase 02 Plan 02 Summary

Implemented route-boundary rewiring so both Riot and localhost evidence paths pass through the shared pipeline contract before analysis proceeds.

## What Changed

- `run_full_analysis()` now builds a shared evidence bundle, applies deterministic stage gates (`ingestion` -> `context_build` -> `analysis_generation` -> `output_validation` -> `delivery`), and treats Riot-only context as `degraded_safe` while still allowing execution.
- Riot analysis now checks pending localhost artifacts (`get_pending_local_evidence`) before bundle creation, produces `riot_plus_local` bundles when local evidence exists, and clears pending artifacts after successful join.
- Local upload processing no longer builds freeform `match_context` from `player_map`; it creates a shared bundle, blocks localhost-only analysis, and persists pending local evidence with explicit `blocked`/`degraded_safe` status handling.
- `analyze_postgame()` now accepts normalized bundle input in addition to legacy positional args, enabling bundle-first orchestration.
- Added route-level regressions:
  - `test_analyze_route_uses_shared_evidence_pipeline`
  - `test_local_upload_uses_shared_evidence_pipeline`
  - `test_riot_analysis_joins_pending_local_evidence`

## Verification

Passed:

- `python -m pytest ProjectB/tests/test_public_read_only_mode.py -k "analyze_route_uses_shared_evidence_pipeline or local_upload_uses_shared_evidence_pipeline or riot_analysis_joins_pending_local_evidence" -x`
- `python -m pytest ProjectB/tests/test_evidence_pipeline.py::test_stage_results_gate_downstream_execution -x`

Note:

- Running the full `test_public_read_only_mode.py` file in this environment hits an unrelated OS temp-directory permission error (`WinError 5`) during `tmp_path` fixture setup for `test_live_upload_cleans_temp_dir_on_failure`.
