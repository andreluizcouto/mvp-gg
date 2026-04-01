---
phase: 03-coaching-quality-and-consistency
plan: 02
subsystem: api
tags: [determinism, cache-policy, coaching-status, pytest]
requires:
  - phase: 03-coaching-quality-and-consistency
    provides: strict output contract and guardrails from 03-01
provides:
  - deterministic similarity fingerprint and stable insight ordering
  - cache-first revisit semantics tied to validated local-plus-riot evidence
  - explicit non-paying regeneration block endpoint and status messaging
affects: [coach-ai-cache, coaching-read-routes, monetization-gate]
key-files:
  modified:
    - ProjectB/coach_ai.py
    - ProjectB/db.py
    - ProjectB/main.py
    - ProjectB/tests/test_coach_ai_cache.py
    - ProjectB/tests/test_public_read_only_mode.py
requirements-completed: [ANLY-03, ANLY-04]
completed: 2026-04-01
---

# Phase 03 Plan 02 Summary

Implemented deterministic coaching behavior and immutable revisit semantics, with explicit blocking for non-paying regeneration attempts.

## What Changed

- `coach_ai.py` now builds similarity fingerprints and deterministic insight ordering to keep repeated similar analyses stable.
- Cache read/write is now gated to validated `riot_plus_local` evidence, preventing weaker-source snapshots from being treated as reusable validated coaching.
- `main.py` now exposes `POST /coaching/{match_id}/regenerate` as a blocked path for non-paying users and returns explicit product messaging.
- `db.py` snapshot normalization now preserves `source` and `weak_signal`, and downgrades unsafe `ready` states to `insufficient_data` when evidence is weak.
- Tests were expanded in `test_coach_ai_cache.py` and `test_public_read_only_mode.py` to cover deterministic output, fingerprint behavior, revisit semantics, and regenerate blocking.

## Verification

Passed:

- `ProjectB/.venv/Scripts/python.exe -m pytest ProjectB/tests/test_coach_ai_cache.py -x`
- `ProjectB/.venv/Scripts/python.exe -m pytest ProjectB/tests/test_public_read_only_mode.py -k "not live_upload_cleans_temp_dir_on_failure" -x`
- `ProjectB/.venv/Scripts/python.exe -m pytest ProjectB/tests/test_guardrails.py ProjectB/tests/test_coach_ai_cache.py ProjectB/tests/test_public_read_only_mode.py ProjectB/tests/test_evidence_pipeline.py -k "not live_upload_cleans_temp_dir_on_failure" -x`

## Issues Encountered

- Full-suite execution that includes `test_live_upload_cleans_temp_dir_on_failure` fails in this environment with `WinError 5` on `%TEMP%` fixture setup (environment permission issue).
