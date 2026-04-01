---
phase: 5
slug: regression-safety-net
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-01
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Backend: pytest + pytest-asyncio + pytest-timeout; Frontend: Vitest + RTL |
| **Config file** | Backend: none detected; Frontend: `frontend/vitest.config.js` ✅ |
| **Quick run command** | `python -m pytest backend/tests/test_public_read_only_mode.py -v --tb=short` |
| **Full suite command** | `python -m pytest backend/tests -v --tb=short --timeout=30` |
| **Estimated runtime** | ~120 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest backend/tests/test_public_read_only_mode.py -v --tb=short`
- **After every plan wave:** Run `python -m pytest backend/tests -v --tb=short --timeout=30`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | QUAL-01 | integration | `python -m pytest backend/tests/test_public_read_only_mode.py -k "coaching_status_exposes_safe_external_states" -v --tb=short` | ✅ | ⬜ pending |
| 05-01-02 | 01 | 1 | QUAL-01 | integration | `python -m pytest backend/tests/test_public_read_only_mode.py -k "ownership or shared_link or hides_analysis" -v --tb=short` | ✅ | ⬜ pending |
| 05-01-03 | 01 | 1 | QUAL-01 | unit/integration | `python -m pytest backend/tests/test_evidence_pipeline.py -v --tb=short && python backend/run_tests.py` | ✅ | ⬜ pending |
| 05-01-04 | 01 | 1 | QUAL-01 | integration | `python -m pytest backend/tests/test_match_history_pagination.py -v --tb=short` | ✅ | ⬜ pending |
| 05-02-01 | 02 | 2 | QUAL-01 | harness/W0 | `cd frontend && npm run test -- --run --passWithNoTests` | ✅ | ⬜ pending |
| 05-02-02 | 02 | 2 | QUAL-01 | component/render | `cd frontend && npm run test -- --run src/__tests__/ResultsScreen.test.jsx src/__tests__/SummonerProfileScreen.test.jsx` | ✅ | ⬜ pending |
| 05-02-03 | 02 | 2 | QUAL-01 | unit | `cd frontend && npm run test -- api` | ✅ | ⬜ pending |
| 05-02-04 | 02 | 2 | QUAL-01 | manual-gated | `grep -n "D-04\\|desktop app\\|owner context\\|Análise privada para este jogador\\|required pre-ship" .planning/phases/05-regression-safety-net/05-VALIDATION.md` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `frontend/vitest.config.js` — test runner config for Vite + jsdom
- [x] `frontend/src/test/setupTests.js` — RTL + matchers bootstrap
- [x] `frontend/src/__tests__/ResultsScreen.test.jsx` — direct-link/private/status rendering coverage
- [x] `frontend/src/__tests__/SummonerProfileScreen.test.jsx` — IA badge gating coverage (`status === "ready"`)
- [x] `frontend/src/services/__tests__/api.test.js` — safe fallback behavior contracts

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Desktop app toast/redirect UX (`análise pronta` -> open direct match link with riot_id + match_id) | QUAL-01 | Depends on Windows tray app runtime + browser handoff not present in backend/frontend unit test harness | Run local app, complete one match, validate redirect opens `/match/:id` with owner identity and no third-party analysis exposure |

### D-04 Required Pre-Ship Checklist (Ownership-safe desktop handoff)

1. Start desktop app and confirm ready notification is emitted after a processed match.
2. Confirm redirect opens `/match/:matchId` with owner identity context (`riot_id`/player context tied to that match).
3. Confirm owner context view can access only that owner's analysis.
4. Open same match link with mismatched or missing owner context and confirm UI shows explicit private-safe state (`Análise privada para este jogador`) with no analysis text visible.

This checklist is **required pre-ship** for QUAL-01 until app-level automation exists.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 120s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** complete (Wave 0 executed; runtime verification pending human execution — see 05-HUMAN-UAT.md)
