# Project Research Summary

**Project:** mvp.gg
**Domain:** League of Legends statistics plus AI post-game analysis
**Researched:** 2026-04-01
**Confidence:** MEDIUM

## Executive Summary

mvp.gg is best treated as a brownfield product-hardening effort, not a greenfield build. The current FastAPI backend, React frontend, Supabase persistence, and local companion app already provide the required technical surface for a meaningful post-game coaching product. The right next move is to improve trust, consistency, and security rather than widen the feature set.

The strongest product recommendation is to make analysis quality and backend trust boundaries the center of the roadmap. Users will only believe the AI if it is specific to the match, consistent across similar inputs, and presented with enough evidence to feel credible. Security work also belongs early because the product is expected to grow into login and monetization.

## Key Findings

### Recommended Stack

Keep the current stack and harden it. FastAPI and Pydantic are a strong fit for request validation, typed context building, and backend-owned logic. React and Vite remain a good browser-first delivery layer. Supabase is acceptable for current persistence needs. The local companion app is part of the moat because localhost-derived post-game context is difficult to replace from public APIs alone.

**Core technologies:**
- FastAPI and Pydantic: backend contracts and validation - supports trust boundaries
- React and Vite: browser delivery - supports fast UX iteration
- Supabase: persistence and caching - supports coaching result storage
- Desktop companion app: localhost match context capture - supports richer analysis inputs

### Expected Features

The product should cover search, match discovery, match detail, and AI coaching as its table stakes. The competitive angle is not sheer stat breadth; it is evidence-backed coaching that points out meaningful errors, strengths, and next actions.

**Must have (table stakes):**
- Riot ID search and recent match history - users expect tracker basics
- Match detail pages with scoreboard and context - users need the game facts
- Stable analysis status and delivery - users need predictable product behavior

**Should have (competitive):**
- Evidence-backed coaching insights - this is the product differentiator
- Trust-oriented presentation of analysis readiness and reasoning - this builds confidence

**Defer (v2+):**
- Dynamic chat about the match - useful but not core for first trust
- Reference-match comparison and deeper phase coaching - valuable after the core works reliably
- Live coaching, team workflows, and mobile - intentionally out of scope

### Architecture Approach

Use the existing three-surface architecture, but enforce stricter boundaries between ingestion, context building, analysis orchestration, and frontend presentation. The backend should remain the source of truth for anything security-sensitive or meaning-defining.

**Major components:**
1. Ingestion - Riot and localhost evidence collection
2. Context builder - normalized analysis-ready match bundle
3. Analysis orchestrator - prompt, validation, caching, fallback
4. Presentation - browser UX for profile, match, and coaching

### Critical Pitfalls

1. **Generic coaching output** - require evidence-backed inputs and structured outputs
2. **Frontend-owned trust or security logic** - enforce sensitive rules server-side
3. **Opaque analysis UX** - show enough evidence and status for the user to trust the result
4. **Fragile upload pipeline** - reject incomplete payloads and make failures visible
5. **Weak regression coverage** - add fixtures and tests for analysis and delivery flows

## Implications for Roadmap

### Phase 1: Trust Boundaries and Security Foundation
**Rationale:** Security and ownership boundaries should be correct before expansion.
**Delivers:** backend validation, endpoint hardening, auth-ready structure, and trust boundaries.
**Addresses:** security requirements and future monetization risk.
**Avoids:** frontend-trust and secret-exposure pitfalls.

### Phase 2: Evidence Pipeline and Analysis Contracts
**Rationale:** Analysis quality depends on input quality and deterministic validation.
**Delivers:** stable evidence bundle rules, payload checks, and analysis contract validation.
**Uses:** FastAPI, Pydantic, and current Riot plus localhost ingestion.
**Implements:** ingestion and context-builder hardening.

### Phase 3: Coaching Quality and Consistency
**Rationale:** Once inputs are stable, the model output can be made more useful and repeatable.
**Delivers:** stronger prompts, schema validation, caching behavior, and regression examples.

### Phase 4: Match Experience and Trustworthy UX
**Rationale:** Good analysis needs good presentation to be believed and shared.
**Delivers:** clearer match pages, better coaching readability, and trust signals.

### Phase 5: Regression Safety Net
**Rationale:** Public-facing iteration is safer when critical flows are tested.
**Delivers:** backend and frontend tests for the core search -> match -> coaching path.

### Phase 6: Community-Ready Hardening
**Rationale:** Final stabilization turns the improved prototype into something fit for broader feedback.
**Delivers:** final polish, failure-state handling, and launch readiness.

### Phase Ordering Rationale

- Security and trust boundaries come first because later features depend on them.
- Input quality and analysis contracts come before prompt tuning because better prompts cannot compensate for bad evidence.
- UX polish follows once the output is reliable enough to present confidently.
- Regression and launch hardening come after the core stack is materially improved.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1:** security review of current endpoint and token patterns
- **Phase 2:** reliability of localhost evidence ingestion and validation rules
- **Phase 3:** evaluation harness for analysis consistency and output quality

Phases with standard patterns:
- **Phase 4:** web UI presentation and loading-state polish
- **Phase 5:** test scaffolding and regression coverage

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Existing architecture already works end to end |
| Features | HIGH | User direction is clear and scoped |
| Architecture | MEDIUM | Strong base exists, but trust boundaries need refinement |
| Pitfalls | MEDIUM | Based on official guidance plus inference from current code |

**Overall confidence:** MEDIUM

### Gaps to Address

- Analysis quality needs validation with real representative match fixtures
- Security review should inspect current backend endpoints and desktop upload paths directly
- Frontend trust signals need to be designed around the actual analysis states in the code

## Sources

### Primary (HIGH confidence)
- Riot Developer Portal: Match-V5 API reference - match and timeline capabilities
  https://developer.riotgames.com/apis#match-v5
- Riot Developer Portal: API policies - operational boundaries
  https://developer.riotgames.com/docs/portal
- OWASP Authentication Cheat Sheet - auth and session guidance
  https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- OWASP Input Validation Cheat Sheet - request validation guidance
  https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html

### Secondary (MEDIUM confidence)
- `.planning/PROJECT.md`
- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/CONCERNS.md`

---
*Research completed: 2026-04-01*
*Ready for roadmap: yes*
