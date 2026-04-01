# Codebase Concerns

**Analysis Date:** 2026-03-30

## Tech Debt

**Backend modularity:**
- Issue: Many domain modules, some tight coupling
- Files: `ProjectB/coach_ai.py`, `ProjectB/context_builder.py`, `ProjectB/riot_client.py`
- Impact: Harder to refactor, risk of logic duplication
- Fix approach: Refactor to clarify module boundaries

## Known Bugs

- Not explicitly documented in codebase

## Security Considerations

**Env secrets:**
- Risk: .env files present, secrets in env vars
- Files: `.env`, `ProjectB/settings.py`
- Current mitigation: Not committed, loaded via dotenv
- Recommendations: Use secret manager in production

## Performance Bottlenecks

**Batch analysis:**
- Problem: Some batch operations may be slow (see postgame_analyzer)
- Files: `ProjectB/postgame_analyzer.py`
- Cause: Large data processed at once
- Improvement path: Profile and optimize batch logic

## Fragile Areas

**AI/LLM integration:**
- Files: `ProjectB/coach_ai.py`, `ProjectB/context_builder.py`
- Why fragile: External API dependencies, error handling
- Safe modification: Add retries, error logging
- Test coverage: Needs more integration tests

## Scaling Limits

**Backend API:**
- Current capacity: Not specified
- Limit: Unknown
- Scaling path: Deploy to scalable cloud infra

## Dependencies at Risk

**Anthropic, Gemini APIs:**
- Risk: API changes, quota limits
- Impact: AI features may break
- Migration plan: Add fallback or monitoring

## Missing Critical Features

- No E2E or frontend automated tests detected

## Test Coverage Gaps

**Frontend:**
- What's not tested: UI, user flows
- Files: `ProjectB-frontend/src/`
- Risk: UI bugs go undetected
- Priority: High

---

*Concerns audit: 2026-03-30*