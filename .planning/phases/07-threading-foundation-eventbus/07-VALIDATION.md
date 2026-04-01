---
phase: 7
slug: threading-foundation-eventbus
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-01
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing in backend/tests/) |
| **Config file** | backend/run_tests.py |
| **Quick run command** | `cd backend && python -m pytest tests/test_threading.py -v --timeout=30` |
| **Full suite command** | `cd backend && python run_tests.py` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/test_threading.py -v --timeout=30`
- **After every plan wave:** Run `cd backend && python run_tests.py`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | APP-02 | unit | `pytest tests/test_event_bus.py -v` | ❌ W0 | ⬜ pending |
| 07-01-02 | 01 | 1 | APP-03 | unit | `pytest tests/test_app_config.py -v` | ❌ W0 | ⬜ pending |
| 07-02-01 | 02 | 2 | APP-01 | integration | `pytest tests/test_threading.py -v` | ❌ W0 | ⬜ pending |
| 07-02-02 | 02 | 2 | APP-01 | integration | `pytest tests/test_threading.py::test_shutdown -v` | ❌ W0 | ⬜ pending |
| 07-02-03 | 02 | 2 | APP-02 | integration | `pytest tests/test_threading.py::test_eventbus_latency -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_event_bus.py` — unit tests for EventBus emit/poll/drain
- [ ] `tests/test_app_config.py` — concurrent config read-modify-write tests
- [ ] `tests/test_threading.py` — integration tests for 3-thread startup/shutdown/EventBus delivery

*These will be created as part of the phase plans.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| GUI window appears and responds to events | APP-01 | Requires display + human visual confirmation | Launch app, verify CTk window opens, tray icon appears, window responds to clicks |
| Tray icon shows correct state colors | APP-01 | Visual verification | Change app state, observe tray icon color changes |
| No frozen/orphan processes after quit | APP-01 | Process-level verification | Click "Sair", verify in Task Manager that no python.exe remains |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
