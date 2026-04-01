"""
Riot Match-V5 API Client
Busca dados históricos de partidas para análise de coach.
Cache em disco (JSON local) para evitar rate limit da Riot API.
"""

import httpx
import json
import logging
import os
import time
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

PLATFORM = "br1"
REGION   = "americas"

BASE_PLATFORM = f"https://{PLATFORM}.api.riotgames.com"
BASE_REGION   = f"https://{REGION}.api.riotgames.com"

# ─────────────────────────────────────────
# Cache em disco
# ─────────────────────────────────────────

CACHE_DIR = ".cache"

CACHE_TTL = {
    "match":           60 * 60 * 24 * 7,
    "timeline":        60 * 60 * 24 * 7,
    "summoner":        60 * 60 * 1,
    "history":         60 * 5,             # 5 minutos — partidas novas aparecem rápido
    "rank":            60 * 15,            # 15 minutos
    "items":           60 * 60 * 24 * 7,
    "ddragon_versions": 60 * 60 * 24,
}


def _cache_path(key: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    safe_key = key.replace("/", "_").replace(":", "_").replace(" ", "_").replace("#", "_")
    return os.path.join(CACHE_DIR, f"{safe_key}.json")


def _cache_get(key: str) -> Optional[dict]:
    path = _cache_path(key)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            cached = json.load(f)
        ttl      = cached.get("_ttl", 0)
        saved_at = cached.get("_saved_at", 0)
        if ttl > 0 and time.time() - saved_at > ttl:
            os.remove(path)
            logger.debug(f"Cache expirado: {key}")
            return None
        logger.debug(f"Cache hit: {key}")
        return cached.get("data")
    except Exception as e:
        logger.error(f"Erro ao ler cache ({key}): {e}")
        return None


def _cache_set(key: str, data, ttl: int) -> None:
    path = _cache_path(key)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"data": data, "_saved_at": time.time(), "_ttl": ttl}, f)
        logger.debug(f"Cache salvo: {key} (TTL: {ttl}s)")
    except Exception as e:
        logger.error(f"Erro ao salvar cache ({key}): {e}")


def cache_invalidate(prefix: str) -> int:
    """Remove todas as entradas de cache que começam com prefix. Retorna quantidade removida."""
    removed = 0
    if not os.path.exists(CACHE_DIR):
        return 0
    safe_prefix = prefix.replace("/", "_").replace(":", "_").replace(" ", "_").replace("#", "_")
    for f in os.listdir(CACHE_DIR):
        if f.startswith(safe_prefix) and f.endswith(".json"):
            os.remove(os.path.join(CACHE_DIR, f))
            removed += 1
    return removed



# ─────────────────────────────────────────
# Dataclasses de retorno
# ─────────────────────────────────────────

@dataclass
class SummonerInfo:
    puuid: str
    summoner_id: str
    name: str
    level: int
    profile_icon_id: int


@dataclass
class MatchParticipant:
    puuid: str
    riot_id: str
    champion_name: str
    team_id: int
    position: str
    kills: int
    deaths: int
    assists: int
    creep_score: int
    gold_earned: int
    vision_score: int
    wards_placed: int
    wards_killed: int
    detector_wards_placed: int
    items: list[int]
    win: bool
    champion_level: int
    damage_dealt: int
    damage_taken: int
    time_spent_dead: int
    summoner_spells: list[str]


@dataclass
class MatchTimeline:
    frames: list = field(default_factory=list)
    events: list = field(default_factory=list)
    participants: list = field(default_factory=list)


@dataclass
class MatchData:
    match_id: str
    game_duration: int
    game_mode: str
    game_version: str
    participants: list[MatchParticipant] = field(default_factory=list)
    timeline: Optional[MatchTimeline] = None
    raw: dict = field(default_factory=dict)


# ─────────────────────────────────────────
# Cliente principal
# ─────────────────────────────────────────

class RiotMatchClient:
    def __init__(self, api_key: str):
        self._api_key = api_key
        self._headers = {"X-Riot-Token": api_key}

    async def _get(self, client: httpx.AsyncClient, url: str) -> Optional[dict]:
        try:
            r = await client.get(url, headers=self._headers, timeout=10)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 403:
                logger.error("Chave de API inválida ou expirada.")
            elif r.status_code == 404:
                logger.error(f"Recurso não encontrado (404): {url}")
            elif r.status_code == 429:
                logger.error("Rate limit atingido. Aguarde antes de tentar novamente.")
            else:
                logger.error(f"Erro {r.status_code}: {url}")
        except httpx.TimeoutException:
            logger.error("Timeout na requisição.")
        except httpx.ConnectError:
            logger.error("Sem conexão com a internet.")
        return None

    # ── Summoner ────────────────────────────

    async def get_summoner_by_name(self, game_name: str, tag_line: str = "BR1") -> Optional[SummonerInfo]:
        cache_key = f"summoner_{game_name}_{tag_line}"
        cached = _cache_get(cache_key)
        if cached:
            return SummonerInfo(**cached)

        async with httpx.AsyncClient() as client:
            url = f"https://{REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
            account = await self._get(client, url)
            if not account:
                return None

            puuid = account["puuid"]

            url2 = f"{BASE_PLATFORM}/lol/summoner/v4/summoners/by-puuid/{puuid}"
            summoner = await self._get(client, url2)
            if not summoner:
                return None

        info = SummonerInfo(
            puuid=puuid,
            summoner_id=summoner.get("id", ""),
            name=f"{game_name}#{tag_line}",
            level=summoner.get("summonerLevel", 0),
            profile_icon_id=summoner.get("profileIconId", 0),
        )

        _cache_set(cache_key, info.__dict__, CACHE_TTL["summoner"])
        return info

    # ── Rank ────────────────────────────────

    async def get_summoner_rank(self, summoner_id: str) -> str:
        """
        Busca o rank atual do jogador no ranked solo/duo.
        Retorna a tier (ex: "GOLD", "DIAMOND").
        Retorna "UNRANKED" se não tiver ranked, "DEFAULT" em caso de erro.
        """
        cache_key = f"rank_{summoner_id}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

        url = f"{BASE_PLATFORM}/lol/league/v4/entries/by-summoner/{summoner_id}"
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(url, headers=self._headers, timeout=10)

            if r.status_code == 403:
                logger.warning("Chave sem permissão para buscar rank.")
                return "DEFAULT"
            elif r.status_code == 429:
                logger.warning("Rate limit ao buscar rank.")
                return "DEFAULT"
            elif r.status_code != 200:
                logger.error(f"Erro {r.status_code} ao buscar rank.")
                return "DEFAULT"

            data = r.json()  # retorna lista, não dict

            # Valida que é uma lista
            if not isinstance(data, list):
                logger.warning(f"Resposta inesperada ao buscar rank: {data}")
                return "DEFAULT"

            # Lista vazia = jogador sem ranked nessa temporada
            if len(data) == 0:
                logger.info(f"Jogador sem ranked → UNRANKED")
                rank = "UNRANKED"
            else:
                # Prioriza ranked solo/duo, fallback para qualquer queue disponível
                solo = next(
                    (q for q in data if q.get("queueType") == "RANKED_SOLO_5x5"),
                    data[0]
                )
                rank = solo.get("tier", "DEFAULT").upper()
                logger.info(f"Rank encontrado: {rank}")

            _cache_set(cache_key, rank, CACHE_TTL["rank"])
            return rank

        except Exception as e:
            logger.warning(f"Falha ao buscar rank: {e}")
            return "DEFAULT"

    # ── Histórico ───────────────────────────

    async def get_match_history(self, puuid: str, count: int = 10, start: int = 0, queue: Optional[int] = None) -> list[str]:
        cache_key = f"history_{puuid}_{start}_{count}_{queue}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

        url = f"{BASE_REGION}/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={count}"
        if queue:
            url += f"&queue={queue}"
        async with httpx.AsyncClient() as client:
            result = await self._get(client, url) or []

        if result:
            _cache_set(cache_key, result, CACHE_TTL["history"])
        return result

    # ── Partida ─────────────────────────────

    async def get_match(self, match_id: str) -> Optional[MatchData]:
        cache_key = f"match_{match_id}"
        cached = _cache_get(cache_key)
        if cached:
            return self._parse_match(cached)

        url = f"{BASE_REGION}/lol/match/v5/matches/{match_id}"
        async with httpx.AsyncClient() as client:
            raw = await self._get(client, url)
        if not raw:
            return None

        _cache_set(cache_key, raw, CACHE_TTL["match"])
        return self._parse_match(raw)

    # ── Timeline ────────────────────────────

    async def get_match_timeline(self, match_id: str) -> Optional[MatchTimeline]:
        cache_key = f"timeline_{match_id}"
        cached = _cache_get(cache_key)
        if cached:
            return self._parse_timeline(cached)

        url = f"{BASE_REGION}/lol/match/v5/matches/{match_id}/timeline"
        async with httpx.AsyncClient() as client:
            raw = await self._get(client, url)
        if not raw:
            return None

        _cache_set(cache_key, raw, CACHE_TTL["timeline"])
        return self._parse_timeline(raw)

    # ── Parsers ─────────────────────────────

    def _parse_match(self, raw: dict) -> MatchData:
        info = raw.get("info", {})
        participants = []

        for p in info.get("participants", []):
            spells = [p.get("summoner1Id", ""), p.get("summoner2Id", "")]
            items  = [p.get(f"item{i}", 0) for i in range(7)]

            participant = MatchParticipant(
                puuid=p.get("puuid", ""),
                riot_id=f"{p.get('riotIdGameName', '')}#{p.get('riotIdTagline', '')}",
                champion_name=p.get("championName", ""),
                team_id=p.get("teamId", 0),
                position=p.get("teamPosition", ""),
                kills=p.get("kills", 0),
                deaths=p.get("deaths", 0),
                assists=p.get("assists", 0),
                creep_score=p.get("totalMinionsKilled", 0) + p.get("neutralMinionsKilled", 0),
                gold_earned=p.get("goldEarned", 0),
                vision_score=p.get("visionScore", 0),
                wards_placed=p.get("wardsPlaced", 0),
                wards_killed=p.get("wardsKilled", 0),
                detector_wards_placed=p.get("detectorWardsPlaced", 0),
                items=items,
                win=p.get("win", False),
                champion_level=p.get("champLevel", 0),
                damage_dealt=p.get("totalDamageDealtToChampions", 0),
                damage_taken=p.get("totalDamageTaken", 0),
                time_spent_dead=p.get("totalTimeSpentDead", 0),
                summoner_spells=spells,
            )
            participants.append(participant)

        return MatchData(
            match_id=raw.get("metadata", {}).get("matchId", ""),
            game_duration=info.get("gameDuration", 0),
            game_mode=info.get("gameMode", ""),
            game_version=info.get("gameVersion", ""),
            participants=participants,
            raw=raw,
        )

    def _parse_timeline(self, raw: dict) -> MatchTimeline:
        info = raw.get("info", {})

        # Apenas eventos relevantes para a análise de coach
        _RELEVANT = frozenset({
            "CHAMPION_KILL", "WARD_PLACED", "WARD_KILL",
            "ELITE_MONSTER_KILL", "RECALL_START", "RECALL", "BUILDING_KILL",
            "ITEM_PURCHASED", "ITEM_SOLD", "ITEM_UNDO",   # VOD Proxy: item timeline
        })
        # Apenas campos de participantFrames que realmente usamos
        _PF_KEYS = ("position", "totalGold", "minionsKilled", "jungleMinionsKilled", "xp")

        slim_frames = []
        all_events  = []

        for frame in info.get("frames", []):
            relevant = [e for e in frame.get("events", []) if e.get("type") in _RELEVANT]
            all_events.extend(relevant)

            slim_pf = {
                pid: {k: data.get(k, ({} if k == "position" else 0)) for k in _PF_KEYS}
                for pid, data in frame.get("participantFrames", {}).items()
            }
            slim_frames.append({
                "timestamp":         frame.get("timestamp", 0),
                "participantFrames": slim_pf,
                "events":            relevant,
            })

        return MatchTimeline(
            frames=slim_frames,
            events=all_events,
            participants=info.get("participants", []),
        )


# ─────────────────────────────────────────
# Item names (DDragon)
# ─────────────────────────────────────────

DDRAGON_VERSIONS_URL = "https://ddragon.leagueoflegends.com/api/versions.json"


async def _resolve_ddragon_version(game_version: str) -> str:
    """Retorna a versão DDragon que casa com o gameVersion do match.

    Ex.: game_version="15.6.1.1" → procura versão DDragon que começa com "15.6."
    Fallback para a versão mais recente se não encontrar match ou game_version vazio.
    """
    cached = _cache_get("ddragon_versions")
    if cached:
        versions = cached
    else:
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(DDRAGON_VERSIONS_URL, timeout=10)
            versions = r.json()  # lista ordenada — [0] é a mais recente
            _cache_set("ddragon_versions", versions, CACHE_TTL["ddragon_versions"])
        except Exception as e:
            logger.warning(f"Falha ao buscar versões DDragon: {e}")
            return "latest"

    if game_version:
        parts = game_version.split(".")
        if len(parts) >= 2:
            prefix = f"{parts[0]}.{parts[1]}."
            for v in versions:
                if v.startswith(prefix):
                    logger.info(f"Versão DDragon casada com patch {game_version}: {v}")
                    return v

    latest = versions[0] if versions else "latest"
    logger.info(f"Sem match DDragon para '{game_version}' — usando versão mais recente: {latest}")
    return latest


async def get_item_names(game_version: str = "") -> dict[str, str]:
    """Retorna dict { "3147": "Nome do Item", ... } com cache por versão de patch.

    Usa o gameVersion do match para buscar o DDragon do patch correto.
    Fallback para o patch mais recente se a versão não for encontrada.
    """
    ddragon_version = await _resolve_ddragon_version(game_version)
    cache_key = f"ddragon_items_{ddragon_version}"

    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    url = f"https://ddragon.leagueoflegends.com/cdn/{ddragon_version}/data/pt_BR/item.json"
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, timeout=10)
        if r.status_code == 200:
            raw   = r.json()
            items = {item_id: data["name"] for item_id, data in raw.get("data", {}).items()}
            _cache_set(cache_key, items, CACHE_TTL["items"])
            logger.info(f"{len(items)} itens carregados do DDragon {ddragon_version}.")
            return items
        else:
            logger.error(f"Erro {r.status_code} ao buscar itens do DDragon {ddragon_version}.")
    except Exception as e:
        logger.error(f"Falha ao buscar nomes de itens: {e}")

    return {}


# ─────────────────────────────────────────
# Funções utilitárias
# ─────────────────────────────────────────

def get_ward_events(timeline: MatchTimeline) -> list[dict]:
    ward_types = {"WARD_PLACED", "WARD_KILL"}
    return [e for e in timeline.events if e.get("type") in ward_types]


def get_kill_events(timeline: MatchTimeline) -> list[dict]:
    return [e for e in timeline.events if e.get("type") == "CHAMPION_KILL"]


