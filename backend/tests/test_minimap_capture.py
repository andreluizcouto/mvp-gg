# ProjectB/tests/test_minimap_capture.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock
import minimap_capture


def _make_mock_screenshot(w, h):
    """Cria um mock de screenshot do mss com dados BGRA."""
    mock = MagicMock()
    mock.size = (w, h)
    mock.bgra = b"\x00\x00\x00\xff" * (w * h)
    return mock


def test_capture_default_is_bottom_right():
    """Sem parâmetros: captura canto inferior direito."""
    with patch("mss.mss") as mock_mss:
        ctx = mock_mss.return_value.__enter__.return_value
        ctx.grab.return_value = _make_mock_screenshot(200, 200)
        minimap_capture.capture_minimap(1920, 1080)
        region = ctx.grab.call_args[0][0]
        # Canto direito: left > 1920/2
        assert region["left"] > 960


def test_capture_left_minimap():
    """minimap_left=True: captura canto inferior esquerdo."""
    with patch("mss.mss") as mock_mss:
        ctx = mock_mss.return_value.__enter__.return_value
        ctx.grab.return_value = _make_mock_screenshot(200, 200)
        minimap_capture.capture_minimap(1920, 1080, minimap_left=True)
        region = ctx.grab.call_args[0][0]
        # Canto esquerdo: left == 10
        assert region["left"] == 10


def test_capture_large_minimap_bigger_region():
    """minimap_large=True: região capturada é maior."""
    with patch("mss.mss") as mock_mss:
        ctx = mock_mss.return_value.__enter__.return_value
        ctx.grab.return_value = _make_mock_screenshot(300, 300)
        minimap_capture.capture_minimap(1920, 1080, minimap_large=False)
        region_normal = ctx.grab.call_args[0][0]

        ctx.grab.return_value = _make_mock_screenshot(300, 300)
        minimap_capture.capture_minimap(1920, 1080, minimap_large=True)
        region_large = ctx.grab.call_args[0][0]

        assert region_large["width"] > region_normal["width"]
