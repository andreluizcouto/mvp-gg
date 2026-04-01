"""Cliente Supabase unificado e helpers de persistencia do pipeline."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Optional

from supabase import create_async_client
from settings import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)

_client = None
_pending_local_evidence_store: dict[tuple[str, str], dict[str, Any]] = {}
_pipeline_snapshot_store: dict[tuple[str, str], dict[str, Any]] = {}
_SAFE_EXTERNAL_STATUSES = {"ready", "pending", "insufficient_data", "failed"}
_legacy_pipeline_snapshot_schema_warned = False
PIPELINE_SNAPSHOT_COLUMNS = "pipeline_snapshot,external_status,coaching_analysis,feedback_geral"
PIPELINE_SNAPSHOT_COLUMNS_FALLBACK = "coaching_analysis,feedback_geral"


def _normalize_pending_key(match_id: str, riot_id: str) -> tuple[str, str]:
    """Normaliza a chave usada pelos caches locais do pipeline."""

    return (match_id.strip(), riot_id.strip().lower())


def _utc_now() -> datetime:
    """Retorna o horario atual em UTC para TTLs do pipeline."""

    return datetime.now(UTC)


def _default_expiry() -> str:
    """Retorna a expiracao padrao do artefato localhost-only."""

    return (_utc_now() + timedelta(minutes=20)).isoformat()


def _is_expired(expires_at: str) -> bool:
    """Valida se um artefato temporario do pipeline ja expirou."""

    try:
        return datetime.fromisoformat(expires_at) <= _utc_now()
    except ValueError:
        return True


def _is_missing_column_error(error: Exception, column_name: str) -> bool:
    message = str(error).lower()
    col = column_name.lower()
    return (
        "column" in message
        and col in message
        and ("does not exist" in message or "not found" in message)
    )


async def get_supabase():
    """Retorna o cliente Supabase (lazy init). None se nao configurado."""
    global _client
    if _client is None and SUPABASE_URL and SUPABASE_KEY:
        _client = await create_async_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


async def get_coaching_analysis(match_id: str, riot_id: str = "") -> Optional[str]:
    """Busca analise de coaching salva no Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        sb = await get_supabase()
        if sb is None:
            return None
        query = sb.table("ai_cache").select("coaching_analysis,feedback_geral").eq("match_id", match_id)
        if riot_id:
            query = query.eq("riot_id", riot_id)
        resp = await query.execute()
        if resp.data:
            row = resp.data[0]
            return row.get("coaching_analysis") or row.get("feedback_geral") or None
    except Exception as e:
        logger.error(f"Erro ao buscar coaching {match_id}: {e}")
    return None


async def save_coaching_analysis(match_id: str, analysis: str, riot_id: str = "") -> None:
    """Salva analise de coaching no Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("SUPABASE_URL/KEY nao configurados — analise NAO foi salva!")
        return
    try:
        sb = await get_supabase()
        if sb is None:
            logger.error("Cliente Supabase retornou None — analise NAO foi salva!")
            return
        await sb.table("ai_cache").upsert(
            {
                "match_id": match_id,
                "riot_id": riot_id,
                "coaching_analysis": analysis,
                "insights": [],
                "feedback_geral": "",
            },
            on_conflict="match_id,riot_id",
        ).execute()
        logger.info(f"Analise de coaching salva no Supabase para {match_id} / {riot_id}")
    except Exception as e:
        logger.error(f"Erro ao salvar coaching {match_id} no Supabase: {e}")


async def save_pending_local_evidence(
    match_id: str,
    riot_id: str,
    *,
    local_events: list[dict[str, Any]],
    image_paths: list[str],
    player_map: dict[str, str],
    source: str = "localhost_only",
    expires_at: str | None = None,
) -> None:
    """Persiste evidencia localhost-only ate a rota Riot poder rejoinar o bundle."""

    _pending_local_evidence_store[_normalize_pending_key(match_id, riot_id)] = {
        "match_id": match_id,
        "riot_id": riot_id,
        "local_events": list(local_events),
        "image_paths": list(image_paths),
        "player_map": dict(player_map),
        "source": source,
        "expires_at": expires_at or _default_expiry(),
    }


async def get_pending_local_evidence(match_id: str, riot_id: str) -> Optional[dict[str, Any]]:
    """Recupera evidencia localhost-only nao expirada para rejoin com a rota Riot."""

    key = _normalize_pending_key(match_id, riot_id)
    payload = _pending_local_evidence_store.get(key)
    if not payload:
        return None
    if _is_expired(payload.get("expires_at", "")):
        _pending_local_evidence_store.pop(key, None)
        return None
    return dict(payload)


async def delete_pending_local_evidence(match_id: str, riot_id: str) -> None:
    """Remove a evidencia localhost-only apos join bem-sucedido ou expiracao."""

    _pending_local_evidence_store.pop(_normalize_pending_key(match_id, riot_id), None)


async def save_pipeline_snapshot(
    match_id: str,
    riot_id: str,
    snapshot: dict[str, Any],
) -> None:
    """Persiste snapshot normalizado com status externo seguro."""

    normalized = _normalize_snapshot_payload(snapshot)
    _pipeline_snapshot_store[_normalize_pending_key(match_id, riot_id)] = normalized

    if not SUPABASE_URL or not SUPABASE_KEY:
        return
    try:
        sb = await get_supabase()
        if sb is None:
            return
        await sb.table("ai_cache").upsert(
            {
                "match_id": match_id,
                "riot_id": riot_id,
                "pipeline_snapshot": normalized,
                "external_status": normalized["external_status"],
            },
            on_conflict="match_id,riot_id",
        ).execute()
    except Exception:
        # Nem todo schema legado possui essas colunas; mantemos fallback in-memory.
        logger.debug("Schema Supabase sem colunas de snapshot - usando cache local.")


async def get_pipeline_snapshot(match_id: str, riot_id: str) -> Optional[dict[str, Any]]:
    """Retorna snapshot normalizado, preferindo cache local e fallback Supabase."""
    global _legacy_pipeline_snapshot_schema_warned

    payload = _pipeline_snapshot_store.get(_normalize_pending_key(match_id, riot_id))
    if payload is not None:
        return dict(payload)

    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        sb = await get_supabase()
        if sb is None:
            return None
        query = sb.table("ai_cache").select(PIPELINE_SNAPSHOT_COLUMNS).eq("match_id", match_id)
        if riot_id:
            query = query.eq("riot_id", riot_id)
        try:
            resp = await query.execute()
        except Exception as exc:
            if not (
                _is_missing_column_error(exc, "external_status")
                or _is_missing_column_error(exc, "pipeline_snapshot")
            ):
                raise
            if not _legacy_pipeline_snapshot_schema_warned:
                logger.warning(
                    "Schema legado detectado em get_pipeline_snapshot (sem external_status/pipeline_snapshot). "
                    "Aplicando fallback seguro."
                )
                _legacy_pipeline_snapshot_schema_warned = True
            fallback_query = sb.table("ai_cache").select(PIPELINE_SNAPSHOT_COLUMNS_FALLBACK).eq("match_id", match_id)
            if riot_id:
                fallback_query = fallback_query.eq("riot_id", riot_id)
            resp = await fallback_query.execute()
        if not resp.data:
            return None
        row = resp.data[0]
        snapshot = row.get("pipeline_snapshot") if isinstance(row.get("pipeline_snapshot"), dict) else {}
        if row.get("external_status"):
            snapshot["external_status"] = row.get("external_status")
        snapshot["has_analysis_text"] = bool(
            (row.get("coaching_analysis") or "").strip() or (row.get("feedback_geral") or "").strip()
        )
        normalized = _normalize_snapshot_payload(snapshot)
        _pipeline_snapshot_store[_normalize_pending_key(match_id, riot_id)] = normalized
        return dict(normalized)
    except Exception as e:
        logger.error(f"Erro ao buscar snapshot do pipeline {match_id}: {e}")
        return None


def _as_text(value: Any) -> str:
    """Converte enums e valores variados para string normalizada."""

    if hasattr(value, "value"):
        return str(getattr(value, "value")).strip().lower()
    return str(value or "").strip().lower()


def _normalize_reason_codes(raw: Any) -> list[str]:
    """Normaliza a lista de reason codes para transporte interno."""

    if not isinstance(raw, list):
        return []
    return [code for code in (_as_text(item) for item in raw) if code]


def _derive_external_status(status: str, reasons: list[str], has_analysis_text: bool) -> str:
    """Resume status interno para estado público seguro."""

    if status == "ready":
        return "ready"
    if status in {"accepted", "degraded_safe", "incomplete_evidence"}:
        return "pending"
    if status == "invalid_input":
        return "failed"
    if status == "blocked":
        if any(reason.startswith("missing_") or "pending_riot_context" in reason for reason in reasons):
            return "insufficient_data"
        return "failed"
    if has_analysis_text:
        return "ready"
    return "pending"


def _normalize_snapshot_payload(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Filtra campos uteis do snapshot para leitura publica e roteamento."""

    stage = _as_text(snapshot.get("stage") or snapshot.get("latest_stage"))
    status = _as_text(snapshot.get("status") or snapshot.get("latest_status"))
    source = _as_text(snapshot.get("source"))
    reasons = _normalize_reason_codes(snapshot.get("reason_codes"))
    has_analysis_text = bool(snapshot.get("has_analysis_text"))
    weak_signal = bool(snapshot.get("weak_signal"))
    external_status = _as_text(snapshot.get("external_status"))

    if external_status not in _SAFE_EXTERNAL_STATUSES:
        external_status = _derive_external_status(status, reasons, has_analysis_text)
    if external_status not in _SAFE_EXTERNAL_STATUSES:
        external_status = "pending"
    if weak_signal and external_status == "ready":
        external_status = "insufficient_data"

    return {
        "stage": stage,
        "status": status,
        "source": source,
        "reason_codes": reasons,
        "external_status": external_status,
        "has_analysis_text": has_analysis_text,
        "weak_signal": weak_signal,
    }
