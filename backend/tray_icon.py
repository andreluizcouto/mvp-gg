# ProjectB/tray_icon.py
'''
Gerencia o icone da bandeja do sistema com 4 estados e menu de configuracao.
Icones gerados programaticamente via Pillow - sem arquivos externos.
'''
import threading
import webbrowser
from typing import Callable

import pystray
from PIL import Image, ImageDraw

from app_config import get_config, update_config

SITE_URL = "https://mvpgg.vercel.app"

# Cores por estado
_COLORS = {
    "waiting":   (120, 120, 120, 255),   # cinza
    "recording": (200, 155,  60, 255),   # dourado
    "uploading": ( 92, 159, 212, 255),   # azul
    "ready":     ( 74, 222, 128, 255),   # verde
}

_STATUS_LABELS = {
    "waiting":   "Aguardando LoL...",
    "recording": "Gravando partida...",
    "uploading": "Enviando analise...",
    "ready":     "Analise pronta!",
}


def _make_icon_image(color: tuple) -> Image.Image:
    '''Gera um icone circular 64x64 com a cor especificada.'''
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill=color)
    return img


class TrayIcon:
    '''
    Encapsula o icone da bandeja. Chame `run_detached()` para iniciar em background thread.
    Use `set_state(state)` de qualquer thread para atualizar o icone e o menu.
    '''

    def __init__(self, on_quit: Callable):
        self._state = "waiting"
        self._detail = ""
        self._on_quit = on_quit
        self._icon: pystray.Icon | None = None
        self._lock = threading.Lock()

    # -- Public API --

    def set_state(self, state: str, detail: str = "") -> None:
        """Atualiza estado do ícone. Thread-safe."""
        if state not in _COLORS:
            raise ValueError(f"Estado inválido: {state!r}. Válidos: {list(_COLORS)}")
        with self._lock:
            self._state = state
            self._detail = detail
            if self._icon:
                self._icon.icon  = _make_icon_image(_COLORS[state])
                self._icon.title = f"CoachApp — {_STATUS_LABELS[state]}"
                self._icon.update_menu()

    def run_detached(self) -> None:
        """Start tray on background thread. Non-blocking."""
        self._icon = pystray.Icon(
            name="CoachApp",
            icon=_make_icon_image(_COLORS["waiting"]),
            title="CoachApp — Aguardando LoL...",
            menu=self._build_menu(),
        )
        self._icon.run_detached(setup=lambda icon: setattr(icon, 'visible', True))

    def stop(self) -> None:
        if self._icon:
            self._icon.stop()

    # -- Menu --

    def _build_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem(
                lambda item: _STATUS_LABELS.get(self._state, ""),
                None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Ver analise",
                self._open_site,
                enabled=lambda item: self._state in ("uploading", "ready"),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Minimapa a esquerda",
                self._toggle_left,
                checked=lambda item: get_config().get("minimap_left", False),
            ),
            pystray.MenuItem(
                "Minimapa grande",
                self._toggle_large,
                checked=lambda item: get_config().get("minimap_large", False),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Sair", self._quit),
        )

    # -- Callbacks --

    def _open_site(self, icon, item) -> None:
        webbrowser.open(SITE_URL)

    def _toggle_left(self, icon, item) -> None:
        cfg = get_config()
        update_config("minimap_left", not cfg.get("minimap_left", False))

    def _toggle_large(self, icon, item) -> None:
        cfg = get_config()
        update_config("minimap_large", not cfg.get("minimap_large", False))

    def _quit(self, icon, item) -> None:
        self._on_quit()
        self.stop()
