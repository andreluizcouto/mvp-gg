from types import SimpleNamespace

import pytest

import coach_ai
import context_builder


@pytest.mark.asyncio
async def test_get_ai_cache_filters_by_riot_id(monkeypatch):
    class FakeQuery:
        def __init__(self):
            self.eq_calls = []

        def select(self, _columns):
            return self

        def eq(self, column, value):
            self.eq_calls.append((column, value))
            return self

        async def execute(self):
            return SimpleNamespace(
                data=[
                    {
                        "insights": [
                            {
                                "category": "PERFORMANCE",
                                "severity": "LOW",
                                "timestamp": 120.0,
                                "title": "ok",
                                "detail": "Aos 02:00 voce teve 1 boa troca.",
                                "suggestion": "Repita esse padrao nas proximas lutas.",
                            }
                        ],
                        "feedback_geral": "texto valido",
                    }
                ]
            )

    query = FakeQuery()

    class FakeSupabase:
        def table(self, name):
            assert name == "ai_cache"
            return query

    async def fake_get_supabase():
        return FakeSupabase()

    monkeypatch.setattr(coach_ai, "get_supabase", fake_get_supabase)

    data = await coach_ai._get_ai_cache("BR1_123", riot_id="tester#BR1")
    assert data["feedback_geral"] == "texto valido"
    assert query.eq_calls == [("match_id", "BR1_123"), ("riot_id", "tester#BR1")]


@pytest.mark.asyncio
async def test_set_ai_cache_uses_match_and_riot_id_conflict(monkeypatch):
    captured = {}

    class FakeQuery:
        async def execute(self):
            captured["executed"] = True
            return SimpleNamespace(data=[])

    class FakeSupabase:
        def table(self, name):
            assert name == "ai_cache"
            return self

        def upsert(self, payload, on_conflict=None):
            captured["payload"] = payload
            captured["on_conflict"] = on_conflict
            return FakeQuery()

    async def fake_get_supabase():
        return FakeSupabase()

    monkeypatch.setattr(coach_ai, "get_supabase", fake_get_supabase)

    await coach_ai._set_ai_cache(
        "BR1_123",
        {
            "insights": [
                {
                    "category": "PERFORMANCE",
                    "severity": "LOW",
                    "timestamp": 120.0,
                    "title": "ok",
                    "detail": "Aos 02:00 voce teve 1 boa troca.",
                    "suggestion": "Repita esse padrao nas proximas lutas.",
                }
            ],
            "feedback_geral": "texto valido",
        },
        riot_id="tester#BR1",
    )

    assert captured["payload"]["match_id"] == "BR1_123"
    assert captured["payload"]["riot_id"] == "tester#BR1"
    assert captured["on_conflict"] == "match_id,riot_id"
    assert captured["executed"] is True


def _make_context(match_id: str = "BR1_123"):
    return context_builder.MatchContext(
        match_id=match_id,
        player_riot_id="tester#BR1",
        player_champion="Ahri",
        role="MIDDLE",
        win=True,
        duration_min=31.2,
        kda="10/3/7",
        cs_per_min=7.4,
        vision_score=22,
        kill_participation_pct=61.0,
        damage_share_pct=27.0,
        time_dead_pct=3.0,
        fact_log=[{"confidence": "HIGH"} for _ in range(30)],
    )


def test_normalize_analysis_result_is_deterministic():
    raw = {
        "insights": [
            {
                "category": "performance",
                "severity": "LOW",
                "timestamp": 640.0,
                "title": "Bom pickoff",
                "detail": "Aos 10:40 voce converteu 2 kills em objetivo.",
                "suggestion": "Repita esse setup e busque 2 conversoes por jogo.",
            },
            {
                "category": "death",
                "severity": "HIGH",
                "timestamp": 450.0,
                "title": "Morte sem visao",
                "detail": "Aos 07:30 voce morreu e cedeu 300g.",
                "suggestion": "Jogue a wave com cobertura e limite mortes a 3.",
            },
        ],
        "feedback_geral": "Aos 07:30 houve erro grave e aos 10:40 teve boa resposta com 2 kills.",
    }
    context = _make_context()

    first = coach_ai._normalize_analysis_result(raw, context)
    second = coach_ai._normalize_analysis_result(raw, context)

    assert first["insights"] == second["insights"]
    assert first["coaching_contract"] == second["coaching_contract"]
    assert first["similarity_fingerprint"] == second["similarity_fingerprint"]
    assert first["insights"][0]["category"] == "DEATH"


def test_similarity_fingerprint_changes_when_role_changes():
    base_context = _make_context()
    alt_context = _make_context(match_id="BR1_999").model_copy(update={"role": "JUNGLE"})
    insights = [
        coach_ai._normalize_insight(
            {
                "category": "CS",
                "severity": "MEDIUM",
                "timestamp": 500.0,
                "title": "CS baixo",
                "detail": "Aos 08:20 voce tinha 52 de CS.",
                "suggestion": "Aumente para 70 ate 10:00.",
            }
        )
    ]

    base_fp = coach_ai._similarity_fingerprint(base_context, insights)
    alt_fp = coach_ai._similarity_fingerprint(alt_context, insights)

    assert base_fp != alt_fp
