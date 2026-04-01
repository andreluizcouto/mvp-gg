import pytest
from unittest.mock import AsyncMock, patch
from postgame_analyzer import build_batch_prompt, analyze_postgame


def test_build_batch_prompt_includes_all_events():
    events = [
        {"event_type": "death", "game_time_sec": 245.0, "champion": "Viktor", "killer": "Zed", "detail": "Morte"},
        {"event_type": "kill", "game_time_sec": 380.0, "champion": "Viktor", "victim": "Jinx", "detail": "Kill em Jinx"},
        {"event_type": "death", "game_time_sec": 610.0, "champion": "Viktor", "killer": "LeeSin", "detail": "Morte"},
    ]
    match_context = "KDA: 5/3/7, CS/min: 7.2, Vision Score: 22"

    prompt = build_batch_prompt(events, match_context, num_images=3)

    assert "Viktor" in prompt
    assert "Zed" in prompt
    assert "Jinx" in prompt
    assert "LeeSin" in prompt
    assert "04:05" in prompt   # 245s
    assert "06:20" in prompt   # 380s
    assert "10:10" in prompt   # 610s
    assert "KDA: 5/3/7" in prompt


def test_build_batch_prompt_death_count():
    events = [
        {"event_type": "death", "game_time_sec": 100.0, "champion": "Jinx", "killer": "Zed", "detail": "Morte"},
        {"event_type": "death", "game_time_sec": 200.0, "champion": "Jinx", "killer": "Zed", "detail": "Morte"},
    ]
    prompt = build_batch_prompt(events, "", num_images=2)
    assert "Morte #1" in prompt
    assert "Morte #2" in prompt


@pytest.mark.asyncio
async def test_analyze_postgame_calls_ai_with_images():
    events = [
        {"event_type": "death", "game_time_sec": 245.0, "champion": "Viktor", "killer": "Zed", "detail": "Morte"},
    ]
    image_paths = ["fake_path.png"]
    match_context = "KDA: 1/1/0"

    with patch("postgame_analyzer._call_haiku_batch", new_callable=AsyncMock, return_value="Analise mock") as mock_haiku, \
         patch("postgame_analyzer._call_gemini_batch", new_callable=AsyncMock, side_effect=Exception("quota")), \
         patch("postgame_analyzer._load_image_bytes", return_value=b"fake_png_bytes"):
        result = await analyze_postgame(events, image_paths, match_context)

    assert result == "Analise mock"
    mock_haiku.assert_called_once()
