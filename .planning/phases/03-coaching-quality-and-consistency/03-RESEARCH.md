# Phase 3: Coaching Quality and Consistency - Research

**Researched:** 2026-04-01
**Domain:** Evidence-bound coaching generation, deterministic output behavior, and cache/revisit policy
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
### Output contract and specificity
- **D-01:** Every analysis must use a fixed 3-block structure: strengths, mistakes, and next steps.
- **D-02:** Default density must stay concise: 3 to 5 insights per analysis.
- **D-03:** Voice must stay direct and practical; praise only with strong proof.
- **D-04:** Every valid insight must include problem, evidence, impact, and action.
- **D-05:** Next steps must include 1 to 3 concrete actions with numeric targets.
- **D-06:** Weak-signal runs must use a conservative fail-safe, reducing claims instead of filling with generic text.

### Evidence binding policy
- **D-07:** Every insight and every feedback paragraph must include explicit evidence (timestamp + metric).
- **D-08:** Factual precision wins over readability when trade-offs exist.
- **D-09:** Guardrails must block or rewrite weak claims, not pass them through.
- **D-10:** Missing evidence must produce insufficient-data behavior, not speculation.

### Consistency and determinism
- **D-11:** Similar matches should produce high deterministic consistency.
- **D-12:** Output contract must be schema-validated before delivery.
- **D-13:** Prioritization is fixed by game impact (gold/xp/objectives/map state), not category balancing.
- **D-14:** Similarity criteria are strict: same champion, same role, close duration/event windows.
- **D-15:** Variation in language should stay very low for similar matches.
- **D-16:** Insight categories must use a closed taxonomy.

### Revisit, cache, and regeneration policy
- **D-17:** Revisit must return validated cache; no automatic regeneration.
- **D-18:** v1 regeneration is not available for non-paying users.
- **D-19:** Non-paying regeneration attempts must be blocked with clear status/message.
- **D-20:** Prompt or model updates must not invalidate historical analyses automatically.

### Availability rule
- **D-21:** Without local app evidence, no analysis should be delivered.
- **D-22:** User-facing unavailable state must guide user to install app and play one match.

### the agent's Discretion
- Exact numeric thresholds for weak-signal classification.
- Exact similarity fingerprint implementation.
- Final API field naming for unavailable/paid-gated status details.

### Deferred Ideas (OUT OF SCOPE)
- Paid entitlement and billing/login implementation for regeneration.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ANLY-01 | User receives concrete strengths, mistakes, and next actions for that specific match | Output contract schema and strict sectioned payload enforce non-generic coaching |
| ANLY-02 | Coaching points are tied to evidence instead of generic advice | Evidence-binding checks on every insight/paragraph and guardrail rewrite/block policy |
| ANLY-03 | Similar matches produce stable structure and quality | Deterministic ranking, closed taxonomy, strict similarity fingerprint, low-variance templates |
| ANLY-04 | Revisit returns same validated result unless intentionally regenerated | Cache-first read path, explicit regeneration gate, immutable historical cache policy |
</phase_requirements>

## Summary

Phase 2 already established fail-closed evidence checkpoints and safe public status mapping. Phase 3 should build directly on that foundation by hardening the generation contract itself: enforce structure, enforce evidence references, and prevent unstable outputs from leaving the backend.

The highest-leverage approach is to separate "generation" from "delivery contract". The model can still generate flexible text internally, but the backend should normalize it into a strict contract and refuse delivery if it cannot satisfy the evidence and structure rules. This keeps quality and trust decisions backend-owned and testable.

**Primary recommendation:** Introduce a strict coaching-output contract module and deterministic ranking rules, then enforce cache-first revisit policy with explicit unavailable/paid-gated status behavior.

## Project Constraints (from PROJECT.md and CLAUDE.md)

- Preserve the brownfield architecture; improve current modules instead of replacing runtime boundaries.
- Keep backend ownership over trust-critical decisions and user-visible status semantics.
- Add explicit tests for critical quality behavior before changing UX assumptions.
- Keep v1 simple: no broad product expansion, no paid entitlement implementation yet.
- Respect existing evidence pipeline contracts from Phase 2.

## Architecture Patterns

### Pattern 1: Strict coaching output contract before delivery
**What:** Normalize model output into a fixed contract containing strengths, mistakes, and next_steps.
**When to use:** Immediately after model response parsing and before cache write/delivery.
**Shape recommendation:**
- `strengths`: 0..2 entries
- `mistakes`: 1..5 entries
- `next_steps`: 1..3 entries
- each insight carries `problem`, `evidence`, `impact`, `action`, and `category`

### Pattern 2: Evidence-bound paragraph and insight validation
**What:** Every insight and every feedback paragraph must include evidence anchors.
**When to use:** In guardrail lint and in final contract validation.
**Rule recommendation:**
- At least one timestamp (`mm:ss`) and one numeric metric per paragraph.
- Any unsupported factual claim becomes rewrite-required or blocked.

### Pattern 3: Deterministic prioritization and closed taxonomy
**What:** Sort candidate insights using explicit impact scoring and fixed tie-breakers.
**When to use:** Right before selecting the final 3-5 insights.
**Rule recommendation:**
- Primary rank: estimated match impact (gold/xp/objective pressure).
- Tie-breakers: earlier objective windows, repeated costly events, confidence level.
- Categories restricted to a fixed enum.

### Pattern 4: Cache-first revisit with explicit regeneration gate
**What:** Revisit path should return validated cache deterministically.
**When to use:** `/coaching/{match_id}`, `/coaching/status`, and any regenerate-like endpoint.
**Rule recommendation:**
- Revisit never regenerates automatically.
- Regeneration attempt by non-paying user returns an explicit blocked status.
- Prompt/model changes do not auto-invalidate existing cache rows.

### Pattern 5: Unavailable coaching state without local evidence
**What:** If local evidence is missing, expose unavailable state and clear CTA.
**When to use:** Status endpoints and coaching fetch endpoints.
**Rule recommendation:**
- External status remains safe and explicit (`insufficient_data` with unavailable reason).
- Response includes actionable message: install app and play one match.

## Anti-Patterns to Avoid

- Letting freeform `feedback_geral` bypass contract validation.
- Treating fallback prose as equivalent to validated coaching.
- Auto-regenerating when cache exists and is valid.
- Mixing paid-feature gating with unfinished auth/billing logic.
- Returning private guardrail reason details directly to public clients.

## Common Pitfalls

### Pitfall 1: Contract drift between internal output and API schemas
If API returns fields not guaranteed by validation, frontend trust breaks.

### Pitfall 2: Evidence checks only on insights, not on feedback paragraphs
Users read narrative first; unsupported paragraphs still damage trust.

### Pitfall 3: Similarity matching too broad
Loose matching creates unstable outputs and false "determinism" assumptions.

### Pitfall 4: Cache keying ignores role/champion constraints
Wrongly shared analyses look deterministic but are factually mismatched.

### Pitfall 5: Unavailable state hidden behind generic pending
Without a clear CTA, users cannot recover and product appears broken.

## Validation Architecture

### Test framework
- `pytest` with existing backend suite under `ProjectB/tests`.

### Wave focus for Phase 3
- Wave 1: output contract + guardrails evidence binding.
- Wave 2: deterministic selection and cache/revisit policy.
- Wave 3: unavailable and weak-signal delivery behavior.

### Suggested verification commands
- `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests/test_guardrails.py -x`
- `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests/test_coach_ai_cache.py ProjectB/tests/test_public_read_only_mode.py -x`
- `& .\ProjectB\.venv\Scripts\python.exe -m pytest ProjectB/tests/test_evidence_pipeline.py ProjectB/tests/test_public_read_only_mode.py -k "coaching or status" -x`

## Sources

### Primary (HIGH confidence)
- `.planning/phases/03-coaching-quality-and-consistency/03-CONTEXT.md`
- `.planning/REQUIREMENTS.md`
- `ProjectB/coach_ai.py`
- `ProjectB/coach_guardrails.py`
- `ProjectB/main.py`
- `ProjectB/db.py`
- `ProjectB/schemas.py`
- `ProjectB/tests/test_guardrails.py`
- `ProjectB/tests/test_coach_ai_cache.py`
- `ProjectB/tests/test_public_read_only_mode.py`

### Secondary (MEDIUM confidence)
- `.planning/phases/02-evidence-pipeline-and-analysis-contracts/02-CONTEXT.md`
- `.planning/phases/02-evidence-pipeline-and-analysis-contracts/02-RESEARCH.md`
- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/CONCERNS.md`

## Metadata

**Confidence breakdown:**
- Output contract strategy: HIGH
- Determinism and cache policy approach: HIGH
- Endpoint delivery semantics: HIGH

**Research date:** 2026-04-01
**Valid until:** 2026-05-01
