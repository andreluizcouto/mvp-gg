from fastapi import HTTPException
import pytest

import main


class DummyRequest:
    def __init__(self, token):
        self.headers = {"X-App-Token": token}
        self.client = type("Client", (), {"host": "127.0.0.1"})


def test_local_auth_rejects_invalid_token(monkeypatch):
    monkeypatch.setattr(main, "LOCAL_APP_TOKEN", "expected-token")
    with pytest.raises(HTTPException) as exc:
        main._require_local_app_auth(DummyRequest("wrong-token"))
    assert exc.value.status_code == 401


def test_local_auth_accepts_valid_token(monkeypatch):
    monkeypatch.setattr(main, "LOCAL_APP_TOKEN", "expected-token")
    main._require_local_app_auth(DummyRequest("expected-token"))
