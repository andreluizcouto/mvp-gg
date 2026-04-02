"""
LoL Coach API - Backend FastAPI
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, StreamingResponse
from typing import Optional
import asyncio
import base64
import binascii
import hashlib
import httpx
import ipaddress
import json
import logging
import os
import re
import secrets
import shutil
import tempfile
import time
import uuid
from urllib.parse import urlsplit

from contextlib import asynccontextmanager

from analysis_contracts import EvidenceSource, PipelineStage
from coach_ai import run_full_analysis, CoachAI, _get_ai_cache, _set_ai_cache, _is_valid_ai_result
from context_builder import ContextBuilder
from evidence_pipeline import build_analysis_evidence_bundle, gate_pipeline_stage
from riot_client import RiotMatchClient, get_item_names, cache_invalidate
from live_coach import LiveCoachSession
from postgame_analyzer import analyze_postgame
from schemas import (
    FeedbackRequest, LiveEventUpload, LiveUploadRequest, LiveUploadResponse,
    CoachingSaveRequest, CoachingAnalysisResponse, CoachingStatusResponse, CoachingRegenerateResponse,
    ScoreboardPlayer, ScoreboardTeam, ScoreboardResponse,
    LocalEventUpload, LocalUploadRequest, LocalUploadResponse,
    AnalyzeRequest, InsightResponse, AnalyzeResponse,
    MatchHistoryItem, MatchHistoryResponse,
)
from settings import (
    RIOT_API_KEY as RIOT_KEY,
    GEMINI_API_KEY as GEMINI_KEY,
    SUPABASE_URL, SUPABASE_KEY,
    APP_TOKEN, INTERNAL_BEARER_TOKEN, LOCAL_APP_TOKEN, PUBLIC_READ_ONLY, RENDER_BACKEND_URL,
    CORS_ORIGINS, MAKE_FEEDBACK_WEBHOOK_URL, DOWNLOAD_APP_URL,
    DAILY_LIMIT, REQUIRE_HTTPS, TRUST_X_FORWARDED_PROTO,
    REQUIRE_RIOT_ID_FOR_COACHING, MAX_IDS_PER_STATUS_QUERY,
    MAX_MATCH_ID_LENGTH, MAX_RIOT_ID_LENGTH,
    MAX_EVENTS_PER_UPLOAD, MAX_MINIMAP_BASE64_LENGTH,
    PUBLIC_READ_RATE_LIMIT_WINDOW_SECONDS, PUBLIC_READ_RATE_LIMIT_MAX_REQUESTS,
    REFRESH_RATE_LIMIT_WINDOW_SECONDS, REFRESH_RATE_LIMIT_MAX_REQUESTS,
    REDIS_URL, REDIS_RATE_LIMIT_PREFIX,
    EDGE_CLIENT_RATE_LIMIT_WINDOW_SECONDS, EDGE_CLIENT_RATE_LIMIT_MAX_REQUESTS, EDGE_CLIENT_ID_HEADERS,
)
from db import (
    delete_pending_local_evidence,
    get_coaching_analysis,
    get_pending_local_evidence,
    get_pipeline_snapshot,
    get_supabase,
    save_coaching_analysis,
    save_pipeline_snapshot,
    save_pending_local_evidence,
)

DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis
except Exception:  # pragma: no cover - opcional em runtime
    redis = None


from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


def _is_secure_request(request: Request) -> bool:
    if request.url.scheme == "https":
        return True
    if TRUST_X_FORWARDED_PROTO:
        forwarded = request.headers.get("X-Forwarded-Proto", "")
        forwarded = forwarded.split(",")[0].strip().lower()
        if forwarded == "https":
            return True
    return False


def _is_local_request(request: Request) -> bool:
    host = (request.url.hostname or "").lower()
    return host in {"localhost", "127.0.0.1"}


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", "").strip()[:64] or str(uuid.uuid4())
        request.state.request_id = request_id
        started_at = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        duration_ms = (time.perf_counter() - started_at) * 1000
        logger.info(
            "req_id=%s method=%s path=%s status=%s duration_ms=%.1f",
            request_id,
            request.method,
            request.url.path[:120],
            response.status_code,
            duration_ms,
        )
        return response


class HTTPSGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if REQUIRE_HTTPS and not _is_local_request(request) and not _is_secure_request(request):
            return Response(status_code=400, content="HTTPS is required.")
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
        response.headers["Cache-Control"] = "no-store"
        return response

app = FastAPI(title="LoL Coach API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-App-Token", "Authorization", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
    max_age=3600,
)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(HTTPSGuardMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Validacao de configuracao na inicializacao
_missing = []
if not RIOT_KEY:
    _missing.append("RIOT_API_KEY")
if not SUPABASE_URL:
    _missing.append("SUPABASE_URL")
if not SUPABASE_KEY:
    _missing.append("SUPABASE_KEY")
if not APP_TOKEN and not INTERNAL_BEARER_TOKEN:
    _missing.append("APP_TOKEN ou INTERNAL_BEARER_TOKEN")
if _missing:
    logger.warning(f"Variaveis de ambiente ausentes: {', '.join(_missing)}")
if PUBLIC_READ_ONLY:
    logger.info("PUBLIC_READ_ONLY ativo: endpoints de IA exigem autenticacao interna.")
if APP_TOKEN and not LOCAL_APP_TOKEN:
    logger.warning("LOCAL_APP_TOKEN nao configurado: /local/* continua aceitando APP_TOKEN como fallback temporario.")
if RIOT_KEY and RIOT_KEY.startswith("RGAPI-"):
    logger.warning("RIOT_API_KEY e uma chave de desenvolvimento (RGAPI-*) — expira a cada 24h!")


# ── Local app jobs (in-memory) ────────────────────────────
# riot_id → match_id (None enquanto processando)
_local_jobs: dict[str, str | None] = {}

_upload_counts: dict[str, list] = {}  # riot_id → [timestamps]
_public_read_hits: dict[str, list[float]] = {}  # scope:ip -> [timestamps]
_edge_client_hits: dict[str, list[float]] = {}  # scope:client -> [timestamps]
_local_upload_client_hits: dict[str, list[float]] = {}  # local-upload:ip -> [timestamps]
_redis_rate_limit_client = None
_redis_fallback_warned = False
_legacy_coaching_status_schema_warned = False

MATCH_ID_RE = re.compile(r"^[A-Za-z0-9_:-]{3,80}$")
SAFE_TEMP_FRAGMENT_RE = re.compile(r"[^A-Za-z0-9_-]+")

MATCH_PUBLIC_COLUMNS = ",".join([
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
])
MATCH_PUBLIC_COLUMNS_FALLBACK = ",".join([
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
])
COACHING_STATUS_COLUMNS = "match_id,coaching_analysis,feedback_geral,external_status,pipeline_snapshot"
COACHING_STATUS_COLUMNS_FALLBACK = "match_id,coaching_analysis,feedback_geral"
SAFE_EXTERNAL_STATUSES = {"ready", "pending", "insufficient_data", "failed"}
# Plan artifact marker: insufficient_data|Coach indisponivel
UNAVAILABLE_COACHING_MESSAGE = "Coach indisponivel, baixe o app e jogue uma partida."
PAID_REGEN_MESSAGE = "Regeneracao e um recurso pago. Em breve no plano premium."


def _normalize_public_status(snapshot: dict | None, has_analysis: bool) -> str:
    """Converte estado interno para um status público seguro e estável."""

    if snapshot:
        external = str(snapshot.get("external_status", "")).strip().lower()
        if external in SAFE_EXTERNAL_STATUSES:
            return external

        status = str(snapshot.get("status", "")).strip().lower()
        if status == "ready":
            return "ready"
        if status in {"accepted", "degraded_safe", "incomplete_evidence"}:
            return "pending"
        if status == "invalid_input":
            return "failed"
        if status == "blocked":
            reasons = [str(code).strip().lower() for code in snapshot.get("reason_codes", []) if str(code).strip()]
            if any(reason.startswith("missing_") or "pending_riot_context" in reason for reason in reasons):
                return "insufficient_data"
            return "failed"

    if has_analysis:
        return "ready"
    # Nothing at all — no snapshot, no analysis → data is truly unavailable
    return "insufficient_data"


def _missing_local_evidence(snapshot: dict | None) -> bool:
    """Returns True when snapshot indicates coaching cannot be trusted without app evidence."""

    if not snapshot:
        return False

    source = str(snapshot.get("source", "")).strip().lower()
    if source == "riot_only":
        return True
    if source in {"riot_plus_local", "localhost_only"}:
        return False

    reasons = [str(code).strip().lower() for code in snapshot.get("reason_codes", []) if str(code).strip()]
    if any(
        reason in {"missing_local_events", "localhost_only_pending_riot_context"}
        or "pending_riot_context" in reason
        for reason in reasons
    ):
        return True

    status = str(snapshot.get("status", "")).strip().lower()
    external = str(snapshot.get("external_status", "")).strip().lower()
    if status in {"incomplete_evidence", "blocked"} and external == "insufficient_data":
        return True

    return False


def _parse_ip_address(value: str):
    try:
        return ipaddress.ip_address(value)
    except ValueError:
        return None


def _is_trusted_proxy_host(host: str) -> bool:
    ip = _parse_ip_address(host)
    if ip is None:
        return False
    if ip.version == 4:
        private_ipv4 = (
            ipaddress.ip_network("10.0.0.0/8"),
            ipaddress.ip_network("172.16.0.0/12"),
            ipaddress.ip_network("192.168.0.0/16"),
        )
        return any(ip in network for network in private_ipv4) or ip.is_loopback or ip.is_link_local

    private_ipv6 = ipaddress.ip_network("fc00::/7")
    return bool(ip in private_ipv6 or ip.is_loopback or ip.is_link_local)


def _client_ip(request: Request) -> str:
    if request.client and request.client.host:
        host = request.client.host.strip()
        if host and _is_trusted_proxy_host(host):
            forwarded = request.headers.get("X-Forwarded-For", "")
            if forwarded:
                first = forwarded.split(",")[0].strip()
                if first and _parse_ip_address(first):
                    return first[:64]
            real_ip = request.headers.get("X-Real-IP", "").strip()
            if real_ip and _parse_ip_address(real_ip):
                return real_ip[:64]
        if host:
            return host[:64]
    return "unknown"


def _local_rate_limit_hit(bucket: dict[str, list[float]], key: str, window_seconds: int) -> int:
    now = time.time()
    window_start = now - window_seconds
    recent = [t for t in bucket.get(key, []) if t > window_start]
    recent.append(now)
    bucket[key] = recent
    return len(recent)


def _hash_fragment(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def _safe_temp_fragment(value: str, fallback: str = "upload") -> str:
    cleaned = SAFE_TEMP_FRAGMENT_RE.sub("_", (value or "").strip()).strip("_")
    return (cleaned or fallback)[:24]


def _create_temp_upload_dir(kind: str, identifier: str) -> str:
    prefix = f"lol_coach_{_safe_temp_fragment(kind, 'job')}_{_safe_temp_fragment(identifier)}_"
    return tempfile.mkdtemp(prefix=prefix)


def _decode_base64_image(value: str) -> bytes:
    try:
        return base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=422, detail="Imagem minimap_base64 inválida.")


def _edge_client_identity(request: Request) -> str:
    for header in EDGE_CLIENT_ID_HEADERS:
        value = request.headers.get(header, "").strip()
        if value:
            return f"{header.lower()}:{value[:128]}"
    return f"ip:{_client_ip(request)}"


async def _get_redis_rate_limit_client():
    global _redis_rate_limit_client
    if _redis_rate_limit_client is not None:
        return _redis_rate_limit_client
    if not REDIS_URL or redis is None:
        return None
    _redis_rate_limit_client = redis.from_url(
        REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        socket_timeout=1.0,
        socket_connect_timeout=1.0,
    )
    return _redis_rate_limit_client


async def _rate_limit_hit(bucket_name: str, identity: str, scope: str, window_seconds: int, local_bucket: dict[str, list[float]]) -> int:
    global _redis_fallback_warned, _redis_rate_limit_client
    if window_seconds <= 0:
        return 0

    redis_key = f"{REDIS_RATE_LIMIT_PREFIX}:{bucket_name}:{scope}:{_hash_fragment(identity)}"
    client = await _get_redis_rate_limit_client()
    if client is not None:
        try:
            count = int(await client.incr(redis_key))
            if count == 1:
                await client.expire(redis_key, window_seconds)
            _redis_fallback_warned = False
            return count
        except Exception as exc:
            if not _redis_fallback_warned:
                logger.warning("Rate limit Redis indisponivel, fallback local ativado: %s", exc)
                _redis_fallback_warned = True
            _redis_rate_limit_client = None

    local_key = f"{scope}:{_hash_fragment(identity)}"
    return _local_rate_limit_hit(local_bucket, local_key, window_seconds)


async def _check_public_read_rate_limit(request: Request, scope: str) -> None:
    """Rate limit por IP+rota para endpoints publicos (Redis com fallback local)."""
    if PUBLIC_READ_RATE_LIMIT_MAX_REQUESTS <= 0 or PUBLIC_READ_RATE_LIMIT_WINDOW_SECONDS <= 0:
        return
    count = await _rate_limit_hit(
        bucket_name="public",
        identity=f"ip:{_client_ip(request)}",
        scope=scope,
        window_seconds=PUBLIC_READ_RATE_LIMIT_WINDOW_SECONDS,
        local_bucket=_public_read_hits,
    )
    if count > PUBLIC_READ_RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit excedido em {scope}. Tente novamente em instantes.",
        )


async def _check_edge_client_rate_limit(request: Request, scope: str) -> None:
    """Rate limit por cliente/API key para reduzir abuso automatizado no edge."""
    if EDGE_CLIENT_RATE_LIMIT_MAX_REQUESTS <= 0 or EDGE_CLIENT_RATE_LIMIT_WINDOW_SECONDS <= 0:
        return
    count = await _rate_limit_hit(
        bucket_name="edge",
        identity=_edge_client_identity(request),
        scope=scope,
        window_seconds=EDGE_CLIENT_RATE_LIMIT_WINDOW_SECONDS,
        local_bucket=_edge_client_hits,
    )
    if count > EDGE_CLIENT_RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit de cliente excedido em {scope}. Reduza a frequencia das requisicoes.",
        )


async def _check_public_limits(request: Request, scope: str) -> None:
    await _check_public_read_rate_limit(request, scope)
    await _check_edge_client_rate_limit(request, scope)


async def _check_refresh_limits(request: Request) -> None:
    """Rate limit mais apertado para refresh manual de perfil."""
    if REFRESH_RATE_LIMIT_MAX_REQUESTS <= 0 or REFRESH_RATE_LIMIT_WINDOW_SECONDS <= 0:
        return
    count = await _rate_limit_hit(
        bucket_name="refresh",
        identity=f"ip:{_client_ip(request)}",
        scope="summoner-refresh",
        window_seconds=REFRESH_RATE_LIMIT_WINDOW_SECONDS,
        local_bucket=_public_read_hits,
    )
    if count > REFRESH_RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Muitas atualizacoes de perfil em pouco tempo. Aguarde um pouco e tente novamente.",
        )
    await _check_edge_client_rate_limit(request, "summoner-refresh")


async def _check_local_upload_limits(request: Request, riot_id: str) -> None:
    if DAILY_LIMIT <= 0:
        return

    riot_count = await _rate_limit_hit(
        bucket_name="local-upload-riot",
        identity=riot_id.strip().lower(),
        scope="local-upload",
        window_seconds=86400,
        local_bucket=_upload_counts,
    )
    if riot_count > DAILY_LIMIT:
        raise HTTPException(status_code=429, detail=f"Limite de {DAILY_LIMIT} análises/dia atingido para {riot_id}.")

    per_ip_limit = max(DAILY_LIMIT * 3, DAILY_LIMIT + 20)
    client_count = await _rate_limit_hit(
        bucket_name="local-upload-client",
        identity=f"ip:{_client_ip(request)}",
        scope="local-upload",
        window_seconds=86400,
        local_bucket=_local_upload_client_hits,
    )
    if client_count > per_ip_limit:
        raise HTTPException(
            status_code=429,
            detail="Limite diário de uploads por cliente/IP atingido. Tente novamente amanhã.",
        )


def _sanitize_match_payload(row: dict) -> dict:
    """Remove campos internos e mantem apenas payload minimo usado pelo frontend."""
    def _as_int(value, default: int = 0) -> int:
        if value is None or value == "":
            return default
        try:
            if isinstance(value, bool):
                return int(value)
            return int(float(value))
        except (TypeError, ValueError):
            return default

    def _as_float(value, default: float = 0.0) -> float:
        if value is None or value == "":
            return default
        try:
            if isinstance(value, bool):
                return float(int(value))
            return float(value)
        except (TypeError, ValueError):
            return default

    def _as_bool(value, default: bool = False) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "t", "yes", "y"}:
                return True
            if normalized in {"0", "false", "f", "no", "n", ""}:
                return False
        return default

    items = row.get("items")
    allies = row.get("allies")
    return {
        "match_id": str(row.get("match_id", "")),
        "riot_id": str(row.get("riot_id", "")),
        "summoner_name": str(row.get("summoner_name", "")),
        "champion": str(row.get("champion", "")),
        "kills": _as_int(row.get("kills"), 0),
        "deaths": _as_int(row.get("deaths"), 0),
        "assists": _as_int(row.get("assists"), 0),
        "win": _as_bool(row.get("win"), False),
        "duration_min": _as_int(row.get("duration_min"), 0),
        "position": str(row.get("position", "")),
        "cs_per_min": _as_float(row.get("cs_per_min"), 0.0),
        "vision_score": _as_int(row.get("vision_score"), 0),
        "kill_participation_pct": _as_float(row.get("kill_participation_pct"), 0.0),
        "damage_share_pct": _as_float(row.get("damage_share_pct"), 0.0),
        "items": items if isinstance(items, list) else [],
        "allies": allies if isinstance(allies, list) else [],
        "puuid": str(row.get("puuid", "")),
        "rank": "" if row.get("rank") is None else str(row.get("rank", "")),
    }


def _is_missing_column_error(error: Exception, column_name: str) -> bool:
    message = str(error).lower()
    col = column_name.lower()
    return (
        "column" in message
        and col in message
        and ("does not exist" in message or "not found" in message)
    )


async def _fetch_match_row(sb, match_id: str) -> dict | None:
    """Busca linha publica da partida com fallback para schemas legados sem coluna rank."""
    try:
        res = await sb.table("ai_cache").select(MATCH_PUBLIC_COLUMNS).eq("match_id", match_id).limit(1).execute()
        return (res.data or [None])[0]
    except Exception as exc:
        if not _is_missing_column_error(exc, "rank"):
            raise
        logger.warning("Schema legado detectado em /match (sem coluna rank). Aplicando fallback seguro.")
        fallback = await sb.table("ai_cache").select(MATCH_PUBLIC_COLUMNS_FALLBACK).eq("match_id", match_id).limit(1).execute()
        return (fallback.data or [None])[0]


async def _fetch_coaching_status_rows(sb, match_ids: list[str], riot_id: str = "") -> dict[str, dict]:
    """Busca status de coaching com fallback para schemas sem colunas novas."""
    global _legacy_coaching_status_schema_warned

    def _base_query(columns: str):
        query = sb.table("ai_cache").select(columns).in_("match_id", match_ids)
        if riot_id:
            query = query.eq("riot_id", riot_id)
        return query

    try:
        response = await _base_query(COACHING_STATUS_COLUMNS).execute()
        return {row["match_id"]: row for row in (response.data or []) if row.get("match_id")}
    except Exception as exc:
        if not (
            _is_missing_column_error(exc, "external_status")
            or _is_missing_column_error(exc, "pipeline_snapshot")
        ):
            raise
        if not _legacy_coaching_status_schema_warned:
            logger.warning(
                "Schema legado detectado em /coaching/status (sem external_status/pipeline_snapshot). "
                "Aplicando fallback seguro."
            )
            _legacy_coaching_status_schema_warned = True
        fallback = await _base_query(COACHING_STATUS_COLUMNS_FALLBACK).execute()
        return {row["match_id"]: row for row in (fallback.data or []) if row.get("match_id")}


def _verify_app_token(request: Request) -> None:
    """Lança 401 se o header X-App-Token estiver ausente ou incorreto."""
    if not APP_TOKEN:
        raise HTTPException(status_code=500, detail="APP_TOKEN não configurado no servidor.")
    token = request.headers.get("X-App-Token", "")
    if not secrets.compare_digest(token, APP_TOKEN):
        raise HTTPException(status_code=401, detail="Token inválido.")


def _verify_internal_bearer(request: Request) -> bool:
    """Retorna True se o bearer token interno for válido."""
    if not INTERNAL_BEARER_TOKEN:
        return False
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return False
    provided = auth[len("Bearer "):].strip()
    return bool(provided) and secrets.compare_digest(provided, INTERNAL_BEARER_TOKEN)


def _require_internal_auth(request: Request) -> None:
    """Aceita APP_TOKEN ou Authorization Bearer interno."""
    if _verify_internal_bearer(request):
        return
    _verify_app_token(request)


def _require_local_app_auth(request: Request) -> None:
    """Aceita apenas o token dedicado do app local; fallback para APP_TOKEN durante migração."""
    expected = (LOCAL_APP_TOKEN or APP_TOKEN or "").strip()
    if not expected:
        raise HTTPException(status_code=500, detail="LOCAL_APP_TOKEN/APP_TOKEN não configurado no servidor.")
    token = request.headers.get("X-App-Token", "")
    if not secrets.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Token do app local inválido.")


def _validate_match_id(match_id: str) -> str:
    cleaned = (match_id or "").strip()
    if not cleaned or len(cleaned) > MAX_MATCH_ID_LENGTH or not MATCH_ID_RE.fullmatch(cleaned):
        raise HTTPException(status_code=422, detail="match_id inválido.")
    return cleaned


def _validate_riot_id(riot_id: str, *, required: bool = False) -> str:
    cleaned = (riot_id or "").strip()
    if required and not cleaned:
        raise HTTPException(status_code=422, detail="riot_id obrigatório.")
    if cleaned and ("\r" in cleaned or "\n" in cleaned or len(cleaned) > MAX_RIOT_ID_LENGTH):
        raise HTTPException(status_code=422, detail="riot_id inválido.")
    return cleaned


def _get_download_app_url() -> str:
    url = (DOWNLOAD_APP_URL or "").strip()
    if not url:
        raise HTTPException(status_code=503, detail="Download indisponivel no momento.")

    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.netloc:
        logger.error("DOWNLOAD_APP_URL invalida: use uma URL HTTPS absoluta.")
        raise HTTPException(status_code=503, detail="Download indisponivel no momento.")

    return url


def _validate_history_page(start: int, count: int) -> tuple[int, int]:
    if start < 0:
        raise HTTPException(status_code=422, detail="start invalido.")
    if count < 1 or count > 20:
        raise HTTPException(status_code=422, detail="count invalido. Use um valor entre 1 e 20.")
    return start, count


def _parse_match_ids(ids: str) -> list[str]:
    raw = [mid.strip() for mid in ids.split(",") if mid.strip()]
    deduped = list(dict.fromkeys(raw))
    if not deduped:
        return []
    if len(deduped) > MAX_IDS_PER_STATUS_QUERY:
        raise HTTPException(
            status_code=422,
            detail=f"Máximo de {MAX_IDS_PER_STATUS_QUERY} ids por consulta.",
        )
    for mid in deduped:
        _validate_match_id(mid)
    return deduped


async def _build_match_history_response(riot: RiotMatchClient, game_name: str, tag_line: str, start: int, count: int) -> MatchHistoryResponse:
    summoner = await riot.get_summoner_by_name(game_name, tag_line)
    if not summoner:
        raise HTTPException(status_code=404, detail="Jogador nÃ£o encontrado.")

    rank = await riot.get_summoner_rank(summoner.summoner_id)
    if rank in ("DEFAULT", "UNRANKED", None):
        rank = "Unranked"

    raw_match_ids = await riot.get_match_history(summoner.puuid, start=start, count=count + 1)
    if not raw_match_ids and start == 0:
        raise HTTPException(status_code=404, detail="Nenhuma partida encontrada.")

    has_more = len(raw_match_ids) > count
    match_ids = raw_match_ids[:count]

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*[
            fetch_match_details(summoner.puuid, mid, start + i, RIOT_KEY, client)
            for i, mid in enumerate(match_ids)
        ], return_exceptions=True)

    matches = [r for r in results if isinstance(r, MatchHistoryItem)]
    wins = sum(1 for m in matches if m.win)

    return MatchHistoryResponse(
        summoner=summoner.name,
        puuid=summoner.puuid,
        rank=rank,
        matches=list(matches),
        wins=wins,
        losses=len(matches) - wins,
        has_more=has_more,
        next_offset=start + len(match_ids),
    )


# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────

async def send_to_make(data: dict, webhook_url: str) -> None:
    if not webhook_url:
        return
    try:
        async with httpx.AsyncClient() as client:
            await client.post(webhook_url, json=data, timeout=5)
        logger.info("Dados enviados ao Make com sucesso.")
    except Exception as e:
        logger.warning(f"Falha ao enviar dados ao Make: {e}")

async def _upload_coaching_to_render(match_id: str, puuid: str, analysis: str) -> None:
    """Envia análise pos-game para o backend na nuvem."""
    if not analysis.strip():
        return
    headers: dict[str, str] = {}
    if INTERNAL_BEARER_TOKEN:
        headers["Authorization"] = f"Bearer {INTERNAL_BEARER_TOKEN}"
    elif APP_TOKEN:
        headers["X-App-Token"] = APP_TOKEN
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{RENDER_BACKEND_URL}/coaching/save",
                json={"match_id": match_id, "puuid": puuid, "analysis": analysis},
                headers=headers,
                timeout=15,
            )
            logger.info(f"Upload coaching: {resp.status_code} — {match_id}")
    except Exception as e:
        logger.error(f"Falha ao fazer upload do coaching: {e}")

async def fetch_match_details(puuid: str, match_id: str, index: int, api_key: str, client: httpx.AsyncClient) -> MatchHistoryItem:
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}"
    resp = await client.get(url, headers={"X-Riot-Token": api_key}, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    participants  = data["info"]["participants"]
    participant   = next(p for p in participants if p["puuid"] == puuid)
    duration_min  = data["info"]["gameDuration"] / 60
    team_id       = participant["teamId"]
    kills         = participant["kills"]
    assists       = participant["assists"]

    cs         = participant.get("totalMinionsKilled", 0) + participant.get("neutralMinionsKilled", 0)
    team_kills = sum(p["kills"] for p in participants if p["teamId"] == team_id)
    team_dmg   = sum(p.get("totalDamageDealtToChampions", 0) for p in participants if p["teamId"] == team_id)
    player_dmg = participant.get("totalDamageDealtToChampions", 0)

    allies = [
        {"champion": p["championName"], "position": p.get("teamPosition", "")}
        for p in participants
        if p["teamId"] == team_id and p["puuid"] != puuid
    ]

    items         = [participant.get(f"item{i}", 0) for i in range(7)]
    total_damage  = participant.get("totalDamageDealtToChampions", 0)

    return MatchHistoryItem(
        match_id=match_id,
        index=index,
        champion=participant["championName"],
        kills=kills,
        deaths=participant["deaths"],
        assists=assists,
        win=participant["win"],
        duration_min=data["info"]["gameDuration"] // 60,
        position=participant.get("teamPosition", ""),
        wards_placed=participant.get("wardsPlaced"),
        wards_killed=participant.get("wardsKilled"),
        summoner1_id=participant.get("summoner1Id"),
        summoner2_id=participant.get("summoner2Id"),
        cs=cs,
        cs_per_min=round(cs / max(duration_min, 1), 1),
        vision_score=participant.get("visionScore", 0),
        kill_participation_pct=round((kills + assists) / max(team_kills, 1) * 100, 1),
        damage_share_pct=round(player_dmg / max(team_dmg, 1) * 100, 1),
        doubles=participant.get("doubleKills", 0),
        triples=participant.get("tripleKills", 0),
        quadras=participant.get("quadraKills", 0),
        pentas=participant.get("pentaKills", 0),
        allies=allies,
        items=items,
        total_damage=total_damage,
    )


# ─────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "message": "LoL Coach API v2.1 funcionando!"}


@app.get("/summoner/{game_name}/{tag_line}", response_model=MatchHistoryResponse)
async def get_summoner(game_name: str, tag_line: str, request: Request, start: int = 0, count: int = 10):
    """Busca o jogador, rank e retorna as últimas partidas hidratadas."""
    await _check_public_limits(request, "summoner")
    start, count = _validate_history_page(start, count)
    riot = RiotMatchClient(api_key=RIOT_KEY)
    return await _build_match_history_response(riot, game_name, tag_line, start, count)

    summoner = await riot.get_summoner_by_name(game_name, tag_line)
    if not summoner:
        raise HTTPException(status_code=404, detail="Jogador não encontrado.")

    rank      = await riot.get_summoner_rank(summoner.summoner_id)
    if rank in ("DEFAULT", "UNRANKED", None):
        rank = "Unranked"
    match_ids = await riot.get_match_history(summoner.puuid, count=10)
    if not match_ids:
        raise HTTPException(status_code=404, detail="Nenhuma partida encontrada.")

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*[
            fetch_match_details(summoner.puuid, mid, i, RIOT_KEY, client)
            for i, mid in enumerate(match_ids)
        ], return_exceptions=True)

    matches = [r for r in results if isinstance(r, MatchHistoryItem)]
    wins    = sum(1 for m in matches if m.win)

    return MatchHistoryResponse(
        summoner=summoner.name,
        puuid=summoner.puuid,
        rank=rank,
        matches=list(matches),
        wins=wins,
        losses=len(matches) - wins,
    )


@app.get("/summoner/{game_name}/{tag_line}/refresh", response_model=MatchHistoryResponse)
async def refresh_summoner(game_name: str, tag_line: str, request: Request, start: int = 0, count: int = 10):
    """Força atualização: limpa cache e busca dados frescos da Riot API."""
    await _check_refresh_limits(request)
    start, count = _validate_history_page(start, count)
    riot = RiotMatchClient(api_key=RIOT_KEY)

    summoner = await riot.get_summoner_by_name(game_name, tag_line)
    if not summoner:
        raise HTTPException(status_code=404, detail="Jogador não encontrado.")

    # Invalida caches de history e rank desse jogador
    cache_invalidate(f"history_{summoner.puuid}")
    cache_invalidate(f"rank_{summoner.summoner_id}")
    return await _build_match_history_response(riot, game_name, tag_line, start, count)

    rank      = await riot.get_summoner_rank(summoner.summoner_id)
    if rank in ("DEFAULT", "UNRANKED", None):
        rank = "Unranked"
    match_ids = await riot.get_match_history(summoner.puuid, count=10)
    if not match_ids:
        raise HTTPException(status_code=404, detail="Nenhuma partida encontrada.")

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*[
            fetch_match_details(summoner.puuid, mid, i, RIOT_KEY, client)
            for i, mid in enumerate(match_ids)
        ], return_exceptions=True)

    matches = [r for r in results if isinstance(r, MatchHistoryItem)]
    wins    = sum(1 for m in matches if m.win)

    return MatchHistoryResponse(
        summoner=summoner.name,
        puuid=summoner.puuid,
        rank=rank,
        matches=list(matches),
        wins=wins,
        losses=len(matches) - wins,
    )


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_match(body: AnalyzeRequest, request: Request):
    """Analisa uma partida e retorna insights + feedback do coach."""
    _require_internal_auth(request)
    if not RIOT_KEY or not GEMINI_KEY:
        raise HTTPException(status_code=500, detail="Chaves de API não configuradas.")

    try:
        # Busca rank real antes de rodar a análise
        riot     = RiotMatchClient(api_key=RIOT_KEY)
        summoner = await riot.get_summoner_by_name(body.game_name, body.tag_line)
        if not summoner:
            raise ValueError(f"Jogador {body.game_name}#{body.tag_line} não encontrado.")

        rank = await riot.get_summoner_rank(summoner.summoner_id)
        if rank in ("DEFAULT", "UNRANKED", None):
            rank = "Unranked"
        logger.info(f"Rank de {body.game_name}#{body.tag_line} → {rank}")

        result = await run_full_analysis(
            riot_api_key=RIOT_KEY,
            gemini_api_key=GEMINI_KEY,
            game_name=body.game_name,
            tag_line=body.tag_line,
            match_index=body.match_index,
            rank=rank,
            summoner=summoner,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")

    context  = result["context"]
    insights = result["insights"]

    response = AnalyzeResponse(
        match_id=context.match_id,
        player=context.player_riot_id,
        champion=context.player_champion,
        position=context.role,
        win=context.win,
        duration_min=context.duration_min,
        kda=context.kda,
        cs_per_min=context.cs_per_min,
        vision_score=context.vision_score,
        kill_participation_pct=context.kill_participation_pct,
        damage_share_pct=context.damage_share_pct,
        time_dead_pct=context.time_dead_pct,
        rank=context.rank,
        insights=[
            InsightResponse(
                category=i.get("category", ""),
                severity=i.get("severity", "MEDIUM"),
                timestamp=float(i.get("timestamp", 0)),
                title=i.get("title", ""),
                detail=i.get("detail", ""),
                suggestion=i.get("suggestion", ""),
            )
            for i in insights
        ],
        feedback=result["feedback"],
    )

    return response


@app.get("/analyze/stream/{game_name}/{tag_line}/{match_index}")
async def analyze_stream(game_name: str, tag_line: str, match_index: int, request: Request):
    """Analisa uma partida via Server-Sent Events — insights + feedback em streaming."""
    _require_internal_auth(request)
    if not RIOT_KEY or not GEMINI_KEY:
        raise HTTPException(status_code=500, detail="Chaves de API não configuradas.")

    async def event_generator():
        def sse(event: str, data: str) -> str:
            return f"event: {event}\ndata: {data}\n\n"

        try:
            # ── Steps 1-4: dados da Riot ─────────────────────────────
            riot     = RiotMatchClient(api_key=RIOT_KEY)
            summoner = await riot.get_summoner_by_name(game_name, tag_line)
            if not summoner:
                yield sse("error", "Jogador não encontrado.")
                return

            rank = await riot.get_summoner_rank(summoner.summoner_id)
            if rank in ("DEFAULT", "UNRANKED", None):
                rank = "Unranked"

            match_ids = await riot.get_match_history(summoner.puuid, count=10)
            if not match_ids or match_index >= len(match_ids):
                yield sse("error", "Partida não encontrada no histórico.")
                return

            match_id = match_ids[match_index]

            match, timeline = await asyncio.gather(
                riot.get_match(match_id),
                riot.get_match_timeline(match_id),
            )
            if not match or not timeline:
                yield sse("error", "Falha ao carregar dados da partida.")
                return

            item_names = await get_item_names(match.game_version)

            builder = ContextBuilder(target_puuid=summoner.puuid, rank=rank)
            context = builder.build(match, timeline, item_names=item_names)

            # ── Meta: dados do jogador/partida para o frontend ───────
            meta = {
                "match_id":              context.match_id,
                "player":                context.player_riot_id,
                "champion":              context.player_champion,
                "position":              context.role,
                "win":                   context.win,
                "duration_min":          context.duration_min,
                "kda":                   context.kda,
                "cs_per_min":            context.cs_per_min,
                "vision_score":          context.vision_score,
                "kill_participation_pct": context.kill_participation_pct,
                "damage_share_pct":      context.damage_share_pct,
                "time_dead_pct":         context.time_dead_pct,
                "rank":                  rank,
            }
            yield sse("meta", json.dumps(meta, ensure_ascii=False))
            # Análise IA removida — coaching agora vem do app local via /coaching/{match_id}
            yield sse("done", "")

        except Exception as e:
            logger.error(f"Erro inesperado no stream: {e}")
            yield sse("error", str(e))

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/feedback")
async def receive_feedback(body: FeedbackRequest, request: Request):
    _require_internal_auth(request)
    if MAKE_FEEDBACK_WEBHOOK_URL:
        asyncio.create_task(send_to_make(body.model_dump(), MAKE_FEEDBACK_WEBHOOK_URL))
    return {"status": "ok"}


@app.get("/analyze/{game_name}/{tag_line}", response_model=AnalyzeResponse)
async def analyze_latest(game_name: str, tag_line: str, request: Request):
    """Atalho: analisa a partida mais recente do jogador via GET."""
    return await analyze_match(AnalyzeRequest(
        game_name=game_name,
        tag_line=tag_line,
        match_index=0,
    ), request)


# ─────────────────────────────────────────
# Live Game Coaching (minimapa ao vivo)
# ─────────────────────────────────────────

_live_session: Optional[LiveCoachSession] = None
_auto_monitor_task: Optional[asyncio.Task] = None
_last_postgame_result: Optional[dict] = None


def _build_match_context(raw: dict, puuid: str) -> str:
    """Monta string de contexto da partida a partir do JSON cru da Riot API."""
    participants = raw.get("info", {}).get("participants", [])
    player = next((p for p in participants if p.get("puuid") == puuid), None)
    if not player:
        return ""
    duration = raw.get("info", {}).get("gameDuration", 1) / 60
    cs = player.get("totalMinionsKilled", 0) + player.get("neutralMinionsKilled", 0)
    return (
        f"Campeão: {player.get('championName')}, "
        f"KDA: {player.get('kills')}/{player.get('deaths')}/{player.get('assists')}, "
        f"CS/min: {cs / max(duration, 1):.1f}, "
        f"Vision Score: {player.get('visionScore', 0)}, "
        f"Resultado: {'Vitória' if player.get('win') else 'Derrota'}, "
        f"Duração: {duration:.0f}min"
    )


async def _auto_monitor_loop():
    """Background loop: detecta jogo automaticamente, captura, analisa no pos-game."""
    global _live_session, _last_postgame_result
    from live_game_client import LiveGameClient

    logger.info("Monitor automatico iniciado — aguardando partidas...")

    while True:
        try:
            # Espera um jogo comecar
            async with LiveGameClient() as client:
                while True:
                    if await client.is_game_active():
                        break
                    await asyncio.sleep(5.0)

            # Jogo detectado — inicia captura
            logger.info("Jogo detectado! Iniciando captura...")
            _live_session = LiveCoachSession()
            await _live_session.start()

            # Espera a sessao terminar (jogo acabou ou erro)
            while _live_session.is_running:
                await asyncio.sleep(1.0)

            logger.info("Sessao encerrada — processando pos-game...")

            # Processa pos-game automaticamente
            payload = _live_session.get_postgame_payload()
            if payload and payload["events"]:
                match_id = payload["match_id"]
                logger.info(f"Analisando {len(payload['events'])} eventos do match {match_id}...")

                # Usa os image_paths direto (ja estao em disco)
                events_data = []
                for evt in payload["events"]:
                    evt_copy = {k: v for k, v in evt.items() if k != "minimap_base64"}
                    events_data.append(evt_copy)

                # Busca contexto da Riot API
                match_context = ""
                if RIOT_KEY and match_id and match_id != "local_session":
                    try:
                        riot = RiotMatchClient(api_key=RIOT_KEY)
                        match_data = await riot.get_match(match_id)
                        if match_data:
                            match_context = _build_match_context(match_data.raw, payload.get("puuid", ""))
                    except Exception as e:
                        logger.error(f"Erro ao buscar dados da Riot API: {e}")

                analysis = await analyze_postgame(events_data, payload["image_paths"], match_context)
                _last_postgame_result = {
                    "match_id": match_id,
                    "analysis": analysis,
                    "event_count": len(events_data),
                }
                logger.info(f"Analise pos-game concluida! ({len(events_data)} eventos)")
                # Upload para o Render (nuvem) para o site exibir
                asyncio.create_task(_upload_coaching_to_render(
                    match_id=match_id,
                    puuid=payload.get("puuid", ""),
                    analysis=analysis,
                ))
            else:
                logger.info("Nenhum evento capturado nesta partida.")
                _last_postgame_result = None

            # Espera antes de voltar a monitorar
            await asyncio.sleep(10.0)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Erro no monitor: {e}")
            await asyncio.sleep(10.0)


@asynccontextmanager
async def _lifespan(app):
    global _auto_monitor_task
    _auto_monitor_task = asyncio.create_task(_auto_monitor_loop())
    yield
    if _auto_monitor_task:
        _auto_monitor_task.cancel()

app.router.lifespan_context = _lifespan


@app.post("/live/start")
async def live_start(request: Request):
    """Inicia o monitoramento ao vivo manualmente (o auto-monitor ja roda em background)."""
    _require_internal_auth(request)
    global _live_session
    if _live_session and _live_session.is_running:
        return {"status": "already_running"}
    _live_session = LiveCoachSession()
    await _live_session.start()
    return {"status": "started"}


@app.post("/live/stop")
async def live_stop(request: Request):
    """Para o monitoramento ao vivo. Retorna dados para upload se a partida acabou."""
    _require_internal_auth(request)
    global _live_session
    if not _live_session or not _live_session.is_running:
        return {"status": "not_running"}
    await _live_session.stop()

    payload = _live_session.get_postgame_payload()
    if payload:
        return {
            "status": "stopped",
            "game_ended": True,
            "match_id": payload["match_id"],
            "event_count": len(payload["events"]),
        }
    return {"status": "stopped", "game_ended": False}


@app.get("/live/postgame")
async def live_postgame(request: Request):
    """Retorna a ultima analise pos-game gerada automaticamente."""
    _require_internal_auth(request)
    if not _last_postgame_result:
        return {"status": "no_analysis"}
    return {"status": "ready", **_last_postgame_result}


@app.get("/live/events")
async def live_events(request: Request):
    """
    SSE stream: emite um evento JSON para cada morte analisada.
    Mantenha a conexão aberta durante a partida.
    """
    _require_internal_auth(request)
    if not _live_session or not _live_session.is_running:
        raise HTTPException(status_code=400, detail="Sessão ao vivo não iniciada. POST /live/start primeiro.")

    async def stream():
        while _live_session and _live_session.is_running:
            try:
                death = await asyncio.wait_for(_live_session.events_queue.get(), timeout=5.0)
                payload = json.dumps(death.to_dict(), ensure_ascii=False)
                yield f"data: {payload}\n\n"
            except asyncio.TimeoutError:
                yield ": heartbeat\n\n"  # mantém a conexão SSE viva

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/live/history")
async def live_history(request: Request):
    """Retorna todos os eventos analisados da sessão atual."""
    _require_internal_auth(request)
    if not _live_session:
        return {"events": []}
    return {"events": [e.to_dict() for e in _live_session.event_history]}


@app.post("/live/upload", response_model=LiveUploadResponse)
async def live_upload(body: LiveUploadRequest, request: Request):
    """Recebe prints de uma partida e retorna a analise pos-game."""
    _require_internal_auth(request)
    if not body.events:
        raise HTTPException(status_code=400, detail="Nenhum evento enviado.")
    if len(body.events) > MAX_EVENTS_PER_UPLOAD:
        raise HTTPException(status_code=422, detail=f"Máximo de {MAX_EVENTS_PER_UPLOAD} eventos por upload.")

    match_id = _validate_match_id(body.match_id)
    prints_dir = _create_temp_upload_dir("upload", match_id)
    image_paths = []
    events_data = []

    try:
        for idx, evt in enumerate(body.events):
            if len(evt.minimap_base64) > MAX_MINIMAP_BASE64_LENGTH:
                raise HTTPException(status_code=413, detail="Imagem minimap_base64 excede tamanho permitido.")
            img_bytes = _decode_base64_image(evt.minimap_base64)
            m = int(evt.game_time_sec // 60)
            s = int(evt.game_time_sec % 60)
            filename = f"evt_{idx:03d}_{m:02d}{s:02d}.png"
            path = os.path.join(prints_dir, filename)
            with open(path, "wb") as f:
                f.write(img_bytes)
            image_paths.append(path)

            events_data.append(evt.model_dump(exclude={"minimap_base64"}))

        match_context = ""
        if RIOT_KEY:
            riot = RiotMatchClient(api_key=RIOT_KEY)
            match_data = await riot.get_match(match_id)
            if match_data:
                match_context = _build_match_context(match_data.raw, body.puuid)

        analysis = await analyze_postgame(events_data, image_paths, match_context)

        return LiveUploadResponse(
            match_id=match_id,
            analysis=analysis,
            event_count=len(body.events),
        )
    finally:
        shutil.rmtree(prints_dir, ignore_errors=True)


# ─────────────────────────────────────────
# Coaching Analysis
# ─────────────────────────────────────────

@app.get("/coaching/status", response_model=dict[str, CoachingStatusResponse])
async def coaching_status(ids: str, request: Request, riot_id: str = ""):
    """
    Retorna status seguro de coaching por match_id.
    Query param: ids=BR1_1,BR1_2,BR1_3&riot_id=nome#tag
    """
    await _check_public_limits(request, "coaching-status")
    match_ids = _parse_match_ids(ids)
    if not match_ids:
        return {}
    riot_id = _validate_riot_id(riot_id, required=REQUIRE_RIOT_ID_FOR_COACHING)
    result: dict[str, CoachingStatusResponse] = {}
    rows_by_match: dict[str, dict] = {}

    if SUPABASE_URL and SUPABASE_KEY:
        try:
            sb = await get_supabase()
            if sb is not None:
                rows_by_match = await _fetch_coaching_status_rows(sb, match_ids, riot_id)
        except Exception as e:
            logger.error(f"Erro ao buscar status batch de coaching: {e}")

    for mid in match_ids:
        row = rows_by_match.get(mid, {})
        has_analysis = bool(
            (row.get("coaching_analysis") or "").strip() or (row.get("feedback_geral") or "").strip()
        )
        snapshot = row.get("pipeline_snapshot") if isinstance(row.get("pipeline_snapshot"), dict) else None
        if row.get("external_status"):
            snapshot = dict(snapshot or {})
            snapshot["external_status"] = row["external_status"]

        if snapshot is None:
            snapshot = await get_pipeline_snapshot(mid, riot_id)
        if snapshot is None and riot_id:
            pending_local = await get_pending_local_evidence(mid, riot_id)
            if pending_local:
                snapshot = {"status": "incomplete_evidence", "external_status": "pending"}
        if snapshot and snapshot.get("has_analysis_text"):
            has_analysis = True

        status = _normalize_public_status(snapshot, has_analysis)
        message = None
        if _missing_local_evidence(snapshot):
            status = "insufficient_data"
            has_analysis = False
            message = UNAVAILABLE_COACHING_MESSAGE
        result[mid] = CoachingStatusResponse(
            match_id=mid,
            has_analysis=has_analysis,
            status=status,
            message=message,
        )

    return result


@app.post("/coaching/save")
async def coaching_save(body: CoachingSaveRequest, request: Request):
    """Recebe análise pos-game do app local e salva no Supabase."""
    _require_internal_auth(request)
    match_id = _validate_match_id(body.match_id)
    if not body.analysis.strip():
        raise HTTPException(status_code=400, detail="Análise vazia.")
    riot_scope = _validate_riot_id(body.riot_id) or body.puuid.strip()
    await save_coaching_analysis(match_id, body.analysis, riot_id=riot_scope)
    await save_pipeline_snapshot(
        match_id,
        riot_scope,
        {
            "stage": "delivery",
            "status": "ready",
            "reason_codes": [],
            "external_status": "ready",
            "has_analysis_text": True,
        },
    )
    return {"status": "saved", "match_id": match_id}


@app.post("/coaching/{match_id}/regenerate", response_model=CoachingRegenerateResponse)
async def coaching_regenerate(match_id: str, request: Request, riot_id: str = ""):
    """Bloqueia regeneracao no v1 para nao-pagantes com status explicito."""

    await _check_public_limits(request, "coaching-regenerate")
    match_id = _validate_match_id(match_id)
    riot_id = _validate_riot_id(riot_id, required=REQUIRE_RIOT_ID_FOR_COACHING)
    await save_pipeline_snapshot(
        match_id,
        riot_id,
        {
            "stage": "delivery",
            "status": "blocked",
            "reason_codes": ["paid_regeneration_required"],
            "external_status": "insufficient_data",
            "has_analysis_text": False,
        },
    )
    return CoachingRegenerateResponse(
        match_id=match_id,
        status="blocked",
        message=PAID_REGEN_MESSAGE,
    )


@app.get("/coaching/{match_id}", response_model=CoachingAnalysisResponse)
async def coaching_get(match_id: str, request: Request, riot_id: str = ""):
    """Retorna a análise de coaching para um match_id, se existir."""
    await _check_public_limits(request, "coaching-get")
    match_id = _validate_match_id(match_id)
    riot_id = _validate_riot_id(riot_id, required=REQUIRE_RIOT_ID_FOR_COACHING)
    analysis = await get_coaching_analysis(match_id, riot_id=riot_id)
    snapshot = await get_pipeline_snapshot(match_id, riot_id)
    has_analysis = analysis is not None or bool((snapshot or {}).get("has_analysis_text"))
    if snapshot is None and riot_id:
        pending_local = await get_pending_local_evidence(match_id, riot_id)
        if pending_local:
            snapshot = {"status": "incomplete_evidence", "external_status": "pending"}

    status = _normalize_public_status(snapshot, has_analysis)
    message = None
    if _missing_local_evidence(snapshot):
        status = "insufficient_data"
        has_analysis = False
        analysis = None
        message = UNAVAILABLE_COACHING_MESSAGE

    return CoachingAnalysisResponse(
        match_id=match_id,
        has_analysis=has_analysis,
        status=status,
        analysis=analysis,
        message=message,
    )


@app.get("/downloads/app")
async def download_app_redirect(request: Request):
    """Esconde a URL final do instalador atras do backend."""
    await _check_public_limits(request, "download-app")
    return RedirectResponse(url=_get_download_app_url(), status_code=307)


# ─────────────────────────────────────────
# Match Scoreboard
# ─────────────────────────────────────────

@app.get("/match/{match_id}")
async def get_match_by_id(match_id: str, request: Request, puuid: str = ""):
    """
    Retorna os dados completos da partida pelo match_id, no formato esperado pelo frontend.
    Tenta Supabase primeiro; se não encontrar, faz fallback para Riot API.
    """
    await _check_public_limits(request, "match")
    match_id = _validate_match_id(match_id)
    try:
        sb = await get_supabase()
        if sb is not None:
            row = await _fetch_match_row(sb, match_id)
            if row:
                return _sanitize_match_payload(row)

        # Fallback: build basic payload from Riot API
        riot = RiotMatchClient(api_key=RIOT_KEY)
        match_data = await riot.get_match(match_id)
        if not match_data:
            raise HTTPException(status_code=404, detail="Partida não encontrada.")

        info = match_data.raw.get("info", {})
        participants = info.get("participants", [])
        duration_min = round(info.get("gameDuration", 0) / 60)

        # Find the target player by puuid (if provided)
        target = None
        if puuid:
            target = next((p for p in participants if p.get("puuid") == puuid), None)
        if not target and participants:
            target = participants[0]
        if not target:
            raise HTTPException(status_code=404, detail="Partida não encontrada.")

        cs = target.get("totalMinionsKilled", 0) + target.get("neutralMinionsKilled", 0)
        riot_name = (target.get("riotIdGameName") or "").strip()
        riot_tag = (target.get("riotIdTagline") or "").strip()
        display_name = f"{riot_name}#{riot_tag}" if riot_name and riot_tag else riot_name

        team_id = target.get("teamId", 100)
        team_dmg = sum(p.get("totalDamageDealtToChampions", 0) for p in participants if p.get("teamId") == team_id) or 1
        team_kills = sum(p.get("kills", 0) for p in participants if p.get("teamId") == team_id) or 1
        player_dmg = target.get("totalDamageDealtToChampions", 0)

        return {
            "match_id": match_id,
            "riot_id": display_name,
            "summoner_name": display_name,
            "champion": target.get("championName", ""),
            "kills": target.get("kills", 0),
            "deaths": target.get("deaths", 0),
            "assists": target.get("assists", 0),
            "win": bool(target.get("win", False)),
            "duration_min": duration_min,
            "position": target.get("teamPosition", ""),
            "cs_per_min": round(cs / max(duration_min, 1), 1),
            "vision_score": target.get("visionScore", 0),
            "kill_participation_pct": round((target.get("kills", 0) + target.get("assists", 0)) / max(team_kills, 1) * 100, 1),
            "damage_share_pct": round(player_dmg / max(team_dmg, 1) * 100, 1),
            "items": [target.get(f"item{i}", 0) for i in range(7)],
            "allies": [],
            "puuid": target.get("puuid", ""),
            "rank": "",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar match {match_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar partida.")


@app.get("/match/{match_id}/scoreboard", response_model=ScoreboardResponse)
async def get_scoreboard(match_id: str, request: Request, puuid: str = ""):
    """Retorna dados completos dos 10 jogadores de uma partida."""
    await _check_public_limits(request, "match-scoreboard")
    match_id = _validate_match_id(match_id)
    if puuid and len(puuid) > 120:
        raise HTTPException(status_code=422, detail="puuid inválido.")
    riot = RiotMatchClient(api_key=RIOT_KEY)
    match_data = await riot.get_match(match_id)
    if not match_data:
        raise HTTPException(status_code=404, detail="Partida não encontrada.")

    info         = match_data.raw.get("info", {})
    participants = info.get("participants", [])
    duration_min = info.get("gameDuration", 0) / 60

    # Pré-calcula dano total por time para damage_share_pct
    team_dmg_totals: dict[int, int] = {}
    for p in participants:
        tid = p["teamId"]
        team_dmg_totals[tid] = team_dmg_totals.get(tid, 0) + p.get("totalDamageDealtToChampions", 0)

    teams_raw: dict[int, dict] = {
        100: {"side": "blue", "win": False, "players": []},
        200: {"side": "red",  "win": False, "players": []},
    }

    for p in participants:
        tid          = p["teamId"]
        if tid not in teams_raw:
            continue
        player_dmg   = p.get("totalDamageDealtToChampions", 0)
        team_dmg     = team_dmg_totals.get(tid, 1)
        cs           = p.get("totalMinionsKilled", 0) + p.get("neutralMinionsKilled", 0)
        riot_name    = (p.get("riotIdGameName") or "").strip()
        riot_tag     = (p.get("riotIdTagline") or "").strip()
        legacy_name  = (p.get("summonerName") or "").strip()
        display_name = f"{riot_name}#{riot_tag}" if riot_name and riot_tag else (riot_name or legacy_name)

        if p.get("win"):
            teams_raw[tid]["win"] = True

        teams_raw[tid]["players"].append(ScoreboardPlayer(
            puuid          = p.get("puuid", ""),
            summoner_name  = display_name,
            champion       = p["championName"],
            position       = p.get("teamPosition", ""),
            kills          = p["kills"],
            deaths         = p["deaths"],
            assists        = p["assists"],
            cs             = cs,
            cs_per_min     = round(cs / max(duration_min, 1), 1),
            total_damage   = player_dmg,
            damage_share_pct = round(player_dmg / max(team_dmg, 1) * 100, 1),
            gold_earned    = p.get("goldEarned", 0),
            vision_score   = p.get("visionScore", 0),
            items          = [p.get(f"item{i}", 0) for i in range(7)],
            summoner1_id   = p.get("summoner1Id", 0),
            summoner2_id   = p.get("summoner2Id", 0),
            is_target      = (p.get("puuid", "") == puuid) if puuid else False,
        ))

    teams = [
        ScoreboardTeam(side=t["side"], win=t["win"], players=t["players"])
        for t in teams_raw.values()
    ]

    return ScoreboardResponse(
        match_id     = match_id,
        duration_min = round(duration_min, 1),
        teams        = teams,
    )


# ─────────────────────────────────────────
# Local App Endpoints
# ─────────────────────────────────────────

@app.post("/local/upload", response_model=LocalUploadResponse)
async def local_upload(body: LocalUploadRequest, request: Request):
    """Recebe dados de partida do CoachApp local. Processa de forma assíncrona."""
    _require_local_app_auth(request)

    riot_id = _validate_riot_id(body.riot_id, required=True)
    match_id = _validate_match_id(body.match_id) if body.match_id else ""
    await _check_local_upload_limits(request, riot_id)

    # Marca job como em processamento
    _local_jobs[riot_id] = None

    # Dispara processamento em background
    asyncio.create_task(_process_local_upload(riot_id, body.events, match_id, body.player_map))

    return LocalUploadResponse(accepted=True, job_id=riot_id)


_RANKED_QUEUES = {420, 440}  # Ranked Solo/Duo, Ranked Flex

_MATCH_REGION = {
    "BR1": "americas", "NA1": "americas", "LA1": "americas", "LA2": "americas",
    "EUW1": "europe", "EUN1": "europe", "TR1": "europe", "RU": "europe",
    "KR": "asia", "JP1": "asia",
    "OC1": "sea", "PH2": "sea", "SG2": "sea", "TH2": "sea", "TW2": "sea", "VN2": "sea",
}

def _match_region(match_id: str) -> str:
    prefix = match_id.split("_")[0]
    return _MATCH_REGION.get(prefix, "americas")


def _parse_game_time(time_str: str) -> float:
    """Converte '03:45' para 225.0 segundos."""
    try:
        parts = time_str.split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except (ValueError, IndexError):
        return 0.0


async def _is_ranked_match(match_id: str) -> bool:
    """Retorna True se a partida é Ranked Solo/Duo ou Ranked Flex."""
    if match_id.startswith("local_"):
        logger.warning(f"Match ID '{match_id}' é local (fallback) — considerado não-ranqueado. Isso indica falha na Riot API.")
        return False
    try:
        region = _match_region(match_id)
        url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers={"X-Riot-Token": RIOT_KEY})
            if resp.status_code == 200:
                queue_id = resp.json().get("info", {}).get("queueId", 0)
                is_ranked = queue_id in _RANKED_QUEUES
                logger.info(f"Match {match_id}: queueId={queue_id}, ranked={is_ranked}")
                return is_ranked
            if resp.status_code == 403:
                logger.error(f"❌ Riot API 403 ao checar ranked — RIOT_API_KEY expirada! Renove em developer.riotgames.com")
            else:
                logger.warning(f"Riot API retornou {resp.status_code} ao checar ranked para {match_id}")
    except Exception as e:
        logger.warning(f"Falha ao checar se partida é ranked ({match_id}): {e}")
    return False


async def _process_local_upload(riot_id: str, events: list[LocalEventUpload], client_match_id: str = "", player_map: dict = None) -> None:
    """Processa upload do app local: busca match_id, analisa, salva no Supabase."""
    if player_map is None:
        player_map = {}
    logger.info(f"Processando upload local: riot_id={riot_id}, {len(events)} eventos, client_match_id={client_match_id}")
    prints_dir = ""
    try:
        match_id = None

        # Se o cliente enviou um match_id válido (BR1_xxx), usar diretamente
        if client_match_id and not client_match_id.startswith(("local_", "pending_")):
            match_id = _validate_match_id(client_match_id)
            logger.info(f"Usando match_id do cliente: {match_id}")
        elif DEBUG_MODE and client_match_id:
            # Em debug mode, aceitar local_* como ID único (bot games)
            match_id = _validate_match_id(client_match_id)
            logger.info(f"🔧 DEBUG_MODE: usando match_id local do cliente: {match_id}")
        else:
            # Busca PUUID e match_id via Riot API
            puuid = None

            if "#" in riot_id:
                game_name, tag_line = riot_id.split("#", 1)
                async with httpx.AsyncClient(timeout=10.0) as client:
                    url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
                    try:
                        resp = await client.get(url, headers={"X-Riot-Token": RIOT_KEY})
                        if resp.status_code == 200:
                            puuid = resp.json().get("puuid")
                            logger.info(f"PUUID encontrado para {riot_id}")
                        elif resp.status_code == 403:
                            logger.error(f"❌ Riot API retornou 403 (Forbidden) — RIOT_API_KEY provavelmente expirada!")
                        else:
                            logger.warning(f"Riot API retornou {resp.status_code} ao buscar PUUID de {riot_id}")
                    except Exception as e:
                        logger.warning(f"Falha ao buscar PUUID de {riot_id}: {e}")
            else:
                logger.warning(f"riot_id '{riot_id}' não contém '#' — não é possível buscar PUUID")

            if puuid:
                riot = RiotMatchClient(api_key=RIOT_KEY)
                for attempt in range(3):
                    match_ids = await riot.get_match_history(puuid, count=1)
                    if match_ids:
                        match_id = match_ids[0]
                        logger.info(f"Match ID encontrado via API: {match_id}")
                        break
                    if attempt < 2:
                        logger.info(f"Match history vazio, tentativa {attempt+1}/3 — aguardando 10s...")
                        await asyncio.sleep(10)
                else:
                    logger.warning(f"Nenhum match_id encontrado no histórico de {riot_id} após 3 tentativas")

        # Fallback: usar client_match_id (mesmo local_*) ou gerar um
        if not match_id:
            if client_match_id:
                match_id = _validate_match_id(client_match_id)
            else:
                match_id = _validate_match_id(f"local_{_safe_temp_fragment(riot_id)}_{int(time.time())}")
            logger.warning(f"Usando match_id fallback: {match_id}")

        # Filtra partidas não ranqueadas — só processa Ranked Solo/Duo e Flex
        # DEBUG_MODE=true permite qualquer tipo de partida (bot, normal, etc.)
        if not DEBUG_MODE:
            if not match_id.startswith("local_") and not await _is_ranked_match(match_id):
                logger.info(f"Partida ignorada (não ranqueada): {match_id}")
                _local_jobs.pop(riot_id, None)
                return
        else:
            logger.info(f"🔧 DEBUG_MODE ativo — processando qualquer tipo de partida")

        # Salva imagens temporariamente para análise
        prints_dir = _create_temp_upload_dir("local", match_id)

        image_paths = []
        events_data = []
        for idx, evt in enumerate(events):
            if evt.minimap_base64:
                img_bytes = _decode_base64_image(evt.minimap_base64)
                filename = f"evt_{idx:03d}_{int(_parse_game_time(evt.game_time)):05d}.png"
                path = os.path.join(prints_dir, filename)
                with open(path, "wb") as f:
                    f.write(img_bytes)
                image_paths.append(path)
            events_data.append({
                "event_type": evt.event_type,
                "game_time":  evt.game_time,
                "game_time_sec": _parse_game_time(evt.game_time),
                "champion":   evt.champion,
                "killer":     evt.killer,
                "victim":     getattr(evt, "victim", None),
                "detail":     getattr(evt, "detail", ""),
                "assisters":  getattr(evt, "assisters", []),
            })

        snapshot = build_analysis_evidence_bundle(
            riot_id=riot_id,
            local_events=events,
            match_id=match_id,
            image_paths=image_paths,
            analysis_payload={"player_map": dict(player_map)},
        )
        if snapshot.bundle is None or snapshot.latest_checkpoint is None:
            raise ValueError("Falha ao criar evidence bundle para upload local.")

        analysis_gate = gate_pipeline_stage(
            PipelineStage.ANALYSIS_GENERATION,
            bundle=snapshot.bundle,
            checkpoint=snapshot.latest_checkpoint,
            allow_degraded=False,
        )
        if not analysis_gate.allows_progress():
            pipeline_status = "blocked"
            if snapshot.bundle.source is EvidenceSource.LOCALHOST_ONLY:
                pipeline_status = "blocked"
            elif snapshot.bundle.source is EvidenceSource.RIOT_ONLY:
                pipeline_status = "degraded_safe"
            await save_pending_local_evidence(
                match_id,
                riot_id,
                local_events=events_data,
                image_paths=image_paths,
                player_map=dict(player_map),
                source=snapshot.bundle.source.value,
            )
            await save_pipeline_snapshot(
                match_id,
                riot_id,
                {
                    "stage": analysis_gate.stage.value,
                    "status": pipeline_status,
                    "reason_codes": [code.value for code in analysis_gate.reason_codes],
                    "external_status": "pending" if pipeline_status == "degraded_safe" else "insufficient_data",
                    "has_analysis_text": False,
                },
            )
            logger.info(
                "Upload local armazenado como pendente: match_id=%s source=%s status=%s",
                match_id,
                snapshot.bundle.source.value,
                pipeline_status,
            )
            _local_jobs[riot_id] = match_id
            return

        pending_local = await get_pending_local_evidence(match_id, riot_id)
        if pending_local:
            merged_events = list(pending_local.get("local_events", [])) + events_data
            await delete_pending_local_evidence(match_id, riot_id)
        else:
            merged_events = events_data

        logger.info(f"Analisando {len(image_paths)} imagens para {match_id}...")
        analysis = await analyze_postgame(
            merged_events,
            image_paths,
            bundle=snapshot.bundle,
        )
        logger.info(f"Análise concluída para {match_id} ({len(analysis)} chars). Salvando...")
        await save_coaching_analysis(match_id, analysis, riot_id=riot_id)
        await save_pipeline_snapshot(
            match_id,
            riot_id,
            {
                "stage": "delivery",
                "status": "ready",
                "reason_codes": [],
                "external_status": "ready",
                "has_analysis_text": True,
            },
        )

        _local_jobs[riot_id] = match_id
    except Exception as e:
        logger.error(f"Erro em _process_local_upload: {e}")
        _local_jobs.pop(riot_id, None)
    finally:
        if prints_dir:
            shutil.rmtree(prints_dir, ignore_errors=True)


@app.get("/local/status")
async def local_status(riot_id: str, request: Request):
    """Verifica se a análise do último jogo do riot_id está pronta."""
    _require_local_app_auth(request)
    riot_id = _validate_riot_id(riot_id, required=True)

    match_id = _local_jobs.get(riot_id)
    if match_id is None:
        return {"ready": False, "status": "pending"}

    # Verifica se já está no Supabase
    analysis = await get_coaching_analysis(match_id, riot_id=riot_id)
    snapshot = await get_pipeline_snapshot(match_id, riot_id)
    if snapshot is None:
        pending_local = await get_pending_local_evidence(match_id, riot_id)
        if pending_local:
            snapshot = {"status": "incomplete_evidence", "external_status": "pending"}
    status = _normalize_public_status(snapshot, analysis is not None)

    if analysis:
        _local_jobs.pop(riot_id, None)
        return {"ready": True, "status": status, "match_id": match_id}

    return {"ready": status == "ready", "status": status, "match_id": match_id}


