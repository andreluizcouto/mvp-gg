# Phase 3: Coaching Quality and Consistency - Context

**Gathered:** 2026-04-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Esta fase melhora a qualidade do coaching gerado para que ele seja especifico, consistente e acionavel, sempre ancorado em evidencias validas da partida. Tambem define regras de revisita/cache para manter estabilidade do resultado ao longo do tempo.

</domain>

<decisions>
## Implementation Decisions

### Output contract and specificity
- **D-01:** Toda analise deve usar estrutura fixa em 3 blocos: forcas, erros e proximos passos.
- **D-02:** Densidade padrao enxuta: 3 a 5 insights por analise.
- **D-03:** Tom do feedback deve ser direto de coach, sem floreio, e elogios so entram com prova forte.
- **D-04:** Cada insight valido precisa conter problema, evidencia, impacto no jogo e acao pratica.
- **D-05:** Proximos passos devem ter 1 a 3 acoes objetivas com meta numerica.
- **D-06:** Em sinal fraco, aplicar fail-safe conservador: reduzir claims e marcar insuficiencia em vez de completar com filler.
- **D-07:** Repeticao de conselho para erro recorrente e permitida, com variacao minima de texto.

### Evidence binding policy
- **D-08:** Rigor maximo: todo insight e todo paragrafo do feedback devem ter evidencia explicita (timestamp + numero/indicador).
- **D-09:** Em conflito entre clareza e precisao, sempre priorizar precisao factual.
- **D-10:** Endurecer guardrails e ampliar casos de bloqueio/rewrite obrigatorio para claims fracos.
- **D-11:** Sem evidencia suficiente, nao afirmar claim; marcar insuficiencia de dados.
- **D-12:** Claims de visao/posicionamento so entram com evidencia local (eventos + minimapa).

### Consistency and determinism
- **D-13:** Alto determinismo para partidas similares.
- **D-14:** Schema rigido com validacao forte; output fora de contrato nao deve ser entregue.
- **D-15:** Priorizacao fixa por impacto real no resultado da partida (gold/xp/objetivo/mapa), nao por categoria.
- **D-16:** Similaridade estrita: mesmo campeao, mesma role, duracao/faixa de eventos proximos.
- **D-17:** Variacao textual muito baixa entre partidas similares.
- **D-18:** Taxonomia fechada de categorias de insight.

### Revisit, cache and regeneration
- **D-19:** Revisita de partida deve retornar sempre cache validado, sem regeneracao automatica.
- **D-20:** v1 nao permite regeneracao para usuario nao pagante.
- **D-21:** Tentativa de regeneracao por nao pagante deve ser bloqueada com status/mensagem clara de recurso pago.
- **D-22:** Mudancas internas de prompt/guardrails/modelo nao invalidam analises historicas automaticamente.
- **D-23:** Regeneracao fica reservada para plano pago em fase futura de monetizacao/login.

### Availability without local app evidence
- **D-24:** Sem app local e sem evidencia local, nao ha analise (nem parcial).
- **D-25:** UX deve exibir estado indisponivel com CTA de download do app e instrucao de jogar uma partida para habilitar coaching.

### the agent's Discretion
- Definir thresholds numericos exatos para classificar "sinal fraco", mantendo o fail-safe conservador.
- Definir heuristica tecnica final para detectar "partidas similares" sem quebrar D-16 e D-17.
- Ajustar copy final da mensagem de indisponibilidade sem mudar o sentido da decisao D-25.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase and requirement source of truth
- `.planning/ROADMAP.md` - Goal, scope and success criteria for Phase 3.
- `.planning/REQUIREMENTS.md` - Requirements `ANLY-01`, `ANLY-02`, `ANLY-03`, `ANLY-04`.
- `.planning/PROJECT.md` - Product promise and trust bar for coaching quality.
- `.planning/STATE.md` - Current execution context and prior milestone state.

### Prior phase constraints that carry forward
- `.planning/phases/01-trust-boundaries-and-security-foundation/01-CONTEXT.md` - Fail-closed and backend trust decisions that still apply.
- `.planning/phases/02-evidence-pipeline-and-analysis-contracts/02-CONTEXT.md` - Evidence pipeline checkpoints and external status model inherited by Phase 3.

### Coaching generation and validation path
- `ProjectB/coach_ai.py` - Prompting, cache policy, evidence bundle gating and full analysis orchestration.
- `ProjectB/coach_guardrails.py` - Lint/rewrite/sanitize guardrail rules for factual output quality.
- `ProjectB/evidence_pipeline.py` - Stage gating contracts used by analysis flow.
- `ProjectB/context_builder.py` - Match context fields that feed evidence-backed coaching claims.
- `ProjectB/postgame_analyzer.py` - Local postgame analysis path and prompt assembly.

### Delivery and status surfaces
- `ProjectB/main.py` - `/analyze`, `/coaching/status`, `/coaching/{match_id}`, `/coaching/save`, and local upload endpoints.
- `ProjectB/db.py` - `ai_cache` persistence, pipeline snapshot normalization, and external status derivation.
- `ProjectB/schemas.py` - Response contracts for coaching payload and status exposure.

### Local app evidence dependency
- `ProjectB/coach_app.py` - Local app state machine, upload and status polling flow.
- `ProjectB/live_coach.py` - Event capture lifecycle feeding local evidence.
- `ProjectB/live_game_client.py` - Riot local client integration used by desktop capture flow.

### Regression references for quality gates
- `ProjectB/tests/test_guardrails.py` - Guardrail rule coverage and expected violation behaviors.
- `ProjectB/tests/test_evidence_pipeline.py` - Stage status and external status regression contracts.
- `ProjectB/tests/test_public_read_only_mode.py` - API behavior including safe public coaching status handling.
- `ProjectB/tests/test_coach_ai_cache.py` - Cache keying behavior across `match_id,riot_id`.

### Codebase maps used during discussion
- `.planning/codebase/ARCHITECTURE.md` - Runtime flow and cross-system integration map.
- `.planning/codebase/CONVENTIONS.md` - Implementation conventions for backend/frontend modules.
- `.planning/codebase/STRUCTURE.md` - Repository layout and module boundaries.
- `.planning/codebase/STACK.md` - Runtime/dependency stack constraints.
- `.planning/codebase/CONCERNS.md` - Known fragility around AI integration and testing gaps.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ProjectB/coach_ai.py`: `run_full_analysis`, pipeline stage gating, and cache read/write helpers can host stricter quality rules.
- `ProjectB/coach_guardrails.py`: existing lint/rewrite/sanitize pipeline is the direct extension point for stronger evidence enforcement.
- `ProjectB/db.py`: snapshot and `external_status` derivation already support safe status signaling when analysis is blocked.
- `ProjectB/main.py`: coaching endpoints already centralize public status and analysis retrieval behavior.
- `ProjectB/coach_app.py` and `ProjectB/live_coach.py`: existing local evidence capture/upload pipeline supports minimap-based claim gating.

### Established Patterns
- Fail-closed decisions and pipeline checkpoints are already standard from Phase 2.
- Pydantic contracts define stable API surfaces for analysis and status payloads.
- Cached analysis is keyed by `match_id,riot_id` and reused across revisits.
- Public exposure uses safe summarized status while internal reasons remain backend-side.

### Integration Points
- Analysis generation path: Riot/local evidence -> `context_builder` -> `coach_ai` -> `ai_cache`.
- User-facing delivery path: `GET /coaching/status` and `GET /coaching/{match_id}` in `ProjectB/main.py`.
- Local evidence ingestion path: desktop app upload/polling in `ProjectB/coach_app.py` with local endpoints in `ProjectB/main.py`.
- Guardrail enforcement path: `coach_ai` output post-processing through `coach_guardrails`.

</code_context>

<specifics>
## Specific Ideas

- User requirement: "Quem nao tiver o app instalado nem vai ter analises."
- Expected UX for unavailable coaching: "Coach indisponivel, baixe o app e jogue uma partida."
- Regeneration should exist only as a paid capability in a future monetization phase.

</specifics>

<deferred>
## Deferred Ideas

- Paid regeneration entitlement implementation (billing/login checks, plan verification, and paid feature flags) belongs to future monetization/auth phases.

</deferred>

---

*Phase: 03-coaching-quality-and-consistency*
*Context gathered: 2026-04-01*
