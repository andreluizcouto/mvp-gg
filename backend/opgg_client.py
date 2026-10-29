"""
Cliente do OP.GG MCP Server (oficial, público, sem chave)
Busca a tier list de campeões por rota para a tela de Tier List.
Os dados são do OP.GG e a tela credita a fonte.
"""

import ast
import asyncio
import json
import logging
import re
import time
from typing import Optional

import httpx

from riot_client import _cache_get, _cache_set, _resolve_ddragon_version

logger = logging.getLogger(__name__)

OPGG_MCP_URL = "https://mcp-api.op.gg/mcp"
POSITIONS = ("top", "jungle", "mid", "adc", "support")
TIER_FIELDS = (
    "champion", "tier", "rank", "rank_prev", "win_rate", "pick_rate",
    "ban_rate", "kda", "play", "is_rip",
)

CACHE_TTL = {
    "tierlist":          60 * 60 * 6,    # 6 horas — a meta muda por patch
    "ddragon_champions": 60 * 60 * 24,
    "champion_elo":      60 * 60 * 12,   # força de um campeão num elo (1 chamada cada)
}

# Elos da faixa "forte em": o OP.GG aceita o elo exato ou faixas com "_plus".
# Sem elo, o OP.GG usa Esmeralda+ (é o que a tier list principal mostra).
ELO_TIERS = (
    ("iron", "Ferro"), ("bronze", "Bronze"), ("silver", "Prata"), ("gold", "Ouro"),
    ("platinum", "Platina"), ("emerald", "Esmeralda"), ("diamond", "Diamante"), ("master_plus", "Mestre+"),
)
ELO_CHAMPIONS_PER_LANE = 6
_opgg_semaphore = asyncio.Semaphore(16)   # não abrir dezenas de conexões de uma vez no OP.GG
# Cálculo em andamento por rota: um pedido novo espera o que já está rodando em vez de repetir.
_inflight: dict[str, asyncio.Task] = {}
_warm_task: Optional[asyncio.Task] = None

_MCP_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


# ─────────────────────────────────────────
# Protocolo MCP (Streamable HTTP)
# ─────────────────────────────────────────

def _parse_rpc_body(text: str) -> dict:
    """A resposta pode vir como JSON puro ou como evento SSE (`data: {...}`)."""
    text = text.strip()
    if text.startswith("{"):
        return json.loads(text)
    for line in text.splitlines():
        if line.startswith("data:"):
            return json.loads(line[5:].strip())
    raise ValueError("Resposta MCP sem JSON.")


async def _call_tool(name: str, arguments: dict) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        init = await client.post(OPGG_MCP_URL, headers=_MCP_HEADERS, json={
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "mvp.gg", "version": "1.0"},
            },
        })
        init.raise_for_status()
        headers = dict(_MCP_HEADERS)
        session_id = init.headers.get("mcp-session-id")
        if session_id:
            headers["Mcp-Session-Id"] = session_id

        await client.post(OPGG_MCP_URL, headers=headers, json={
            "jsonrpc": "2.0", "method": "notifications/initialized",
        })
        r = await client.post(OPGG_MCP_URL, headers=headers, json={
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        })
        r.raise_for_status()

    body = _parse_rpc_body(r.text)
    if "error" in body:
        raise RuntimeError(f"OP.GG MCP erro: {body['error']}")
    content = body.get("result", {}).get("content", [])
    return "".join(part.get("text", "") for part in content if part.get("type") == "text")


# ─────────────────────────────────────────
# Parser do formato de saída do OP.GG
# ─────────────────────────────────────────
#
# O servidor devolve um texto assim:
#   class Positions: top,mid,jungle,adc,support
#   class Top: champion,is_rip,play,win_rate,...
#   LolListLaneMetaChampions(Data(Positions([Top("Malphite",false,110012,...),...],[Top(...)],...)))
# As linhas `class X: a,b,c` dizem a ordem dos campos de cada construtor. Quando as rotas
# pedem os mesmos campos, todas reaproveitam a mesma classe (Top); a ordem das listas
# dentro de Positions(...) segue a linha `class Positions`.

_CLASS_RE = re.compile(r"^class (\w+): (.+)$", re.M)
_ROW_RE = re.compile(r'\b(\w+)\(((?:"[^"]*"|[^()"])*)\)')
_JSON_LITERALS = {"true": "True", "false": "False", "null": "None"}


def _split_top_level_lists(body: str) -> list[str]:
    """Separa `[...],[...]` do nível de cima, ignorando colchetes dentro de strings."""
    lists, depth, start, in_str = [], 0, 0, False
    for i, ch in enumerate(body):
        if ch == '"':
            in_str = not in_str
        elif in_str:
            continue
        elif ch == "[":
            if depth == 0:
                start = i + 1
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                lists.append(body[start:i])
    return lists


def _literal(args: str) -> tuple:
    # Troca true/false/null fora de strings pelos equivalentes Python.
    parts = re.split(r'("[^"]*")', args)
    parts = [p if p.startswith('"') else re.sub(r"\b(true|false|null)\b", lambda m: _JSON_LITERALS[m.group(1)], p) for p in parts]
    return ast.literal_eval(f"({''.join(parts)},)")


def _parse_lane_meta(text: str) -> dict[str, list[dict]]:
    field_order = {name: [f.strip() for f in fields.split(",")] for name, fields in _CLASS_RE.findall(text)}
    order = field_order.get("Positions", list(POSITIONS))
    marker = text.find("Positions(")
    if marker < 0:
        return {}

    result: dict[str, list[dict]] = {}
    for position, chunk in zip(order, _split_top_level_lists(text[marker + len("Positions("):])):
        rows = []
        for cls, args in _ROW_RE.findall(chunk):
            fields = field_order.get(cls)
            if not fields:
                continue
            try:
                values = _literal(args)
            except (ValueError, SyntaxError):
                continue
            rows.append(dict(zip(fields, values)))
        result[position] = rows
    return result


# ─────────────────────────────────────────
# Data Dragon: nome do campeão → chave da imagem
# ─────────────────────────────────────────

def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


async def _champion_keys() -> tuple[str, dict[str, str]]:
    version = await _resolve_ddragon_version("")
    cache_key = f"ddragon_champions_{version}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return version, cached

    url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json"
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, timeout=10)
        if r.status_code == 200:
            keys = {_normalize_name(c["name"]): c["id"] for c in r.json().get("data", {}).values()}
            _cache_set(cache_key, keys, CACHE_TTL["ddragon_champions"])
            return version, keys
        logger.error(f"Erro {r.status_code} ao buscar campeões do DDragon {version}.")
    except Exception as e:
        logger.error(f"Falha ao buscar campeões do DDragon: {e}")
    return version, {}


# ─────────────────────────────────────────
# Tier list
# ─────────────────────────────────────────

async def get_tierlist() -> Optional[dict]:
    """Retorna { positions: {top: [...], ...}, ddragon_version, updated_at } ou None em caso de erro."""
    cached = _cache_get("tierlist")
    if cached is not None:
        return cached

    fields = [f"data.positions.{p}[].{{{','.join(TIER_FIELDS)}}}" for p in POSITIONS]
    try:
        text = await _call_tool("lol_list_lane_meta_champions", {
            "position": "all",
            "lang": "en_US",
            "desired_output_fields": fields,
        })
        positions = _parse_lane_meta(text)
    except Exception as e:
        logger.error(f"Falha ao buscar tier list do OP.GG: {e}")
        return None

    if not any(positions.values()):
        logger.error("Tier list do OP.GG veio vazia.")
        return None

    version, keys = await _champion_keys()
    for rows in positions.values():
        for row in rows:
            row["champion_key"] = keys.get(_normalize_name(str(row.get("champion", ""))), "")

    payload = {
        "positions": positions,
        "ddragon_version": version,
        "updated_at": int(time.time()),
        "source": "OP.GG",
    }
    _cache_set("tierlist", payload, CACHE_TTL["tierlist"])
    logger.info("Tier list do OP.GG carregada: " + ", ".join(f"{p}={len(r)}" for p, r in positions.items()))
    return payload


# ─────────────────────────────────────────
# Força de cada campeão por elo ("forte em")
# ─────────────────────────────────────────

_AVERAGE_RE = re.compile(r"AverageStats\(([^()]*)\)")
_ELO_FIELDS = ("win_rate", "tier", "rank", "play")


async def _champion_elo(champion_key: str, lane: str, elo: str) -> Optional[dict]:
    cache_key = f"champion_elo_{champion_key}_{lane}_{elo}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached or None

    fields = [f"data.summary.average_stats.{{{','.join(_ELO_FIELDS)}}}"]
    try:
        async with _opgg_semaphore:
            text = await _call_tool("lol_get_champion_analysis", {
                "game_mode": "ranked", "champion": champion_key.upper(), "position": lane,
                "tier": elo, "desired_output_fields": fields,
            })
        order = dict(_CLASS_RE.findall(text)).get("AverageStats", ",".join(_ELO_FIELDS))
        match = _AVERAGE_RE.search(text)
        stats = dict(zip([f.strip() for f in order.split(",")], _literal(match.group(1)))) if match else {}
    except Exception as e:
        logger.warning(f"Falha ao buscar {champion_key}/{lane}/{elo} no OP.GG: {e}")
        return None

    # Guarda também o "sem dados" (dict vazio) para não repetir a chamada.
    _cache_set(cache_key, stats, CACHE_TTL["champion_elo"])
    return stats or None


def _lane_task(lane: str) -> asyncio.Task:
    task = _inflight.get(lane)
    if task is None:
        task = asyncio.get_running_loop().create_task(_compute_lane_elo_strength(lane))
        _inflight[lane] = task
        task.add_done_callback(lambda _t, done=lane: _inflight.pop(done, None))
    return task


async def get_lane_elo_strength(lane: str) -> Optional[dict]:
    """
    Para os primeiros campeões da rota (tier list Esmeralda+), o tier e o winrate em cada elo.
    { lane, elos: [{id, label}], champions: { "Ahri": [{elo, tier, win_rate, rank, play} | None, ...] } }
    """
    # shield: se quem pediu desistir (timeout), o cálculo continua e fica no cache.
    return await asyncio.shield(_lane_task(lane))


async def _compute_lane_elo_strength(lane: str, limit: int = ELO_CHAMPIONS_PER_LANE) -> Optional[dict]:
    tierlist = await get_tierlist()
    if tierlist is None or lane not in tierlist["positions"]:
        return None

    rows = [r for r in tierlist["positions"][lane] if not r.get("is_rip") and r.get("champion_key")][:limit]
    results = await asyncio.gather(*[
        _champion_elo(row["champion_key"], lane, elo) for row in rows for elo, _ in ELO_TIERS
    ])

    champions: dict[str, list] = {}
    for i, row in enumerate(rows):
        chunk = results[i * len(ELO_TIERS):(i + 1) * len(ELO_TIERS)]
        champions[row["champion_key"]] = [
            {"elo": elo, **stats} if stats else None
            for (elo, _), stats in zip(ELO_TIERS, chunk)
        ]

    return {
        "lane": lane,
        "elos": [{"id": elo, "label": label} for elo, label in ELO_TIERS],
        "champions": champions,
    }


def warm_all_lanes() -> None:
    """Calcula todas as rotas em segundo plano, uma de cada vez e a mid primeiro (é a que a home abre)."""
    global _warm_task
    if _warm_task is not None and not _warm_task.done():
        return

    async def run():
        for lane in ("mid", "top", "jungle", "adc", "support"):
            try:
                await _lane_task(lane)
            except Exception as e:
                logger.warning(f"Falha ao pré-calcular a rota {lane}: {e}")

    _warm_task = asyncio.get_running_loop().create_task(run())
