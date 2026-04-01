# Phase 4: Match Experience and Trustworthy UX - Context

**Gathered:** 2026-04-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Esta fase melhora a experiencia de busca, navegacao e leitura da partida para que o fluxo ate o coaching fique claro, polido e confiavel para compartilhamento. O foco e UX de descoberta e apresentacao; nao adiciona novos produtos fora de escopo (chat, comparador, recursos pagos completos, etc.).

</domain>

<decisions>
## Implementation Decisions

### Fluxo de navegacao e retorno
- **D-01:** Abrir `/match/:id` direto (link compartilhado, sem historico) deve carregar o dashboard da partida sempre que houver dados publicos suficientes.
- **D-02:** No acesso direto por link, o botao "Voltar" deve ir para a home (`/`) em vez de depender apenas de `navigate(-1)`.
- **D-03:** Busca da home fica com validacao forte e mensagens completas; busca global (navbar) fica com validacao minima e delega erros de dados para as telas de destino.
- **D-04:** Se falhar o carregamento da partida por `match_id`, a tela da partida deve mostrar erro inline com duas acoes: "Tentar novamente" e "Ir para home".

### Estados de coaching no frontend
- **D-05:** O badge "IA" na lista de partidas (perfil) aparece apenas quando o status for `ready`.
- **D-06:** Estados `pending` e `failed` usam o mesmo card generico bloqueado no bloco de coaching.
- **D-07:** Para indisponibilidade por falta de evidencia local, manter copy fixa: `Coach indisponivel, baixe o app e jogue uma partida.`
- **D-08:** Em link compartilhado sem contexto de dono da analise, mostrar estado explicito `Analise privada para este jogador` (sem blur fake).

### Hierarquia visual da tela de partida
- **D-09:** Acima da dobra: header da partida + resumo curto (resultado/KDA/champion) + bloco de coaching; scoreboard vem abaixo.
- **D-10:** Manter scoreboard denso em todos os breakpoints (sem versao simplificada mobile nesta fase).
- **D-11:** Abas "Detalhes" e "Runas" permanecem visiveis, mas desabilitadas com rotulo "Em breve" (nao clicaveis).
- **D-12:** Adicionar bloco curto de "Status da analise" com estado atual e motivo amigavel para aumentar confianca.

### the agent's Discretion
- Copy final do card generico bloqueado para `pending/failed`, desde que nao conflite com D-07 e D-08.
- Posicionamento exato do bloco "Status da analise" dentro da tela de partida.
- Ajustes finos de espacamento/tipografia para reduzir ruido sem remover densidade util.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase and requirement source of truth
- `.planning/ROADMAP.md` - Phase 4 goal, scope, success criteria, and plan breakdown (`04-01`, `04-02`, `04-03`).
- `.planning/REQUIREMENTS.md` - Requirements `UX-01`, `UX-02`, `DATA-03`.
- `.planning/PROJECT.md` - Product trust bar and sharing-readiness expectations.
- `.planning/STATE.md` - Current phase position and milestone status.

### Prior phase decisions that constrain UX behavior
- `.planning/phases/02-evidence-pipeline-and-analysis-contracts/02-CONTEXT.md` - safe external status model and internal vs external status boundaries.
- `.planning/phases/03-coaching-quality-and-consistency/03-CONTEXT.md` - no-analysis-without-local-evidence and unavailable-state policy.
- `.planning/phases/03-coaching-quality-and-consistency/03-VERIFICATION.md` - validated behavior that Phase 4 must preserve in UI.

### Frontend navigation and match experience files
- `ProjectB-frontend/src/App.jsx` - route map for `/`, `/summoner/:name/:tag`, `/match/:matchId`.
- `ProjectB-frontend/src/components/Navbar.jsx` - global search behavior and navigation entry point.
- `ProjectB-frontend/src/screens/SearchScreen.jsx` - home search validation and entry UX.
- `ProjectB-frontend/src/screens/SummonerProfileScreen.jsx` - match list, coaching status badges, and route handoff to match page.
- `ProjectB-frontend/src/screens/ResultsScreen.jsx` - direct match load fallback, scoreboard/coaching layout, and tab UX.
- `ProjectB-frontend/src/components/CoachingSection.jsx` - ready/locked coaching presentation logic.
- `ProjectB-frontend/src/services/api.js` - `fetchMatchDetails`, `fetchCoachingStatus`, `fetchCoachingAnalysis` contracts.

### Backend status and delivery contracts consumed by frontend
- `ProjectB/main.py` - `/coaching/status` and `/coaching/{match_id}` behavior and message semantics.
- `ProjectB/schemas.py` - `CoachingStatusResponse` and `CoachingAnalysisResponse` public shape.
- `ProjectB/db.py` - external status normalization and weak-signal handling.
- `ProjectB/coach_ai.py` - weak-signal / insufficient-data behavior that drives frontend states.

No external specs - requirements are fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Navbar.jsx` and `SearchScreen.jsx` already contain two search entry points that can be aligned by shared validation/copy decisions.
- `ResultsScreen.jsx` already has fallback loading for direct `/match/:id` access via `fetchMatchDetails`.
- `SummonerProfileScreen.jsx` already prefetches `fetchCoachingStatus` and can gate IA badge visibility.
- `CoachingSection.jsx` already centralizes locked/unlocked rendering and is the right place for status-driven presentation.

### Established Patterns
- Frontend is route-driven (`react-router-dom`) with screen-level data fetching and local loading/error state.
- API layer in `services/api.js` uses safe fallbacks for non-critical coaching/status reads.
- Visual style is dark Tailwind utility pattern with compact data-dense cards and gradient separators.

### Integration Points
- Search flow: `SearchScreen`/`Navbar` -> `/summoner/:name/:tag` -> `SummonerProfileScreen`.
- Match flow: `SummonerProfileScreen` -> `/match/:matchId` -> `ResultsScreen`.
- Coaching visibility flow: `fetchCoachingStatus` (profile list) + `fetchCoachingAnalysis` (match page) backed by Phase 3 safe statuses.

</code_context>

<specifics>
## Specific Ideas

- Link compartilhado de partida deve abrir dashboard para melhorar experiencia de compartilhamento.
- Analise personalizada nao deve aparecer para quem nao e dono/contexto correto.
- Sinal de status curto e explicito na tela melhora confianca e reduz confusao sobre "tem IA ou nao tem IA".

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope.

</deferred>

---

*Phase: 04-match-experience-and-trustworthy-ux*
*Context gathered: 2026-04-01*
