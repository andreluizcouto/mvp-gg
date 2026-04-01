"""
Cliente para a Riot Live Client Data API (localhost:2999).
Disponível apenas durante partidas ativas do League of Legends.
"""
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

LIVE_CLIENT_BASE = "https://127.0.0.1:2999"


class LiveGameClient:
    """
    Wrapper assíncrono para a Riot Live Client Data API.
    Use como context manager: async with LiveGameClient() as client:
    """

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        # verify=False necessário por conta do certificado self-signed da Riot
        self._client = httpx.AsyncClient(verify=False, timeout=3.0)
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()

    async def is_game_active(self) -> bool:
        try:
            resp = await self._client.get(f"{LIVE_CLIENT_BASE}/liveclientdata/gamestats")
            return resp.status_code == 200
        except Exception:
            return False

    async def get_active_player(self) -> Optional[dict]:
        try:
            resp = await self._client.get(
                f"{LIVE_CLIENT_BASE}/liveclientdata/activeplayer"
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.debug(f"get_active_player failed: {e}")
            return None

    async def get_player_list(self) -> list[dict]:
        try:
            resp = await self._client.get(f"{LIVE_CLIENT_BASE}/liveclientdata/playerlist")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.debug(f"get_player_list failed: {e}")
            return []

    async def get_game_stats(self) -> Optional[dict]:
        try:
            resp = await self._client.get(f"{LIVE_CLIENT_BASE}/liveclientdata/gamestats")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.debug(f"get_game_stats failed: {e}")
            return None

    async def get_events(self) -> list[dict]:
        try:
            resp = await self._client.get(f"{LIVE_CLIENT_BASE}/liveclientdata/eventdata")
            resp.raise_for_status()
            return resp.json().get("Events", [])
        except Exception as e:
            logger.debug(f"get_events failed: {e}")
            return []

    async def get_recent_match_ids(self, puuid: str, api_key: str, count: int = 5) -> list[str]:
        """Busca match IDs recentes via Riot Match-V5 API."""
        url = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
        try:
            resp = await self._client.get(
                url,
                params={"count": count},
                headers={"X-Riot-Token": api_key},
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.debug(f"get_recent_match_ids failed: {e}")
            return []

    async def get_puuid_from_riot_id(self, game_name: str, tag_line: str, api_key: str) -> Optional[str]:
        """Busca PUUID via Riot Account API."""
        url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        try:
            resp = await self._client.get(url, headers={"X-Riot-Token": api_key}, timeout=10.0)
            resp.raise_for_status()
            return resp.json().get("puuid")
        except Exception as e:
            logger.debug(f"get_puuid_from_riot_id failed: {e}")
            return None

    async def get_active_player_with_status(self) -> Optional[dict]:
        """
        Combina dados do activeplayer com o isDead/respawnTimer da playerlist.
        Retorna o dict completo do jogador local, ou None se não encontrado.
        """
        active = await self.get_active_player()
        if not active:
            return None

        riot_id = active.get("riotId", "")
        summoner_name = active.get("summonerName", "")

        player_list = await self.get_player_list()
        for player in player_list:
            if player.get("riotId") == riot_id or player.get("summonerName") == summoner_name:
                return player

        return None
