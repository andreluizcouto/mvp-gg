# Security Baseline (ProjectB Backend)

## Cadeia de segurança aplicada

1. HTTPS obrigatório (com suporte a `X-Forwarded-Proto` em proxy reverso)
2. Modo `PUBLIC_READ_ONLY` para operação pública somente leitura (default em produção)
3. Autenticacao forte para rotas internas (`APP_TOKEN` ou `Authorization: Bearer`)
4. Token dedicado para o app local (`LOCAL_APP_TOKEN`) com escopo separado das rotas internas
5. Endpoints de IA (`/analyze*` e `/feedback`) protegidos por autenticacao interna
6. Rate limit distribuido via Redis/ElastiCache (com fallback local) por IP nos endpoints publicos de leitura
7. Rate limit adicional por cliente/API key no edge para reduzir abuso automatizado
8. Rate limit diario adicional para uploads do app local por `riot_id` e por cliente/IP
9. Autorizacao por escopo de usuario (`riot_id`) nas rotas de coaching
10. Validacao rigida de entrada com Pydantic v2 + limites de tamanho
11. Validacao de `match_id`, decodificacao base64 estrita e nomes de arquivo temporario sem entrada do usuario
12. Headers de seguranca (CSP restrita para API, HSTS, no-sniff, frame deny, no-referrer)
13. Sessao segura: API stateless, sem cookie de sessao, `Cache-Control: no-store`
14. Banco protegido por filtro de `riot_id` e validacao de `match_id`
15. Segredos fora do codigo (`.env`, `.env.example`, sem hardcode em cliente distribuido)
16. Dependencias com gate de teste ativo antes de deploy
17. Logs estruturados por requisicao (`X-Request-ID`, status, latencia)
18. Conformidade legal (LGPD/GDPR): minimizacao de dados, rastreabilidade, retencao controlada

## Operação segura recomendada

- Em produção, manter `ENVIRONMENT=production` e `REQUIRE_HTTPS=true`.
- Em produção, manter `PUBLIC_READ_ONLY=true`.
- Definir ao menos um segredo interno: `APP_TOKEN` ou `INTERNAL_BEARER_TOKEN`.
- Configurar `LOCAL_APP_TOKEN` separado do token interno e distribuir esse valor fora do repositorio/binario.
- Manter `REQUIRE_RIOT_ID_FOR_COACHING=true` para impedir enumeração simples por `match_id`.
- Ajustar `PUBLIC_READ_RATE_LIMIT_WINDOW_SECONDS` e `PUBLIC_READ_RATE_LIMIT_MAX_REQUESTS` conforme tráfego esperado.
- Configurar `REDIS_URL` (ElastiCache) e manter fallback local apenas como contingência.
- Ajustar `EDGE_CLIENT_RATE_LIMIT_WINDOW_SECONDS`, `EDGE_CLIENT_RATE_LIMIT_MAX_REQUESTS` e `EDGE_CLIENT_ID_HEADERS`.
- Rotacionar `APP_TOKEN` e `LOCAL_APP_TOKEN` periodicamente e auditar acessos por `request_id`.
- Manter política de retenção para dados de coaching com prazo documentado.
