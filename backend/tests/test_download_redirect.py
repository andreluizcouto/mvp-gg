from fastapi.testclient import TestClient

import main


def _disable_redis(monkeypatch):
    monkeypatch.setattr(main, "REDIS_URL", "")
    monkeypatch.setattr(main, "_redis_rate_limit_client", None)
    monkeypatch.setattr(main, "_redis_fallback_warned", False)


def _reset_public_limits(monkeypatch):
    _disable_redis(monkeypatch)
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_MAX_REQUESTS", 60)
    monkeypatch.setattr(main, "PUBLIC_READ_RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_MAX_REQUESTS", 999)
    monkeypatch.setattr(main, "EDGE_CLIENT_RATE_LIMIT_WINDOW_SECONDS", 60)
    main._public_read_hits.clear()
    main._edge_client_hits.clear()


def test_download_redirect_uses_backend_managed_url(monkeypatch):
    _reset_public_limits(monkeypatch)
    monkeypatch.setattr(main, "DOWNLOAD_APP_URL", "https://downloads.example.com/mvpgg-app.exe")

    client = TestClient(main.app)
    resp = client.get("/downloads/app", follow_redirects=False)

    assert resp.status_code == 307
    assert resp.headers["location"] == "https://downloads.example.com/mvpgg-app.exe"


def test_download_redirect_requires_configured_https_url(monkeypatch):
    _reset_public_limits(monkeypatch)
    monkeypatch.setattr(main, "DOWNLOAD_APP_URL", "http://downloads.example.com/mvpgg-app.exe")

    client = TestClient(main.app)
    resp = client.get("/downloads/app", follow_redirects=False)

    assert resp.status_code == 503
    assert resp.json()["detail"] == "Download indisponivel no momento."
