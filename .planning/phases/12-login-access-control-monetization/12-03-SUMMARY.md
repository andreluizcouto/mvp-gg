---
phase: 12-login-access-control-monetization
plan: 03
subsystem: ui
tags: [react, auth, dashboard, access-control]
requires:
  - phase: 12-01
    provides: "Auth/session and entitlement data contracts"
  - phase: 12-02
    provides: "Protected auth and coaching APIs"
provides:
  - "Login and protected dashboard UX wired to backend auth outcomes"
  - "Authoritative user-owned match mapping enforcement in backend + dashboard wiring"
affects: [12-04]
tech-stack:
  added: []
  patterns: ["frontend presents backend auth decisions only", "ownership-scoped coaching reads"]
key-files:
  created: [frontend/src/screens/LoginScreen.jsx, frontend/src/screens/DashboardScreen.jsx]
  modified: [frontend/src/App.jsx, frontend/src/services/api.js, frontend/src/services/auth.js, backend/main.py, backend/db.py, backend/docs/sql/12_auth_monetization.sql]
key-decisions:
  - "Ownership is derived server-side via user_identities mapping; frontend cannot widen scope."
  - "Unknown or foreign match ownership returns insufficient_data fail-closed."
patterns-established:
  - "Dashboard status queries are seeded from /auth/me matches_with_analysis."
requirements-completed: [AUTH-01, AUTH-02, BILL-01]
duration: 55min
completed: 2026-04-02
---

# Phase 12 Plan 03: Login + Dashboard Ownership Scope Summary

**Protected dashboard flow now uses backend-authoritative user-to-riot ownership mapping so coaching lists and reads are securely scoped per authenticated user.**

## Performance
- **Duration:** 55 min
- **Started:** 2026-04-02T10:30:00Z
- **Completed:** 2026-04-02T10:52:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Delivered login/dashboard route flow and session-backed client wrappers.
- Added authoritative `user_identities` persistence + retrieval logic for ownership checks.
- Enforced fail-closed ownership filtering in `/auth/me`, `/coaching/status`, and `/coaching/{match_id}` and wired dashboard to use backend-provided match list.

## Task Commits
1. **Task 1: Add auth client + route wiring** - `a6629cd` (feat)
2. **Task 2: Implement screens + ownership-scoped match retrieval** - `1a22e8e` (feat), `3c3283e` (feat), `3edea6e` (feat)

## Files Created/Modified
- `backend/docs/sql/12_auth_monetization.sql` - Added `user_identities` table + index.
- `backend/db.py` - Added user identity mapping persistence and owned-match lookup helpers.
- `backend/main.py` - Switched `/auth/me` and protected coaching endpoints to ownership-scoped resolution.
- `backend/tests/test_auth_endpoints.py` - Added coverage that `/auth/me` only returns owned matches.
- `backend/tests/test_ia_access_guard.py` - Added fail-closed ownership test for foreign match access.
- `frontend/src/screens/DashboardScreen.jsx` - Uses `/auth/me` authoritative `matches_with_analysis`.
- `frontend/src/__tests__/DashboardScreen.test.jsx` - Updated counters/status expectations for backend list input.
- `frontend/src/__tests__/auth-coaching-e2e.test.jsx` - Updated smoke payload with backend-provided owned matches.

## Decisions Made
- Enforced backend-only ownership resolution via `user_identities` mapping and server checks.
- Returned safe `insufficient_data` responses for non-owned matches rather than exposing ownership internals.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added authoritative user-to-riot mapping table and enforcement**
- **Found during:** Task 2 (Dashboard ownership scope)
- **Issue:** Existing `/auth/me` + coaching access used direct email/riot filter and static frontend sample IDs, allowing non-authoritative scope.
- **Fix:** Added `user_identities` schema + DB helpers, mapped identities on login and request usage, enforced ownership map in `/auth/me` and coaching reads.
- **Files modified:** `backend/docs/sql/12_auth_monetization.sql`, `backend/db.py`, `backend/main.py`, `backend/tests/test_auth_endpoints.py`, `backend/tests/test_ia_access_guard.py`
- **Verification:** `cd backend && python -m pytest tests/test_auth_endpoints.py tests/test_ia_access_guard.py -x -v`
- **Committed in:** `3c3283e`

**2. [Rule 2 - Missing Critical] Rewired dashboard to backend-owned match list**
- **Found during:** Task 2
- **Issue:** Dashboard queried coaching status using hardcoded sample match IDs instead of backend-authorized ownership list.
- **Fix:** Replaced sample IDs with `/auth/me` `matches_with_analysis` payload and updated tests.
- **Files modified:** `frontend/src/screens/DashboardScreen.jsx`, `frontend/src/__tests__/DashboardScreen.test.jsx`, `frontend/src/__tests__/auth-coaching-e2e.test.jsx`
- **Verification:** `cd frontend && npm run test -- src/__tests__/LoginScreen.test.jsx src/__tests__/DashboardScreen.test.jsx src/__tests__/auth-coaching-e2e.test.jsx`
- **Committed in:** `3edea6e`

---

**Total deviations:** 2 auto-fixed (2 missing critical)
**Impact on plan:** Required to satisfy secure backend-authoritative ownership scope with fail-closed behavior.

## Issues Encountered
- The planned frontend test command used `--runInBand` (Jest flag), but project uses Vitest; executed equivalent Vitest command without `--runInBand`.

## Known Stubs
None identified in files modified for this plan.

## Next Phase Readiness
- Ownership-scoped dashboard and coaching authorization are in place.
- Ready for final Phase 12 release gate execution and documentation.

## Self-Check: PASSED
