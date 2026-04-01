# Stack Research

**Project:** mvp.gg
**Domain:** League of Legends statistics plus AI post-game analysis
**Researched:** 2026-04-01
**Confidence:** MEDIUM

## Recommendation

The current stack is already viable for the product goal. The right move is not a rewrite. It is to harden the existing FastAPI + React + Supabase + local companion architecture with stronger contracts, evaluation, and security boundaries.

For this milestone, the most important stack decision is to preserve typed backend ownership of match context and analysis generation. The frontend should remain a presentation layer. Any scoring, permissions, request validation, or trust decisions that matter to product integrity should live in backend code or persisted backend-controlled state.

## Keep

- **FastAPI + Pydantic**: Good fit for explicit schemas, request validation, and server-owned contracts.
- **React + Vite**: Good fit for a browser-first stat product that needs fast iteration on UI.
- **Supabase**: Good enough for analysis persistence and cache-backed reads in the current architecture.
- **Desktop companion app**: Still needed because localhost-derived post-game context is part of the product moat.

## Strengthen

- **Structured analysis contract**: Lock the AI output to a stable schema with validation and fallback handling.
- **Evaluation layer**: Add deterministic checks around prompt inputs, output validity, evidence coverage, and regression review.
- **Server-side trust boundaries**: Move or keep all critical logic server-side, including validation of uploads, sensitive endpoints, and analysis eligibility.
- **Test coverage**: Add backend tests around context building, upload validation, and analysis shaping; add at least a frontend smoke path for search -> match -> coaching rendering.

## Defer

- Replacing the stack wholesale
- Adding new databases or queueing systems unless scale or reliability data proves they are needed
- Introducing heavy real-time infrastructure before post-game quality is trusted

## Implications

- Phase planning should begin with trust boundaries and evidence validation, not UI-only work.
- AI quality improvements should be built on top of a stable context schema and repeatable analysis contract.
- Frontend polish should follow once backend output is reliable enough to present confidently.

## Sources

### Primary
- Riot Developer Portal: Match-V5 API reference - official source for match and timeline capabilities
  https://developer.riotgames.com/apis#match-v5
- Riot Developer Portal: API policies and operational constraints - official source for usage expectations
  https://developer.riotgames.com/docs/portal

### Secondary
- Existing brownfield codebase and codebase map under `.planning/codebase/`

---
*Research completed: 2026-04-01*
