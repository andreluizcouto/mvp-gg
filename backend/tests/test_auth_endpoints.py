from datetime import UTC, datetime

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
    db._user_identity_store.clear()
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
    yield


def _authz(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def test_login_success_returns_access_refresh_and_session_id():
    client = TestClient(main.app)
    response = client.post("/auth/login", json={"email": "user@test.com", "password": "password-123"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"]
    assert payload["refresh_token"]
    assert payload["session_id"]
    assert payload["plan_tier"] == "pro"


def test_refresh_rotates_tokens():
    client = TestClient(main.app)
    login = client.post("/auth/login", json={"email": "user@test.com", "password": "password-123"})
    assert login.status_code == 200
    original = login.json()

    refreshed = client.post("/auth/refresh", json={"refresh_token": original["refresh_token"]})
    assert refreshed.status_code == 200
    refreshed_payload = refreshed.json()
    assert refreshed_payload["refresh_token"] != original["refresh_token"]
    assert refreshed_payload["session_id"] != original["session_id"]

    old_refresh = client.post("/auth/refresh", json={"refresh_token": original["refresh_token"]})
    assert old_refresh.status_code == 401


def test_logout_revokes_session_and_protected_call_becomes_401():
    client = TestClient(main.app)
    login = client.post("/auth/login", json={"email": "user@test.com", "password": "password-123"}).json()

    me_before = client.get("/auth/me", headers=_authz(login["access_token"]))
    assert me_before.status_code == 200

    logout = client.post(
        "/auth/logout",
        headers=_authz(login["access_token"]),
        json={"refresh_token": login["refresh_token"]},
    )
    assert logout.status_code == 200

    me_after = client.get("/auth/me", headers=_authz(login["access_token"]))
    assert me_after.status_code == 401
    assert me_after.json()["detail"] == "Sessão inválida ou expirada."


def test_auth_me_lists_only_owned_matches_via_identity_mapping():
    client = TestClient(main.app)
    login = client.post("/auth/login", json={"email": "user@test.com", "password": "password-123"}).json()

    user_id = login["user_id"]
    db._pipeline_snapshot_store[("BR1_OWNED", "user@test.com")] = {
        "status": "ready",
        "external_status": "ready",
        "has_analysis_text": True,
    }
    db._pipeline_snapshot_store[("BR1_FOREIGN", "other@test.com")] = {
        "status": "ready",
        "external_status": "ready",
        "has_analysis_text": True,
    }

    payload = client.get("/auth/me", headers=_authz(login["access_token"])).json()
    assert payload["user_id"] == user_id
    assert "BR1_OWNED" in payload["matches_with_analysis"]
    assert "BR1_FOREIGN" not in payload["matches_with_analysis"]
