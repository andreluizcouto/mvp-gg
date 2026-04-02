from fastapi.testclient import TestClient
import pytest

import db
import main


@pytest.fixture(autouse=True)
def _reset_auth_state(monkeypatch):
    db._auth_session_store.clear()
    db._entitlement_store.clear()
    db._usage_operation_store.clear()
    db._users_store_by_email.clear()
    db._users_store_by_id.clear()
    main._auth_rate_limit_hits.clear()
    main._auth_access_index.clear()
    main._bootstrap_auth_seeded = False

    monkeypatch.setattr(main, "AUTH_BOOTSTRAP_EMAIL", "user@test.com")
    monkeypatch.setattr(main, "AUTH_BOOTSTRAP_PASSWORD", "password-123")
    monkeypatch.setattr(main, "AUTH_BOOTSTRAP_PLAN_TIER", "pro")
    monkeypatch.setattr(main, "AUTH_BOOTSTRAP_ANALYSIS_QUOTA", 20)
    monkeypatch.setattr(main, "ACCESS_TOKEN_TTL_SECONDS", 600)
    monkeypatch.setattr(main, "REFRESH_TOKEN_TTL_SECONDS", 3600)
    monkeypatch.setattr(main, "AUTH_RATE_LIMIT_MAX_REQUESTS", 100)
    monkeypatch.setattr(main, "AUTH_RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(main, "REQUIRE_RIOT_ID_FOR_COACHING", False)
    yield


def _authz(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def test_coaching_get_rejects_unauthenticated_caller():
    client = TestClient(main.app)
    response = client.get("/coaching/BR1_123")
    assert response.status_code == 401
    assert response.json()["detail"] == "Autenticação obrigatória."


def test_coaching_get_rejects_without_entitlement(monkeypatch):
    client = TestClient(main.app)
    login = client.post("/auth/login", json={"email": "user@test.com", "password": "password-123"}).json()
    db._entitlement_store[login["user_id"]]["active"] = False
    response = client.get("/coaching/BR1_123", headers=_authz(login["access_token"]))
    assert response.status_code == 403
    assert response.json()["detail"] == "Acesso negado para análises IA."


def test_coaching_get_returns_consistent_status_for_entitled_user(monkeypatch):
    client = TestClient(main.app)
    login = client.post("/auth/login", json={"email": "user@test.com", "password": "password-123"}).json()

    async def fake_get_analysis(_match_id: str, riot_id: str = ""):
        return None

    async def fake_get_snapshot(_match_id: str, riot_id: str = ""):
        return {"status": "blocked", "external_status": "failed", "has_analysis_text": False}

    monkeypatch.setattr(main, "get_coaching_analysis", fake_get_analysis)
    monkeypatch.setattr(main, "get_pipeline_snapshot", fake_get_snapshot)

    response = client.get("/coaching/BR1_123", headers=_authz(login["access_token"]))
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"ready", "pending", "failed", "insufficient_data"}
    assert payload["status"] == "failed"
