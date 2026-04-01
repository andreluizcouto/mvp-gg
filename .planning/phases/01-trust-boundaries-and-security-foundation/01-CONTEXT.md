# Phase 1: Trust Boundaries and Security Foundation - Context

**Gathered:** 2026-04-01
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase hardens backend trust boundaries, request validation, internal authentication, and security-sensitive architecture decisions for the existing brownfield system. It does not add new user-facing product capabilities; it secures the foundation that later phases will build on.

</domain>

<decisions>
## Implementation Decisions

### Internal authentication model
- **D-01:** Internal administrative and AI-triggering routes must use only internal bearer authentication.
- **D-02:** Local desktop app routes under `/local/*` must use only the dedicated local app token.
- **D-03:** The temporary fallback between local app token and general internal token must be removed in this phase.

### Public route boundary
- **D-04:** Public access must remain limited to the minimum read-only routes required for the current web product to function.
- **D-05:** Public routes must stay sanitized and rate-limited, with no sensitive or trust-defining behavior exposed.
- **D-06:** Any route that triggers analysis, handles internal feedback flows, accepts local uploads, or changes protected state must require internal protection.

### Validation and failure policy
- **D-07:** The backend must fail closed by default for invalid, incomplete, or suspicious inputs.
- **D-08:** Degradation is allowed only when it is explicitly designed as safe and cannot mislead the user about trust or completeness.
- **D-09:** Backend decisions must never depend on frontend-enforced state or validation.

### Security test bar
- **D-10:** This phase must ship with automated backend tests covering internal authentication, token separation, input validation, rate limiting, and non-leakage of sensitive fields on public routes.
- **D-11:** Security hardening in this phase is not considered complete without automated verification of those guarantees.

### the agent's Discretion
- Exact implementation structure for auth helpers, middleware, and route grouping
- Exact test organization and fixture strategy, as long as the required guarantees are covered
- Whether to centralize some protections in shared helpers, dependencies, or middleware, provided the locked trust boundaries above remain intact

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase definition
- `.planning/ROADMAP.md` - Phase 1 goal, requirements, and success criteria
- `.planning/REQUIREMENTS.md` - Security requirements `SECU-01`, `SECU-02`, `SECU-03`, `SECU-04`
- `.planning/PROJECT.md` - Project-level security principles and non-negotiables

### Existing backend trust boundaries
- `ProjectB/main.py` - Current CORS, security headers, auth helpers, validation helpers, and protected route definitions
- `ProjectB/settings.py` - Environment-driven security configuration including tokens and CORS origins
- `ProjectB/coach_app.py` - Local desktop app token usage and upload polling behavior
- `ProjectB/live_game_client.py` - Local Riot client integration and HTTPS handling on localhost

### Existing verification coverage
- `ProjectB/tests/test_security_hardening.py` - Current auth, validation, and client-IP hardening coverage
- `ProjectB/tests/test_public_read_only_mode.py` - Current public/internal route behavior, rate limit, and field exposure coverage

No external specs - requirements are fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ProjectB/main.py`: already contains `_require_internal_auth`, `_require_local_app_auth`, `_validate_match_id`, and `_validate_riot_id` that can be hardened instead of replaced
- `ProjectB/tests/test_security_hardening.py`: existing security-focused test file provides a starting point for expanding coverage
- `ProjectB/tests/test_public_read_only_mode.py`: existing route-protection and public-read tests provide fixtures and patterns for this phase
- `ProjectB-frontend/src/services/api.js`: current frontend-side input validation and secure base URL checks can remain as defense-in-depth, but not as trust anchors

### Established Patterns
- FastAPI + helper-function based auth and validation in `ProjectB/main.py`
- Environment-variable driven configuration in `ProjectB/settings.py`
- pytest-based backend verification in `ProjectB/tests/`
- Public GET routes are intentionally kept simple in the frontend client to reduce CORS preflight complexity

### Integration Points
- Sensitive route protection and validation logic are centered in `ProjectB/main.py`
- Token configuration and security environment defaults are centralized in `ProjectB/settings.py`
- Local desktop upload behavior connects through `ProjectB/coach_app.py` to backend `/local/*` endpoints
- Public web consumption of safe read routes flows through `ProjectB-frontend/src/services/api.js`

</code_context>

<specifics>
## Specific Ideas

- Security should be treated as a core requirement now, before login and monetization exist.
- Backend must never trust logic that lives only in the frontend.
- The system should include verification between stages and tests, not only implementation hardening.
- Fail-closed is the default posture for this phase.

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope.

</deferred>

---

*Phase: 01-trust-boundaries-and-security-foundation*
*Context gathered: 2026-04-01*
