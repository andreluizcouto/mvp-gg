"""
Captura da região do minimapa da tela durante partidas ao vivo.
"""
import base64
import io
import os

import mss
from PIL import Image


def get_screen_resolution() -> tuple[int, int]:
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Monitor primário
        return monitor["width"], monitor["height"]


def capture_minimap(
    screen_width: int,
    screen_height: int,
    minimap_left: bool = False,
    minimap_large: bool = False,
) -> Image.Image:
    """Captura a região do minimapa.

    Args:
        minimap_left:  True se o minimapa está no canto inferior esquerdo.
        minimap_large: True se o jogador usa minimapa maior (fator 0.27 vs 0.21).
    """
    factor = 0.43 if minimap_large else 0.37
    minimap_size = int(screen_height * factor)
    left = 10 if minimap_left else screen_width - minimap_size - 10
    top  = screen_height - minimap_size - 10

    with mss.mss() as sct:
        region = {
            "left":   left,
            "top":    top,
            "width":  minimap_size,
            "height": minimap_size,
        }
        screenshot = sct.grab(region)
        return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")


def image_to_base64(img: Image.Image) -> str:
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


def save_minimap_to_disk(img: Image.Image, output_dir: str, event_type: str, game_time_sec: float) -> str:
    """Salva o print do minimapa como PNG e retorna o caminho.

    O nome do arquivo usa o tempo de jogo em segundos com 4 dígitos,
    por exemplo: death_0945.png para 945 segundos de partida.
    """
    os.makedirs(output_dir, exist_ok=True)
    t = int(game_time_sec)
    base_filename = f"{event_type}_{t:04d}.png"
    path = os.path.join(output_dir, base_filename)
    counter = 1
    while os.path.exists(path):
        filename = f"{event_type}_{t:04d}_{counter}.png"
        path = os.path.join(output_dir, filename)
        counter += 1
    img.save(path, format="PNG")
    return path
