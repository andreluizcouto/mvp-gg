# ProjectB/app_config.py
"""
Lê e salva configurações do usuário em config.json.
config_dir padrão é a pasta do executável (ou pasta atual em dev).
"""
import json
import os
import sys

_DEFAULTS = {
    "minimap_left":  False,
    "minimap_large": False,
}


def _default_dir() -> str:
    """Retorna a pasta do .exe em produção ou a pasta do script em dev."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_config(config_dir: str | None = None) -> dict:
    """Retorna configuração atual. Usa defaults se config.json não existir."""
    config_dir = config_dir or _default_dir()
    path = os.path.join(config_dir, "config.json")
    if not os.path.exists(path):
        return dict(_DEFAULTS)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return {
            "minimap_left":  bool(data.get("minimap_left",  _DEFAULTS["minimap_left"])),
            "minimap_large": bool(data.get("minimap_large", _DEFAULTS["minimap_large"])),
        }
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULTS)


def save_config(cfg: dict, config_dir: str | None = None) -> None:
    """Salva configuração em config.json."""
    config_dir = config_dir or _default_dir()
    path = os.path.join(config_dir, "config.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
