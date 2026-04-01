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

### v1.1 — MVPApp Desktop GUI

- [x] **Phase 7: Threading Foundation + EventBus** - restructure main() for three-thread model with thread-safe communication and config locking
- [ ] **Phase 8: GUI Shell + Tray Integration** - dark-themed window that coexists with system tray (hide-on-close, double-click restore)
- [ ] **Phase 9: Content Panels — Status, How-It-Works, Settings** - informational and configuration panels inside the window shell
- [ ] **Phase 10: Activity Log + Event Bridge** - real-time color-coded event feed bridged from asyncio to GUI
- [ ] **Phase 11: Build Configuration + Validation** - PyInstaller bundles CustomTkinter into a distributable .exe

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

---

## v1.1 — MVPApp Desktop GUI

### Overview

This section extends the roadmap for milestone v1.1. The existing MVPApp is a headless tray-only app that captures minimap screenshots and uploads them for AI coaching analysis. v1.1 adds a visual interface so users can understand what the app does, see it working in real time, and configure capture settings — without breaking the proven async + tray architecture.

The core challenge is a threading integration: CustomTkinter needs the main thread, pystray currently blocks the main thread, and asyncio runs on a daemon thread. The phase order reflects risk: threading model first (everything depends on it), then the window shell (validates the model), then content panels, then the showcase feature (activity log), then the build (can only validate when everything works).

### Phase 7: Threading Foundation + EventBus
**Goal**: MVPApp runs three concurrent threads (GUI, tray, asyncio) without deadlocks, with a thread-safe communication channel and protected config access
**Depends on**: Nothing (v1.1 foundation — existing coach_app.py is the starting point)
**Requirements**: [APP-01, APP-02, APP-03]
**Success Criteria** (what must be TRUE):
  1. App launches with CustomTkinter mainloop on main thread, pystray on background thread, and asyncio on daemon thread — all three coexist without freezing or crashing
  2. EventBus messages put from any thread are received by the main thread via after() polling within 200ms
  3. Config changes from any thread are protected by locking — concurrent read-modify-write never produces corrupted or lost writes
  4. App shuts down cleanly from tray "Quit" — all three threads exit without orphan processes or frozen windows
**Plans**: 2 plans

Plans:
- [x] 07-01-PLAN.md — EventBus module + thread-safe config locking (APP-02, APP-03)
- [x] 07-02-PLAN.md — 3-thread model restructure + integration tests (APP-01, APP-02)

### Phase 8: GUI Shell + Tray Integration
**Goal**: User sees a functional app window that correctly coexists with the system tray — hiding, showing, and persisting across close actions
**Depends on**: Phase 7
**Requirements**: [WIN-01, WIN-02, WIN-03]
**Success Criteria** (what must be TRUE):
  1. User sees a dark-themed window with app branding when launching MVPApp
  2. User can close the window via the X button and the app continues running in the system tray
  3. User can double-click the tray icon to restore the window to the foreground
  4. Tray context menu includes an "Open MVPApp" option that shows the window
**Plans**: TBD
**UI hint**: yes

### Phase 9: Content Panels — Status, How-It-Works, Settings
**Goal**: User can understand what the app does, see its current state, and configure capture settings — all from within the window
**Depends on**: Phase 8
**Requirements**: [CNT-01, CNT-02, CNT-03, CNT-04, WIN-04]
**Success Criteria** (what must be TRUE):
  1. User sees a "How it works" explanation that describes the capture-analyze-coach flow in 3-4 visual steps
  2. User sees current app status (waiting, recording, uploading, ready) updating in real time to match tray icon state
  3. User can toggle minimap position between left and right, and the setting persists across app restarts
  4. User can see the minimap size option with a "recommended for AI accuracy" label on the large setting
  5. Window auto-hides when the app enters recording state to prevent minimap capture interference
**Plans**: TBD
**UI hint**: yes

### Phase 10: Activity Log + Event Bridge
**Goal**: User can watch a live feed of game events proving the app is actively working, with visual clarity for quick scanning
**Depends on**: Phase 9
**Requirements**: [LOG-01, LOG-02, LOG-03]
**Success Criteria** (what must be TRUE):
  1. User sees game events (deaths, kills, objectives, uploads, errors) appear in real time with game-time timestamps
  2. Events are visually distinguishable by type through color coding (deaths red, kills green, objectives gold, errors orange)
  3. Log stays bounded in memory — old entries are dropped after reaching the cap, and no sensitive data (URLs, tokens, payloads) is ever displayed
**Plans**: TBD
**UI hint**: yes

### Phase 11: Build Configuration + Validation
**Goal**: User can download and run a single .exe that includes the full GUI experience without requiring Python or manual setup
**Depends on**: Phase 10
**Requirements**: [APP-04]
**Success Criteria** (what must be TRUE):
  1. PyInstaller produces a working .exe that launches the full GUI (dark theme, all panels, activity log) without import errors or crashes
  2. Built .exe includes CustomTkinter assets (fonts, themes) and renders with modern dark styling — not raw tkinter gray widgets
  3. Built .exe runs correctly on a clean Windows machine without Python installed
**Plans**: TBD

## Progress

### v1.0 — Core Product

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Trust Boundaries and Security Foundation | 0/3 | Not started | - |
| 2. Evidence Pipeline and Analysis Contracts | 3/3 | Completed | 2026-04-01 |
| 3. Coaching Quality and Consistency | 3/3 | Complete   | 2026-04-01 |
| 4. Match Experience and Trustworthy UX | 3/3 | Complete | 2026-04-01 |
| 5. Regression Safety Net | 2/2 | Complete (pending test execution) | 2026-04-01 |
| 6. Community-Ready Hardening | 0/2 | Not started | - |

### v1.1 — MVPApp Desktop GUI

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 7. Threading Foundation + EventBus | 2/2 | Complete   | 2026-04-01 |
| 8. GUI Shell + Tray Integration | 0/? | Not started | - |
| 9. Content Panels — Status, How-It-Works, Settings | 0/? | Not started | - |
| 10. Activity Log + Event Bridge | 0/? | Not started | - |
| 11. Build Configuration + Validation | 0/? | Not started | - |
