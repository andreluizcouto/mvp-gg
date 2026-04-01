---
phase: 03-coaching-quality-and-consistency
plan: 01
subsystem: api
tags: [coach-ai, guardrails, evidence-binding, pytest]
requires:
  - phase: 02-evidence-pipeline-and-analysis-contracts
    provides: shared evidence pipeline and delivery-safe status contracts
provides:
  - strict coaching normalization contract before delivery
  - evidence-bound guardrail lint for unsupported praise and weak evidence
  - regression coverage for hard guardrail violations
affects: [coach-ai, coaching-delivery, output-validation]
key-files:
  modified:
    - ProjectB/coach_ai.py
    - ProjectB/coach_guardrails.py
    - ProjectB/schemas.py
    - ProjectB/tests/test_guardrails.py
requirements-completed: [ANLY-01, ANLY-02]
completed: 2026-04-01
---

# Phase 03 Plan 01 Summary

Implemented strict contract normalization and hard evidence-bound guardrails so generic or unsupported coaching does not reach users.

## What Changed

- `coach_ai.py` now normalizes model output through deterministic helpers, closed category taxonomy, stable sorting, and stricter output validation before cache/public delivery.
- `coach_guardrails.py` now flags unsupported praise without evidence anchors using explicit violation code `VIOL_UNSUPPORTED_PRAISE`.
- `schemas.py` was aligned with the stricter coaching payload flow used by API delivery.
- `test_guardrails.py` gained regressions for unsupported praise and evidence anchor behavior.

## Verification

Passed:

- `ProjectB/.venv/Scripts/python.exe -m pytest ProjectB/tests/test_guardrails.py -x`
- `ProjectB/.venv/Scripts/python.exe -m pytest ProjectB/tests/test_guardrails.py ProjectB/tests/test_coach_ai_cache.py ProjectB/tests/test_public_read_only_mode.py ProjectB/tests/test_evidence_pipeline.py -k "not live_upload_cleans_temp_dir_on_failure" -x`

## Issues Encountered

- Full-suite execution that includes `test_live_upload_cleans_temp_dir_on_failure` fails in this environment with `WinError 5` on `%TEMP%` fixture setup (environment permission issue).
