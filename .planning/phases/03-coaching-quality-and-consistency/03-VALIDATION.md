---
phase: 3
slug: coaching-quality-and-consistency
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-01
---

# Phase 3 - Validation Strategy

> Per-phase validation contract for coaching quality and consistency.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + fastapi.testclient |
| **Config file** | none |
| **Quick run command** | `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests/test_guardrails.py -x` |
| **Full suite command** | `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests -x` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** run task-targeted tests from this matrix.
- **After every plan wave:** run `test_guardrails.py`, `test_coach_ai_cache.py`, and `test_public_read_only_mode.py`.
- **Before `$gsd-verify-work`:** full backend suite must pass.
- **Max feedback latency:** 45 seconds.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | ANLY-01, ANLY-02 | unit | `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests/test_guardrails.py -k "contract or evidence" -x` | Yes | pending |
| 03-01-02 | 01 | 1 | ANLY-01, ANLY-02 | unit | `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests/test_guardrails.py -k "timestamp or number or rewrite" -x` | Yes | pending |
| 03-02-01 | 02 | 2 | ANLY-03 | unit | `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests/test_coach_ai_cache.py -k "riot_id or deterministic" -x` | Yes | pending |
| 03-02-02 | 02 | 2 | ANLY-04 | integration | `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests/test_public_read_only_mode.py -k "coaching and cache" -x` | Yes | pending |
| 03-03-01 | 03 | 3 | ANLY-01, ANLY-02 | integration | `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests/test_public_read_only_mode.py -k "insufficient_data or unavailable" -x` | Yes | pending |
| 03-03-02 | 03 | 3 | ANLY-03, ANLY-04 | unit/integration | `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests/test_evidence_pipeline.py ProjectB/tests/test_public_read_only_mode.py -k "status or coaching" -x` | Yes | pending |

*Status: pending, green, red, flaky*

---

## Wave 0 Requirements

- [ ] Add explicit tests for structured coaching contract fields (`strengths`, `mistakes`, `next_steps`) if missing.
- [ ] Add deterministic similarity/cache tests for repeated analysis requests on similar inputs.
- [ ] Add unavailable-state tests proving "no app evidence -> no analysis" user flow.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Coaching text feels direct and actionable without filler | ANLY-01 | Quality-of-tone still needs human review | Review 5 generated analyses and confirm they keep fixed structure and measurable next steps |
| Unavailable CTA is clear and recoverable for users without local app | ANLY-02 | Product copy quality is UX-sensitive | Validate API status and frontend message consistently show install-app + play-one-match guidance |

---

## Validation Sign-Off

- [ ] All tasks have automated verify steps.
- [ ] Sampling continuity: no 3 consecutive tasks without automated checks.
- [ ] Contract, determinism, and unavailable-state coverage are present.
- [ ] No watch-mode flags in verification commands.
- [ ] Feedback latency < 45s.
- [ ] `nyquist_compliant: true` remains in frontmatter.

**Approval:** pending
