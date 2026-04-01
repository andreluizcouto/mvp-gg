# Plan 07-02 Summary

**Phase:** 07-threading-foundation-eventbus
**Plan:** 02 — 3-thread model restructure + integration tests
**Status:** Complete
**Date:** 2026-04-01

## What Was Built

### TrayIcon Refactored (`backend/tray_icon.py`)
- Replaced blocking `run()` with `run_detached()` (calls `pystray.Icon.run_detached()`)
- `_toggle_left`/`_toggle_large` now use atomic `update_config()` instead of race-prone get+save pattern
- Removed `save_config` import, added `update_config` import

### 3-Thread Model (`backend/coach_app.py`)
- **Main thread**: CustomTkinter `CTk()` with `app.mainloop()`, `app.withdraw()` (hidden — Phase 8 adds visible shell)
- **Background thread**: pystray via `tray.run_detached()` (non-blocking)
- **Daemon thread**: asyncio `coach_loop()` with EventBus emission for state changes
- **Shutdown coordination**: `stop_event.set()` → `app.after(0, app.quit)` → `tray.stop()` → `async_thread.join(5s)` → `app.destroy()`
- EventBus emissions added alongside existing `tray.set_state()` calls (STATE_CHANGE, ERROR events)

### Integration Tests (`backend/tests/test_threading.py`)
- `test_eventbus_polling_with_tk_mainloop` — EventBus delivers events via after() on tk mainloop
- `test_cross_thread_emit_to_tk_mainloop` — cross-thread emit received on main thread
- `test_eventbus_delivery_latency` — delivery within 200ms (APP-02 requirement verified)
- `test_shutdown_via_stop_event` — shutdown exits mainloop cleanly in < 2s
- `test_multiple_events_from_async_thread` — 3 events delivered in order from background thread
- Module-scoped `tk.Tk()` fixture to avoid Tcl state corruption on Windows

## Tests
- 5 integration tests all passing
- Full suite: 88/88 tests passing, 0 regressions

## Commits
- `3474d70` feat(07-02): modify TrayIcon for run_detached() and atomic config updates
- `1c0faa7` feat(07-02): restructure coach_app.py for 3-thread model with EventBus
- `0e6f484` test(07-02): add integration tests for 3-thread model
- `670426e` fix(07-02): use module-scoped tk_root fixture for Windows Tcl compatibility

## Requirements Addressed
- **APP-01**: 3-thread coexistence (CTk main, pystray background, asyncio daemon) without deadlocks
- **APP-02**: EventBus wired into coach_loop — cross-thread events delivered via after() polling within 200ms
