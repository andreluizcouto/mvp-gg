import asyncio

import pytest
from fastapi import HTTPException

import main
from riot_client import RiotMatchClient


class FakeHistoryClient(RiotMatchClient):
    """Histórico falso por fila; os IDs maiores são as partidas mais novas."""

    def __init__(self, by_queue):
        super().__init__(api_key="test")
        self.by_queue = by_queue
        self.calls = []

    async def get_match_history(self, puuid, count=10, start=0, queue=None):
        self.calls.append((queue, start, count))
        return self.by_queue.get(queue, [])[start:start + count]


def test_merges_queues_newest_first_and_paginates():
    client = FakeHistoryClient({
        400: ["BR1_900", "BR1_500", "BR1_100"],
        490: ["BR1_800", "BR1_300"],
    })
    first = asyncio.run(client.get_match_history_for_queues("p", [400, 490], count=3, start=0))
    second = asyncio.run(client.get_match_history_for_queues("p", [400, 490], count=3, start=3))
    assert first == ["BR1_900", "BR1_800", "BR1_500"]
    assert second == ["BR1_300", "BR1_100"]


def test_single_queue_uses_riot_pagination_directly():
    client = FakeHistoryClient({420: ["BR1_3", "BR1_2", "BR1_1"]})
    assert asyncio.run(client.get_match_history_for_queues("p", [420], count=2, start=1)) == ["BR1_2", "BR1_1"]
    assert client.calls == [(420, 1, 2)]


def test_validate_queue_group():
    assert main._validate_queue_group("ARENA") == "arena"
    assert main._validate_queue_group("") == "all"
    with pytest.raises(HTTPException):
        main._validate_queue_group("urf")
