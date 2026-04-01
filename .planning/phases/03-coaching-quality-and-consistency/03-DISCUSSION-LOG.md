# Phase 3: Coaching Quality and Consistency - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `03-CONTEXT.md`; this log preserves alternatives considered and selected choices.

**Date:** 2026-04-01
**Phase:** 03-coaching-quality-and-consistency
**Areas discussed:** Politica de especificidade, Vinculo com evidencias, Consistencia entre partidas similares, Revisao/regeneracao, Dependencia do app local

---

## Politica de especificidade

### Q1 - Estrutura base da analise
| Option | Description | Selected |
|--------|-------------|----------|
| Fixo em 3 blocos | Forcas + Erros + Proximos passos, ordem fixa | yes |
| Totalmente flexivel | Modelo escolhe estrutura por partida | |
| Hibrido | Blocos obrigatorios + secao extra variavel | |

### Q2 - Densidade de conteudo
| Option | Description | Selected |
|--------|-------------|----------|
| Enxuta | 3 a 5 insights + feedback curto e direto | yes |
| Media | 5 a 7 insights + feedback detalhado | |
| Profunda | 7 a 10 insights + feedback extenso | |

### Q3 - Pouco sinal forte
| Option | Description | Selected |
|--------|-------------|----------|
| Fail-safe conservador | Reduz claims e marca insuficiencia | yes |
| Coaching completo sempre | Preenche com orientacao geral | |
| Hibrido | Entrega com marcacao explicita de confianca | |

### Q4 - Criterio minimo de insight valido
| Option | Description | Selected |
|--------|-------------|----------|
| Completo e verificavel | Problema + evidencia + impacto + acao | yes |
| Objetivo e curto | Problema + acao; evidencia opcional | |
| Flexivel por contexto | Modelo decide caso a caso | |

### Q5 - Tom do feedback_geral
| Option | Description | Selected |
|--------|-------------|----------|
| Direto de coach | Frases objetivas, foco em execucao | yes |
| Didatico-explicativo | Mais contexto e explicacoes longas | |
| Misto | Direto nos criticos, didatico no restante | |

### Q6 - Regra de elogios
| Option | Description | Selected |
|--------|-------------|----------|
| Elogio so com prova forte | Sem elogio motivacional sem evidencia | yes |
| Elogio moderado sempre | Mantem 1 ponto positivo mesmo com pouco dado | |
| Opcional | Pode nao ter secao de forcas | |

### Q7 - Repeticao de conselho
| Option | Description | Selected |
|--------|-------------|----------|
| Permitir repeticao com variacao minima | Erro recorrente pode repetir conselho | yes |
| Evitar repeticao agressivamente | Reframing sempre obrigatorio | |
| Equilibrio | Maximo 1 conselho identico | |

### Q8 - Formato de proximos passos
| Option | Description | Selected |
|--------|-------------|----------|
| 1 a 3 acoes com meta numerica | Metas mensuraveis por partida/fase | yes |
| Acoes sem numero | Recomendacao qualitativa | |
| Checklist curto | Lista de prioridades | |

**User's choices summary:** Todas as 8 decisoes foram para a opcao 1 (rigor/objetividade maxima).

---

## Vinculo com evidencias

### Q1 - Nivel de ancoragem factual
| Option | Description | Selected |
|--------|-------------|----------|
| Rigor maximo | Todo insight e paragrafo com evidencia explicita | yes |
| Rigor medio | Insights com evidencia; feedback mais livre | |
| Rigor adaptativo | Exige explicito so nos pontos criticos | |

### Q2 - Clareza vs precisao
| Option | Description | Selected |
|--------|-------------|----------|
| Precisao factual sempre | Texto pode ficar mais seco | yes |
| Equilibrio | Permite simplificacoes leves | |
| Legibilidade primeiro | Abstracao maior | |

### Q3 - Regras do coach_guardrails.py
| Option | Description | Selected |
|--------|-------------|----------|
| Endurecer | Mais violacoes viram bloqueio/rewrite | yes |
| Manter | Regras atuais | |
| Flexibilizar | Menos bloqueio | |

### Q4 - Evidencia incompleta
| Option | Description | Selected |
|--------|-------------|----------|
| Nao afirmar e marcar insuficiencia | Claim bloqueado sem prova | yes |
| Afirmar com baixa confianca | Hipotese explicita no texto | |
| Conselho generico | Omitir claim e manter orientacao ampla | |

**User's choices summary:** Todas as 4 decisoes foram para a opcao 1 (evidence-first estrito).

---

## Consistencia entre partidas similares

### Q1 - Nivel de determinismo
| Option | Description | Selected |
|--------|-------------|----------|
| Alto determinismo | Estrutura/ordem/estilo muito estaveis | yes |
| Moderado | Estrutura fixa com variacao parcial | |
| Baixo | Coerencia geral com maior liberdade | |

### Q2 - Estrategia para reduzir variancia
| Option | Description | Selected |
|--------|-------------|----------|
| Schema rigido + validacao forte | Rejeita saida fora do contrato | yes |
| Schema rigido + rewrite automatico | Corrige antes de rejeitar | |
| Schema leve | Valida so o essencial | |

### Q3 - Output parcialmente fora do padrao
| Option | Description | Selected |
|--------|-------------|----------|
| Fail e nao entregar | Sem fallback textual fraco | yes |
| 1 rewrite e depois bloquear | Tentativa unica de reparo | |
| Entregar degradado | Versao simplificada mesmo fora do ideal | |

### Q4 - Prioridade quando ha concorrencia de pontos
| Option | Description | Selected |
|--------|-------------|----------|
| Impacto no resultado | Gold/xp/objetivo/mapa manda | yes |
| Frequencia | O que mais se repetiu | |
| Balanceado por categoria | Forca distribuicao por categoria | |

### Q5 - Definicao de "partidas similares"
| Option | Description | Selected |
|--------|-------------|----------|
| Criterio estrito | Mesmo campeao, role e faixa de duracao/eventos | yes |
| Criterio medio | Mesmo campeao e role, mais tolerancia | |
| Criterio amplo | Role igual com sinais gerais | |

### Q6 - Variacao de linguagem
| Option | Description | Selected |
|--------|-------------|----------|
| Muito baixa | Espinha textual quase igual | yes |
| Baixa-moderada | Estrutura igual, reformulacoes parciais | |
| Moderada | Sentido igual com texto variado | |

### Q7 - Taxonomia de categorias
| Option | Description | Selected |
|--------|-------------|----------|
| Fechada | So categorias pre-definidas | yes |
| Semi-fechada | Categorias principais + poucas extensoes | |
| Aberta | Modelo pode criar categorias novas | |

### Q8 - Categoria vs impacto
| Option | Description | Selected |
|--------|-------------|----------|
| Ranking por impacto | Categoria nao define prioridade | yes |
| Reserva por categoria | Garantir minimos por categoria | |
| Hibrido | Impacto com limite de concentracao | |

**User's choices summary:** Todas as 8 decisoes foram para a opcao 1 (determinismo e contrato estritos).

---

## Revisao e regeneracao

### Q1 - Comportamento na revisita
| Option | Description | Selected |
|--------|-------------|----------|
| Sempre usar cache validado | Sem regeneracao automatica | yes |
| Regenerar periodicamente | Janela temporal automatica | |
| Hibrido | Cache + gatilhos tecnicos | |

### Q2 - Gatilho de regeneracao
| Option | Description | Selected |
|--------|-------------|----------|
| So acao explicita do usuario | Botao/regra direta | |
| Usuario + gatilhos tecnicos | Invalida por fixes criticos | |
| Automatico amplo | Versao/modelo/tempo | |
| Free-text decision | "Nao sera possivel regenerar, a menos que pague" | yes |

### Q2b - Confirmacao de regra temporaria
| Option | Description | Selected |
|--------|-------------|----------|
| v1 sem regeneracao + futuro pago | Nenhum usuario v1 regenera; futuro restrito a pagante | yes |
| Ajustar regra | Usuario pode propor variacao | |

### Q3 - Tentativa de nao pagante
| Option | Description | Selected |
|--------|-------------|----------|
| Bloquear com status claro | Mensagem objetiva de recurso pago | yes |
| Bloquear silenciosamente | Mantem estado sem mensagem especifica | |
| Fila futura | Aceita pedido sem executar | |

### Q4 - Atualizacao de prompt/guardrails/modelo
| Option | Description | Selected |
|--------|-------------|----------|
| Manter historico | Sem retro-regeneracao automatica | yes |
| Marcar desatualizada | Mostra que existe versao mais nova | |
| Invalidar em massa | Forca novo ciclo quando permitido | |

---

## Dependencia do app local

### Q1 - Claims de visao/posicionamento
| Option | Description | Selected |
|--------|-------------|----------|
| Exigir evidencia local | So entra com evento/minimapa local | yes |
| Permitir Riot-only com baixa confianca | Claim entra com disclaimer | |
| Nao exigir local | Sem bloqueio por fonte | |

### Q2 - Sem evidencia local
| Option | Description | Selected |
|--------|-------------|----------|
| Analise parcial + insufficient_data | Entrega parcial sem claims dependentes | |
| Bloquear analise inteira | Sem coaching ate existir evidencia local | |
| Completa com aviso | Mantem claims com disclaimer | |
| Free-text decision | "Quem nao tiver o app instalado nem vai ter analises..." | yes |

**Captured UX statement:** "Coach indisponivel, baixe o app e jogue uma partida."

---

## the agent's Discretion

Nenhuma area foi marcada como "voce decide"; usuario travou escolhas em nivel alto de especificidade.

## Deferred Ideas

- Implementacao de entitlement pago para regeneracao (billing/login/plan checks) fica para fase futura de monetizacao.
