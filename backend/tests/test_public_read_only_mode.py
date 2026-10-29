import asyncio
from types import SimpleNamespace
import os

from fastapi.testclient import TestClient

import coach_ai
import context_builder
import evidence_pipeline
import main
import riot_client
from tests.fixtures.coaching_contracts import (
    failed_snapshot,
    insufficient_snapshot,
    pending_snapshot,
    ready_snapshot,
)


def _feedback_payload():
    return {
        "match_id": "BR1_123",
        "player": "tester#BR1",
        "rating": 5,
        "comment": "ok",
    }


def _disable_redis(monkeypatch):
    monkeypatch.setattr(main, "REDIS_URL", "")
    monkeypatch.setattr(main, "_redis_rate_limit_client", None)
    monkeypatch.setattr(main, "_redis_fallback_warned", False)


def test_ai_endpoints_block_without_token(monkeypatch):
    monkeypatch.setattr(main, "INTERNAL_BEARER_TOKEN", "bearer-interno")
    client = TestClient(main.app)

    analyze = client.post(
        "/analyze",
        json={"game_name": "tester", "tag_line": "BR1", "match_index": 0},
    )
    assert analyze.status_code == 401

    stream = client.get("/analyze/stream/tester/BR1/0")
    assert stream.status_code == 401

    latest = client.get("/analyze/tester/BR1")
    assert latest.status_code == 401

    feedback = client.post("/feedback", json=_feedback_payload())
    assert feedback.status_code == 401


def test_analyze_allows_valid_internal_token(monkeypatch):
    class FakeRiotClient:
        async def get_summoner_by_name(self, game_name, tag_line):
            return SimpleNamespace(summoner_id="sid-1", name=f"{game_name}#{tag_line}", puuid="puuid-1")

        async def get_summoner_rank(self, summoner_id):
            return "GOLD IV"


        async def get_ranked_entries(self, _puuid):
            return []

    async def fake_run_full_analysis(**kwargs):
        context = SimpleNamespace(
            match_id="BR1_123",
            player_riot_id="tester#BR1",
            player_champion="Ahri",
            role="MIDDLE",
            win=True,
            duration_min=29.5,
            kda="9/2/7",
            cs_per_min=7.8,
            vision_score=23,
            kill_participation_pct=61.0,
            damage_share_pct=27.5,
            time_dead_pct=3.1,
            rank="GOLD IV",
        )
        return {"context": context, "insights": [], "feedback": "ok"}

    monkeypatch.setattr(main, "INTERNAL_BEARER_TOKEN", "bearer-interno")
    monkeypatch.setattr(main, "RIOT_KEY", "riot-key")
    monkeypatch.setattr(main, "GEMINI_KEY", "gemini-key")
    monkeypatch.setattr(main, "RiotMatchClient", lambda api_key: FakeRiotClient())
    monkeypatch.setattr(main, "run_full_analysis", fake_run_full_analysis)
    monkeypatch.setattr(main, "MAKE_FEEDBACK_WEBHOOK_URL", "")

    client = TestClient(main.app)
    resp = client.post(
        "/analyze",
        headers={"Authorization": "Bearer bearer-interno"},
        json={"game_name": "tester", "tag_line": "BR1", "match_index": 0},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["match_id"] == "BR1_123"
    assert data["player"] == "tester#BR1"

    feedback = client.post("/feedback", headers={"Authorization": "Bearer bearer-interno"}, json=_feedback_payload())
    assert feedback.status_code == 200


def test_public_read_rate_limit_200_then_429(monkeypatch):
    _disable_redis(monkeypatch)
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_MAX_REQUESTS", 2)
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_MAX_REQUESTS", 999)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(main, "SUPABASE_URL", "")
    monkeypatch.setattr(main, "SUPABASE_KEY", "")
    main._public_read_hits.clear()
    main._edge_client_hits.clear()

    client = TestClient(main.app)
    params = {"ids": "BR1_1", "riot_id": "tester#BR1"}

    ok1 = client.get("/coaching/status", params=params)
    ok2 = client.get("/coaching/status", params=params)
    limited = client.get("/coaching/status", params=params)

    assert ok1.status_code == 200
    assert ok2.status_code == 200
    assert limited.status_code == 429


def test_edge_client_rate_limit_by_api_key(monkeypatch):
    _disable_redis(monkeypatch)
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_MAX_REQUESTS", 999)
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_MAX_REQUESTS", 2)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(main, "SUPABASE_URL", "")
    monkeypatch.setattr(main, "SUPABASE_KEY", "")
    main._public_read_hits.clear()
    main._edge_client_hits.clear()

    client = TestClient(main.app)
    params = {"ids": "BR1_1", "riot_id": "tester#BR1"}

    ok1 = client.get("/coaching/status", params=params, headers={"X-API-Key": "client-A"})
    ok2 = client.get("/coaching/status", params=params, headers={"X-API-Key": "client-A"})
    limited = client.get("/coaching/status", params=params, headers={"X-API-Key": "client-A"})
    fresh_client = client.get("/coaching/status", params=params, headers={"X-API-Key": "client-B"})

    assert ok1.status_code == 200
    assert ok2.status_code == 200
    assert limited.status_code == 429
    assert fresh_client.status_code == 200


def test_match_endpoint_returns_only_public_fields(monkeypatch):
    _disable_redis(monkeypatch)
    class FakeQuery:
        def __init__(self, row):
            self._row = row
            self.selected = ""

        def select(self, columns):
            self.selected = columns
            return self

        def eq(self, _column, _value):
            return self

        def limit(self, _amount):
            return self

        async def execute(self):
            return SimpleNamespace(data=[self._row])

    class FakeSupabase:
        def __init__(self, row):
            self._row = row

        def table(self, name):
            assert name == "ai_cache"
            return FakeQuery(self._row)

    async def fake_get_supabase():
        return FakeSupabase(
            {
                "match_id": "BR1_123",
                "riot_id": "tester#BR1",
                "summoner_name": "tester#BR1",
                "champion": "Ahri",
                "kills": 10,
                "deaths": 3,
                "assists": 8,
                "win": True,
                "duration_min": 30,
                "position": "MIDDLE",
                "cs_per_min": 7.2,
                "vision_score": 20,
                "kill_participation_pct": 60.0,
                "damage_share_pct": 25.0,
                "items": [6655, 3020],
                "allies": [{"champion": "JarvanIV", "position": "JUNGLE"}],
                "puuid": "puuid-1",
                "rank": "GOLD IV",
                "internal_secret": "must-not-leak",
            }
        )

    monkeypatch.setattr(main, "get_supabase", fake_get_supabase)
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_MAX_REQUESTS", 60)
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_MAX_REQUESTS", 999)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_WINDOW_SECONDS", 60)
    main._public_read_hits.clear()
    main._edge_client_hits.clear()

    client = TestClient(main.app)
    resp = client.get("/match/BR1_123")
    assert resp.status_code == 200

    payload = resp.json()
    assert "internal_secret" not in payload
    assert set(payload.keys()) == {
        "match_id",
        "riot_id",
        "summoner_name",
        "champion",
        "kills",
        "deaths",
        "assists",
        "win",
        "duration_min",
        "position",
        "cs_per_min",
        "vision_score",
        "kill_participation_pct",
        "damage_share_pct",
        "items",
        "allies",
        "puuid",
        "rank",
    }


def test_match_endpoint_handles_missing_rank_column_without_500(monkeypatch):
    _disable_redis(monkeypatch)

    class FakeMissingRankQuery:
        def select(self, columns):
            self._columns = columns
            return self

        def eq(self, _column, _value):
            return self

        def limit(self, _amount):
            return self

        async def execute(self):
            if "rank" in self._columns:
                raise Exception('column "rank" does not exist')
            return SimpleNamespace(
                data=[
                    {
                        "match_id": "BR1_123",
                        "riot_id": "tester#BR1",
                        "summoner_name": "tester#BR1",
                        "champion": "Ahri",
                        "kills": 10,
                        "deaths": 3,
                        "assists": 8,
                        "win": True,
                        "duration_min": 30,
                        "position": "MIDDLE",
                        "cs_per_min": 7.2,
                        "vision_score": 20,
                        "kill_participation_pct": 60.0,
                        "damage_share_pct": 25.0,
                        "items": [6655, 3020],
                        "allies": [{"champion": "JarvanIV", "position": "JUNGLE"}],
                        "puuid": "puuid-1",
                    }
                ]
            )

    class FakeSupabase:
        def table(self, name):
            assert name == "ai_cache"
            return FakeMissingRankQuery()

    async def fake_get_supabase():
        return FakeSupabase()

    monkeypatch.setattr(main, "get_supabase", fake_get_supabase)
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_MAX_REQUESTS", 60)
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_MAX_REQUESTS", 999)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_WINDOW_SECONDS", 60)
    main._public_read_hits.clear()
    main._edge_client_hits.clear()

    client = TestClient(main.app)
    resp = client.get("/match/BR1_123")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["match_id"] == "BR1_123"
    assert payload["rank"] == ""


def test_match_endpoint_sanitizes_invalid_numeric_types(monkeypatch):
    _disable_redis(monkeypatch)

    class FakeQuery:
        def __init__(self, row):
            self._row = row

        def select(self, _columns):
            return self

        def eq(self, _column, _value):
            return self

        def limit(self, _amount):
            return self

        async def execute(self):
            return SimpleNamespace(data=[self._row])

    class FakeSupabase:
        def __init__(self, row):
            self._row = row

        def table(self, name):
            assert name == "ai_cache"
            return FakeQuery(self._row)

    async def fake_get_supabase():
        return FakeSupabase(
            {
                "match_id": "BR1_777",
                "riot_id": "tester#BR1",
                "summoner_name": "tester#BR1",
                "champion": "Ahri",
                "kills": "N/A",
                "deaths": None,
                "assists": "4.0",
                "win": "true",
                "duration_min": "31.2",
                "position": "MIDDLE",
                "cs_per_min": "abc",
                "vision_score": "12",
                "kill_participation_pct": "47.5",
                "damage_share_pct": "",
                "items": "not-a-list",
                "allies": None,
                "puuid": "puuid-1",
                "rank": None,
            }
        )

    monkeypatch.setattr(main, "get_supabase", fake_get_supabase)
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_MAX_REQUESTS", 60)
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_MAX_REQUESTS", 999)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_WINDOW_SECONDS", 60)
    main._public_read_hits.clear()
    main._edge_client_hits.clear()

    client = TestClient(main.app)
    resp = client.get("/match/BR1_777")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["kills"] == 0
    assert payload["deaths"] == 0
    assert payload["assists"] == 4
    assert payload["duration_min"] == 31
    assert payload["cs_per_min"] == 0.0
    assert payload["vision_score"] == 12
    assert payload["kill_participation_pct"] == 47.5
    assert payload["damage_share_pct"] == 0.0
    assert payload["win"] is True
    assert payload["items"] == []
    assert payload["allies"] == []
    assert payload["rank"] == ""


def test_local_upload_rejects_unsafe_match_id(monkeypatch):
    monkeypatch.setattr(main, "LOCAL_APP_TOKEN", "local-token")
    monkeypatch.setattr(main, "APP_TOKEN", "internal-token")
    client = TestClient(main.app)

    resp = client.post(
        "/local/upload",
        headers={"X-App-Token": "local-token"},
        json={
            "riot_id": "tester#BR1",
            "match_id": "..\\..\\loot",
            "events": [
                {
                    "event_type": "kill",
                    "game_time": "00:10",
                    "champion": "Ahri",
                    "detail": "",
                    "assisters": [],
                    "minimap_base64": "",
                }
            ],
            "player_map": {},
        },
    )
    assert resp.status_code == 422


def test_live_upload_cleans_temp_dir_on_failure(monkeypatch, tmp_path):
    async def fake_analyze_postgame(*_args, **_kwargs):
        raise RuntimeError("boom")

    created_dir = tmp_path / "live-upload-dir"

    def fake_mkdtemp(prefix):
        created_dir.mkdir(exist_ok=True)
        return str(created_dir)

    monkeypatch.setattr(main, "APP_TOKEN", "internal-token")
    monkeypatch.setattr(main, "LOCAL_APP_TOKEN", "")
    monkeypatch.setattr(main, "analyze_postgame", fake_analyze_postgame)
    monkeypatch.setattr(main.tempfile, "mkdtemp", fake_mkdtemp)

    client = TestClient(main.app, raise_server_exceptions=False)
    payload = {
        "puuid": "puuid-123",
        "match_id": "BR1_12345",
        "events": [
            {
                "event_type": "kill",
                "game_time_sec": 15,
                "champion": "Ahri",
                "detail": "",
                "assisters": [],
                "objective_stolen": False,
                "minimap_base64": "MDEyMzQ1Njc4OWFiY2RlZg==",
            }
        ],
    }

    resp = client.post("/live/upload", headers={"X-App-Token": "internal-token"}, json=payload)
    assert resp.status_code == 500
    assert not os.path.exists(created_dir)


def _patch_analyze_pipeline_dependencies(monkeypatch, match_id: str):
    class FakeRiotClient:
        def __init__(self, fixed_match_id: str):
            self._match_id = fixed_match_id

        async def get_summoner_by_name(self, game_name, tag_line):
            return SimpleNamespace(summoner_id="sid-1", name=f"{game_name}#{tag_line}", puuid="puuid-1")

        async def get_summoner_rank(self, summoner_id):
            return "GOLD IV"


        async def get_ranked_entries(self, _puuid):
            return []

        async def get_match_history(self, puuid, count=10):
            return [self._match_id]

        async def get_match(self, requested_match_id):
            assert requested_match_id == self._match_id
            return SimpleNamespace(game_version="14.1")

        async def get_match_timeline(self, requested_match_id):
            assert requested_match_id == self._match_id
            return SimpleNamespace(frames=[])

    class FakeContextBuilder:
        def __init__(self, target_puuid, rank):
            self.target_puuid = target_puuid
            self.rank = rank

        def build(self, match, timeline, item_names=None):
            return context_builder.MatchContext(
                match_id=match_id,
                player_riot_id="tester#BR1",
                player_champion="Ahri",
                role="MIDDLE",
                win=True,
                duration_min=29.5,
                kda="9/2/7",
                cs_per_min=7.8,
                vision_score=23,
                kill_participation_pct=61.0,
                damage_share_pct=27.5,
                time_dead_pct=3.1,
                rank="GOLD IV",
            )

    async def fake_get_item_names(_game_version):
        return {}

    async def fake_generate_feedback(self, _context):
        return {"insights": [{"category": "PERFORMANCE", "severity": "LOW"}], "feedback_geral": "ok"}

    async def fake_get_ai_cache(*_args, **_kwargs):
        return None

    async def fake_set_ai_cache(*_args, **_kwargs):
        return None

    monkeypatch.setattr(main, "INTERNAL_BEARER_TOKEN", "bearer-interno")
    monkeypatch.setattr(main, "RIOT_KEY", "riot-key")
    monkeypatch.setattr(main, "GEMINI_KEY", "gemini-key")
    monkeypatch.setattr(main, "RiotMatchClient", lambda api_key: FakeRiotClient(match_id))
    monkeypatch.setattr(riot_client, "RiotMatchClient", lambda api_key: FakeRiotClient(match_id))
    monkeypatch.setattr(riot_client, "get_item_names", fake_get_item_names)
    monkeypatch.setattr(context_builder, "ContextBuilder", FakeContextBuilder)
    monkeypatch.setattr(coach_ai.CoachAI, "generate_feedback", fake_generate_feedback)
    monkeypatch.setattr(coach_ai, "_get_ai_cache", fake_get_ai_cache)
    monkeypatch.setattr(coach_ai, "_set_ai_cache", fake_set_ai_cache)


def test_analyze_route_uses_shared_evidence_pipeline(monkeypatch):
    _patch_analyze_pipeline_dependencies(monkeypatch, match_id="BR1_PIPE_1")

    bundle_calls = []
    stage_calls = []
    real_build = evidence_pipeline.build_analysis_evidence_bundle
    real_gate = evidence_pipeline.gate_pipeline_stage

    def spy_build(*args, **kwargs):
        bundle_calls.append((args, kwargs))
        return real_build(*args, **kwargs)

    def spy_gate(stage, *args, **kwargs):
        stage_calls.append(stage.value)
        return real_gate(stage, *args, **kwargs)

    monkeypatch.setattr(coach_ai, "build_analysis_evidence_bundle", spy_build)
    monkeypatch.setattr(coach_ai, "gate_pipeline_stage", spy_gate)

    client = TestClient(main.app)
    resp = client.post(
        "/analyze",
        headers={"Authorization": "Bearer bearer-interno"},
        json={"game_name": "tester", "tag_line": "BR1", "match_index": 0},
    )

    assert resp.status_code == 200
    assert bundle_calls
    assert "analysis_generation" in stage_calls
    assert "output_validation" in stage_calls
    assert "delivery" in stage_calls


def test_local_upload_uses_shared_evidence_pipeline(monkeypatch):
    captured = {}
    saved_pending = {}

    async def fake_build_match_context(*_args, **_kwargs):
        return None

    def fake_create_task(coro):
        captured["coro"] = coro
        return SimpleNamespace(cancel=lambda: None)

    async def fake_is_ranked_match(_match_id):
        return True

    async def fake_save_pending(match_id, riot_id, *, local_events, image_paths, player_map, source, expires_at=None):
        saved_pending["payload"] = {
            "match_id": match_id,
            "riot_id": riot_id,
            "local_events": local_events,
            "image_paths": image_paths,
            "player_map": player_map,
            "source": source,
            "expires_at": expires_at,
        }

    async def forbidden_analyze_postgame(*_args, **_kwargs):
        raise AssertionError("localhost_only nao deveria executar analyze_postgame")

    monkeypatch.setattr(main, "LOCAL_APP_TOKEN", "local-token")
    monkeypatch.setattr(main, "APP_TOKEN", "internal-token")
    monkeypatch.setattr(main.asyncio, "create_task", fake_create_task)
    monkeypatch.setattr(main, "_is_ranked_match", fake_is_ranked_match)
    monkeypatch.setattr(main, "_build_match_context_for_local_upload", fake_build_match_context)
    monkeypatch.setattr(main, "save_pending_local_evidence", fake_save_pending)
    monkeypatch.setattr(main, "analyze_postgame", forbidden_analyze_postgame)

    client = TestClient(main.app)
    payload = {
        "riot_id": "tester#BR1",
        "match_id": "BR1_PIPE_2",
        "events": [
            {
                "event_type": "kill",
                "game_time": "00:10",
                "champion": "Ahri",
                "detail": "test",
                "assisters": [],
                "minimap_base64": "MDEyMzQ1Njc4OWFiY2RlZg==",
            }
        ],
        "player_map": {"tester#BR1": "Ahri"},
    }

    resp = client.post("/local/upload", headers={"X-App-Token": "local-token"}, json=payload)
    assert resp.status_code == 200
    assert "coro" in captured

    asyncio.run(captured["coro"])

    assert saved_pending["payload"]["match_id"] == "BR1_PIPE_2"
    assert saved_pending["payload"]["riot_id"] == "tester#BR1"
    assert saved_pending["payload"]["source"] == "localhost_only"
    assert main._local_jobs["tester#BR1"] == "BR1_PIPE_2"
    main._local_jobs.pop("tester#BR1", None)


def test_local_upload_resolves_riot_context_and_saves_analysis(monkeypatch):
    saved = {}
    snapshots = []
    deleted = []

    async def fake_is_ranked_match(_match_id):
        return True

    async def fake_build_match_context(_riot_id, match_id):
        assert match_id == "BR1_PIPE_4"
        return context_builder.MatchContext(
            match_id=match_id,
            player_riot_id="tester#BR1",
            player_champion="Ahri",
            role="MIDDLE",
            win=True,
            duration_min=29.5,
            kda="9/2/7",
            cs_per_min=7.8,
            vision_score=23,
            kill_participation_pct=61.0,
            damage_share_pct=27.5,
            time_dead_pct=3.1,
            rank="GOLD IV",
        )

    async def fake_analyze_postgame(events, image_paths, bundle=None, match_context=""):
        assert bundle is not None
        assert bundle.source.value == "riot_plus_local"
        assert bundle.match_context is not None
        assert len(events) == 1
        assert len(image_paths) == 1
        return "analise pronta"

    async def fake_save_coaching_analysis(match_id, analysis, riot_id=""):
        saved["match_id"] = match_id
        saved["analysis"] = analysis
        saved["riot_id"] = riot_id

    async def fake_save_pipeline_snapshot(match_id, riot_id, snapshot):
        snapshots.append((match_id, riot_id, snapshot))

    async def fake_get_pending(_match_id, _riot_id):
        return None

    async def fake_delete_pending(match_id, riot_id):
        deleted.append((match_id, riot_id))

    monkeypatch.setattr(main, "_is_ranked_match", fake_is_ranked_match)
    monkeypatch.setattr(main, "_build_match_context_for_local_upload", fake_build_match_context)
    monkeypatch.setattr(main, "analyze_postgame", fake_analyze_postgame)
    monkeypatch.setattr(main, "save_coaching_analysis", fake_save_coaching_analysis)
    monkeypatch.setattr(main, "save_pipeline_snapshot", fake_save_pipeline_snapshot)
    monkeypatch.setattr(main, "get_pending_local_evidence", fake_get_pending)
    monkeypatch.setattr(main, "delete_pending_local_evidence", fake_delete_pending)

    event = main.LocalEventUpload(
        event_type="kill",
        game_time="00:10",
        champion="Ahri",
        detail="test",
        assisters=[],
        minimap_base64="MDEyMzQ1Njc4OWFiY2RlZg==",
    )

    asyncio.run(main._process_local_upload("tester#BR1", [event], "BR1_PIPE_4", {"tester#BR1": "Ahri"}))

    assert saved == {
        "match_id": "BR1_PIPE_4",
        "analysis": "analise pronta",
        "riot_id": "tester#BR1",
    }
    assert snapshots[-1][2]["external_status"] == "ready"
    assert snapshots[-1][2]["source"] == "riot_plus_local"
    assert deleted == []
    assert main._local_jobs["tester#BR1"] == "BR1_PIPE_4"
    main._local_jobs.pop("tester#BR1", None)


def test_riot_analysis_joins_pending_local_evidence(monkeypatch):
    _patch_analyze_pipeline_dependencies(monkeypatch, match_id="BR1_PIPE_3")

    sources = []
    deleted = []

    async def fake_get_pending(match_id, riot_id):
        assert match_id == "BR1_PIPE_3"
        assert riot_id == "tester#BR1"
        return {
            "match_id": match_id,
            "riot_id": riot_id,
            "local_events": [
                {
                    "event_type": "kill",
                    "game_time": "12:34",
                    "champion": "Ahri",
                    "detail": "picked support",
                    "assisters": ["Jarvan IV"],
                }
            ],
            "image_paths": [],
            "player_map": {"tester#BR1": "Ahri"},
        }

    async def fake_delete_pending(match_id, riot_id):
        deleted.append((match_id, riot_id))

    real_build = evidence_pipeline.build_analysis_evidence_bundle

    def spy_build(*args, **kwargs):
        snapshot = real_build(*args, **kwargs)
        if snapshot.bundle is not None:
            sources.append(snapshot.bundle.source.value)
        return snapshot

    monkeypatch.setattr(coach_ai, "get_pending_local_evidence", fake_get_pending)
    monkeypatch.setattr(coach_ai, "delete_pending_local_evidence", fake_delete_pending)
    monkeypatch.setattr(coach_ai, "build_analysis_evidence_bundle", spy_build)

    client = TestClient(main.app)
    resp = client.post(
        "/analyze",
        headers={"Authorization": "Bearer bearer-interno"},
        json={"game_name": "tester", "tag_line": "BR1", "match_index": 0},
    )

    assert resp.status_code == 200
    assert "riot_plus_local" in sources
    assert deleted == [("BR1_PIPE_3", "tester#BR1")]


def test_coaching_status_exposes_safe_external_states(monkeypatch):
    _disable_redis(monkeypatch)
    monkeypatch.setattr(main, "SUPABASE_URL", "")
    monkeypatch.setattr(main, "SUPABASE_KEY", "")
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_MAX_REQUESTS", 60)
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_MAX_REQUESTS", 999)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_WINDOW_SECONDS", 60)
    main._public_read_hits.clear()
    main._edge_client_hits.clear()

    snapshots = {
        "BR1_READY": ready_snapshot(),
        "BR1_PENDING": pending_snapshot(),
        "BR1_INSUF": insufficient_snapshot(),
        "BR1_FAILED": failed_snapshot(),
    }

    async def fake_get_pipeline_snapshot(match_id, riot_id):
        return snapshots.get(match_id)

    async def fake_get_pending_local(_match_id, _riot_id):
        return None

    monkeypatch.setattr(main, "get_pipeline_snapshot", fake_get_pipeline_snapshot)
    monkeypatch.setattr(main, "get_pending_local_evidence", fake_get_pending_local)

    client = TestClient(main.app)
    resp = client.get(
        "/coaching/status",
        params={
            "ids": "BR1_READY,BR1_PENDING,BR1_INSUF,BR1_FAILED",
            "riot_id": "tester#BR1",
        },
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["BR1_READY"]["status"] == "ready"
    assert payload["BR1_PENDING"]["status"] == "pending"
    assert payload["BR1_INSUF"]["status"] == "insufficient_data"
    assert payload["BR1_FAILED"]["status"] == "failed"
    for mid in payload:
        assert payload[mid]["status"] in {"ready", "pending", "insufficient_data", "failed"}
        assert "reason_codes" not in payload[mid]
        assert "details" not in payload[mid]
        assert "message" in payload[mid]


def test_coaching_get_hides_internal_reason_codes(monkeypatch):
    _disable_redis(monkeypatch)
    monkeypatch.setattr(main, "SUPABASE_URL", "")
    monkeypatch.setattr(main, "SUPABASE_KEY", "")
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_MAX_REQUESTS", 60)
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_MAX_REQUESTS", 999)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_WINDOW_SECONDS", 60)
    main._public_read_hits.clear()
    main._edge_client_hits.clear()

    async def fake_get_coaching_analysis(_match_id, riot_id=""):
        return None

    async def fake_get_pipeline_snapshot(_match_id, riot_id):
        return {
            "stage": "analysis_generation",
            "status": "blocked",
            "reason_codes": ["missing_match_context"],
            "external_status": "insufficient_data",
            "has_analysis_text": False,
        }

    async def fake_get_pending_local(_match_id, _riot_id):
        return None

    monkeypatch.setattr(main, "get_coaching_analysis", fake_get_coaching_analysis)
    monkeypatch.setattr(main, "get_pipeline_snapshot", fake_get_pipeline_snapshot)
    monkeypatch.setattr(main, "get_pending_local_evidence", fake_get_pending_local)

    client = TestClient(main.app)
    resp = client.get("/coaching/BR1_HIDE", params={"riot_id": "tester#BR1"})
    assert resp.status_code == 200

    payload = resp.json()
    assert payload["status"] == "insufficient_data"
    assert payload["has_analysis"] is False
    assert set(payload.keys()) == {"match_id", "has_analysis", "status", "analysis", "message"}
    assert "reason_codes" not in payload
    assert "details" not in payload


def test_coaching_get_blocks_analysis_without_local_evidence(monkeypatch):
    _disable_redis(monkeypatch)
    monkeypatch.setattr(main, "SUPABASE_URL", "")
    monkeypatch.setattr(main, "SUPABASE_KEY", "")
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_MAX_REQUESTS", 60)
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_MAX_REQUESTS", 999)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_WINDOW_SECONDS", 60)
    main._public_read_hits.clear()
    main._edge_client_hits.clear()

    async def fake_get_coaching_analysis(_match_id, riot_id=""):
        return "analise preexistente"

    async def fake_get_pipeline_snapshot(_match_id, riot_id):
        return ready_snapshot() | {"source": "riot_only"}

    async def fake_get_pending_local(_match_id, _riot_id):
        return None

    monkeypatch.setattr(main, "get_coaching_analysis", fake_get_coaching_analysis)
    monkeypatch.setattr(main, "get_pipeline_snapshot", fake_get_pipeline_snapshot)
    monkeypatch.setattr(main, "get_pending_local_evidence", fake_get_pending_local)

    client = TestClient(main.app)
    resp = client.get("/coaching/BR1_NO_LOCAL", params={"riot_id": "tester#BR1"})
    assert resp.status_code == 200

    payload = resp.json()
    assert payload["status"] == "insufficient_data"
    assert payload["has_analysis"] is False
    assert payload["analysis"] is None
    assert payload["message"] == "Coach indisponivel, baixe o app e jogue uma partida."


def test_coaching_get_hides_analysis_on_riot_id_mismatch(monkeypatch):
    _disable_redis(monkeypatch)
    monkeypatch.setattr(main, "SUPABASE_URL", "")
    monkeypatch.setattr(main, "SUPABASE_KEY", "")
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_MAX_REQUESTS", 60)
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_MAX_REQUESTS", 999)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_WINDOW_SECONDS", 60)
    main._public_read_hits.clear()
    main._edge_client_hits.clear()

    async def fake_get_coaching_analysis(_match_id, riot_id=""):
        return "analise privada do dono"

    async def fake_get_pipeline_snapshot(_match_id, riot_id):
        if riot_id == "owner#BR1":
            return ready_snapshot()
        return insufficient_snapshot()

    async def fake_get_pending_local(_match_id, _riot_id):
        return None

    monkeypatch.setattr(main, "get_coaching_analysis", fake_get_coaching_analysis)
    monkeypatch.setattr(main, "get_pipeline_snapshot", fake_get_pipeline_snapshot)
    monkeypatch.setattr(main, "get_pending_local_evidence", fake_get_pending_local)

    client = TestClient(main.app)
    owner = client.get("/coaching/BR1_OWNER", params={"riot_id": "owner#BR1"})
    viewer = client.get("/coaching/BR1_OWNER", params={"riot_id": "viewer#BR1"})

    assert owner.status_code == 200
    owner_payload = owner.json()
    assert owner_payload["status"] == "ready"
    assert owner_payload["has_analysis"] is True
    assert owner_payload["analysis"] == "analise privada do dono"

    assert viewer.status_code == 200
    viewer_payload = viewer.json()
    assert viewer_payload["status"] == "insufficient_data"
    assert viewer_payload["has_analysis"] is False
    assert viewer_payload["analysis"] is None
    assert viewer_payload["message"] == "Coach indisponivel, baixe o app e jogue uma partida."


def test_coaching_status_hides_ready_on_riot_id_mismatch(monkeypatch):
    _disable_redis(monkeypatch)
    monkeypatch.setattr(main, "SUPABASE_URL", "")
    monkeypatch.setattr(main, "SUPABASE_KEY", "")
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_MAX_REQUESTS", 60)
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_MAX_REQUESTS", 999)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_WINDOW_SECONDS", 60)
    main._public_read_hits.clear()
    main._edge_client_hits.clear()

    async def fake_get_pipeline_snapshot(match_id, riot_id):
        if riot_id == "owner#BR1":
            return ready_snapshot()
        return insufficient_snapshot()

    async def fake_get_pending_local(_match_id, _riot_id):
        return None

    monkeypatch.setattr(main, "get_pipeline_snapshot", fake_get_pipeline_snapshot)
    monkeypatch.setattr(main, "get_pending_local_evidence", fake_get_pending_local)

    client = TestClient(main.app)
    owner = client.get("/coaching/status", params={"ids": "BR1_OWNER", "riot_id": "owner#BR1"})
    viewer = client.get("/coaching/status", params={"ids": "BR1_OWNER", "riot_id": "viewer#BR1"})

    assert owner.status_code == 200
    assert viewer.status_code == 200
    assert owner.json()["BR1_OWNER"]["status"] == "ready"
    assert owner.json()["BR1_OWNER"]["has_analysis"] is True
    assert viewer.json()["BR1_OWNER"]["status"] == "insufficient_data"
    assert viewer.json()["BR1_OWNER"]["has_analysis"] is False


def test_coaching_status_requires_riot_id_when_configured(monkeypatch):
    _disable_redis(monkeypatch)
    monkeypatch.setattr(main, "SUPABASE_URL", "")
    monkeypatch.setattr(main, "SUPABASE_KEY", "")
    monkeypatch.setattr(main, "REQUIRE_RIOT_ID_FOR_COACHING", True)
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_MAX_REQUESTS", 60)
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_MAX_REQUESTS", 999)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_WINDOW_SECONDS", 60)
    main._public_read_hits.clear()
    main._edge_client_hits.clear()

    client = TestClient(main.app)
    response = client.get("/coaching/status", params={"ids": "BR1_REQUIRED"})
    assert response.status_code == 422


def test_coaching_regenerate_is_blocked_for_non_paying(monkeypatch):
    _disable_redis(monkeypatch)
    monkeypatch.setattr(main, "SUPABASE_URL", "")
    monkeypatch.setattr(main, "SUPABASE_KEY", "")
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_MAX_REQUESTS", 60)
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_MAX_REQUESTS", 999)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_WINDOW_SECONDS", 60)
    main._public_read_hits.clear()
    main._edge_client_hits.clear()

    captured = {}

    async def fake_save_pipeline_snapshot(match_id, riot_id, snapshot):
        captured["match_id"] = match_id
        captured["riot_id"] = riot_id
        captured["snapshot"] = snapshot

    monkeypatch.setattr(main, "save_pipeline_snapshot", fake_save_pipeline_snapshot)

    client = TestClient(main.app)
    resp = client.post("/coaching/BR1_123/regenerate", params={"riot_id": "tester#BR1"})
    assert resp.status_code == 200
    payload = resp.json()

    assert payload["status"] == "blocked"
    assert payload["match_id"] == "BR1_123"
    assert "pago" in payload["message"].lower() or "premium" in payload["message"].lower()
    assert captured["snapshot"]["external_status"] == "insufficient_data"
