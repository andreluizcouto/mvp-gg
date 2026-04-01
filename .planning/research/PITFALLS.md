# Pitfalls Research

**Project:** mvp.gg
**Domain:** League of Legends statistics plus AI post-game analysis
**Researched:** 2026-04-01
**Confidence:** MEDIUM

## Critical Pitfalls

### 1. Generic AI coaching that ignores concrete match evidence

**Warning signs**
- Repeated advice across very different matches
- Text that could apply to any player or champion
- Little connection to timeline events, builds, or context

**Prevention**
- Enforce a strict evidence bundle
- Require structured output fields for mistakes, strengths, and actions
- Add regression examples and review prompts against known-good analyses

**Best phase to address**
- Phase 2 and Phase 3

### 2. Frontend-owned truth or security decisions

**Warning signs**
- Browser-computed logic decides access, trust, or workflow state
- Sensitive endpoints rely on client-side assumptions
- Internal tokens or control paths leak into user-visible surfaces

**Prevention**
- Keep critical logic on the backend
- Add server-side validation for all sensitive requests and uploads
- Add explicit negative tests for malformed or abusive inputs

**Best phase to address**
- Phase 1

### 3. Opaque analysis that users cannot trust

**Warning signs**
- Users cannot tell why the tool reached a conclusion
- Analysis is presented as absolute truth with no evidence or status
- Failed or partial analyses look identical to successful ones

**Prevention**
- Add evidence-backed presentation
- Show clear readiness or fallback states
- Surface enough context for the user to connect the advice to their game

**Best phase to address**
- Phase 3 and Phase 4

### 4. Fragile localhost upload and post-game pipeline

**Warning signs**
- Missing screenshots or events silently degrade results
- Partial uploads produce low-quality analyses
- Failures are hard to detect or recover from

**Prevention**
- Validate payload completeness
- Track explicit job states and failure reasons
- Fail safely instead of showing misleading analysis

**Best phase to address**
- Phase 2

### 5. Weak regression protection while the prompts and pipeline evolve

**Warning signs**
- Analysis quality changes unexpectedly after small backend edits
- Security fixes break working flows
- UI changes hide missing or degraded analysis states

**Prevention**
- Add test coverage around ingestion, context build, output validation, and rendering
- Keep representative fixtures for known match scenarios
- Verify critical flows before public-facing changes

**Best phase to address**
- Phase 5

## Sources

### Primary
- OWASP Authentication Cheat Sheet
  https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- OWASP Input Validation Cheat Sheet
  https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html

### Secondary
- Existing project concerns in `.planning/codebase/CONCERNS.md`
- Existing architecture in `.planning/codebase/ARCHITECTURE.md`

---
*Research completed: 2026-04-01*
