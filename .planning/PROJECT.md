# mvp.gg

## What This Is

mvp.gg is a web product for League of Legends players who want more than raw match statistics. It combines familiar match-history and match-detail views with AI-driven post-game analysis that explains mistakes, strengths, and improvement opportunities for solo queue players trying to climb.

The current system already spans a web frontend, a cloud API, and a local companion app that collects post-game context from Riot's local APIs. This milestone focuses on turning that prototype into a more trustworthy, consistent, secure, and community-ready product.

## Core Value

The product must show a solo queue player meaningful errors and strengths they would not have identified alone, in a way they can trust and act on.

## Requirements

### Validated

- [x] User can search League of Legends players by Riot ID and retrieve recent matches - existing
- [x] User can open detailed match pages with scoreboard and match context data - existing
- [x] System can ingest Riot public API data including history, picks, builds, runes, and match timelines - existing
- [x] Local desktop companion can capture live/post-game event context and minimap imagery through Riot localhost APIs - existing
- [x] System can generate and store AI-based post-game analysis for matches - existing
- [x] Web frontend can display stored coaching analysis when available - existing
- [x] Coaching analysis now returns a strict strengths/mistakes/next_steps contract with evidence-bound claims - validated in Phase 3 (ANLY-01, ANLY-02)
- [x] Similar matches now produce deterministic coaching structure and stable ordering - validated in Phase 3 (ANLY-03)
- [x] Revisit behavior is cache-first and regeneration is explicitly gated - validated in Phase 3 (ANLY-04)
- [x] Missing local evidence now fails safe with unavailable/insufficient_data user messaging - validated in Phase 3

### Active

- [ ] End-to-end product flow is stable and polished enough to share with the wider League community for feedback
- [ ] Interface quality is strong enough to feel modern, clear, and worth using repeatedly in the browser
- [ ] Security posture is improved so the codebase is safe to extend toward login, monetization, and user data features
- [ ] Backend architecture, boundaries, and verification points are strong enough to evolve without trusting critical logic to the frontend
- [ ] Tests and validation checks cover critical flows and reduce the chance of regressions or unsafe changes

### Out of Scope

- Live in-game coaching or real-time decision assistance - this milestone is focused on post-game analysis quality first
- Coach/team workflows - the product is aimed at solo players, and human coaching remains a different offering
- Mobile app clients - the product is browser-first for now
- Deep phase-by-phase recommendations, dynamic AI chat, and match-reference comparison - intentionally deferred until the simpler core analysis earns positive community feedback

## Context

The current codebase is a brownfield system with three runtimes: a FastAPI cloud backend, a React web frontend, and a Windows desktop companion app. The existing architecture already integrates Riot APIs, Supabase persistence, Gemini-based analysis, and localhost capture flows for post-game context.

The product direction is not to compete on raw stats alone with sites like op.gg, but to differentiate through useful AI interpretation after a match. The main product risk is not data access; it is trust. Today the prototype already works end to end, but the analysis is not yet reliable or consistent enough to earn user confidence.

Community perception matters early. The first-use experience should make a player feel that the analysis exposed mistakes they had not noticed alone. Security also matters early: the system is expected to grow into login, monetization, and richer user data, so insecure shortcuts now would create expensive risk later.

## Constraints

- **Architecture**: Existing brownfield architecture should be improved, not discarded - there is already working backend, frontend, localhost integration, and analysis flow
- **Security**: Backend must own critical trust decisions and never rely on frontend-enforced business logic - future login and monetization increase the cost of weak boundaries
- **Validation**: Important flows should include verification between stages plus test coverage - reliability and safety depend on catching bad assumptions early
- **Platform**: Web browser is the primary product surface — mobile apps are intentionally excluded for now
- **Product Scope**: v1 should stay simple and execute well before adding advanced coaching features — early community trust matters more than feature breadth
- **Data Sources**: Analysis depends on Riot public APIs plus localhost-derived match context from the desktop companion — these integration paths must remain viable

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Build around post-game AI analysis instead of stats alone | Stats products already exist; the differentiation is helping players understand why games went wrong or right | - Pending |
| Focus the initial product on solo queue players trying to climb | Narrow audience improves clarity of requirements, UX, and analysis tone | - Pending |
| Keep v1 intentionally simple and defer chat/reference-comparison/deeper phase coaching | The current need is trust, consistency, and positive feedback, not maximum feature count | - Pending |
| Treat security as a core requirement before login and monetization arrive | Weak boundaries now create higher risk later when accounts and payments exist | - Pending |
| Do not trust frontend logic for backend-critical decisions | Security and integrity require server-side enforcement and verification at each stage | - Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-01 after Phase 03 completion*
