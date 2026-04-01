# Roadmap: mvp.gg

## Overview

This roadmap improves an already working brownfield prototype into a trustworthy, secure, and community-ready post-game coaching product. The phase order reflects the real dependency chain: security and trust boundaries first, then evidence quality, then coaching quality, then presentation, then regression safety, then public-facing hardening.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions if needed later

- [ ] **Phase 1: Trust Boundaries and Security Foundation** - harden backend ownership, validation, and auth-ready architecture
- [x] **Phase 2: Evidence Pipeline and Analysis Contracts** - make analysis inputs complete, validated, and deterministic
- [x] **Phase 3: Coaching Quality and Consistency** - improve AI output reliability and usefulness (completed 2026-04-01)
- [x] **Phase 4: Match Experience and Trustworthy UX** - present stats and coaching in a clearer, more polished browser flow
- [x] **Phase 5: Regression Safety Net** - add tests and verification around the highest-risk paths (tests written, awaiting execution verification)
- [ ] **Phase 6: Community-Ready Hardening** - finalize launch-readiness, resilience, and trust signals

## Phase Details

### Phase 1: Trust Boundaries and Security Foundation
**Goal**: Ensure the backend owns trust, validation, and security-sensitive decisions before the product expands further.
**Depends on**: Nothing
**Requirements**: [SECU-01, SECU-02, SECU-03, SECU-04]
**Success Criteria** (what must be TRUE):
1. Sensitive backend flows validate requests server-side and do not depend on frontend-enforced logic
2. Secrets, internal controls, and critical trust decisions are kept out of browser-owned paths
3. Riot ID lookup, match fetch, and local upload routes enforce clear validation and abuse-aware protections
4. Current architecture can accept future login and monetization without moving trust logic into the frontend
**Plans**: 3 plans

Plans:
- [ ] 01-01: Audit current trust boundaries, sensitive endpoints, and exposed assumptions
- [ ] 01-02: Implement backend validation, server-side ownership, and auth-ready cleanup
- [ ] 01-03: Add security-focused checks and documentation for protected flows

### Phase 2: Evidence Pipeline and Analysis Contracts
**Goal**: Make the evidence bundle feeding AI analysis complete, validated, and safe to trust.
**Depends on**: Phase 1
**Requirements**: [DATA-01, DATA-02, QUAL-02]
**Success Criteria** (what must be TRUE):
1. Analysis runs from a normalized evidence bundle built from Riot and localhost-derived context
2. Incomplete or corrupted evidence is rejected, flagged, or safely degraded before analysis is shown
3. Explicit verification exists between ingestion, context building, and analysis execution
**Plans**: 3 plans

Plans:
- [x] 02-01-PLAN.md — Define strict evidence-bundle contracts, stage checkpoints, and pipeline tests
- [x] 02-02-PLAN.md — Wire Riot and localhost analysis entry points onto the shared evidence pipeline
- [x] 02-03-PLAN.md — Persist safe pipeline status and verify summarized delivery behavior

### Phase 3: Coaching Quality and Consistency
**Goal**: Make the generated coaching specific, stable, and worth acting on.
**Depends on**: Phase 2
**Requirements**: [ANLY-01, ANLY-02, ANLY-03, ANLY-04]
**Success Criteria** (what must be TRUE):
1. Users receive match-specific strengths, mistakes, and next actions instead of generic filler
2. Analysis references real evidence from the match when explaining conclusions
3. Similar matches produce outputs with stable structure and quality
4. Revisited matches return validated cached results unless intentionally regenerated
**Plans**: 3 plans

Plans:
- [x] 03-01: Refine prompt and output schema around evidence-backed coaching
- [x] 03-02: Add consistency checks, fixtures, and cache rules for stable results
- [x] 03-03: Improve fallback and failure behavior for weak or partial analyses

### Phase 4: Match Experience and Trustworthy UX
**Goal**: Deliver a polished match page and discovery flow that makes the improved coaching easy to use and believe.
**Depends on**: Phase 3
**Requirements**: [UX-01, UX-02, DATA-03]
**UI hint**: yes
**Success Criteria** (what must be TRUE):
1. Users can move from Riot ID search to the target match analysis page without confusion
2. Match pages present stats and coaching in a polished and readable browser experience
3. Coaching status is clearly communicated as ready, pending, unavailable, or failed
**Plans**: 3 plans

Plans:
- [x] 04-01-PLAN.md — Fix IA badge gating (status=ready only), smart back button (D-02), inline match load error with retry actions (D-04)
- [x] 04-02-PLAN.md — Rewrite CoachingSection with 5 status states (ready/pending/failed/unavailable/private), create AnalysisStatusBlock trust-signal component (D-12)
- [x] 04-03-PLAN.md — Restructure match page layout (coaching above scoreboard D-09), wire coaching API status, disabled tabs with "Em breve" (D-11), fix scoreboard empty copy

### Phase 5: Regression Safety Net
**Goal**: Protect the highest-risk product paths with tests and repeatable verification.
**Depends on**: Phase 4
**Requirements**: [QUAL-01]
**Success Criteria** (what must be TRUE):
1. Automated tests cover critical backend flows for search, ingestion, analysis, and protected routes
2. Automated tests cover the primary frontend rendering path for search, match details, and coaching display
3. The team can detect major regressions before public-facing changes are shipped
**Plans**: 2 plans

Plans:
- [x] 05-01: Add backend test coverage for critical flows and fixtures
- [x] 05-02: Add frontend smoke and rendering coverage for key user journeys

### Phase 6: Community-Ready Hardening
**Goal**: Make the product feel safe, credible, and ready for broader community feedback.
**Depends on**: Phase 5
**Requirements**: [UX-03]
**Success Criteria** (what must be TRUE):
1. The product communicates clear trust signals around analysis quality, readiness, and safety
2. Public-facing failure states are understandable and do not undermine confidence
3. The end-to-end experience is stable enough to share with the League community for early feedback
**Plans**: 2 plans

Plans:
- [ ] 06-01: Finalize trust signals, failure-state presentation, and public-facing polish
- [ ] 06-02: Verify launch-readiness against the product promise and current roadmap

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Trust Boundaries and Security Foundation | 0/3 | Not started | - |
| 2. Evidence Pipeline and Analysis Contracts | 3/3 | Completed | 2026-04-01 |
| 3. Coaching Quality and Consistency | 3/3 | Complete   | 2026-04-01 |
| 4. Match Experience and Trustworthy UX | 3/3 | Complete | 2026-04-01 |
| 5. Regression Safety Net | 2/2 | Complete (pending test execution) | 2026-04-01 |
| 6. Community-Ready Hardening | 0/2 | Not started | - |
