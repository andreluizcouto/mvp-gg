---
phase: 02-evidence-pipeline-and-analysis-contracts
plan: 03
subsystem: api
tags: [fastapi, schemas, status-delivery, pytest]
requires:
  - phase: 02-evidence-pipeline-and-analysis-contracts
    provides: shared evidence pipeline and entry-point rewiring from 02-02
provides:
  - latest pipeline snapshot persistence for deterministic public status delivery
  - response-model filtered coaching status endpoints with safe external states only
  - regression coverage for coaching status safety and external status summarization
affects: [coaching-status, coaching-get, local-status, db-snapshot-storage]
key-files:
  modified:
    - ProjectB/db.py
    - ProjectB/main.py
    - ProjectB/schemas.py
    - ProjectB/coach_ai.py
    - ProjectB/tests/test_public_read_only_mode.py
    - ProjectB/tests/test_evidence_pipeline.py
completed: 2026-04-01
---

# Phase 02 Plan 03 Summary

Implemented delivery-stage status safety by persisting pipeline snapshots and exposing only summarized public coaching states.

## What Changed

- Added normalized snapshot persistence in `db.py` with `save_pipeline_snapshot()` and `get_pipeline_snapshot()`:
  - stores `stage`, `status`, `reason_codes`, `external_status`, and `has_analysis_text`
  - normalizes internal statuses into safe public states (`ready`, `pending`, `insufficient_data`, `failed`)
  - keeps in-memory fallback and best-effort Supabase upsert/read via `ai_cache`
- Extended public schemas in `schemas.py`:
  - `CoachingStatusResponse`
  - `CoachingAnalysisResponse.status` with the same safe status set
- Updated `main.py` delivery routes:
  - `/coaching/status` now uses `response_model=dict[str, CoachingStatusResponse]`
  - `/coaching/{match_id}` now includes summarized `status`
  - `/local/status` now reports summarized `status` while preserving `ready`
  - added `_normalize_public_status()` guard to prevent leaking internal checkpoint details
- Wired snapshot writes at execution points:
  - Riot analysis flow in `coach_ai.run_full_analysis()` persists checkpoint outcomes
  - localhost upload flow persists blocked/pending and ready delivery snapshots
  - `/coaching/save` stores a ready delivery snapshot

## Verification

Passed:

- `python -m pytest ProjectB/tests/test_public_read_only_mode.py -k coaching -x`
- `python -m pytest ProjectB/tests/test_evidence_pipeline.py ProjectB/tests/test_public_read_only_mode.py -k "coaching or external_status" -x`
- `python -m pytest ProjectB/tests/test_evidence_pipeline.py ProjectB/tests/test_public_read_only_mode.py -k "coaching or external_status or analyze_route_uses_shared_evidence_pipeline or local_upload_uses_shared_evidence_pipeline or riot_analysis_joins_pending_local_evidence" -x`

Added regressions:

- `test_coaching_status_exposes_safe_external_states`
- `test_coaching_get_hides_internal_reason_codes`
- `test_summarize_external_status_degraded_safe_is_not_ready`
- `test_summarize_external_status_localhost_only_is_pending`
