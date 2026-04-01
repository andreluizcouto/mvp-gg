---
description: "Investiga e corrige um bug no projeto mvp.gg. Analisa o código, encontra a causa raiz, e implementa a correção."
agent: "frontend-dev"
argument-hint: "Descreva o bug (ex: 'a página de perfil fica em loading infinito')"
---
Investigue e corrija o bug reportado no projeto mvp.gg.

## Processo
1. Leia o código dos arquivos relacionados ao bug
2. Identifique a causa raiz (não apenas o sintoma)
3. Verifique se o bug pode afetar outras áreas
4. Implemente a correção mínima necessária (não refatorar além do necessário)
5. Verifique se a correção não quebra nada
6. Explique o que causou o bug e o que foi feito — em português simples

## Contexto da API
- Backend: FastAPI via `src/services/api.js`
- Endpoints: fetchMatches, refreshMatches, fetchCoachingAnalysis, fetchCoachingStatus, fetchScoreboard
- Teste com summoner: `natus vincere#navi1` (BR)
