# Phase 2: Evidence Pipeline and Analysis Contracts - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-04-01
**Phase:** 02-Evidence Pipeline and Analysis Contracts
**Areas discussed:** Verification checkpoints

---

## Verification checkpoints

| Option | Description | Selected |
|--------|-------------|----------|
| Checkpoints fortes e formais | Cada etapa valida entrada e saida, gera status claro e registra motivo quando falhar | Yes |
| Checkpoints medios | Validacoes existem, mas sem modelo forte de status | |
| Checkpoints minimos | Validacao so nos pontos mais criticos | |

**User's choice:** Checkpoints fortes e formais
**Notes:** O pipeline deve ter verificacao explicita entre etapas, consistente com a politica fail-closed herdada da Fase 1.

---

## Status model

| Option | Description | Selected |
|--------|-------------|----------|
| Status por etapa + motivo estruturado | Cada etapa gera estado formal e motivo legivel por maquina | Yes |
| Status simples + logs detalhados | Estados curtos e o resto fica nos logs | |
| Status so no final | Apenas o resultado final vira status formal | |

**User's choice:** Status por etapa + motivo estruturado
**Notes:** Isso deve permitir distinguir claramente accepted, blocked, degraded e causas equivalentes.

---

## Internal versus external visibility

| Option | Description | Selected |
|--------|-------------|----------|
| Status interno detalhado + status externo resumido | Backend guarda o detalhe, frontend recebe um resumo seguro | Yes |
| Mesmo status em tudo | O vocabulário detalhado interno tambem aparece externamente | |
| Quase tudo interno | O frontend ve apenas algo muito generico | |

**User's choice:** Status interno detalhado + status externo resumido
**Notes:** A rastreabilidade tecnica deve existir sem vazar complexidade ou detalhes internos para a UX.

---

## the agent's Discretion

- Nome exato dos estados
- Modelagem precisa do schema de status interno e externo
- Local exato de persistencia e propagacao desses estados no pipeline

## Deferred Ideas

None.
