---
phase: 2
slug: evidence-pipeline-and-analysis-contracts
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-01
---

# Phase 2 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + fastapi.testclient + pytest-asyncio |
| **Config file** | none |
| **Quick run command** | `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests/test_evidence_pipeline.py -x` |
| **Full suite command** | `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests -x` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests/test_evidence_pipeline.py -x`
- **After every plan wave:** Run `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests/test_public_read_only_mode.py ProjectB/tests/test_security_hardening.py ProjectB/tests/test_coach_ai_cache.py -x`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-00 | 01 | 0 | phase prerequisite | environment | `& .\ProjectB\.venv\Scripts\python.exe --version` and `& .\ProjectB\.venv\Scripts\python.exe -m pytest --version` | n/a | pending |
| 02-01-01 | 01 | 1 | DATA-01 | unit | `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests/test_evidence_pipeline.py::test_builds_normalized_bundle_from_riot_and_local -x` | No W0 | pending |
| 02-01-02 | 01 | 1 | DATA-02 | unit | `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests/test_evidence_pipeline.py::test_incomplete_bundle_returns_checkpoint_reason -x` | No W0 | pending |
| 02-02-01 | 02 | 2 | DATA-01 | integration | `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests/test_public_read_only_mode.py -k "local_upload_uses_shared_evidence_pipeline or riot_analysis_joins_pending_local_evidence" -x` | Yes | pending |
| 02-02-02 | 02 | 2 | QUAL-02 | unit/integration | `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests/test_evidence_pipeline.py::test_stage_results_gate_downstream_execution -x` | No W0 | pending |
| 02-03-01 | 03 | 3 | QUAL-02 | integration | `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests/test_public_read_only_mode.py -k coaching -x` | Yes | pending |

*Status: pending, green, red, flaky*

---

## Wave 0 Requirements

- [ ] `ProjectB/tests/test_evidence_pipeline.py` - create stubs and core coverage for DATA-01, DATA-02, and QUAL-02
- [ ] pipeline helper extraction - expose testable functions/modules for bundle build and stage verification
- [ ] workspace Python runtime available at `ProjectB/.venv/Scripts/python.exe` - satisfy Plan `02-01` Task 0 before any backend pytest command is attempted

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| External coaching status feels appropriately summarized for product UX | QUAL-02 | Final UX wording and semantics are product-facing, not only technical | Verify that frontend-facing responses expose only summarized safe states such as `ready`, `pending`, `insufficient_data`, or `failed`, without leaking internal checkpoint reasons |

---

## Validation Sign-Off

- [ ] All tasks have automated verify steps or explicit Wave 0 dependencies
- [ ] Plan `02-01` Task 0 clears the workspace Python / pytest prerequisite before wave 1 starts
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all missing verification references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
