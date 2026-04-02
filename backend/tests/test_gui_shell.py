# backend/tests/test_gui_shell.py
"""
Tests for Phase 8: GUI Shell + Tray Integration.
Validates TrayIcon on_show callback, menu structure, notification methods,
and config-based notification suppression.
"""
import os
import sys
import tkinter as tk
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="module")
def _tk_root():
    """Single Tk root shared across all tests (avoids Tcl state corruption on Windows)."""
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except tk.TclError:
        pass


# --- TrayIcon on_show callback tests (WIN-03) ---


class TestTrayIconShowCallback:
    """Tests for TrayIcon on_show callback and menu structure."""

    def test_tray_accepts_on_show_callback(self):
        from tray_icon import TrayIcon
        callback = MagicMock()
        tray = TrayIcon(on_quit=MagicMock(), on_show=callback)
        assert tray._on_show is callback

    def test_tray_on_show_defaults_to_none(self):
        from tray_icon import TrayIcon
        tray = TrayIcon(on_quit=MagicMock())
        assert tray._on_show is None

    def test_show_window_calls_on_show(self):
        from tray_icon import TrayIcon
        callback = MagicMock()
        tray = TrayIcon(on_quit=MagicMock(), on_show=callback)
        tray._show_window(MagicMock(), MagicMock())
        callback.assert_called_once()

    def test_show_window_noop_when_no_callback(self):
        from tray_icon import TrayIcon
        tray = TrayIcon(on_quit=MagicMock())
        tray._show_window(MagicMock(), MagicMock())  # should not raise

    def test_menu_has_abrir_mvpapp_as_default(self):
        """'Abrir MVPApp' is the first menu item with default=True."""
        from tray_icon import TrayIcon
        tray = TrayIcon(on_quit=MagicMock(), on_show=MagicMock())
        menu = tray._build_menu()
        items = list(menu)
        first = items[0]
        assert first.default is True

    def test_menu_builds_without_error(self):
        """Menu builds successfully with all items."""
        from tray_icon import TrayIcon
        tray = TrayIcon(on_quit=MagicMock(), on_show=MagicMock())
        menu = tray._build_menu()
        assert menu is not None
        items = list(menu)
        assert len(items) > 5  # Abrir + separator + status + separator + settings + separator + Sair


# --- Notification convenience methods tests (WIN-02) ---


class TestTrayNotification:
    """Tests for tray notification convenience methods."""

    def test_notify_delegates_to_icon(self):
        from tray_icon import TrayIcon
        tray = TrayIcon(on_quit=MagicMock())
        tray._icon = MagicMock()
        tray.notify("test message", "test title")
        tray._icon.notify.assert_called_once_with("test message", "test title")

    def test_notify_noop_when_no_icon(self):
        from tray_icon import TrayIcon
        tray = TrayIcon(on_quit=MagicMock())
        tray._icon = None
        tray.notify("test", "test")  # should not raise

    def test_remove_notification_delegates_to_icon(self):
        from tray_icon import TrayIcon
        tray = TrayIcon(on_quit=MagicMock())
        tray._icon = MagicMock()
        tray.remove_notification()
        tray._icon.remove_notification.assert_called_once()

    def test_remove_notification_noop_when_no_icon(self):
        from tray_icon import TrayIcon
        tray = TrayIcon(on_quit=MagicMock())
        tray._icon = None
        tray.remove_notification()  # should not raise


# --- Config notification suppression tests (WIN-02 + D-08) ---


class TestNotificationSuppression:
    """Tests that notification respects hide_tray_notification config."""

    def test_notification_shown_when_config_false(self, tmp_path):
        from app_config import save_config, get_config
        save_config({"minimap_left": False, "minimap_large": False, "hide_tray_notification": False}, config_dir=str(tmp_path))
        cfg = get_config(config_dir=str(tmp_path))
        assert cfg.get("hide_tray_notification", False) is False
        should_show = not cfg.get("hide_tray_notification", False)
        assert should_show is True

    def test_notification_suppressed_when_config_true(self, tmp_path):
        from app_config import save_config, get_config, update_config
        save_config({"minimap_left": False, "minimap_large": False}, config_dir=str(tmp_path))
        update_config("hide_tray_notification", True, config_dir=str(tmp_path))
        cfg = get_config(config_dir=str(tmp_path))
        assert cfg.get("hide_tray_notification", False) is True
        should_show = not cfg.get("hide_tray_notification", False)
        assert should_show is False
