# Security Baseline (ProjectB Frontend)

## Princípios aplicados

- Frontend é ambiente não confiável por definição.
- Toda validação crítica e autorização devem existir no backend.
- Sem segredos no bundle cliente (`VITE_*` é público).

## Controles implementados

1. Cliente HTTP com timeout e abort (`AbortController`)
2. `credentials: omit` e `cache: no-store` em todas as chamadas
3. Geração de `X-Request-ID` para rastreio ponta-a-ponta
4. Validação client-side de `riot_id` e `match_id` (camada adicional)
5. Queda segura (fallback) sem expor stack traces
6. Headers de segurança no deploy estático (`vercel.json`)
7. Obrigatoriedade de HTTPS para URL de API em produção
8. Variáveis públicas isoladas em `.env.example` sem segredos

## Conformidade legal (LGPD/GDPR)

- Não persistir dados sensíveis no navegador (sem localStorage de tokens).
- Exibir política de privacidade e finalidade de tratamento de dados.
- Solicitar no backend exclusão/retificação quando necessário.
