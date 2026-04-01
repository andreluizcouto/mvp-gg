# ProjectB/tests/test_app_config.py
import json
import os
import sys
import tempfile
import threading

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


# ---------------------------------------------------------------------------
# NEW TESTS: Thread-safety with RLock (APP-03)
# ---------------------------------------------------------------------------


def test_concurrent_config_writes(tmp_path):
    """5 threads writing concurrently do not corrupt the JSON file."""
    from app_config import get_config, save_config, update_config

    # Seed initial config
    save_config({"minimap_left": False, "minimap_large": False}, config_dir=str(tmp_path))

    errors = []

    def toggle_config(thread_id: int):
        try:
            for i in range(50):
                val = (i % 2 == 0)
                update_config("minimap_left", val, config_dir=str(tmp_path))
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=toggle_config, args=(tid,)) for tid in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # No exceptions during concurrent writes
    assert errors == [], f"Errors during concurrent writes: {errors}"

    # Final config must be valid JSON and readable
    cfg = get_config(config_dir=str(tmp_path))
    assert "minimap_left" in cfg
    assert "minimap_large" in cfg


def test_update_config_atomic(tmp_path):
    """update_config persists atomically — re-read confirms change."""
    from app_config import get_config, save_config, update_config

    save_config({"minimap_left": False, "minimap_large": False}, config_dir=str(tmp_path))

    result = update_config("minimap_left", True, config_dir=str(tmp_path))
    assert result["minimap_left"] is True

    # Re-read from disk confirms persistence
    cfg = get_config(config_dir=str(tmp_path))
    assert cfg["minimap_left"] is True


def test_update_config_returns_updated(tmp_path):
    """update_config returns the full updated config dict, not just the changed key."""
    from app_config import save_config, update_config

    save_config({"minimap_left": False, "minimap_large": False}, config_dir=str(tmp_path))

    result = update_config("minimap_large", True, config_dir=str(tmp_path))
    assert result["minimap_large"] is True
    # Must contain all keys, not just the changed one
    assert "minimap_left" in result


@pytest.mark.timeout(5)
def test_rlock_allows_reentrance(tmp_path):
    """Acquiring _config_lock then calling get_config() does not deadlock (RLock)."""
    from app_config import get_config, save_config, _config_lock

    save_config({"minimap_left": False, "minimap_large": False}, config_dir=str(tmp_path))

    # This would deadlock with a plain Lock but succeeds with RLock
    with _config_lock:
        cfg = get_config(config_dir=str(tmp_path))

    assert cfg["minimap_left"] is False
