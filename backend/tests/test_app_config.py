# ProjectB/tests/test_app_config.py
import json
import os
import sys
import tempfile
import pytest

# Garante que o módulo pode ser importado sem mss/pystray
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_get_config_returns_defaults_when_no_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Remove qualquer config.json residual
    cfg_path = tmp_path / "config.json"
    if cfg_path.exists():
        cfg_path.unlink()

    from app_config import get_config
    cfg = get_config(config_dir=str(tmp_path))
    assert cfg == {"minimap_left": False, "minimap_large": False}


def test_save_and_reload_config(tmp_path):
    from app_config import get_config, save_config
    save_config({"minimap_left": True, "minimap_large": False}, config_dir=str(tmp_path))
    cfg = get_config(config_dir=str(tmp_path))
    assert cfg["minimap_left"] is True
    assert cfg["minimap_large"] is False


def test_get_config_ignores_unknown_keys(tmp_path):
    """Config com chaves extras não deve quebrar."""
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps({"minimap_left": True, "minimap_large": True, "unknown": 99}))
    from app_config import get_config
    cfg = get_config(config_dir=str(tmp_path))
    assert cfg["minimap_left"] is True
    assert cfg["minimap_large"] is True


def test_get_config_returns_defaults_for_corrupted_json(tmp_path):
    """Config com JSON inválido retorna defaults sem lançar exceção."""
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text("NOT_VALID_JSON{{{")
    from app_config import get_config
    cfg = get_config(config_dir=str(tmp_path))
    assert cfg == {"minimap_left": False, "minimap_large": False}
