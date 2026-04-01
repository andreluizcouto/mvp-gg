# Phase 4: Match Experience and Trustworthy UX - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-04-01T10:43:12.748Z
**Phase:** 04-match-experience-and-trustworthy-ux
**Areas discussed:** Fluxo de navegacao e retorno, Estados de coaching no frontend, Hierarquia visual da tela de partida

---

## Fluxo de navegacao e retorno

### Q1: Botao "Voltar" quando entrou por link direto

| Option | Description | Selected |
|--------|-------------|----------|
| A | Volta para `/` (home) | YES |
| B | Tenta reconstruir e voltar para `/summoner/:name/:tag` | |
| C | Sempre `navigate(-1)` | |

**User's choice:** `1A`  
**Notes:** em acesso direto por link compartilhado, retorno previsivel para home.

### Q2: Busca da Home e busca da Navbar

| Option | Description | Selected |
|--------|-------------|----------|
| A | Mesmo comportamento e mesmas mensagens nas duas | |
| B | Home com validacao forte, Navbar validacao minima | YES |
| C | Navbar so redireciona e erro aparece no destino | |

**User's choice:** `2B`  
**Notes:** manter agilidade na busca global e rigor principal na home.

### Q3: Falha ao carregar dados em `/match/:id`

| Option | Description | Selected |
|--------|-------------|----------|
| A | Erro inline na tela + "Tentar novamente" e "Ir para home" | YES |
| B | Redirecionar automaticamente para home | |
| C | Pagina separada 404/indisponivel | |

**User's choice:** `3A`  
**Notes:** evitar quebra de contexto; manter usuario na tela com acoes claras.

---

## Estados de coaching no frontend

### Q1: Badge IA na lista de partidas

| Option | Description | Selected |
|--------|-------------|----------|
| A | Mostrar `IA` so quando status for `ready` | YES |
| B | Mostrar badge em todos os status | |
| C | Nao mostrar badge na lista | |

**User's choice:** `2.1A`

### Q2: Card de coaching para `pending` e `failed`

| Option | Description | Selected |
|--------|-------------|----------|
| A | Cards distintos por estado | |
| B | Mesmo card generico bloqueado para os dois | YES |
| C | Esconder coaching quando nao-ready | |

**User's choice:** `2.2B`

### Q3: Copy para indisponibilidade sem evidencia local

| Option | Description | Selected |
|--------|-------------|----------|
| A | Manter copy fixa: `Coach indisponivel, baixe o app e jogue uma partida.` | YES |
| B | Versao curta generica | |
| C | Versao longa explicativa | |

**User's choice:** `2.3A`

### Q4: Link compartilhado sem permissao/contexto da analise

| Option | Description | Selected |
|--------|-------------|----------|
| A | Mostrar estado explicito "Analise privada para este jogador" | YES |
| B | Reusar card bloqueado padrao com CTA de app | |
| C | Esconder totalmente o bloco de coaching | |

**User's choice:** `2.4A`  
**Notes:** dashboard da partida visivel para compartilhamento; analise personalizada privada.

---

## Hierarquia visual da tela de partida

### Q1: Conteudo acima da dobra

| Option | Description | Selected |
|--------|-------------|----------|
| A | Header + resumo + coaching; scoreboard abaixo | YES |
| B | Header + scoreboard primeiro | |
| C | Header + metricas primeiro | |

**User's choice:** `3.1A`

### Q2: Densidade do scoreboard

| Option | Description | Selected |
|--------|-------------|----------|
| A | Denso no desktop e simplificado mobile | |
| B | Mesmo layout denso para todos | YES |
| C | Layout compacto para todos | |

**User's choice:** `3.2B`

### Q3: Abas "Detalhes/Runas"

| Option | Description | Selected |
|--------|-------------|----------|
| A | Manter visiveis, mas desabilitadas com "Em breve" | YES |
| B | Manter clicaveis como hoje | |
| C | Remover por enquanto | |

**User's choice:** `3.3A`

### Q4: Sinal visual de confianca

| Option | Description | Selected |
|--------|-------------|----------|
| A | Bloco curto "Status da analise" com estado e motivo amigavel | YES |
| B | So texto dentro do card de coaching | |
| C | Sem bloco extra | |

**User's choice:** `3.4A`

---

## the agent's Discretion

- Copy final de estado bloqueado para `pending/failed`.
- Posicionamento exato do bloco "Status da analise".
- Ajustes finos de layout para reduzir ruido sem reduzir densidade de dados.

## Deferred Ideas

None - no out-of-scope capability was added during discussion.
