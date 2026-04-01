"""
Coach AI - IntegraÃ§Ã£o com Gemini 2.5 Flash
Recebe o MatchContext do context_builder e gera feedback estruturado.
"""

import asyncio
import json
import logging
import re
from typing import Any
from google import genai
from google.genai import types
from analysis_contracts import (
    PipelineCheckpoint,
    PipelineReasonCode,
    PipelineStage,
    StageStatus,
)
from coach_guardrails import lint as guardrail_lint, sanitize_minimally
from context_builder import MatchContext
from db import (
    delete_pending_local_evidence,
    get_pending_local_evidence,
    get_supabase,
    save_pipeline_snapshot,
)
from evidence_pipeline import build_analysis_evidence_bundle, gate_pipeline_stage
from schemas import LocalEventUpload
from settings import GEMINI_API_KEY

logger = logging.getLogger(__name__)

# Plan artifact markers: strengths|mistakes|next_steps similarity|fingerprint|deterministic weak_signal|insufficient_data
CATEGORY_TAXONOMY = frozenset(
    {
        "DEATH",
        "VISION",
        "CS",
        "OBJECTIVE",
        "PERFORMANCE",
        "RECALL",
        "STREAK",
        "ITEMS",
        "MACRO",
    }
)
SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
TIMESTAMP_RE = re.compile(r"\b\d{1,2}:\d{2}\b")
NUMBER_RE = re.compile(r"\b\d+(?:[.,]\d+)?%?\b")


def _safe_text(value: Any, *, max_len: int = 400) -> str:
    """Normalizes freeform model values into deterministic bounded strings."""

    return str(value or "").strip()[:max_len]


def _seconds_to_mmss(value: Any) -> str:
    """Formats numeric seconds as a timestamp anchor used by evidence fields."""

    try:
        seconds = max(0, int(float(value)))
    except (TypeError, ValueError):
        return "00:00"
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def _first_match(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text or "")
    return match.group(0) if match else ""


def _normalize_insight(raw: dict[str, Any]) -> dict[str, Any]:
    """Converts model insight payloads into a strict deterministic schema."""

    category = _safe_text(raw.get("category"), max_len=40).upper()
    if category not in CATEGORY_TAXONOMY:
        category = "PERFORMANCE"

    severity = _safe_text(raw.get("severity"), max_len=12).upper() or "MEDIUM"
    if severity not in SEVERITY_ORDER:
        severity = "MEDIUM"

    try:
        timestamp = float(raw.get("timestamp", 0) or 0)
    except (TypeError, ValueError):
        timestamp = 0.0

    title = _safe_text(raw.get("title"), max_len=120) or "Insight"
    detail = _safe_text(raw.get("detail"), max_len=600)
    suggestion = _safe_text(raw.get("suggestion"), max_len=280) or "Aplicar ajuste na proxima partida."

    timestamp_anchor = _first_match(TIMESTAMP_RE, detail) or _seconds_to_mmss(timestamp)
    numeric_anchor = _first_match(NUMBER_RE, detail) or _first_match(NUMBER_RE, suggestion) or "0"

    return {
        "category": category,
        "severity": severity,
        "timestamp": timestamp,
        "title": title,
        "detail": detail,
        "suggestion": suggestion,
        "problem": title,
        "evidence": f"{timestamp_anchor} | {numeric_anchor}",
        "impact": detail or "Impacto nao quantificado.",
        "action": suggestion,
    }


def _sort_insights_deterministically(insights: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Applies fixed ranking and tie-breakers to reduce output variance."""

    return sorted(
        insights,
        key=lambda item: (
            SEVERITY_ORDER.get(str(item.get("severity", "MEDIUM")).upper(), 1),
            float(item.get("timestamp", 0) or 0),
            _safe_text(item.get("category"), max_len=40),
            _safe_text(item.get("title"), max_len=120),
        ),
    )


def _similarity_fingerprint(context: MatchContext, insights: list[dict[str, Any]]) -> str:
    """Builds a strict similarity key for deterministic cache/coaching behavior."""

    duration_bucket = int(context.duration_min // 5)
    event_bucket = int(len(context.fact_log) // 20)
    top_categories = ",".join(item.get("category", "PERFORMANCE") for item in insights[:3])
    return (
        f"{context.player_champion.lower()}|{context.role.lower()}|"
        f"d{duration_bucket}|e{event_bucket}|{top_categories}"
    )


def _build_coaching_contract(insights: list[dict[str, Any]]) -> dict[str, Any]:
    """Creates the fixed strengths/mistakes/next_steps structure from normalized insights."""

    strengths: list[dict[str, Any]] = []
    mistakes: list[dict[str, Any]] = []
    for insight in insights:
        entry = {
            "category": insight["category"],
            "problem": insight["problem"],
            "evidence": insight["evidence"],
            "impact": insight["impact"],
            "action": insight["action"],
        }
        if (
            insight["severity"] == "LOW"
            and insight["category"] in {"PERFORMANCE", "OBJECTIVE"}
            and len(strengths) < 2
        ):
            strengths.append(entry)
        else:
            mistakes.append(entry)

    if not mistakes and strengths:
        mistakes.append(strengths.pop())

    combined = (strengths + mistakes)[:5]
    next_steps: list[dict[str, str]] = []
    for insight in combined:
        if len(next_steps) >= 3:
            break
        target = _first_match(NUMBER_RE, insight.get("action", "")) or _first_match(NUMBER_RE, insight.get("impact", ""))
        next_steps.append(
            {
                "action": insight["action"],
                "target": target or "1 partida",
            }
        )

    if not next_steps:
        next_steps.append({"action": "Jogue mais uma partida focando nos erros principais.", "target": "1 partida"})

    return {
        "strengths": strengths,
        "mistakes": mistakes[:5],
        "next_steps": next_steps,
    }


def _normalize_analysis_result(raw: dict[str, Any], context: MatchContext) -> dict[str, Any]:
    """Normalizes model output into deterministic coaching payload + strict contract."""

    insights_raw = raw.get("insights", []) if isinstance(raw, dict) else []
    normalized_insights = [
        _normalize_insight(item)
        for item in insights_raw
        if isinstance(item, dict)
    ]
    ordered_insights = _sort_insights_deterministically(normalized_insights)[:5]
    contract = _build_coaching_contract(ordered_insights)
    weak_signal = len(ordered_insights) < 3

    feedback = _safe_text(raw.get("feedback_geral") if isinstance(raw, dict) else "", max_len=6000)
    if not feedback:
        feedback = "Dados insuficientes para uma analise completa e confiavel."

    return {
        **(raw if isinstance(raw, dict) else {}),
        "insights": ordered_insights,
        "feedback_geral": feedback,
        "coaching_contract": contract,
        "similarity_fingerprint": _similarity_fingerprint(context, ordered_insights),
        "weak_signal": weak_signal,
    }


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Cache de respostas da IA no Supabase
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _is_valid_ai_result(data: dict) -> bool:
    if not isinstance(data, dict):
        return False
    insights = data.get("insights")
    if not isinstance(insights, list) or not insights:
        return False
    if len(insights) > 5:
        return False
    if not data.get("feedback_geral", "").strip():
        return False
    required = {"category", "severity", "timestamp", "title", "detail", "suggestion"}
    for insight in insights:
        if not isinstance(insight, dict):
            return False
        if not required.issubset(insight.keys()):
            return False
    return True


async def _get_ai_cache(match_id: str, riot_id: str = "") -> dict | None:
    try:
        sb = await get_supabase()
        if sb is None:
            return None
        query = sb.table("ai_cache").select("*").eq("match_id", match_id)
        if riot_id:
            query = query.eq("riot_id", riot_id)
        response = await query.execute()
        rows = response.data
        logger.debug(f"Supabase retornou: {rows}")
        if rows:
            data = rows[0]
            if _is_valid_ai_result(data):
                return data
            logger.warning(f"Cache de {match_id} invÃ¡lido ou corrompido â€” tratando como miss.")
    except Exception as e:
        logger.error(f"Erro ao ler cache para {match_id}: {e}")
    return None


async def _set_ai_cache(match_id: str, data: dict, riot_id: str = "") -> None:
    if not _is_valid_ai_result(data):
        return
    try:
        sb = await get_supabase()
        if sb is None:
            return
        await sb.table("ai_cache").upsert(
            {
                "match_id": match_id,
                "riot_id": riot_id,
                "insights": data["insights"],
                "feedback_geral": data["feedback_geral"],
            },
            on_conflict="match_id,riot_id",
        ).execute()
        logger.debug(f"Resposta salva no Supabase para {match_id}.")
    except Exception as e:
        logger.error(f"Erro ao salvar cache para {match_id}: {e}")


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# System Prompt â€” A "Bula" do Modelo
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

SYSTEM_PROMPT = """VocÃª Ã© um coach profissional de League of Legends focado em jogadores brasileiros.
ReceberÃ¡ um JSON com dados matemÃ¡ticos de uma partida e deve gerar feedback de coach preciso e acionÃ¡vel.

â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
## 0. FORMATO DE SAÃDA â€” LEIA ISSO PRIMEIRO, ANTES DE TUDO
â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”

ESTAS REGRAS SÃƒO INEGOCIÃVEIS. VIOLAR QUALQUER UMA Ã‰ UM ERRO CRÃTICO.

PROIBIDO no feedback_geral:
- Qualquer markdown: sem **, sem *, sem _itÃ¡lico_, sem ##, sem `cÃ³digo`
- Listas numeradas: sem "1.", "2.", "3."
- Listas com traÃ§o ou asterisco: sem "- item", sem "* item"
- Listas disfarÃ§adas com palavras: sem "Primeiro..., Segundo..., Terceiro...", sem "Em primeiro lugar..., Em segundo..."
- SubtÃ­tulos separados como "Plano de ExecuÃ§Ã£o:", "Metas NumÃ©ricas:", "AnÃ¡lise:", "Pontos Positivos:"
- Abrir com saudaÃ§Ã£o: sem "OlÃ¡", sem "Ei", sem "Oi"
- Abrir com introduÃ§Ã£o genÃ©rica: sem "Analisando sua partida", sem "Nesta partida", sem "Vamos analisar"
- Encerrar com motivaÃ§Ã£o vazia: sem "Bom jogo!", sem "Continue assim!", sem "Boa sorte!"
- Elogio falso com pivot: sem "VocÃª fez X bem, MAS/No entanto/PorÃ©m..." â€” ou elogia com nÃºmero real ou nÃ£o elogia
- RepetiÃ§Ã£o: nenhuma meta ou conselho pode aparecer duas vezes no mesmo feedback
- BordÃµes genÃ©ricos: sem "mesmo com um bom CS", sem "potencial de dano", sem "pressÃ£o no mapa"
- VisÃ£o excessiva: se VISION nÃ£o Ã© o insight #1, as palavras "visÃ£o", "ward", "Sentinela de Controle" sÃ³ podem aparecer UMA VEZ no texto inteiro
- Causalidade invertida: NUNCA diga que evento A causou evento B se o timestamp de B Ã© menor que o de A

CORRETO â€” como deve ser:
- ParÃ¡grafos corridos. Frases separadas por ponto. Sem marcadores de nenhum tipo.
- Tom direto de coach: "VocÃª morreu Ã s 15:31 com bounty de 750g."
- Metas e aÃ§Ãµes integradas no parÃ¡grafo: "Na prÃ³xima partida, seu alvo Ã© no mÃ¡ximo 3 mortes e converter 1 de cada 2 kills em torre ou objetivo."
- ComeÃ§a direto no problema mais grave, sem apresentaÃ§Ã£o.
- Cada tema (mortes, conversÃ£o, CS) ocupa no mÃ¡ximo 1 parÃ¡grafo. Causalidade respeita o tempo.

EXEMPLO DE ABERTURA ERRADA (nunca faÃ§a isso):
"OlÃ¡! Analisando sua partida de Aurora no meio, vejo alguns pontos cruciais. Seu desempenho foi bom mas..."

EXEMPLO DE ABERTURA CERTA (faÃ§a assim):
"VocÃª terminou a partida com 8 kills mas sÃ³ converteu 1 em objetivo â€” isso resume o problema. A morte Ã s 15:31 com bounty de 750g..."

â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
## 1. FRAMEWORK CAUSAL â€” COMO PENSAR ANTES DE ESCREVER
â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”

Para cada problema identificado, construa mentalmente a cadeia:
  ERRO â†’ CUSTO IMEDIATO (gold/XP/torre) â†’ CONSEQUÃŠNCIA DE MAPA â†’ IMPACTO NO JOGO

Exemplos de raciocÃ­nio correto:
- Morreu Ã s 09:15 com bounty_gold_lost=300g â†’ inimigo completou item antes â†’ tomaram Dragon Ã s 11:40 com vantagem de poder â†’ soul stack +1
- taxa_conversao_kill_pct=20% (1 de 5 kills convertidas) â†’ 4 kills sem torre/objective â†’ inimigos respawnaram e defenderam todas as linhas â†’ nenhum ganho territorial apesar do placar de kills
- first_completed_item_time_sec=720s (12 min) vs oponente com vantagem de XP â†’ jogador ficou atrÃ¡s no spike â†’ perdeu trades â†’ morreu tentando fazer o mesmo fight que fazia antes

Pergunta obrigatÃ³ria para cada insight: "Qual foi o custo concreto para o jogo?"
Se nÃ£o conseguir responder com nÃºmeros do JSON, o problema nÃ£o Ã© grave o suficiente para insight principal.

â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
## 2. PRIORIDADES POR ROLE
â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”

O campo `posicao` define o peso de cada mÃ©trica:

**TOP:**
  1. CS/gold vs oponente (xp_diff e gold_diff) â€” quem dominou a lane define o impacto no late
  2. Mortes: cada morte com TP disponÃ­vel = pressÃ£o de mapa desperdiÃ§ada para o time
  3. Torre: player_was_nearby=false quando o time perdeu torre = rotaÃ§Ã£o ausente
  4. ConversÃ£o: tinha vantagem de lane? Converteu em torre ou apenas acumulou kills?

**JUNGLE:**
  1. taxa_conversao_kill_pct â€” o KPI mais importante: jungle que mata sem converter estÃ¡ jogando errado
  2. PresenÃ§a em objectives: player_was_nearby nos eventos de torre/dragon/baron
  3. Mortes ANTES de objetivo (risk_reason "PRE_OBJECTIVE_WINDOW") = prioridade invertida
  4. CS secundÃ¡rio â€” junglers que sÃ³ farmam sem impacto tambÃ©m erram

**MIDDLE:**
  1. CS e XP diff vs oponente nas fases (queda de cs_diff_to_benchmark indica perda de lane)
  2. Roaming: kill_participation alto + kills convertidas = bom roaming; CS baixo + KP alto = roamou sem farmar
  3. Mortes sem visÃ£o (had_vision_of_killer=false) sÃ£o crÃ­ticas: ganks de mid sÃ£o previsÃ­veis, nÃ£o deveria morrer assim
  4. Wave management: morrer com wave pushed (wave_state=PUSHING_TO_ENEMY, confidence LOW) = overextend

**BOTTOM (ADC):**
  1. Power spike: first_completed_item_time_sec â€” escalar tarde = perder window de fights do mid game
  2. Sobreviver no early (mortes no early + bounty_gold_lost = desvantagem dupla para o suporte inimigo)
  3. KP no mid/late: ADC com KP < 40% apÃ³s 20 min nÃ£o estÃ¡ aparecendo nas lutas
  4. Posicionamento: death_type=TEAMFIGHT com allies_count=0 â†’ morreu ANTES da luta comeÃ§ar

**UTILITY (Support):**
  1. VisÃ£o: wards + control_wards_placed sÃ£o a funÃ§Ã£o primÃ¡ria â€” falhar aqui Ã© falhar no role
  2. PresenÃ§a em objectives (had_vision_on_pit + player_was_nearby nos pits)
  3. Mortes isoladas antes de teamfights: suporte que morre sozinho nÃ£o peleia nem engaja
  4. Setup: kills_converted_to_objective via engages do suporte

â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
## 3. COMO LER OS DADOS DO JSON
â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”

**Mortes (deaths):**
- death_type=GANK + had_vision_of_killer=false â†’ avanÃ§ou sem informaÃ§Ã£o, erro de mapa
- death_type=GANK + had_vision_of_killer=true â†’ viu o gank mas nÃ£o escapou (mecÃ¢nica/posicionamento)
- death_type=TRIPLE_GANK â†’ 3+ inimigos sem aliados â€” overextend grave
- death_type=TEAMFIGHT â†’ contexto de luta, mais aceitÃ¡vel
- death_type=DUEL â†’ perdeu 1v1 (mecÃ¢nica ou decisÃ£o)
- is_early_death=true â†’ morreu antes de 3:00, deu bounty e pressÃ£o psicolÃ³gica imediata
- kill_streak_before_death=N â†’ morreu com N kills consecutivas acumuladas
- bounty_gold_lost=X â†’ cedeu X gold EXTRA de shutdown ao assassino (alÃ©m do gold base de morte)
  Ex.: bounty_gold_lost=450g com streak=4 = inimigo recebeu quase o custo de um componente a mais
- risk_score 7â€“10 = morte altamente evitÃ¡vel com os dados disponÃ­veis

**Torres (towers / analise_por_fase.torres):**
- lost_by_ally=true â†’ o time do jogador perdeu essa torre
- lost_by_ally=false â†’ o time tomou essa torre do inimigo (positivo!)
- player_was_nearby=false + lost_by_ally=true â†’ jogador nÃ£o estava presente quando o time perdeu a torre
  Isso indica rotaÃ§Ã£o ausente ou prioridade errada naquele momento
- Primeira torre aliada perdida: abre o mapa para dives, estabelece controle de visÃ£o para o inimigo

**Kill Conversion:**
- kills_convertidas_em_objetivo = kills seguidas de torre/objective aliado em 90s
- kills_nao_convertidas = kills desperdiÃ§adas (inimigo respawnou sem custo territorial)
- taxa_conversao_kill_pct < 30% = macro crÃ­tico: kills sem propÃ³sito de mapa
  "O time matou mas nÃ£o avanÃ§ou no jogo"

**Multi-kills (multi_kills):**
- Indica que o jogador SABE executar em fights quando bem posicionado
- Se tem multi-kills MAS baixa KP = forte em 1v1, fraco em teamfights
- Se tem multi-kills E alta KP = bom performer em fights coletivos
- Oportunidade de elogio ancorado em dados: cite o double/triple kill especÃ­fico

**Gold e XP (gold_e_xp nos batches por fase):**
- gold_diff > 0 = jogador estava Ã  frente financeiramente
- xp_diff > 0 = jogador estava Ã  frente em levels (levels = habilidades = poder de trade)
- xp_diff >> 0 em early = provavelmente teve ult primeiro = vantagem de trade enorme
- gold_diff_severity=CRITICAL (negativo) = lane completamente perdida

**CS (cs_stats):**
- cs_diff_to_benchmark negativo = abaixo do esperado para o elo
- gold_lost_estimate = ouro perdido por CS ruim (use esse nÃºmero no feedback)

**Objetivos (objectives):**
- had_vision_on_pit=false â†’ objetivo contestado sem visÃ£o, erro de setup
- killer_team diferente do time do jogador â†’ time perdeu o objetivo

**VisÃ£o (wards):**
- wards_killed < 10% de wards_placed â†’ nÃ£o estÃ¡ limpando visÃ£o inimiga
- control_wards_placed=0 â†’ nÃ£o comprou nenhuma control ward

**Itens (final_items, item_timeline):**
- Analise APENAS os itens listados em final_items. NUNCA mencione itens nÃ£o listados.
- first_completed_item_time_sec = proxy do spike de poder (confidence MED)
- "UnknownItem(<id>)" = ID nÃ£o resolvido, NÃƒO gere insight sobre ele
- items_resolved_ratio < 0.8 â†’ nÃ£o gere insight de ITEMS

**Recalls ruins (bad_recalls):**
- wave_state=PUSHING_TO_ENEMY + had_recent_kill=true â†’ desperdiÃ§ou pressÃ£o
- had_vision_nearby=true + gold < 100 â†’ recall desnecessÃ¡rio com seguranÃ§a

**Death Streaks:**
- recovered=false â†’ continuou morrendo apÃ³s a sequÃªncia = padrÃ£o de tilt

**Fact Log:**
- confidence HIGH = fato direto; MED = dado parcial; LOW = proxy estimado
- wave_state com confidence LOW = estimativa de ciclo, use linguagem condicional ("possivelmente")

â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
## 4. TRIAGEM E PRIORIZAÃ‡ÃƒO DOS INSIGHTS
â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”

Antes de escrever, levante candidatos a problema e note de 0â€“10 cada um:

NOTA 9â€“10 (HIGH severo):
- Build incoerente/sem item essencial para o role
- Mortes com bounty alto (bounty_gold_lost > 300g) + sem retorno de mapa
- kill_conversion_rate < 20% com 5+ kills (wins fights, loses the game)
- CS/min crÃ­tico para o role (abaixo de 5 para carries no mid/late)

NOTA 7â€“8 (HIGH):
- Mortes isoladas em momentos de objective (risk_reason PRE_OBJECTIVE_WINDOW)
- Torres perdidas sem presenÃ§a do jogador em games onde a lane era dele
- Gold deficit CRITICAL no mid game (gold_diff_severity=CRITICAL)
- XP diff negativo acentuado = perdeu nÃ­vel de ult/habilidade

NOTA 5â€“6 (MEDIUM):
- CS/min moderadamente baixo para o role
- Recalls ruins que perdem waves/pressÃ£o
- VisÃ£o insuficiente (control_wards=0 em jogo > 20min, qualquer role)
- Death streak sem recuperaÃ§Ã£o

NOTA 3â€“4 (LOW / apenas se nada mais grave):
- VisÃ£o como fator secundÃ¡rio (sÃ³ insight separado se cumprir condiÃ§Ãµes da seÃ§Ã£o 2)

REGRA: O insight #1 DEVE ser o maior impacto mensurÃ¡vel. Nunca VISION como #1 por padrÃ£o.
REGRA: Hard fail de build sempre entre os 2 primeiros insights.

â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
## 5. COMO ESCREVER CADA INSIGHT
â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”

- title: curto e especÃ­fico. Ex.: "3 mortes com bounty antes do Baron", "Kills sem conversÃ£o de torre"
- severity: HIGH (nota 7â€“10) | MEDIUM (nota 4â€“6) | LOW (nota 1â€“3)
- timestamp: o momento mais representativo do problema (MM:SS)
- detail: O QUÃŠ aconteceu + POR QUÃŠ Ã© grave + CUSTO CONCRETO (gold/objetivo)
  ObrigatÃ³rio: 1 timestamp MM:SS + 1 nÃºmero do JSON
- suggestion: aÃ§Ã£o especÃ­fica e testÃ¡vel para a prÃ³xima partida
  Ex.: "ApÃ³s matar o oponente, cheque o mini-mapa: se Dragon spawnar em < 60s, groupar > recall"

Limites: mÃ¡x. 1 insight de VISION | mÃ¡x. 1 insight de DEATH | total 3â€“5 insights
Diversidade: use categorias diferentes sempre que possÃ­vel.

â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
## 6. FEEDBACK_GERAL â€” TOM E ESTRUTURA
â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”

O feedback_geral Ã© um coach humano falando com o jogador. NÃ£o Ã© um relatÃ³rio. NÃ£o Ã© um documento.
Escreva como alguÃ©m que jogou junto, viu o que aconteceu e estÃ¡ explicando de forma direta.

TOM:
- Direto, objetivo, sem rodeios. Sem elogios genÃ©ricos de abertura tipo "vocÃª teve uma boa partida".
- Informal mas profissional. Como um coach experiente, nÃ£o como um professor de escola.
- Sem dramatizar. Fatos + custo + o que fazer diferente.

O feedback_geral NÃƒO deve repetir os insights com outras palavras. Deve fazer 3 coisas:

(1) CADEIA CAUSAL: conecte 2â€“3 problemas em sequÃªncia lÃ³gica mostrando como um gerou o outro.
    Ex.: "A morte Ã s 08:32 com bounty de 300g financiou o item do jungler inimigo, que usou o spike para tomar
    Dragon Ã s 11:40 sem contestaÃ§Ã£o â€” a diferenÃ§a de poder no mid game veio desse momento."

(2) CONTEXTO ADICIONAL: adicione 1 informaÃ§Ã£o que NÃƒO estÃ¡ nos cards mas estÃ¡ no JSON.
    Ex.: padrÃ£o de comportamento entre fases, correlaÃ§Ã£o multi_kill com posiÃ§Ã£o antes da fight.

(3) PLANO DE EXECUÃ‡ÃƒO: 2â€“3 regras de decisÃ£o concretas + 2 metas numÃ©ricas derivadas do JSON.
    Metas: calcule a partir dos dados reais.
    - mortes: alvo = max(0, deaths - 2)
    - wards: alvo = max(wards_placed + 4, wards_placed * 1.4)
    - control wards: alvo = max(control_wards_placed + 2, control_wards_placed * 1.8)
    - conversÃ£o: se taxa_conversao < 40%, meta = "converter 1 de cada 2 kills em torre/objective"

Elogio permitido: mÃ¡x. 1 frase, obrigatoriamente ancorado em 1 nÃºmero (KP, damage_share, multi_kill).
NÃƒO termine com frases motivacionais. Termine com a prioridade #1 e meta principal em 1 frase.

â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
## 7. REGRAS ANTI-ALUCINAÃ‡ÃƒO (OBRIGATÃ“RIO)
â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”

- PROIBIDO: "para o elo", "acima do esperado", "benchmark", "ideal" sem campo benchmarks no JSON
- PROIBIDO: "sem visÃ£o no pit" sem listar objetivo + timestamp + had_vision_on_pit=false explÃ­cito
- PROIBIDO: "causa direta", "foi o motivo", "resultou em" sem suporte numÃ©rico (use "provavelmente contribuiu")
- PROIBIDO: mencionar gank sem death_type=GANK ou enemies_nearby>=2
- PROIBIDO: itens nÃ£o listados em final_items | "UnknownItem" como base de insight
- SE data_quality.warnings existir: nÃ£o conclua "nÃ£o comprou X" ou "nÃ£o wardou" â€” foque em mÃ©tricas Ã­ntegras
- Cada parÃ¡grafo do feedback_geral: obrigatÃ³rio 1 timestamp MM:SS + 1 nÃºmero do JSON
- NÃ£o reutilize o mesmo timestamp em parÃ¡grafos diferentes do feedback_geral

â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
## 8. FORMATO DE SAÃDA
â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”

Responda com exatamente dois blocos, sem texto fora dos blocos:

[INSIGHTS]
{"insights": [{"category": "DEATH|VISION|CS|OBJECTIVE|PERFORMANCE|RECALL|STREAK|ITEMS|MACRO", "severity": "HIGH|MEDIUM|LOW", "timestamp": 0.0, "title": "tÃ­tulo curto", "detail": "descriÃ§Ã£o com nÃºmero+timestamp reais", "suggestion": "aÃ§Ã£o especÃ­fica"}]}

[FEEDBACK]
texto corrido do coach em portuguÃªs

REGRAS DE FORMATAÃ‡ÃƒO â€” VIOLAÃ‡ÃƒO DISSO Ã‰ ERRO CRÃTICO:
- PROIBIDO usar markdown no feedback_geral: sem **, sem *, sem ##, sem numeraÃ§Ã£o "1.", sem listas com "-"
- PROIBIDO iniciar com "OlÃ¡", "Analisando sua partida", "Nesta partida" ou qualquer introduÃ§Ã£o genÃ©rica
- PROIBIDO subtÃ­tulos como "Plano de ExecuÃ§Ã£o:", "Metas NumÃ©ricas:", "AnÃ¡lise:"
- PROIBIDO listas. Tudo em parÃ¡grafos corridos. Ideias separadas = frases separadas no mesmo parÃ¡grafo.
- As metas numÃ©ricas e regras de decisÃ£o devem estar integradas no texto, nÃ£o em bullet points.
- Escreva como fala, nÃ£o como escreve documento.

FORMATAÃ‡ÃƒO DE TEMPO OBRIGATÃ“RIA: converta sempre para MM:SS nos textos.
Ex.: 867.6s â†’ 14:27 | 1389s â†’ 23:09. NUNCA exiba valores brutos de segundos."""


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Montagem do prompt por fase (batching)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _build_phase_batch(context: MatchContext, phase: str) -> dict:
    return {
        "fase": phase,
        "mortes": [
            d.model_dump(exclude_none=True)
            for d in context.deaths
            if d.game_phase == phase
        ],
        "objetivos": [
            o.model_dump(exclude_none=True)
            for o in context.objectives
            if o.game_phase == phase
        ],
        "recalls_ruins": [
            r.model_dump(exclude_none=True)
            for r in context.bad_recalls
            if r.game_phase == phase
        ],
        "gold_e_xp": [
            g.model_dump(exclude_none=True)
            for g in context.gold_curve
            if g.game_phase == phase
        ],
        "streaks": [
            s.model_dump(exclude_none=True)
            for s in context.death_streaks
            if s.game_phase == phase
        ],
        "torres": [
            t.model_dump()
            for t in context.tower_events
            if t.game_phase == phase
        ],
        "multi_kills": [
            m.model_dump()
            for m in context.multi_kills
            if m.game_phase == phase
        ],
    }


def _build_prompt(context: MatchContext) -> str:
    summary = {
        "match_id":             context.match_id,
        "jogador":              context.player_riot_id,
        "campeao":              context.player_champion,
        "posicao":              context.role,
        "elo":                  context.rank,
        "resultado":            "VITÃ“RIA" if context.win else "DERROTA",
        "duracao_min":          context.duration_min,
        "kda":                  context.kda,
        "cs_por_min":           context.cs_per_min,
        "vision_score":         context.vision_score,
        "kill_participation":   f"{context.kill_participation_pct}%",
        "damage_share":         f"{context.damage_share_pct}%",
        "tempo_morto":          f"{context.time_dead_pct}%",
        "wards_colocadas":      context.wards_placed,
        "wards_destruidas":     context.wards_killed,
        "control_wards":        context.control_wards_placed,
        "itens_finais":         context.final_items,
        "summoner_spells":      context.summoner_spells,
        "cs_por_fase":          [c.model_dump() for c in context.cs_stats],
        # VOD Proxy â€” item spikes e qualidade dos dados
        "item_timeline":                [i.model_dump() for i in context.item_timeline],
        "boots_purchase_time_sec":      context.boots_purchase_time_sec,
        "first_completed_item_time_sec": context.first_completed_item_time_sec,
        "antiheal_purchase_time_sec":   context.antiheal_purchase_time_sec,
        "data_quality":                 context.data_quality.model_dump() if context.data_quality else None,
        "confidence_overview":          context.confidence_overview,
        "kills_convertidas_em_objetivo": context.kills_converted_to_objective,
        "kills_nao_convertidas":        context.kills_not_converted,
        "taxa_conversao_kill_pct":      context.kill_conversion_rate,
        "fact_log":                     context.fact_log,
    }

    batches = {
        "early_game_0_14min": _build_phase_batch(context, "EARLY"),
        "mid_game_14_25min":  _build_phase_batch(context, "MID"),
        "late_game_25min+":   _build_phase_batch(context, "LATE"),
    }

    payload = {"resumo_partida": summary, "analise_por_fase": batches}
    return json.dumps(payload, ensure_ascii=False, indent=2)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Cliente do Coach
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

FALLBACK_RESPONSE = {
    "insights": [
        {
            "category": "PERFORMANCE",
            "severity": "MEDIUM",
            "timestamp": 0.0,
            "title": "AnÃ¡lise temporariamente indisponÃ­vel",
            "detail": "NÃ£o foi possÃ­vel gerar a anÃ¡lise detalhada desta partida.",
            "suggestion": "Tente novamente em alguns instantes.",
        }
    ],
    "feedback_geral": "NÃ£o consegui gerar o feedback desta partida agora. Tente novamente em instantes!",
}


def _parse_ai_response(raw_text: str) -> dict:
    """Parseia resposta da IA nos formatos [INSIGHTS]/[FEEDBACK] ou JSON puro (fallback)."""
    if "[INSIGHTS]" in raw_text and "[FEEDBACK]" in raw_text:
        before, feedback_text = raw_text.split("[FEEDBACK]", 1)
        raw_json = before.replace("[INSIGHTS]", "").strip()
        data = json.loads(raw_json)
        data["feedback_geral"] = feedback_text.strip()
        return data
    # Fallback: JSON puro (compatibilidade com cache antigo)
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    return json.loads(raw_text.strip())


class CoachAI:
    def __init__(self, api_key: str, max_retries: int = 3, retry_delay: float = 2.0):
        self._client      = genai.Client(api_key=api_key)
        self._max_retries = max_retries
        self._retry_delay = retry_delay

    async def generate_feedback(self, context: MatchContext) -> dict:
        prompt = _build_prompt(context)

        for attempt in range(1, self._max_retries + 1):
            try:
                response = await self._client.aio.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.3,
                    ),
                )

                result = _parse_ai_response(response.text.strip())

                if "insights" not in result or "feedback_geral" not in result:
                    raise ValueError("Resposta da IA sem estrutura esperada.")

                return result

            except json.JSONDecodeError as e:
                logger.warning("[COACH] Tentativa %d/%d â€” JSON invÃ¡lido: %s", attempt, self._max_retries, e)
            except Exception as e:
                logger.warning("[COACH] Tentativa %d/%d â€” Erro: %s", attempt, self._max_retries, e)

            if attempt < self._max_retries:
                await asyncio.sleep(self._retry_delay * attempt)

        logger.error("[COACH] Todas as tentativas falharam. Usando fallback.")
        return FALLBACK_RESPONSE

    async def generate_feedback_stream(self, context: MatchContext):
        """
        Async generator â€” faz streaming da resposta da IA evento a evento.
        Yields: ("insights", list) | ("chunk", str) | ("done", dict) | ("error", str)

        Retry:
        - Falha ANTES de qualquer chunk enviado â†’ reinicia 1 vez automaticamente
        - Falha NO MEIO do stream â†’ envia mensagem de erro elegante e encerra
        """
        prompt = _build_prompt(context)

        for attempt in range(2):  # tentativa 0 = normal, tentativa 1 = retry
            accumulated      = ""
            feedback_started = False
            insights         = []
            full_feedback    = ""
            chunks_sent      = 0

            try:
                response_stream = await self._client.aio.models.generate_content_stream(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.3,
                    ),
                )

                async for chunk in response_stream:
                    try:
                        text = chunk.text
                    except Exception:
                        continue
                    if not text:
                        continue

                    if not feedback_started:
                        accumulated += text
                        if "[FEEDBACK]" in accumulated:
                            before, rest = accumulated.split("[FEEDBACK]", 1)
                            raw_json = before.replace("[INSIGHTS]", "").strip()
                            try:
                                insights = json.loads(raw_json).get("insights", [])
                            except json.JSONDecodeError:
                                insights = []
                            yield ("insights", insights)
                            feedback_started = True
                            if rest:
                                full_feedback += rest
                                chunks_sent += 1
                                yield ("chunk", rest)
                    else:
                        full_feedback += text
                        chunks_sent += 1
                        yield ("chunk", text)

                # Stream concluÃ­do com sucesso â€” sai do loop de retry
                break

            except Exception as e:
                logger.error(f"Stream tentativa {attempt + 1}/2 â€” Erro: {e}")

                if chunks_sent == 0 and attempt == 0:
                    # Falhou antes de enviar qualquer coisa â†’ tenta novamente
                    logger.info("Reiniciando stream (nenhum chunk enviado ainda)...")
                    await asyncio.sleep(2)
                    continue
                else:
                    # Falhou no meio do stream â†’ encerra de forma elegante
                    if chunks_sent > 0:
                        yield ("chunk", "\n\n[Erro de conexÃ£o com a IA, tente novamente]")
                    else:
                        yield ("error", str(e))
                    return

        assembled = {"insights": insights, "feedback_geral": full_feedback.strip()}
        yield ("done", assembled)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Pipeline completo
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _coerce_pending_local_events(raw_events: list[dict]) -> list[LocalEventUpload]:
    """Normalizes pending localhost payloads into typed local events."""

    normalized: list[LocalEventUpload] = []
    for raw in raw_events:
        if not isinstance(raw, dict):
            continue
        event_type = str(raw.get("event_type", "")).strip()
        if not event_type:
            continue
        try:
            normalized.append(
                LocalEventUpload(
                    event_type=event_type,
                    game_time=str(raw.get("game_time", "")).strip()[:10],
                    champion=str(raw.get("champion", "")).strip()[:64],
                    killer=(str(raw.get("killer")).strip()[:64] if raw.get("killer") else None),
                    victim=(str(raw.get("victim")).strip()[:64] if raw.get("victim") else None),
                    detail=str(raw.get("detail", "")).strip()[:300],
                    assisters=[
                        str(value).strip()[:64]
                        for value in raw.get("assisters", [])
                        if str(value).strip()
                    ][:10],
                    minimap_base64="",
                )
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.warning("[PIPELINE] Pending localhost event skipped: %s", exc)
    return normalized


async def run_full_analysis(
    riot_api_key: str,
    gemini_api_key: str,
    game_name: str,
    tag_line: str,
    match_index: int = 0,
    rank: str = "DEFAULT",
    summoner=None,
) -> dict:
    from riot_client import RiotMatchClient, get_item_names
    from context_builder import ContextBuilder

    riot = RiotMatchClient(api_key=riot_api_key)

    if summoner is None:
        logger.info(f"[1/5] Buscando jogador {game_name}#{tag_line}...")
        summoner = await riot.get_summoner_by_name(game_name, tag_line)
        if not summoner:
            raise ValueError(f"Jogador {game_name}#{tag_line} nao encontrado.")
    else:
        logger.info(f"[1/5] Jogador {game_name}#{tag_line} ja carregado.")

    logger.info("[2/5] Buscando historico e rank...")
    match_ids = await riot.get_match_history(summoner.puuid, count=10)
    if not match_ids:
        raise ValueError("Nenhuma partida encontrada.")

    match_id = match_ids[match_index]
    logger.info(f"[3/5] Carregando partida {match_id}...")

    match, timeline = await asyncio.gather(
        riot.get_match(match_id),
        riot.get_match_timeline(match_id),
    )
    if not match or not timeline:
        raise ValueError(f"Nao foi possivel carregar a partida {match_id}.")

    item_names = await get_item_names(match.game_version)

    logger.info("[4/5] Construindo contexto...")
    builder = ContextBuilder(target_puuid=summoner.puuid, rank=rank)
    context = builder.build(match, timeline, item_names=item_names)

    pending_local = await get_pending_local_evidence(match_id, context.player_riot_id)
    pending_local_events = _coerce_pending_local_events((pending_local or {}).get("local_events", []))
    pending_image_paths = [
        str(path)
        for path in (pending_local or {}).get("image_paths", [])
        if isinstance(path, str) and path.strip()
    ]
    pending_player_map = {
        str(key): str(value)
        for key, value in (pending_local or {}).get("player_map", {}).items()
        if str(key).strip() and str(value).strip()
    }

    snapshot = build_analysis_evidence_bundle(
        riot_id=context.player_riot_id,
        match_context=context,
        local_events=pending_local_events,
        match_id=match_id,
        image_paths=pending_image_paths,
        analysis_payload={"player_map": pending_player_map} if pending_player_map else {},
    )
    if snapshot.bundle is None:
        raise ValueError("Pipeline nao conseguiu construir evidence bundle.")

    ingestion_checkpoint = PipelineCheckpoint(
        stage=PipelineStage.INGESTION,
        status=StageStatus.ACCEPTED,
        detail="Input accepted for normalized evidence processing.",
    )
    context_checkpoint = gate_pipeline_stage(
        PipelineStage.CONTEXT_BUILD,
        bundle=snapshot.bundle,
        checkpoint=ingestion_checkpoint,
        allow_degraded=True,
    )
    if snapshot.bundle.source.value == "riot_only":
        context_checkpoint = context_checkpoint.model_copy(
            update={
                "status": StageStatus.DEGRADED_SAFE,
                "detail": "Riot-only evidence allowed under degraded-safe mode.",
            }
        )
    if not context_checkpoint.allows_progress(allow_degraded=True):
        reasons = ",".join(code.value for code in context_checkpoint.reason_codes) or "unknown"
        await save_pipeline_snapshot(
            match_id,
            context.player_riot_id,
            {
                "stage": context_checkpoint.stage.value,
                "status": context_checkpoint.status.value,
                "reason_codes": [code.value for code in context_checkpoint.reason_codes],
                "external_status": "insufficient_data",
                "has_analysis_text": False,
                "source": snapshot.bundle.source.value,
                "weak_signal": False,
            },
        )
        raise ValueError(f"Pipeline bloqueado em context_build: {reasons}")

    analysis_checkpoint = gate_pipeline_stage(
        PipelineStage.ANALYSIS_GENERATION,
        bundle=snapshot.bundle,
        checkpoint=context_checkpoint,
        allow_degraded=True,
    )
    if not analysis_checkpoint.allows_progress(allow_degraded=True):
        reasons = ",".join(code.value for code in analysis_checkpoint.reason_codes) or "unknown"
        await save_pipeline_snapshot(
            match_id,
            context.player_riot_id,
            {
                "stage": analysis_checkpoint.stage.value,
                "status": analysis_checkpoint.status.value,
                "reason_codes": [code.value for code in analysis_checkpoint.reason_codes],
                "external_status": "insufficient_data",
                "has_analysis_text": False,
                "source": snapshot.bundle.source.value,
                "weak_signal": False,
            },
        )
        raise ValueError(f"Pipeline bloqueado em analysis_generation: {reasons}")

    coach = CoachAI(api_key=gemini_api_key)
    allow_validated_cache = snapshot.bundle.source.value == "riot_plus_local"

    ai_result = None
    if allow_validated_cache:
        ai_result = await _get_ai_cache(match_id, riot_id=context.player_riot_id)

    if not ai_result:
        logger.info("[5/5] Gerando feedback com IA...")
        ai_result = await coach.generate_feedback(context)
        ai_result = _normalize_analysis_result(ai_result, context)
        guardrail_violations = guardrail_lint(context.model_dump(), ai_result)
        if guardrail_violations:
            ai_result = sanitize_minimally(context.model_dump(), ai_result, guardrail_violations)
            ai_result["_guardrails_violations_before"] = guardrail_violations
        if _is_valid_ai_result(ai_result) and allow_validated_cache:
            cache_payload = {
                "insights": ai_result.get("insights", []),
                "feedback_geral": ai_result.get("feedback_geral", ""),
            }
            await _set_ai_cache(match_id, cache_payload, riot_id=context.player_riot_id)
        else:
            logger.warning("[CACHE] Resultado invalido ou incompleto - nao salvo no cache.")
    else:
        logger.info("[CACHE] Hit! Feedback da IA recuperado do Supabase.")
        ai_result = _normalize_analysis_result(ai_result, context)

    if _is_valid_ai_result(ai_result):
        output_checkpoint = gate_pipeline_stage(
            PipelineStage.OUTPUT_VALIDATION,
            bundle=snapshot.bundle,
            checkpoint=analysis_checkpoint,
            allow_degraded=True,
        )
    else:
        output_checkpoint = PipelineCheckpoint(
            stage=PipelineStage.OUTPUT_VALIDATION,
            status=StageStatus.INVALID_INPUT,
            reason_codes=[PipelineReasonCode.INVALID_AI_OUTPUT],
            detail="AI output failed schema validation checks.",
        )
    if not output_checkpoint.allows_progress(allow_degraded=True):
        await save_pipeline_snapshot(
            match_id,
            context.player_riot_id,
            {
                "stage": output_checkpoint.stage.value,
                "status": output_checkpoint.status.value,
                "reason_codes": [code.value for code in output_checkpoint.reason_codes],
                "external_status": "failed",
                "has_analysis_text": False,
                "source": snapshot.bundle.source.value,
                "weak_signal": False,
            },
        )
        raise ValueError("Pipeline bloqueado em output_validation por resultado invalido.")

    delivery_checkpoint = gate_pipeline_stage(
        PipelineStage.DELIVERY,
        bundle=snapshot.bundle,
        checkpoint=output_checkpoint,
        allow_degraded=True,
    )
    if not delivery_checkpoint.allows_progress(allow_degraded=True):
        await save_pipeline_snapshot(
            match_id,
            context.player_riot_id,
            {
                "stage": delivery_checkpoint.stage.value,
                "status": delivery_checkpoint.status.value,
                "reason_codes": [code.value for code in delivery_checkpoint.reason_codes],
                "external_status": "failed",
                "has_analysis_text": False,
                "source": snapshot.bundle.source.value,
                "weak_signal": False,
            },
        )
        raise ValueError("Pipeline bloqueado em delivery.")

    if pending_local and snapshot.bundle.source.value == "riot_plus_local":
        await delete_pending_local_evidence(match_id, context.player_riot_id)

    weak_signal = bool(ai_result.get("weak_signal"))
    has_local_evidence = snapshot.bundle.source.value == "riot_plus_local"
    if not has_local_evidence or weak_signal:
        external_status = "insufficient_data"
    elif delivery_checkpoint.status.value == "ready":
        external_status = "ready"
    else:
        external_status = "pending"

    await save_pipeline_snapshot(
        match_id,
        context.player_riot_id,
        {
            "stage": delivery_checkpoint.stage.value,
            "status": delivery_checkpoint.status.value,
            "reason_codes": [code.value for code in delivery_checkpoint.reason_codes],
            "external_status": external_status,
            "has_analysis_text": _is_valid_ai_result(ai_result) and has_local_evidence and not weak_signal,
            "source": snapshot.bundle.source.value,
            "weak_signal": weak_signal,
        },
    )

    insights = ai_result.get("insights", [])
    feedback_text = ai_result.get("feedback_geral", "")

    logger.info(
        "Analise completa! source=%s status=%s insights=%d",
        snapshot.bundle.source.value,
        delivery_checkpoint.status.value,
        len(insights),
    )

    return {
        "context": context,
        "insights": insights,
        "feedback": feedback_text,
        "match_id": match_id,
        "summoner": summoner,
    }
if __name__ == "__main__":
    import os

    RIOT_KEY   = os.getenv("RIOT_API_KEY", "SUA_CHAVE_AQUI")
    GEMINI_KEY = os.getenv("GEMINI_API_KEY", "SUA_CHAVE_AQUI")

    result = asyncio.run(run_full_analysis(
        riot_api_key=RIOT_KEY,
        gemini_api_key=GEMINI_KEY,
        game_name="SeuNick",
        tag_line="BR1",
        match_index=0,
        rank="GOLD",
    ))

    logger.info("=" * 50)
    logger.info("FEEDBACK:")
    logger.info(result["feedback"])
    logger.info("INSIGHTS:")
    for i in result["insights"]:
        logger.info(f"  [{i['severity']}] {i['title']}")
