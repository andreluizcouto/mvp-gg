---
phase: 07-threading-foundation-eventbus
plan: 01
subsystem: threading
tags: [eventbus, queue, rlock, threading, tkinter-after, cross-thread]

# Dependency graph
requires: []
provides:
  - "EventBus module (emit/subscribe/poll) for cross-thread communication"
  - "Thread-safe app_config with RLock wrapping get_config/save_config/update_config"
  - "EventType enum and Event dataclass for typed event payloads"
affects: [07-02-PLAN, coach_app, tray_icon, live_coach]

# Tech tracking
tech-stack:
  added: [queue.Queue, threading.RLock, dataclasses.dataclass, enum.Enum]
  patterns: ["EventBus queue+after() polling for cross-thread GUI updates", "Module-level RLock for file I/O thread-safety", "Atomic read-modify-write via update_config"]

key-files:
  created:
    - backend/event_bus.py
    - backend/tests/test_event_bus.py
  modified:
    - backend/app_config.py
    - backend/tests/test_app_config.py

key-decisions:
  - "EventBus uses queue.Queue (stdlib, thread-safe by design) — no external dependency"
  - "POLL_INTERVAL_MS = 100ms for sub-200ms latency on GUI updates"
  - "RLock (not Lock) chosen for config so update_config can call get_config+save_config re-entrantly"
  - "update_config returns full config dict for caller convenience"

patterns-established:
  - "EventBus pattern: any thread calls bus.emit(), main thread drains via bus._poll() scheduled by after()"
  - "Handler exception isolation: try/except around each handler, log via logger.exception"
  - "Thread-safe config: all reads/writes go through module-level _config_lock RLock"

requirements-completed: [APP-02, APP-03]

# Metrics
duration: 8min
completed: 2026-04-01
---

# Phase 7 Plan 01: Threading Foundation — EventBus + Thread-Safe Config Summary

**EventBus with queue.Queue + after() polling and RLock-protected app_config for cross-thread communication**

## Performance

- **Duration:** 8 min
- **Started:** 2026-04-01T22:10:00Z
- **Completed:** 2026-04-01T22:18:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Created `backend/event_bus.py` — standalone EventBus module with EventType enum (6 event types), Event dataclass, and EventBus class supporting emit/subscribe/start_polling/_poll
- Added thread-safety to `backend/app_config.py` — module-level `_config_lock = threading.RLock()` wrapping get_config, save_config, and new atomic `update_config()`
- 14 total tests passing: 6 EventBus tests + 8 app_config tests (4 existing preserved + 4 new concurrent/atomic tests)
- Both modules importable independently with zero cross-dependencies — ready for Plan 02

## Task Commits

Each task was committed atomically (TDD: RED → GREEN):

1. **Task 1: Create EventBus module with unit tests (APP-02)**
   - `cfbd765` (test) — RED: 6 failing test stubs for EventBus
   - `6cf01ce` (feat) — GREEN: EventBus implementation, all 6 tests pass

2. **Task 2: Add RLock thread-safety to app_config + concurrent tests (APP-03)**
   - `c54cb6e` (test) — RED: 4 failing tests for thread-safe config
   - `df49bf8` (feat) — GREEN: RLock + update_config, all 8 tests pass

## Files Created/Modified

- `backend/event_bus.py` — EventBus class with queue.Queue emit, after()-based polling, EventType enum, Event dataclass (58 lines)
- `backend/tests/test_event_bus.py` — 6 unit tests: emit/subscribe, multiple subscribers, unhandled event, cross-thread, exception isolation, drain multiple (95 lines)
- `backend/app_config.py` — Added `import threading`, `_config_lock = threading.RLock()`, wrapped get_config/save_config with lock, added `update_config()` atomic helper (61 lines)
- `backend/tests/test_app_config.py` — Extended with 4 new tests: concurrent writes (5 threads × 50 iterations), atomic update, returns full dict, RLock re-entrance (128 lines)

## Decisions Made

- **queue.Queue over asyncio.Queue:** stdlib queue.Queue is thread-safe by design, simpler, and doesn't tie EventBus to asyncio
- **POLL_INTERVAL_MS = 100:** Provides sub-200ms latency for GUI updates while keeping CPU usage negligible
- **RLock over Lock:** Allows update_config to call get_config and save_config internally without deadlock
- **Handler exception isolation via logger.exception:** Prevents one bad handler from crashing the entire poll loop

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## Known Stubs

None — both modules are fully functional with no placeholder data or TODOs.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- EventBus and thread-safe config are standalone modules ready for Plan 02
- Plan 02 can restructure coach_app.py to create CTk window, use `tray.run_detached()`, and wire EventBus polling
- EventType enum already includes all types needed for Phase 7-11 features (STATE_CHANGE, CONFIG_CHANGED, GAME_EVENT, LOG_MESSAGE, ERROR, SHUTDOWN)

---
*Phase: 07-threading-foundation-eventbus, Plan: 01*
*Completed: 2026-04-01*
