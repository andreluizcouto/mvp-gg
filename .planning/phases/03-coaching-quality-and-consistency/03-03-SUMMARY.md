---
phase: 03-coaching-quality-and-consistency
plan: 03
subsystem: api
tags: [weak-signal, insufficient-data, public-status, fastapi, pytest]
requires:
  - phase: 03-coaching-quality-and-consistency
    provides: deterministic cache semantics and regenerate gating from 03-02
provides:
  - weak-signal fail-safe mapping to insufficient_data
  - explicit unavailable CTA when local app evidence is missing
  - stable public response models for blocked/unavailable coaching states
affects: [coaching-status, coaching-get, evidence-pipeline, schemas]
key-files:
  modified:
    - ProjectB/coach_ai.py
    - ProjectB/main.py
    - ProjectB/db.py
    - ProjectB/schemas.py
    - ProjectB/tests/test_public_read_only_mode.py
    - ProjectB/tests/test_evidence_pipeline.py
requirements-completed: [ANLY-01, ANLY-02, ANLY-03, ANLY-04]
completed: 2026-04-01
---

# Phase 03 Plan 03 Summary

Finalized weak-signal and unavailable-state behavior so users do not receive misleading coaching when local evidence is absent or insufficient.

## What Changed

- `coach_ai.py` now marks weak-signal/no-local-evidence paths with `insufficient_data`, disables analysis text for unsafe evidence states, and snapshots `source` plus `weak_signal` for deterministic delivery decisions.
- `main.py` now enforces no-analysis-without-local-evidence in `/coaching/status` and `/coaching/{match_id}`, returning the explicit CTA: `Coach indisponivel, baixe o app e jogue uma partida.`
- `schemas.py` now includes optional `message` fields for coaching status/analysis responses and `CoachingRegenerateResponse` for blocked regenerate flow.
- `db.py` now normalizes weak-signal snapshot payloads into safe external status values.
- New regressions in `test_public_read_only_mode.py` and `test_evidence_pipeline.py` cover unavailable CTA delivery, blocked analysis without local evidence, blocked regenerate semantics, and weak-signal status mapping.

## Verification

Passed:

- `ProjectB/.venv/Scripts/python.exe -m pytest ProjectB/tests/test_evidence_pipeline.py -x`
- `ProjectB/.venv/Scripts/python.exe -m pytest ProjectB/tests/test_public_read_only_mode.py -k "not live_upload_cleans_temp_dir_on_failure" -x`
- `ProjectB/.venv/Scripts/python.exe -m pytest ProjectB/tests/test_guardrails.py ProjectB/tests/test_coach_ai_cache.py ProjectB/tests/test_public_read_only_mode.py ProjectB/tests/test_evidence_pipeline.py -k "not live_upload_cleans_temp_dir_on_failure" -x`

Result:

- `36 passed, 1 deselected, 2 warnings` in the combined targeted run.

## Issues Encountered

- Full-suite execution that includes `test_live_upload_cleans_temp_dir_on_failure` fails in this environment with `WinError 5` on `%TEMP%` fixture setup (environment permission issue).
