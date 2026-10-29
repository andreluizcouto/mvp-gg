import pytest


@pytest.fixture(autouse=True)
def offline_queue_names(monkeypatch):
    """Os testes não baixam a lista de filas do CommunityDragon."""
    import main

    async def no_names():
        return {}

    monkeypatch.setattr(main, "get_queue_names", no_names)
