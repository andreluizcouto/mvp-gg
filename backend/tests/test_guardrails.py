"""
tests/test_guardrails.py — Testes unitários do linter de guardrails

Execução:
  cd ProjectB
  python -m pytest tests/test_guardrails.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from coach_guardrails import lint, needs_rewrite, sanitize_minimally

# ─────────────────────────────────────────
# Fixtures base
# ─────────────────────────────────────────

# input_json "bom" — representa MatchContext.model_dump() com dados realistas
BASE_INPUT = {
    "match_id":             "TEST_001",
    "kda":                  "13/5/11",
    "duration_min":         34.2,
    "cs_per_min":           7.3,
    "wards_placed":         6,
    "control_wards_placed": 2,
    "deaths": [
        {"timestamp_sec": 1167.0, "had_vision_of_killer": False, "death_type": "GANK",      "enemies_count": 2, "allies_count": 0},
        {"timestamp_sec": 1459.0, "had_vision_of_killer": False, "death_type": "GANK",      "enemies_count": 2, "allies_count": 0},
        {"timestamp_sec": 1727.3, "had_vision_of_killer": True,  "death_type": "TEAMFIGHT", "enemies_count": 3, "allies_count": 2},
        {"timestamp_sec": 2045.0, "had_vision_of_killer": False, "death_type": "GANK",      "enemies_count": 2, "allies_count": 0},
        {"timestamp_sec": 2300.0, "had_vision_of_killer": True,  "death_type": "DUEL",      "enemies_count": 1, "allies_count": 0},
    ],
    "objectives": [
        {"objective_type": "DRAGON",      "timestamp_sec": 854.0,  "had_vision_on_pit": False},
        {"objective_type": "DRAGON",      "timestamp_sec": 1440.0, "had_vision_on_pit": True},
        {"objective_type": "BARON_NASHOR","timestamp_sec": 1860.0, "had_vision_on_pit": False},
    ],
    "cs_stats": [
        {"phase": "EARLY", "cs_at_phase_end": 102, "benchmark": 97, "cs_diff_to_benchmark": 5.0},
    ],
}

# Output "OK" de referência — serve de base para os testes que manipulam só o feedback
GOOD_OUTPUT = {
    "insights": [
        {
            "category": "DEATH", "severity": "HIGH", "timestamp": 1167.0,
            "title": "Sequência de mortes no mid-game",
            "detail": "3 mortes entre 19:27 e 34:05 com 0 aliados próximos.",
            "suggestion": "Reduzir mortes de 5 → ≤ 3.",
        }
    ],
    "feedback_geral": (
        "Com KDA 13/5/11 e CS/min 7.3, você foi impactante nos 34:12 de jogo.\n\n"
        "A sequência de 3 ganks sofridos entre 19:27 e 34:05 com 0 aliados próximos "
        "mostra padrão de posicionamento em side sem suporte.\n\n"
        "Meta para as próximas 5 partidas: reduzir mortes de 5 → ≤ 3 até 25:00 "
        "e aumentar wards de 6 → ≥ 10 por partida."
    ),
}


# ─────────────────────────────────────────
# Caso 1: Parágrafo sem timestamp
# ─────────────────────────────────────────

def test_paragraph_missing_timestamp():
    output = dict(GOOD_OUTPUT)
    output["feedback_geral"] = (
        "Você teve um desempenho sólido com CS/min 7.3 e KDA 13/5/11.\n\n"
        "As mortes no mid-game mostraram padrão de posicionamento problemático com 0 aliados.\n\n"
        "Meta: reduzir mortes de 5 para ≤ 3 nas próximas partidas."
    )
    violations = lint(BASE_INPUT, output)
    # Parágrafos 1, 2 e 3 não têm timestamp — esperamos pelo menos 1 violação
    timestamp_viols = [v for v in violations if "MISSING_TIMESTAMP" in v]
    assert len(timestamp_viols) >= 1, f"Esperado MISSING_TIMESTAMP, obtido: {violations}"


# ─────────────────────────────────────────
# Caso 2: Parágrafo sem número significativo
# ─────────────────────────────────────────

def test_paragraph_missing_number():
    output = dict(GOOD_OUTPUT)
    # Parágrafo sem nenhum número (apenas palavras)
    output["feedback_geral"] = (
        "Sua performance foi excelente, mantendo vantagem constante no jogo [34:12].\n\n"
        "Você se expôs em side lanes e tomou ganks repetidamente.\n\n"  # sem número
        "Meta: reduzir mortes e aumentar wards nas próximas partidas."
    )
    violations = lint(BASE_INPUT, output)
    number_viols = [v for v in violations if "MISSING_NUMBER" in v]
    assert len(number_viols) >= 1, f"Esperado MISSING_NUMBER, obtido: {violations}"


# ─────────────────────────────────────────
# Caso 3: "ausência de visão no mapa" sem campo global
# ─────────────────────────────────────────

def test_global_map_vision_claim():
    output = dict(GOOD_OUTPUT)
    output["feedback_geral"] = (
        "Com 13 kills e CS/min 7.3 aos 34:12, o jogo estava sob controle.\n\n"
        "A ausência de visão no mapa foi o principal problema que levou às 5 mortes "
        "entre 19:27 e 34:05.\n\n"
        "Meta: 6 → ≥ 10 wards e 2 → ≥ 4 controls."
    )
    violations = lint(BASE_INPUT, output)
    assert "VIOL_GLOBAL_MAP_VISION_CLAIM" in violations, (
        f"Esperado VIOL_GLOBAL_MAP_VISION_CLAIM, obtido: {violations}"
    )


# ─────────────────────────────────────────
# Caso 4: "pit sem visão" sem listar objetivos com had_vision_on_pit=false + timestamp
# ─────────────────────────────────────────

def test_pit_claim_without_evidence():
    output = dict(GOOD_OUTPUT)
    # Menciona "pit sem visão" mas NÃO cita nenhum timestamp de objetivo com had_vision_on_pit=false
    output["feedback_geral"] = (
        "Com 5 mortes e CS/min 7.3 aos 34:12, a partida foi difícil.\n\n"
        "Todos os objetivos foram disputados sem visão no pit, o que gerou desvantagem.\n\n"
        "Meta: 5 mortes → ≤ 3 e 2 → ≥ 4 control wards até 34:12."
    )
    violations = lint(BASE_INPUT, output)
    assert "VIOL_PIT_CLAIM_WITHOUT_EVIDENCE" in violations or "VIOL_PIT_ALL_OBJECTIVES_OVERCLAIM" in violations, (
        f"Esperado pit violation, obtido: {violations}"
    )


# ─────────────────────────────────────────
# Caso 5: "visão como causa principal" sem atingir threshold
# ─────────────────────────────────────────

def test_vision_primary_without_threshold():
    # Input onde thresholds NÃO são atingidos:
    # - apenas 1/5 mortes sem visão (20% < 50%)
    # - 0 objetivos sem visão
    # - control_wards_placed = 3 (não é 0)
    low_vision_input = {
        **BASE_INPUT,
        "deaths": [
            {"timestamp_sec": 1167.0, "had_vision_of_killer": False, "death_type": "DUEL",      "enemies_count": 1, "allies_count": 0},
            {"timestamp_sec": 1459.0, "had_vision_of_killer": True,  "death_type": "TEAMFIGHT", "enemies_count": 3, "allies_count": 2},
            {"timestamp_sec": 1727.3, "had_vision_of_killer": True,  "death_type": "TEAMFIGHT", "enemies_count": 3, "allies_count": 2},
            {"timestamp_sec": 2045.0, "had_vision_of_killer": True,  "death_type": "TEAMFIGHT", "enemies_count": 3, "allies_count": 2},
            {"timestamp_sec": 2300.0, "had_vision_of_killer": True,  "death_type": "TEAMFIGHT", "enemies_count": 3, "allies_count": 2},
        ],
        "objectives": [
            {"objective_type": "DRAGON", "timestamp_sec": 854.0,  "had_vision_on_pit": True},
            {"objective_type": "DRAGON", "timestamp_sec": 1440.0, "had_vision_on_pit": True},
        ],
        "control_wards_placed": 3,
    }
    output = dict(GOOD_OUTPUT)
    output["feedback_geral"] = (
        "Com 5 mortes e CS/min 7.3 aos 34:12, o jogo foi competitivo.\n\n"
        "A falha crítica na visão foi a causa principal das 5 mortes entre 19:27 e 34:05, "
        "expondo o time sem informação.\n\n"
        "Meta: 5 mortes → ≤ 3 e aumentar wards de 6 → ≥ 10 até 34:12."
    )
    violations = lint(low_vision_input, output)
    assert "VIOL_VISION_PRIMARY_WITH_LOW_SUPPORT" in violations, (
        f"Esperado VIOL_VISION_PRIMARY_WITH_LOW_SUPPORT, obtido: {violations}"
    )


# ─────────────────────────────────────────
# Caso 6: Metas fixas sem base real do JSON
# ─────────────────────────────────────────

def test_fixed_goals_violation():
    output = dict(GOOD_OUTPUT)
    output["feedback_geral"] = (
        "Com CS/min 7.3 e KDA 13/5/11 aos 34:12, a performance foi sólida.\n\n"
        "As 5 mortes entre 19:27 e 34:05 foram o principal problema do jogo.\n\n"
        "Meta: ward por minuto e 5 control wards por partida a partir de 20:00."
    )
    violations = lint(BASE_INPUT, output)
    assert "VIOL_FIXED_GOALS" in violations, (
        f"Esperado VIOL_FIXED_GOALS, obtido: {violations}"
    )


# ─────────────────────────────────────────
# Casos extras: output OK não gera violações
# ─────────────────────────────────────────

def test_good_output_no_violations():
    violations = lint(BASE_INPUT, GOOD_OUTPUT)
    assert violations == [], f"Output OK gerou violações inesperadas: {violations}"


def test_needs_rewrite_true():
    assert needs_rewrite(["VIOL_BENCHMARK_LANGUAGE", "FB_P1_MISSING_TIMESTAMP"]) is True


def test_needs_rewrite_false_paragraph_only():
    # Apenas violações de parágrafo não disparam rewrite do LLM
    assert needs_rewrite(["FB_P1_MISSING_TIMESTAMP", "FB_P2_MISSING_NUMBER"]) is False


def test_sanitize_injects_timestamp():
    output = {
        "insights": [],
        "feedback_geral": "Você jogou bem. Parabéns pela vitória.",
    }
    result = sanitize_minimally(BASE_INPUT, output, ["FB_P1_MISSING_TIMESTAMP"])
    assert "34:12" in result["feedback_geral"] or ":" in result["feedback_geral"]
    assert result.get("_guardrails_sanitized") is True


def test_sanitize_removes_benchmark_sentence():
    output = {
        "insights": [],
        "feedback_geral": (
            "Seu CS foi excelente, acima do esperado para o elo com 7.3/min. "
            "Suas 5 mortes foram o ponto fraco às 19:27."
        ),
    }
    result = sanitize_minimally(BASE_INPUT, output, ["VIOL_BENCHMARK_LANGUAGE"])
    assert "para o elo" not in result["feedback_geral"].lower()


def test_unsupported_praise_without_evidence_triggers_violation():
    output = dict(GOOD_OUTPUT)
    output["feedback_geral"] = (
        "Voce jogou muito bem nesta partida e teve uma performance excelente.\n\n"
        "Continue assim e mantenha esse nivel."
    )

    violations = lint(BASE_INPUT, output)
    assert "VIOL_UNSUPPORTED_PRAISE" in violations


def test_supported_praise_with_timestamp_and_number_is_allowed():
    output = dict(GOOD_OUTPUT)
    output["feedback_geral"] = (
        "Aos 12:34 voce jogou muito bem no pickoff e converteu 2 kills em objetivo.\n\n"
        "Mantenha esse padrao nas proximas lutas."
    )

    violations = lint(BASE_INPUT, output)
    assert "VIOL_UNSUPPORTED_PRAISE" not in violations
