"""
Nomes oficiais das filas em português, direto da lista do cliente do LoL (CommunityDragon).
O queues.json da documentação da Riot está desatualizado (não tem ARAM: Desordem nem o Arena novo);
esta lista acompanha o cliente e já traz o nome traduzido.
"""

import logging

import httpx

from riot_client import _cache_get, _cache_set

logger = logging.getLogger(__name__)

QUEUES_URL = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/pt_br/v1/queues.json"
QUEUES_TTL = 60 * 60 * 24


async def get_queue_names() -> dict[int, str]:
    """{ 2400: "ARAM: Desordem", 420: "Ranqueada Solo/Duo", ... }. Vazio se a lista não carregar."""
    cached = _cache_get("queue_names_pt_br")
    if cached:
        return {int(k): v for k, v in cached.items()}

    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(QUEUES_URL, timeout=10)
        r.raise_for_status()
        names = {int(q["id"]): q["name"] for q in r.json() if q.get("id") and q.get("name")}
    except Exception as e:
        logger.warning(f"Falha ao carregar nomes das filas: {e}")
        return {}

    _cache_set("queue_names_pt_br", {str(k): v for k, v in names.items()}, QUEUES_TTL)
    return names
