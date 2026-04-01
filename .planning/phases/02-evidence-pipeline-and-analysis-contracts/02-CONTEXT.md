# Phase 2: Evidence Pipeline and Analysis Contracts - Context

**Gathered:** 2026-04-01
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase defines and hardens the evidence pipeline contract that feeds AI analysis. It covers how evidence moves from ingestion to normalized context to analysis execution, what validation checkpoints exist between those stages, and how pipeline state is represented so the system can safely trust or reject an analysis attempt.

</domain>

<decisions>
## Implementation Decisions

### Verification checkpoints
- **D-01:** The evidence pipeline must use strong, formal checkpoints between stages rather than relying only on logs or ad hoc exceptions.
- **D-02:** Each major stage in the pipeline must validate both its input and its output before the next stage can proceed.
- **D-03:** The pipeline must fail closed by default when a checkpoint does not pass.

### Status model
- **D-04:** Each checkpoint must produce a structured machine-readable status, not just a boolean pass/fail.
- **D-05:** Checkpoint status must include a structured reason when a stage is rejected, blocked, or degraded.
- **D-06:** The status model should support distinctions such as accepted, invalid input, incomplete evidence, degraded-safe, ready, and blocked, or equivalent explicit categories.

### Internal versus external visibility
- **D-07:** The backend must keep detailed internal pipeline statuses for verification, debugging, and deterministic behavior.
- **D-08:** The frontend and user-facing product should consume only a summarized and safe external status model.
- **D-09:** External statuses should stay simple and product-oriented, such as ready, pending, insufficient_data, or failed, while detailed internal causes remain backend-only.

### the agent's Discretion
- Exact stage boundaries and naming for the checkpoint model
- Exact schema shape for internal versus external status payloads
- Whether checkpoint reasons are represented as enums, typed codes, structured objects, or a combination, as long as they stay machine-readable and deterministic

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase definition
- `.planning/ROADMAP.md` - Phase 2 goal, requirements, and success criteria
- `.planning/REQUIREMENTS.md` - Phase requirements `DATA-01`, `DATA-02`, `QUAL-02`
- `.planning/PROJECT.md` - Project trust and validation principles
- `.planning/phases/01-trust-boundaries-and-security-foundation/01-CONTEXT.md` - inherited trust-boundary and fail-closed decisions from Phase 1

### Existing evidence pipeline
- `ProjectB/main.py` - current ingestion, upload handling, analysis execution, and coaching delivery routes
- `ProjectB/schemas.py` - current request and response contracts for uploads and coaching responses
- `ProjectB/context_builder.py` - normalized match context construction
- `ProjectB/coach_ai.py` - AI analysis contract, cache interaction, and structured result handling
- `ProjectB/postgame_analyzer.py` - post-game multimodal analysis entry point
- `ProjectB/db.py` - current persistence shape for coaching analysis and cache data
- `ProjectB/live_coach.py` - local event capture and payload assembly
- `ProjectB/coach_guardrails.py` - current output guardrails and sanitization logic

### Existing tests and concerns
- `ProjectB/tests/test_public_read_only_mode.py` - current protected/public flow behavior and upload-related tests
- `.planning/codebase/ARCHITECTURE.md` - current data flow across backend, frontend, and local app
- `.planning/codebase/CONCERNS.md` - current fragile areas around AI integration and verification gaps

No external specs - requirements are fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ProjectB/schemas.py`: already defines typed upload and response models that can anchor stricter checkpoint contracts
- `ProjectB/context_builder.py`: already centralizes normalization into `MatchContext`, making it a natural checkpoint boundary
- `ProjectB/coach_guardrails.py`: existing guardrail layer can be treated as one of the later verification stages in the pipeline
- `ProjectB/tests/test_public_read_only_mode.py`: existing backend tests provide patterns for asserting blocked and accepted flows

### Established Patterns
- FastAPI route handlers orchestrate ingestion and analysis in `ProjectB/main.py`
- Pydantic models are the codebase standard for contracts
- AI outputs already have partial structured expectations (`insights`, `feedback_geral`) in `ProjectB/coach_ai.py`
- Current persistence is centered around the `ai_cache` table in `ProjectB/db.py`

### Integration Points
- Upload ingestion enters through backend routes in `ProjectB/main.py`
- Evidence normalization happens in `ProjectB/context_builder.py`
- Analysis execution and cache interaction happen in `ProjectB/coach_ai.py` and `ProjectB/postgame_analyzer.py`
- User-visible availability and analysis read paths flow through coaching endpoints in `ProjectB/main.py`

</code_context>

<specifics>
## Specific Ideas

- The evidence pipeline should be explicitly traceable between stages rather than inferred from logs.
- Detailed status and cause tracking should remain internal to the backend.
- User-facing delivery should expose only a safe summarized status model.
- This phase should make later UI states like ready, pending, insufficient data, and failed unambiguous.

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope.

</deferred>

---

*Phase: 02-evidence-pipeline-and-analysis-contracts*
*Context gathered: 2026-04-01*
