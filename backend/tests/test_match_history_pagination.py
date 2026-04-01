from types import SimpleNamespace

from fastapi.testclient import TestClient

import main
from schemas import MatchHistoryItem


def _disable_redis(monkeypatch):
    monkeypatch.setattr(main, "REDIS_URL", "")
    monkeypatch.setattr(main, "_redis_rate_limit_client", None)
    monkeypatch.setattr(main, "_redis_fallback_warned", False)


def test_summoner_history_supports_pagination(monkeypatch):
    class FakeRiotClient:
        def __init__(self, *_args, **_kwargs):
            self.calls = []

        async def get_summoner_by_name(self, game_name, tag_line):
            return SimpleNamespace(summoner_id="sid-1", name=f"{game_name}#{tag_line}", puuid="puuid-1")

        async def get_summoner_rank(self, _summoner_id):
            return "GOLD IV"

        async def get_match_history(self, puuid, count=10, start=0, queue=None):
            self.calls.append((puuid, start, count, queue))
            return [f"BR1_{i}" for i in range(start, start + count)]

    async def fake_fetch_match_details(puuid, match_id, index, _api_key, _client):
        return MatchHistoryItem(
            match_id=match_id,
            index=index,
            champion="Ahri",
            kills=10,
            deaths=2,
            assists=8,
            win=True,
            duration_min=30,
            position="MIDDLE",
        )

    fake_client = FakeRiotClient()
    _disable_redis(monkeypatch)
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_MAX_REQUESTS", 60)
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_MAX_REQUESTS", 999)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(main, "RiotMatchClient", lambda api_key: fake_client)
    monkeypatch.setattr(main, "fetch_match_details", fake_fetch_match_details)
    main._public_read_hits.clear()
    main._edge_client_hits.clear()

    client = TestClient(main.app)
    resp = client.get("/summoner/tester/BR1", params={"start": 10, "count": 10})

    assert resp.status_code == 200
    payload = resp.json()
    assert len(payload["matches"]) == 10
    assert payload["matches"][0]["match_id"] == "BR1_10"
    assert payload["matches"][0]["index"] == 10
    assert payload["has_more"] is True
    assert payload["next_offset"] == 20
    assert fake_client.calls == [("puuid-1", 10, 11, None)]
    assert set(payload["matches"][0].keys()) >= {
        "match_id",
        "index",
        "champion",
        "kills",
        "deaths",
        "assists",
        "win",
        "duration_min",
        "position",
    }


def test_refresh_summoner_history_supports_pagination(monkeypatch):
    class FakeRiotClient:
        def __init__(self, *_args, **_kwargs):
            self.calls = []
            self.summoner_id = "sid-refresh"

        async def get_summoner_by_name(self, game_name, tag_line):
            return SimpleNamespace(
                summoner_id=self.summoner_id,
                name=f"{game_name}#{tag_line}",
                puuid="puuid-refresh",
            )

        async def get_summoner_rank(self, _summoner_id):
            return "PLATINUM I"

        async def get_match_history(self, puuid, count=10, start=0, queue=None):
            self.calls.append((puuid, start, count, queue))
            return [f"BR1_REFRESH_{i}" for i in range(start, start + count)]

    async def fake_fetch_match_details(puuid, match_id, index, _api_key, _client):
        return MatchHistoryItem(
            match_id=match_id,
            index=index,
            champion="LeBlanc",
            kills=12,
            deaths=4,
            assists=9,
            win=True,
            duration_min=34,
            position="MIDDLE",
        )

    invalidated = []

    def fake_cache_invalidate(key: str):
        invalidated.append(key)

    fake_client = FakeRiotClient()
    _disable_redis(monkeypatch)
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_MAX_REQUESTS", 60)
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_MAX_REQUESTS", 999)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(main, "RiotMatchClient", lambda api_key: fake_client)
    monkeypatch.setattr(main, "fetch_match_details", fake_fetch_match_details)
    monkeypatch.setattr(main, "cache_invalidate", fake_cache_invalidate)
    main._public_read_hits.clear()
    main._edge_client_hits.clear()

    client = TestClient(main.app)
    resp = client.get("/summoner/tester/BR1/refresh", params={"start": 5, "count": 10})

    assert resp.status_code == 200
    payload = resp.json()
    assert len(payload["matches"]) == 10
    assert payload["matches"][0]["match_id"] == "BR1_REFRESH_5"
    assert payload["matches"][0]["index"] == 5
    assert payload["has_more"] is True
    assert payload["next_offset"] == 15
    assert fake_client.calls == [("puuid-refresh", 5, 11, None)]
    assert f"history_puuid-refresh" in invalidated
    assert f"rank_{fake_client.summoner_id}" in invalidated


def test_summoner_history_rejects_invalid_pagination(monkeypatch):
    _disable_redis(monkeypatch)
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_MAX_REQUESTS", 60)
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_MAX_REQUESTS", 999)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_WINDOW_SECONDS", 60)
    main._public_read_hits.clear()
    main._edge_client_hits.clear()

    client = TestClient(main.app)

    bad_start = client.get("/summoner/tester/BR1", params={"start": -1, "count": 10})
    bad_count = client.get("/summoner/tester/BR1", params={"start": 0, "count": 99})

    assert bad_start.status_code == 422
    assert bad_count.status_code == 422
