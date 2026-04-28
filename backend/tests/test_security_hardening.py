import pytest
from fastapi import HTTPException
from starlette.requests import Request

import main


def _make_request(
    headers: dict[str, str] | None = None,
    scheme: str = "https",
    host: str = "api.test",
    client_host: str = "127.0.0.1",
) -> Request:
    raw_headers = []
    for key, value in (headers or {}).items():
        raw_headers.append((key.lower().encode("latin-1"), value.encode("latin-1")))
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": raw_headers,
        "scheme": scheme,
        "server": (host, 443),
        "client": (client_host, 12345),
        "query_string": b"",
        "http_version": "1.1",
    }
    return Request(scope)


def test_parse_match_ids_dedupes_and_validates():
    ids = main._parse_match_ids("BR1_1, BR1_2,BR1_1")
    assert ids == ["BR1_1", "BR1_2"]


def test_parse_match_ids_rejects_too_many(monkeypatch):
    monkeypatch.setattr(main, "MAX_IDS_PER_STATUS_QUERY", 1)
    with pytest.raises(HTTPException) as exc:
        main._parse_match_ids("BR1_1,BR1_2")
    assert exc.value.status_code == 422


def test_validate_riot_id_required_rejects_empty():
    with pytest.raises(HTTPException) as exc:
        main._validate_riot_id("", required=True)
    assert exc.value.status_code == 422


def test_validate_match_id_rejects_path_traversal():
    with pytest.raises(HTTPException) as exc:
        main._validate_match_id("..\\..\\loot")
    assert exc.value.status_code == 422


def test_require_internal_auth_accepts_bearer(monkeypatch):
    monkeypatch.setattr(main, "INTERNAL_BEARER_TOKEN", "token-interno")
    req = _make_request(headers={"Authorization": "Bearer token-interno"})
    main._require_internal_auth(req)


def test_require_internal_auth_rejects_without_valid_token(monkeypatch):
    monkeypatch.setattr(main, "INTERNAL_BEARER_TOKEN", "token-interno")
    req = _make_request(headers={"Authorization": "Bearer invalido"})
    with pytest.raises(HTTPException) as exc:
        main._require_internal_auth(req)
    assert exc.value.status_code == 401


def test_local_app_auth_uses_dedicated_token(monkeypatch):
    monkeypatch.setattr(main, "INTERNAL_BEARER_TOKEN", "token-interno")
    monkeypatch.setattr(main, "LOCAL_APP_TOKEN", "local-token")

    req = _make_request(headers={"X-App-Token": "local-token"})
    main._require_local_app_auth(req)

    with pytest.raises(HTTPException) as exc:
        main._require_internal_auth(req)
    assert exc.value.status_code == 401


def test_local_app_auth_rejects_non_local_token(monkeypatch):
    monkeypatch.setattr(main, "LOCAL_APP_TOKEN", "local-token")
    req = _make_request(headers={"X-App-Token": "other-token"})
    with pytest.raises(HTTPException) as exc:
        main._require_local_app_auth(req)
    assert exc.value.status_code == 401


def test_client_ip_ignores_spoofed_forwarded_for_from_public_client():
    req = _make_request(
        headers={"X-Forwarded-For": "8.8.8.8"},
        client_host="198.51.100.20",
    )
    assert main._client_ip(req) == "198.51.100.20"


def test_client_ip_trusts_forwarded_for_from_private_proxy():
    req = _make_request(
        headers={"X-Forwarded-For": "203.0.113.9"},
        client_host="10.0.0.8",
    )
    assert main._client_ip(req) == "203.0.113.9"
