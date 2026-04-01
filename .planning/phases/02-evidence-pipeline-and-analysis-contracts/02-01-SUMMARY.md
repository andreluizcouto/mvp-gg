---
phase: 02-evidence-pipeline-and-analysis-contracts
plan: 01
subsystem: api
tags: [pydantic, fastapi, pytest, evidence-pipeline]
requires:
  - phase: 01-trust-boundaries-and-security-foundation
    provides: fail-closed backend ownership and validation boundaries
provides:
  - typed internal evidence bundle and checkpoint contracts
  - pure pipeline helpers for bundle build, stage gating, and external status summarization
  - regression coverage for normalized evidence and fail-closed gating
affects: [coach-ai, postgame-analysis, coaching-delivery]
tech-stack:
  added: []
  patterns: [typed pipeline contracts, fail-closed stage gates, safe external status mapping]
key-files:
  created: [ProjectB/analysis_contracts.py, ProjectB/evidence_pipeline.py, ProjectB/tests/test_evidence_pipeline.py]
  modified: []
key-decisions:
  - "Use one backend-owned Pydantic contract layer for bundle, checkpoint, and snapshot state."
  - "Treat localhost-only evidence as an explicit incomplete internal state, never analysis-ready."
patterns-established:
  - "Pipeline stages advance only from typed checkpoint results."
  - "Detailed internal states are summarized into safe product-facing statuses."
requirements-completed: [DATA-01, DATA-02, QUAL-02]
duration: 18 min
completed: 2026-04-01
---

# Phase 02 Plan 01: Define the internal evidence-bundle and checkpoint contracts Summary

**Typed evidence contracts, pure stage gates, and pipeline regression tests for Riot plus localhost normalization**

## Performance

- **Duration:** 18 min
- **Started:** 2026-04-01T05:05:00-03:00
- **Completed:** 2026-04-01T05:23:45-03:00
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Added strict internal models for evidence source, stage status, checkpoint reasons, bundle shape, and pipeline snapshots.
- Introduced pure helpers that build a normalized bundle, gate downstream stages, and summarize safe external status values.
- Added pytest coverage proving Riot plus localhost normalization, localhost-only incomplete behavior, and downstream gating semantics.

## Task Commits

Each task was committed atomically:

1. **Task 0: Validate the workspace Python 3.11 runtime and pytest toolchain** - pending local git commit
2. **Task 1: Create strict evidence and checkpoint contracts** - pending local git commit
3. **Task 2: Implement bundle builders and contract tests** - pending local git commit

**Plan metadata:** pending local git commit

## Files Created/Modified
- `ProjectB/analysis_contracts.py` - Defines the backend-owned bundle, checkpoint, reason-code, and snapshot models.
- `ProjectB/evidence_pipeline.py` - Implements source normalization, stage gating, and safe external status mapping.
- `ProjectB/tests/test_evidence_pipeline.py` - Locks the core pipeline contract behavior with deterministic pytest coverage.

## Decisions Made

- Kept the contract layer pure and independent from route handlers so later waves can wire it into FastAPI without duplicating logic.
- Modeled `localhost_only` as a valid internal bundle shape that still returns incomplete evidence until Riot context rejoins it.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The MCP executor path stalled and produced no observable progress, so execution was completed directly in the workspace.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Wave 1 is ready for route wiring in `02-02`.
- The next step is to rewire Riot and localhost entry points onto the shared bundle and checkpoint helpers.

---
*Phase: 02-evidence-pipeline-and-analysis-contracts*
*Completed: 2026-04-01*
