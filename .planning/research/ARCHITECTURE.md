# Architecture Research

**Project:** mvp.gg
**Domain:** League of Legends statistics plus AI post-game analysis
**Researched:** 2026-04-01
**Confidence:** MEDIUM

## Recommended Architecture

The current three-surface architecture is directionally correct:

1. **Data and ingestion layer** - Riot API access, localhost event capture, and upload handling
2. **Context and analysis layer** - deterministic match-context building, analysis orchestration, output validation, and caching
3. **Presentation layer** - profile pages, match pages, and trustworthy analysis UX in the web app

The next improvement is not adding more components. It is tightening the boundaries between them.

## Component Boundaries

### Ingestion
- Owns Riot API fetches, localhost event capture, upload authentication, and raw evidence collection
- Must reject malformed or incomplete payloads before they enter analysis generation

### Context Builder
- Owns normalization of raw match, timeline, builds, runes, and local signals into one analysis-ready evidence bundle
- Must remain deterministic and testable

### Analysis Orchestrator
- Owns prompt construction, schema validation, caching, confidence rules, and fallback behavior
- Must never let raw model output go directly to the UI without validation

### Persistence and Access
- Owns storage for coaching analyses, cache state, and analysis readiness metadata
- Must preserve which inputs produced which analysis result

### Frontend
- Owns discovery, readability, and presentation
- Must not own security-sensitive or truth-defining logic

## Data Flow

1. User requests player or match data from the web app
2. Backend assembles Riot and stored context
3. If local companion evidence exists, backend merges it into the evidence bundle
4. Context builder produces a normalized analysis input
5. Analysis orchestrator validates inputs, runs or reuses analysis, validates outputs, and stores results
6. Frontend renders the result with status, evidence, and clear fallback states

## Build Order

1. Tighten trust boundaries and payload validation
2. Stabilize evidence bundle and analysis contracts
3. Improve coaching quality and consistency
4. Improve presentation and trust signals in the match page
5. Add stronger regression tests and release hardening

## Implications

- Security and validation work comes before UI-heavy roadmap items.
- A dedicated evaluation layer is a better investment than adding more AI surface area early.
- Future login and monetization should plug into this structure without moving trust logic into the browser.

## Sources

### Primary
- Riot Developer Portal: Match-V5 API reference
  https://developer.riotgames.com/apis#match-v5
- Riot Developer Portal: API policies
  https://developer.riotgames.com/docs/portal

### Secondary
- Existing brownfield architecture in `.planning/codebase/ARCHITECTURE.md`

---
*Research completed: 2026-04-01*
