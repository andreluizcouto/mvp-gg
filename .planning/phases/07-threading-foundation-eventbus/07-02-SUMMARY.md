---
phase: 07-threading-foundation-eventbus
plan: 02
subsystem: threading
tags: [customtkinter, pystray, asyncio, threading, eventbus, tkinter]

requires:
  - phase: 07-threading-foundation-eventbus (plan 01)
    provides: "EventBus module (event_bus.py), thread-safe app_config with update_config()"
provides:
  - "TrayIcon with run_detached() non-blocking API"
  - "3-thread coach_app.py bootstrap: CTk main, pystray background, asyncio daemon"
  - "EventBus wiring in coach_loop with STATE_CHANGE and ERROR emissions"
  - "Shutdown coordination via threading.Event + after(0, app.quit)"
  - "Integration tests proving EventBus + tk mainloop + cross-thread delivery"
affects: [phase-08-gui-shell, phase-09-state-machine, phase-10-activity-log, phase-11-minimap-settings]

tech-stack:
  added: [customtkinter]
  patterns: [3-thread-model, run_detached-tray, after-0-quit-shutdown, module-scoped-tk-fixture]

key-files:
  created:
    - backend/tests/test_threading.py
  modified:
    - backend/tray_icon.py
    - backend/coach_app.py

key-decisions:
  - "app.withdraw() on startup — GUI starts hidden, Phase 8 adds visible shell"
  - "Module-scoped tk.Tk() fixture in tests — avoids Tcl state corruption on Windows from repeated create/destroy"
  - "EventBus emissions alongside tray.set_state() — dual notification path (tray + GUI) during transition"

patterns-established:
  - "3-thread bootstrap: CTk main → tray.run_detached() → asyncio daemon thread"
  - "Shutdown: stop_event.set() + app.after(0, app.quit) from any thread"
  - "EventBus emission from asyncio: event_bus.emit(Event(EventType.STATE_CHANGE, {...}))"

requirements-completed: [APP-01, APP-02]

duration: 8min
completed: 2026-04-01
---

# Phase 7 Plan 02: 3-Thread Model Restructure Summary

**CTk main thread + pystray background + asyncio daemon with EventBus cross-thread delivery under 200ms and coordinated shutdown**

## Performance

- **Duration:** 8 min
- **Started:** 2026-04-01T22:19:33Z
- **Completed:** 2026-04-01T22:27:00Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- TrayIcon refactored from blocking `run()` to non-blocking `run_detached()` with atomic config updates
- coach_app.py restructured from 2-thread (pystray main + asyncio) to 3-thread (CTk main + pystray background + asyncio daemon) with EventBus integration
- 5 integration tests proving EventBus polling, cross-thread delivery (<200ms), and clean shutdown coordination
- Full test suite: 88/88 passing, zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Modify TrayIcon for run_detached() and atomic config updates** - `3474d70` (feat)
2. **Task 2: Restructure coach_app.py for 3-thread model with EventBus and shutdown** - `1c0faa7` (feat)
3. **Task 3: Create integration tests for 3-thread model** - `d3c3a09` (test)

## Files Created/Modified
- `backend/tray_icon.py` - TrayIcon with run_detached() replacing blocking run(), _toggle_* using atomic update_config()
- `backend/coach_app.py` - 3-thread bootstrap: CTk mainloop on main, pystray run_detached on background, asyncio.run on daemon. EventBus wired into coach_loop
- `backend/tests/test_threading.py` - 5 integration tests for EventBus+tk, cross-thread delivery, latency, shutdown, multi-event ordering

## Decisions Made
- **app.withdraw() on startup:** GUI window starts hidden — same user experience as before (tray-only). Phase 8 will deiconify and add the visible shell.
- **Module-scoped Tk fixture:** On Windows, repeated `tk.Tk()`/`destroy()` cycles corrupt the Tcl interpreter. Using a single shared root per test module avoids this.
- **Dual notification path:** EventBus emissions added alongside existing tray.set_state() calls. Both tray icon and future GUI will receive state updates.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Tcl interpreter corruption in test suite**
- **Found during:** Task 3 (Integration tests)
- **Issue:** Creating and destroying multiple `tk.Tk()` instances across tests caused `TclError: invalid command name "tcl_findLibrary"` on Windows — 5th Tk create/destroy cycle in full suite corrupted Tcl state
- **Fix:** Changed from per-test `tk.Tk()`/`destroy()` to module-scoped fixture with a single shared Tk root reused across all 5 tests
- **Files modified:** `backend/tests/test_threading.py`
- **Verification:** Full suite 88/88 passing after fix
- **Committed in:** `d3c3a09` (amended Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Test infrastructure fix was necessary for Windows compatibility. Same tests, same assertions, more robust Tk lifecycle. No scope creep.

## Issues Encountered
None beyond the Tk fixture issue documented above.

## User Setup Required
None - no external service configuration required.

## Known Stubs
None - all wiring is functional. `app.withdraw()` is intentional (Phase 8 adds visible window).

## Next Phase Readiness
- 3-thread model validated and operational — ready for Phase 8 GUI shell
- EventBus infrastructure proven for cross-thread communication — Phase 9 state machine can subscribe
- TrayIcon can be extended with new menu items in Phase 10-11
- Shutdown coordination pattern established for all future components

---
*Phase: 07-threading-foundation-eventbus*
*Completed: 2026-04-01*
