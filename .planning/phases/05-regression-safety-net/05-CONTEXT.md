# Phase 5: Regression Safety Net - Context

**Gathered:** 2026-04-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Esta fase protege os fluxos mais críticos com testes automatizados e verificações repetíveis para detectar regressões antes de envio público.
O foco é cobertura e confiabilidade do que já existe (especialmente coaching/status), sem adicionar novas capacidades de produto.

</domain>

<decisions>
## Implementation Decisions

### Cobertura backend crítica (prioridade da fase)
- **D-01:** A primeira frente da Fase 5 será cobertura de regressão para os endpoints públicos de coaching e status.
- **D-02:** Regra não-negociável: nunca expor conteúdo de análise quando faltar evidência local válida.
- **D-03:** Em acesso sem ownership/contexto correto, a API deve responder com estado seguro (`private` no frontend derivado de contexto ausente, ou `insufficient_data`/indisponível no backend), sem texto de análise.

### Fluxo de ownership e privacidade (app desktop + web)
- **D-04:** O app desktop é somente sinalizador de prontidão e direcionamento: avisa que a análise ficou pronta e leva para o link direto da partida.
- **D-05:** O usuário deve conseguir ver apenas a própria análise (riot_id + match_id corretos); visualização de terceiros não deve liberar conteúdo.
- **D-06:** Testes devem validar explicitamente que link compartilhado sem identidade compatível nunca retorna análise.

### the agent's Discretion
- Seleção exata dos casos de teste complementares (rate-limit, schema shape e compatibilidade de payload) desde que não despriorize D-01..D-06.
- Organização dos testes entre arquivos existentes (`test_public_read_only_mode.py` e correlatos) ou novos módulos de regressão, mantendo padrão atual do backend.

</decisions>

<specifics>
## Specific Ideas

- "a intenção do app é só pro cara ver que tem algo rodando no pc dele"
- "o app vai direcionar ele falando que a analise ficou pronta"
- "vai levar ele direto pro link da partida com o riot id dele + matchid"
- "ele vai conseguir ver só a analise dele"
- Regra explícita escolhida: "Nunca mostrar análise; retornar estado privado/indisponível."

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase and requirement source of truth
- `.planning/ROADMAP.md` — Phase 5 goal, success criteria, and plan split (`05-01`, `05-02`).
- `.planning/REQUIREMENTS.md` — Requirement `QUAL-01`.
- `.planning/PROJECT.md` — Core value and trust boundary expectations.
- `.planning/STATE.md` — Current execution state and carry-over constraints.

### Prior phase decisions that constrain test expectations
- `.planning/phases/03-coaching-quality-and-consistency/03-CONTEXT.md` — no-analysis-without-local-evidence and unavailable behavior.
- `.planning/phases/04-match-experience-and-trustworthy-ux/04-CONTEXT.md` — frontend status model and direct-link/private behavior.

### Backend contracts under regression protection
- `backend/main.py` — `/coaching/status`, `/coaching/{match_id}`, auth/rate-limit and safe response behavior.
- `backend/schemas.py` — `CoachingStatusResponse`, `CoachingAnalysisResponse`, `CoachingRegenerateResponse`.
- `backend/db.py` — snapshot normalization and external status derivation.
- `backend/coach_ai.py` — cache/evidence gating used by coaching delivery paths.

### Existing regression suites and helpers
- `backend/tests/test_public_read_only_mode.py` — safe external states, unavailable responses, blocked regenerate, read-only protections.
- `backend/tests/test_evidence_pipeline.py` — evidence stage gating and external status summarization contracts.
- `backend/run_tests.py` — existing pytest entrypoint pattern.

### Frontend consumers that reflect backend status/ownership constraints
- `frontend/src/services/api.js` — `fetchCoachingStatus` and `fetchCoachingAnalysis` consumption behavior.
- `frontend/src/screens/SummonerProfileScreen.jsx` — IA badge gating (`status === "ready"`).
- `frontend/src/screens/ResultsScreen.jsx` — direct-link handling and private/insufficient display derivation.

No external specs — requirements are fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/tests/test_public_read_only_mode.py`: já cobre grande parte dos contratos públicos de segurança/status e é o ponto mais direto para expandir regressão de ownership.
- `backend/tests/test_evidence_pipeline.py`: já valida caminhos de `pending`/`insufficient_data` no pipeline e reduz risco de falso `ready`.
- `frontend/src/services/api.js`: centraliza leitura dos endpoints de coaching para validar coerência backend→frontend em testes.

### Established Patterns
- Backend usa pytest com monkeypatch e `TestClient` para simular estados e falhas de infraestrutura sem depender de serviços externos.
- Contratos de status públicos já estão normalizados para `ready|pending|insufficient_data|failed`.
- Frontend trata falhas de coaching com fallback seguro (sem crash, sem expor conteúdo indevido).

### Integration Points
- Fluxo protegido principal: desktop/local evidence -> backend snapshot/status -> endpoints `/coaching/*` -> `api.js` -> `ResultsScreen`/`SummonerProfileScreen`.
- A regressão desta fase deve verificar esse fluxo com foco em ownership e não exposição de análise.

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 05-regression-safety-net*
*Context gathered: 2026-04-01*
