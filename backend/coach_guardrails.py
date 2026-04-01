"""
coach_guardrails.py — Linter + Rewrite + Sanitização pós-LLM
Garante que o feedback do coach seja factual mesmo quando o Gemini desobedece o SYSTEM_PROMPT.

Pipeline:
  lint() → se violações → rewrite (2ª chamada LLM) → revalida → sanitize_minimally (último recurso)
"""

import json
import logging
import math
import re
from typing import Awaitable, Callable

logger = logging.getLogger(__name__)

# Plan artifact marker: timestamp|number|VIOL_

# ─────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────

# Violações que exigem rewrite obrigatório (impacto factual)
_REWRITE_TRIGGERS: frozenset[str] = frozenset({
    "VIOL_BENCHMARK_LANGUAGE",
    "VIOL_GLOBAL_MAP_VISION_CLAIM",
    "VIOL_ABSOLUTE_CAUSALITY",
    "VIOL_INFERENTIAL_POSITIONING",
    "VIOL_FIXED_GOALS",
    "VIOL_PIT_CLAIM_WITHOUT_EVIDENCE",
    "VIOL_PIT_ALL_OBJECTIVES_OVERCLAIM",
    "VIOL_VISION_PRIMARY_WITH_LOW_SUPPORT",
    "VIOL_GANK_CLAIM_WITHOUT_EVIDENCE",
    "VIOL_GOALS_NOT_DERIVED",
    "VIOL_UNSUPPORTED_PRAISE",
})

REWRITE_PROMPT = """\
Você é um revisor de compliance de coach de League of Legends.
Receberá INPUT_JSON, OUTPUT_ATUAL e VIOLATIONS.

Reescreva apenas o necessário para remover TODAS as violações listadas.
Regras obrigatórias:
- Não adicione fatos novos além do INPUT_JSON e do que já está no OUTPUT_ATUAL.
- Se um claim não tiver evidência no INPUT_JSON, remova-o ou transforme em recomendação neutra.
- Garanta: cada parágrafo do feedback_geral tem 1 timestamp mm:ss + 1 número do JSON.
- Proibido: linguagem de "para o elo", "acima do esperado", "benchmark", "ideal" sem campo benchmarks.
- Proibido: "ausência de visão no mapa" ou "sem visão no mapa" como claim global.
- Proibido: "diretamente", "causa direta", "foi o motivo" sem suporte numérico provado.
- Proibido: "sobreextensão", "overextend", "sem informação do inimigo" sem evidência de death_type.
- Proibido: metas fixas de wards/controls sem citar os valores base do JSON.
Retorne no mesmo formato exato (dois blocos: [INSIGHTS] e [FEEDBACK]). NÃO imprima checklist.\
"""

# ─────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────

_RE_TIMESTAMP = re.compile(r"\b\d{1,2}:\d{2}\b")
# Número "significativo" = não apenas "0", "1" ou pontuação isolada
_RE_NUMBER = re.compile(r"\b(\d+[.,]\d+%?|\d{2,}%?|\d+%)\b")
_PRAISE_RE = re.compile(
    r"\b(excelente|otim[oa]|mandou bem|jogou muito bem|bom trabalho)\b",
    re.IGNORECASE,
)


def _paragraphs(text: str) -> list[str]:
    """Divide feedback_geral em parágrafos por linha em branco."""
    blocks = re.split(r"\n\s*\n", text.strip())
    return [b.strip() for b in blocks if b.strip()]


def _mm_ss(ts_sec: float) -> str:
    m = int(ts_sec) // 60
    s = int(ts_sec) % 60
    return f"{m:02d}:{s:02d}"


def _deaths_total(input_json: dict) -> int:
    deaths = input_json.get("deaths", [])
    if deaths:
        return len(deaths)
    kda = input_json.get("kda", "0/0/0")
    try:
        return int(kda.split("/")[1])
    except Exception:
        return 0


# ─────────────────────────────────────────
# LINTER
# ─────────────────────────────────────────

def lint(input_json: dict, output: dict) -> list[str]:
    """
    Valida o output do LLM contra as regras anti-alucinação.
    Retorna lista de códigos de violação (lista vazia = OK).

    input_json: MatchContext.model_dump() ou dict equivalente com campos:
      deaths[], objectives[], wards_placed, control_wards_placed, duration_min, kda
    output: dict com chaves "insights" e "feedback_geral"
    """
    violations: list[str] = []
    feedback = output.get("feedback_geral", "")
    fb_lower = feedback.lower()

    # ── Check 1: Cada parágrafo tem timestamp mm:ss e número significativo ──
    for i, para in enumerate(_paragraphs(feedback), start=1):
        if not _RE_TIMESTAMP.search(para):
            violations.append(f"FB_P{i}_MISSING_TIMESTAMP")
        if not _RE_NUMBER.search(para):
            violations.append(f"FB_P{i}_MISSING_NUMBER")

    # ── Check 2: Proibições absolutas de linguagem ─────────────────────────

    # "para o elo" sempre proibido (LLM usando conhecimento interno de rank)
    # "benchmark/ideal" proibido se não houver cs_stats ou benchmarks no JSON
    has_benchmarks = bool(input_json.get("benchmarks") or input_json.get("cs_stats"))

    benchmark_terms = ["para o elo", "acima do esperado", "acima do ideal",
                       "abaixo do esperado", "abaixo do ideal"]
    if not has_benchmarks:
        benchmark_terms += ["benchmark", "ideal para"]

    if any(t in fb_lower for t in benchmark_terms):
        violations.append("VIOL_BENCHMARK_LANGUAGE")

    map_vision_phrases = [
        "ausência de visão no mapa", "sem visão no mapa",
        "sem visão no mapa inteiro", "falta de visão no mapa",
    ]
    if any(p in fb_lower for p in map_vision_phrases):
        violations.append("VIOL_GLOBAL_MAP_VISION_CLAIM")

    causality_terms = ["diretamente", "causa direta", "foi o motivo", "resultou em"]
    if any(t in fb_lower for t in causality_terms):
        violations.append("VIOL_ABSOLUTE_CAUSALITY")

    positioning_terms = ["sobreextensão", "overextend", "sem informação do inimigo"]
    if any(t in fb_lower for t in positioning_terms):
        violations.append("VIOL_INFERENTIAL_POSITIONING")

    fixed_goal_terms = [
        "1 ward por minuto", "ward por minuto",
        "5 control wards", "no mínimo 5 control wards", "pelo menos 5 control",
    ]
    if any(t in fb_lower for t in fixed_goal_terms):
        violations.append("VIOL_FIXED_GOALS")

    if _PRAISE_RE.search(feedback):
        has_anchor = bool(_RE_TIMESTAMP.search(feedback) and _RE_NUMBER.search(feedback))
        if not has_anchor:
            violations.append("VIOL_UNSUPPORTED_PRAISE")

    # ── Check 3: "Pit sem visão" precisa de evidência com timestamp ────────
    _PIT_CLAIM_RE = re.compile(
        r"(sem visão no pit|falta de visão no pit|ausência de visão no pit|pit sem visão)",
        re.IGNORECASE,
    )
    _ALL_OBJ_VISION_RE = re.compile(
        r"(todos os objetivos sem visão|ausência de visão em todos|"
        r"todos sem visão no pit|todos os objetivos listados)",
        re.IGNORECASE,
    )

    objectives = input_json.get("objectives", [])
    obj_no_vision = [o for o in objectives if not o.get("had_vision_on_pit", True)]

    if _PIT_CLAIM_RE.search(feedback):
        cited_secs = []
        for ts_str in _RE_TIMESTAMP.findall(feedback):
            parts = ts_str.split(":")
            try:
                cited_secs.append(int(parts[0]) * 60 + int(parts[1]))
            except Exception:
                pass

        evidence = any(
            any(abs(int(o.get("timestamp_sec", 0)) - c) <= 5 for c in cited_secs)
            for o in obj_no_vision
        )
        if not evidence:
            violations.append("VIOL_PIT_CLAIM_WITHOUT_EVIDENCE")

    if _ALL_OBJ_VISION_RE.search(feedback):
        all_no_vision = objectives and all(
            not o.get("had_vision_on_pit", True) for o in objectives
        )
        if not all_no_vision:
            violations.append("VIOL_PIT_ALL_OBJECTIVES_OVERCLAIM")

    # ── Check 4: "Visão como causa principal" exige threshold ──────────────
    _VISION_PRIMARY_RE = re.compile(
        r"(causa\s+principal[^.]{0,40}vis[ãa]o|"
        r"fator\s+cr[ií]tico[^.]{0,40}vis[ãa]o|"
        r"principal\s+problema[^.]{0,40}vis[ãa]o|"
        r"problema\s+principal[^.]{0,40}vis[ãa]o|"
        r"falha\s+cr[ií]tica[^.]{0,40}vis[ãa]o)",
        re.IGNORECASE,
    )
    if _VISION_PRIMARY_RE.search(feedback):
        deaths_list      = input_json.get("deaths", [])
        d_total          = _deaths_total(input_json)
        no_vision_deaths = sum(1 for d in deaths_list if not d.get("had_vision_of_killer", True))
        obj_nv           = len(obj_no_vision)
        cw               = input_json.get("control_wards_placed", -1)
        dur              = input_json.get("duration_min", 0)

        cond_a = d_total > 0 and (no_vision_deaths / d_total) >= 0.5
        cond_b = obj_nv >= 2
        cond_c = cw == 0 and dur >= 20

        if not (cond_a or cond_b or cond_c):
            violations.append("VIOL_VISION_PRIMARY_WITH_LOW_SUPPORT")

    # ── Check 5: Metas de wards devem ser derivadas do JSON ────────────────
    _WARD_GOAL_RE = re.compile(
        r"(\d+)\s*(?:a\s+)?(?:wards?\b|controles?\b|control\s*wards?\b)", re.IGNORECASE
    )
    wards_placed = input_json.get("wards_placed")
    cw_placed    = input_json.get("control_wards_placed")

    for m in _WARD_GOAL_RE.finditer(feedback):
        value    = int(m.group(1))
        wt_lower = m.group(0).lower()
        if "control" in wt_lower or "controle" in wt_lower:
            if cw_placed is not None:
                target_min = max(cw_placed + 2, math.ceil(cw_placed * 1.8))
                if value < target_min and value <= 10:
                    violations.append("VIOL_GOALS_NOT_DERIVED")
                    break
        else:
            if wards_placed is not None:
                target_min = max(wards_placed + 4, math.ceil(wards_placed * 1.4))
                if value < target_min and value <= 20:
                    violations.append("VIOL_GOALS_NOT_DERIVED")
                    break

    # ── Check 6: "Gank" como fato sem evidência ────────────────────────────
    if re.search(r"\bgank\b", fb_lower):
        deaths_list = input_json.get("deaths", [])
        has_gank_evidence = any(
            d.get("death_type") in ("GANK", "TRIPLE_GANK") or d.get("enemies_count", 0) >= 2
            for d in deaths_list
        )
        if not has_gank_evidence:
            violations.append("VIOL_GANK_CLAIM_WITHOUT_EVIDENCE")

    return violations


def needs_rewrite(violations: list[str]) -> bool:
    """Retorna True se houver pelo menos 1 violação que exige rewrite do LLM."""
    return bool(set(violations) & _REWRITE_TRIGGERS)


# ─────────────────────────────────────────
# SANITIZAÇÃO FINAL (último recurso — sem LLM)
# ─────────────────────────────────────────

def sanitize_minimally(input_json: dict, output: dict, violations: list[str]) -> dict:
    """
    Sanitização cirúrgica sem chamar o LLM.
    Remove/neutraliza trechos problemáticos. Último recurso após falha no rewrite.
    """
    feedback = output.get("feedback_geral", "")

    _REMOVE_SENTENCE: list[tuple[re.Pattern, str]] = [
        (re.compile(r"[^.]*\b(para o elo|acima do esperado|acima do ideal|abaixo do esperado)\b[^.]*\.", re.IGNORECASE), ""),
        (re.compile(r"[^.]*\b(ausência de visão no mapa|sem visão no mapa)\b[^.]*\.", re.IGNORECASE), ""),
        (re.compile(r"[^.]*\b(causa direta|foi o motivo|resultou em)\b[^.]*\.", re.IGNORECASE), ""),
        (re.compile(r"[^.]*\b(sobreextensão|overextend|sem informação do inimigo)\b[^.]*\.", re.IGNORECASE), ""),
    ]
    for pattern, repl in _REMOVE_SENTENCE:
        feedback = pattern.sub(repl, feedback)

    # Suavizar "diretamente" → "possivelmente"
    feedback = re.sub(r"\bdiretamente\b", "possivelmente", feedback, flags=re.IGNORECASE)

    # Garantir timestamp e número por parágrafo
    paragraphs = _paragraphs(feedback)
    dur_sec    = input_json.get("duration_min", 0) * 60
    dur_str    = _mm_ss(dur_sec)
    d_total    = _deaths_total(input_json)
    cs_pm      = input_json.get("cs_per_min", "")

    fixed: list[str] = []
    for i, para in enumerate(paragraphs, start=1):
        if f"FB_P{i}_MISSING_TIMESTAMP" in violations:
            para = f"[{dur_str}] " + para
        if f"FB_P{i}_MISSING_NUMBER" in violations:
            anchor = f"{d_total} mortes" if d_total else (f"CS/min {cs_pm}" if cs_pm else "")
            if anchor:
                para = para + f" ({anchor} no total)"
        fixed.append(para)

    result = dict(output)
    result["feedback_geral"]      = "\n\n".join(fixed)
    result["_guardrails_sanitized"] = True
    return result


# ─────────────────────────────────────────
# PIPELINE COM GUARDRAILS
# ─────────────────────────────────────────

async def run_with_guardrails(
    input_json: dict,
    output: dict,
    llm_fn: Callable[[str, dict, str], Awaitable[dict]],
    match_id: str = "",
) -> dict:
    """
    Orquestra: lint → rewrite (se necessário) → revalida → sanitize_minimally.

    Parâmetros:
      input_json : MatchContext.model_dump()
      output     : dict com "insights" e "feedback_geral"
      llm_fn     : async (rewrite_payload_str, input_json, mode) → dict
      match_id   : para logging
    """
    violations = lint(input_json, output)

    if not violations:
        logger.info("[GUARDRAILS] %s — OK (0 violações)", match_id or "?")
        return output

    logger.warning(
        "[GUARDRAILS] %s — %d violação(ões): %s",
        match_id or "?", len(violations), violations,
    )

    if needs_rewrite(violations):
        logger.info("[GUARDRAILS] %s — Iniciando rewrite...", match_id or "?")
        rewrite_payload = json.dumps(
            {"INPUT_JSON": input_json, "OUTPUT_ATUAL": output, "VIOLATIONS": violations},
            ensure_ascii=False,
        )
        try:
            rewritten       = await llm_fn(rewrite_payload, input_json, "rewrite")
            v_after         = lint(input_json, rewritten)

            if v_after:
                logger.warning(
                    "[GUARDRAILS] %s — Rewrite ainda tem %d violação(ões): %s. Sanitizando.",
                    match_id or "?", len(v_after), v_after,
                )
                final = sanitize_minimally(input_json, rewritten, v_after)
            else:
                logger.info("[GUARDRAILS] %s — Rewrite passou no lint.", match_id or "?")
                final = rewritten

            final["_guardrails_violations_before"] = violations
            final["_guardrails_violations_after"]  = v_after
            return final

        except Exception as exc:
            logger.error(
                "[GUARDRAILS] %s — Rewrite falhou (%s). Sanitizando original.", match_id or "?", exc
            )
            sanitized = sanitize_minimally(input_json, output, violations)
            sanitized["_guardrails_violations_before"] = violations
            return sanitized

    # Apenas violações de parágrafo (sem triggers de rewrite) → sanitize direto
    final = sanitize_minimally(input_json, output, violations)
    final["_guardrails_violations_before"] = violations
    return final


