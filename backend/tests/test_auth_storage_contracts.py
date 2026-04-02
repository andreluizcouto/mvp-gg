from datetime import UTC, datetime, timedelta

import pytest

import db


@pytest.fixture(autouse=True)
def _reset_auth_storage():
    db._auth_session_store.clear()
    db._entitlement_store.clear()
    db._usage_operation_store.clear()
    yield
    db._auth_session_store.clear()
    db._entitlement_store.clear()
    db._usage_operation_store.clear()


@pytest.mark.asyncio
async def test_save_auth_session_stores_hash_only():
    now = datetime.now(UTC)
    await db.save_auth_session(
        user_id="user-1",
        session_id="sess-1",
        access_token="access-token-plain",
        refresh_token="refresh-token-plain",
        access_token_expires_at=now + timedelta(minutes=5),
        refresh_token_expires_at=now + timedelta(days=7),
    )

    record = db._auth_session_store["sess-1"]
    assert record["access_token_hash"] == db.hash_auth_token("access-token-plain")
    assert record["refresh_token_hash"] == db.hash_auth_token("refresh-token-plain")
    assert "access-token-plain" not in str(record)
    assert "refresh-token-plain" not in str(record)


@pytest.mark.asyncio
async def test_revoke_session_marks_record_unusable():
    now = datetime.now(UTC)
    await db.save_auth_session(
        user_id="user-1",
        session_id="sess-2",
        access_token="access-token-plain",
        refresh_token="refresh-token-plain",
        access_token_expires_at=now + timedelta(minutes=5),
        refresh_token_expires_at=now + timedelta(days=7),
    )

    token_hash = db.hash_auth_token("refresh-token-plain")
    active_before = await db.get_active_session_by_hash(token_hash, token_type="refresh")
    assert active_before is not None

    await db.revoke_session("sess-2")
    active_after = await db.get_active_session_by_hash(token_hash, token_type="refresh")
    assert active_after is None
    assert db._auth_session_store["sess-2"]["revoked_at"] is not None


@pytest.mark.asyncio
async def test_increment_usage_counter_is_idempotent_by_operation_id():
    first = await db.increment_usage_counter(
        user_id="user-1",
        operation_id="op-123",
        analyses_consumed_delta=1,
        analyses_performed_delta=1,
    )
    second = await db.increment_usage_counter(
        user_id="user-1",
        operation_id="op-123",
        analyses_consumed_delta=1,
        analyses_performed_delta=1,
    )

    assert first.analyses_consumed == 1
    assert first.analyses_performed == 1
    assert second.analyses_consumed == 1
    assert second.analyses_performed == 1
