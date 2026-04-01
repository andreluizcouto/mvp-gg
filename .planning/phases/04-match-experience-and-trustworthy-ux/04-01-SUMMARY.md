---
phase: 04-match-experience-and-trustworthy-ux
plan: "01"
subsystem: frontend
tags: [ux, routing, error-handling, badge-gating]
dependency_graph:
  requires: []
  provides: [ia-badge-gating, from-state-routing, smart-back-button, inline-error-block]
  affects: [SummonerProfileScreen, ResultsScreen]
tech_stack:
  added: []
  patterns: [react-router-state, retry-pattern, smart-navigation]
key_files:
  created: []
  modified:
    - ProjectB-frontend/src/screens/SummonerProfileScreen.jsx
    - ProjectB-frontend/src/screens/ResultsScreen.jsx
decisions:
  - "Use retryCount state increment to re-trigger useEffect for retry (avoids resetting matchStats)"
  - "Use window.history.length <= 2 guard for direct-link detection alongside !location.state?.from"
metrics:
  duration: ~15min
  completed: "2026-04-01"
---

# Phase 04 Plan 01: Match UX Polish — IA Badge Gating, Smart Back Button, Inline Error Block

## One-liner

Gated the IA badge to `status === "ready"` only, wired `from`-state routing for smart back-navigation, and replaced the bare error string with an actionable inline error block (warning icon + retry + home).

## Tasks Completed

| # | Task | Status | Files |
|---|------|--------|-------|
| 1 | SummonerProfileScreen — IA badge gating (D-05) + from-state in navigate | ✅ Done | SummonerProfileScreen.jsx |
| 2 | ResultsScreen — smart back button (D-02) + inline error state (D-04) | ✅ Done | ResultsScreen.jsx |

## Changes Made

### Task 1 — SummonerProfileScreen.jsx

**Change 1:** Added `useLocation` to the react-router-dom import.

**Change 2:** Declared `const location = useLocation()` inside the component after `useNavigate()`.

**Change 3:** Updated `handleSelect` to pass `from: location.pathname` in route state, enabling the back button on ResultsScreen to know where to return to (D-02 prep).

**Change 4:** Changed `hasCoaching={!!coachingStatus[match.match_id]}` → `hasCoaching={coachingStatus[match.match_id]?.status === "ready"}`. The IA badge (gold) now only appears when the backend confirms `status === "ready"`. Pending, failed, and `insufficient_data` matches no longer show the badge (D-05).

### Task 2 — ResultsScreen.jsx

**Change 1:** Replaced `const { state } = useLocation()` with `const location = useLocation()` + `const state = location.state` — makes `location` available in the back button handler.

**Change 2:** Added `const [retryCount, setRetryCount] = useState(0)` state variable.

**Change 3:** Added `retryCount` to the matchDetails fetch effect dependency array, enabling the "Tentar novamente" button to re-trigger the fetch.

**Change 4:** Replaced `navigate(-1)` back button with smart back button (D-02): navigates to `/` when `window.history.length <= 2 || !location.state?.from` (direct-link access), otherwise `navigate(-1)`.

**Change 5:** Replaced bare `<div>{errorMatch}</div>` with full inline error block (D-04): warning triangle SVG, error message text, "Tentar novamente" button (increments retryCount), and "Ir para home" button.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all changes are fully wired with real state and navigation logic.

## Notes

> ⚠️ Shell unavailable: The PowerShell tool requires pwsh.exe (PowerShell Core 6+) which is not installed in this environment. Git commits and npm build verification could not be executed. All file edits were applied correctly and verified via view tool. Commits will need to be applied manually or by the orchestrator.

## Self-Check

### Files Modified
- ✅ `ProjectB-frontend/src/screens/SummonerProfileScreen.jsx` — verified via view tool:
  - Line 2: `useLocation` in import
  - Line 493: `const location = useLocation()`
  - Line 541: `from: location.pathname` in handleSelect state
  - Line 665: `coachingStatus[match.match_id]?.status === "ready"`
- ✅ `ProjectB-frontend/src/screens/ResultsScreen.jsx` — verified via view tool:
  - Lines 272-274: `location = useLocation()`, `state = location.state`
  - Line 294: `const [retryCount, setRetryCount] = useState(0)`
  - Line 328: `[isMockMode, matchId, matchStats, retryCount]`
  - Lines 392-425: Inline error block with Tentar novamente + Ir para home
  - Lines 431-440: Smart back button with `window.history.length <= 2 || !location.state?.from`

### Success Criteria Verification
- ✅ IA badge shows only for `status === "ready"` — gated via optional chaining
- ✅ `from: location.pathname` passed in navigate state from SummonerProfileScreen
- ✅ Back button navigates to `/` for direct-link access
- ✅ Error block shows warning icon + two action buttons with D-04 copy
- ✅ "Tentar novamente" increments retryCount → useEffect re-runs → new fetch triggered

## Self-Check: PASSED
