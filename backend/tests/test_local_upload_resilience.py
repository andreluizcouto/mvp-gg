import asyncio

import pytest

import coach_app
import main


@pytest.mark.asyncio
async def test_local_upload_retries_then_reports_terminal_failure(monkeypatch):
    class FakeResponse:
        status_code = 200

        def json(self):
            return {"ready": False, "status": "failed", "error": "processing failed"}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.calls = 0

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, *args, **kwargs):
            self.calls += 1
            if self.calls < 3:
                raise main.httpx.TimeoutException("temporary timeout")
            return FakeResponse()

    class FakeTray:
        def __init__(self):
            self.states = []

        def set_state(self, state, detail=None):
            self.states.append((state, detail))

    monkeypatch.setattr(coach_app.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(coach_app, "POLL_INTERVAL", 0)

    tray = FakeTray()
    await coach_app._poll_status("riot#br1", tray)
    assert tray.states == []


@pytest.mark.asyncio
async def test_local_status_returns_failed_when_job_state_failed(monkeypatch):
    main._local_jobs.clear()
    main._local_job_states.clear()
    main._local_job_states["user#br1"] = {"state": "failed", "error": "request_id=req-123"}

    class DummyRequest:
        headers = {"X-App-Token": "token"}
        client = type("Client", (), {"host": "127.0.0.1"})

    monkeypatch.setattr(main, "LOCAL_APP_TOKEN", "token")
    monkeypatch.setattr(main, "_validate_riot_id", lambda riot_id, required=False: riot_id)

    response = await main.local_status("user#br1", DummyRequest())
    assert response["status"] == "failed"
    assert "request_id" in response["error"]
