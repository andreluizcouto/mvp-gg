# Phase 1: Trust Boundaries and Security Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-04-01
**Phase:** 01-Trust Boundaries and Security Foundation
**Areas discussed:** Internal authentication model, Public route boundary, Validation and failure policy, Security test bar

---

## Internal authentication model

| Option | Description | Selected |
|--------|-------------|----------|
| Separacao rigida agora | Bearer interno apenas para rotas internas/admin/IA e `LOCAL_APP_TOKEN` apenas para `/local/*`, sem fallback | Yes |
| Migracao curta | Manter fallback temporario so nesta fase, com remocao planejada logo depois | |
| Manter como esta por enquanto | Endurecer outras areas primeiro sem mexer no modelo de tokens | |

**User's choice:** Separacao rigida agora
**Notes:** O usuario quer endurecimento real ja nesta fase, sem ambiguidade entre os papeis de autenticacao.

---

## Public route boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Publico minimo | Apenas leituras publicas indispensaveis, sempre com rate limit e resposta sanitizada | Yes |
| Publico amplo controlado | Algumas operacoes extras continuam publicas com controles compensatorios | |
| Mais fechado desde ja | Quase tudo protegido, deixando publico so o estritamente essencial | |

**User's choice:** Publico minimo
**Notes:** A superficie publica deve continuar pequena para o produto atual funcionar sem abrir risco desnecessario.

---

## Validation and failure policy

| Option | Description | Selected |
|--------|-------------|----------|
| Fail-closed por padrao | Bloquear cedo inputs invalidos, incompletos ou suspeitos; degradar apenas quando explicitamente seguro | Yes |
| Degradacao preferencial | Tentar seguir sempre que possivel com avisos | |
| Hibrido solto | Cada rota ou pipeline decide sem regra central forte | |

**User's choice:** Fail-closed por padrao
**Notes:** O usuario explicitou preferencia por verificacoes entre etapas e por nao confiar em fronteiras frouxas.

---

## Security test bar

| Option | Description | Selected |
|--------|-------------|----------|
| Barra alta no backend agora | Cobrir autenticacao, separacao de tokens, validacao, rate limit e nao-vazamento | Yes |
| Barra media | Cobrir auth e validacao primeiro, deixando o resto parcial | |
| Barra minima | Focar em implementacao agora e testes mais completos depois | |

**User's choice:** Barra alta no backend agora
**Notes:** A fase deve sair com garantias automatizadas, nao apenas com endurecimento manual do codigo.

---

## the agent's Discretion

- Estrutura final de middleware, helpers ou dependencies no FastAPI
- Organizacao exata dos testes e fixtures

## Deferred Ideas

None.
