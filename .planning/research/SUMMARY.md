# Research Summary: CoachApp Desktop GUI (v1.1)

**Project:** mvp.gg CoachApp
**Domain:** Desktop companion app — GUI integration onto existing headless pystray + asyncio architecture
**Researched:** 2025-07-17
**Confidence:** HIGH

## Executive Summary

The CoachApp v1.1 milestone is a **threading integration challenge**, not a feature-complexity challenge. The existing headless app already captures minimap screenshots, detects game events (deaths, kills, objectives), and uploads to the cloud for AI coaching analysis. What's needed is a visual layer that explains, displays, and configures that behavior — without breaking the proven async + tray architecture that powers it.

The core technical risk is the **three-way threading conflict**: pystray currently blocks the main thread, asyncio runs on a daemon thread, and now CustomTkinter needs the main thread for its GUI event loop. The recommended architecture — verified via live proof-of-concept — inverts the current model: CustomTkinter takes the main thread, pystray moves to a background thread via `run_detached()` (confirmed in pystray 0.19.5 source), and asyncio stays on its daemon thread unchanged. A new `EventBus` backed by `queue.Queue` bridges all three threads, with tkinter's `after(100ms)` polling the queue on the main thread. This restructuring touches primarily `coach_app.py`'s `main()` function; the capture pipeline, Riot API client, and upload logic require zero modification.

The second critical finding is that **the infrastructure for the showcase feature (activity log) already exists** — `LiveCoachSession.events_queue` produces typed `LiveEvent` objects with game time, event type, champion names, and details, but is currently unconsumed. A simple asyncio-to-thread bridge completes the pipeline. The third finding is a **PyInstaller build blocker**: `coach.spec` line 35 explicitly excludes `tkinter`, and CustomTkinter's fonts/themes (~360 KB) must be bundled as data or the built .exe crashes silently. The total new dependency footprint is minimal: `customtkinter==5.2.2` + `darkdetect==0.8.0` (~1.5 MB source, ~5-7 MB in bundle including the Tcl/Tk runtime).

## Key Findings

### Recommended Stack

The stack addition is intentionally minimal — one new package with one transitive dependency. No web engine, no Qt bindings, no database.

**New dependencies:**
- **customtkinter 5.2.2**: Modern tkinter wrapper — dark-mode-first themed widgets (CTkButton, CTkTextbox, CTkSwitch, CTkSegmentedButton, CTkTabview). ~1.5 MB. Python-native, no C compilation, no Electron overhead. All widgets needed for settings panel and activity log verified as available.
- **darkdetect 0.8.0**: Auto-detect OS dark/light mode. Pure Python, ~9 KB. Required by CustomTkinter.

**Critical version/config requirements:**
- Pin `customtkinter==5.2.2` — API has broken between major versions.
- Remove `"tkinter"` from `coach.spec` `excludes` list (currently line 35).
- Bundle `customtkinter` package directory as PyInstaller `datas` — fonts, themes, icon resolve via `__file__`-relative paths.
- Add `customtkinter`, `darkdetect`, `darkdetect._windows_detect` to `hiddenimports`.
- Bundle size increases ~5-7 MB (mostly the Tcl/Tk runtime DLLs, unavoidable).

**Alternatives rejected:** PyQt6/PySide6 (50+ MB, licensing complexity), Electron/webview (100+ MB, separate runtime), raw tkinter (functional but looks like Windows 95), Dear PyGui (less mature PyInstaller story).

### Expected Features

**Must-have (table stakes) — users expect these or the app feels broken:**
- **Status display** — prominent, always-visible indicator of app state (waiting/recording/uploading/ready). Maps directly to existing `TrayIcon.set_state()` 4-state model.
- **Settings: minimap position (left/right)** — if capture region is wrong, the entire product is broken. Binary toggle for existing `minimap_left` config boolean.
- **Settings: minimap size** — wrong size means cropped captures. Toggle for existing `minimap_large` boolean with "Recommended for AI" label.
- **Minimize to system tray on close** — gaming companions MUST not clutter the taskbar during gameplay. Intercept `WM_DELETE_WINDOW` → `withdraw()`.
- **First-run "How it works"** — screen-capture companion that sends data to cloud needs immediate trust. 3-4 step visual explanation.
- **Activity log** — real-time event feed proving the app is working. Consumes the existing (but unconsumed) `LiveCoachSession.events_queue`.

**Should-have (differentiators) — not expected but significantly improve UX:**
- **Color-coded activity log** — deaths red, kills green, objectives gold, errors orange. CustomTkinter's `CTkTextbox` supports tag-based coloring.
- **Game timestamps** on every log entry — `[14:32] 💀 Death — killed by Zed`. Uses existing `LiveEvent.game_time_str()`.
- **"Recommended for AI" badge** on minimap size — builds trust that settings matter for analysis quality.
- **Upload progress feedback** in log — turns opaque post-game upload into a narrative (`Uploading 7 events...` → `Analysis ready!`).
- **Champion name in status** during recording — "Recording — Jinx". Already available via existing `tray.set_state("recording", detail=champion)`.

**Defer to v2+ (anti-features for this milestone):**
- In-game overlay (anti-cheat risk, massive complexity)
- Auto-start with Windows (registry manipulation, user suspicion)
- Sound notifications (gamers have tuned audio — mid-teamfight notification = rage)
- Continuous minimap size slider (AI tuned for two discrete sizes, not continuous)
- Log persistence (RAM-only per PROJECT.md — `coach_app.log` exists for debugging)
- Dark/light theme toggle (gaming apps are dark, ship dark-only)
- Multi-monitor / capture region preview (primary monitor only for now)
- Backend URL or auth token in GUI (security risk — `.env` only)

### Architecture Approach

The architecture is a **three-thread model with a central event bus**. CustomTkinter owns the main thread (hard requirement — tkinter is most reliable on the main thread on Windows). pystray moves to a daemon thread (its Win32 backend creates an independent message pump that works correctly from any thread). asyncio stays on its existing daemon thread. A new `EventBus` (wrapper around `queue.Queue`) is the single communication channel: any thread can write, the main thread drains via `after(100ms)` polling.

**Major components:**

| Component | File | Status | Responsibility |
|-----------|------|--------|----------------|
| **EventBus** | `event_bus.py` | NEW | Thread-safe `queue.Queue` wrapper with typed `BusMessage` (GAME_EVENT, STATUS_CHANGE, SHOW_WINDOW, HIDE_WINDOW, SHUTDOWN) |
| **GuiWindow** | `gui_window.py` | NEW | CustomTkinter CTk window — status bar, settings panel, activity log, how-it-works. Polls EventBus via `after()`. |
| **TrayIcon** | `tray_icon.py` | MODIFIED | Add "Open CoachApp" menu item (`default=True` for double-click). Show/hide via EventBus, never direct tkinter calls. |
| **coach_app** | `coach_app.py` | MODIFIED | Entry point restructured for 3-thread model. Creates EventBus, wires components, manages shutdown sequence. |
| **LiveCoachSession** | `live_coach.py` | UNCHANGED | Event detection, minimap capture. Already emits to `events_queue`. |
| **AppConfig** | `app_config.py` | MINOR MOD | Add `threading.Lock` for thread-safe read-modify-write (currently zero synchronization). |

**Key data flow patterns:**
1. **Activity log** (asyncio → GUI): `LiveCoachSession._emit()` → `asyncio.Queue` → bridge task → `queue.Queue` (EventBus) → `after()` poll → CTkTextbox widget
2. **Status updates** (asyncio → tray + GUI): coach_loop → `tray.set_state()` (direct, lock-protected, unchanged) + `bus.put(STATUS_CHANGE)` (additive)
3. **Show/hide window** (tray → GUI): pystray callback → `bus.put(SHOW_WINDOW)` → poll → `deiconify()` on main thread. **Never call tkinter methods from pystray thread.**
4. **Settings** (GUI → config → capture): GUI toggle → `save_config()` → config.json. Capture reads config fresh each time via `get_config()`. No cross-thread notification needed.

### Critical Pitfalls

The 17 identified pitfalls distill into 5 architectural threats that must be addressed in specific phases:

1. **Main thread war** (Pitfall #1, CRITICAL) — pystray `Icon.run()` and CustomTkinter `mainloop()` both block and expect to own the main thread. **Prevention:** Invert the threading model — CTk on main, pystray on daemon thread. This is the foundational decision; everything else depends on it.

2. **Cross-thread GUI updates crash tkinter** (Pitfall #2, CRITICAL) — Calling any widget method from the asyncio or pystray thread causes random `TclError`, frozen windows, or segfaults. tkinter's Tcl interpreter is single-threaded. `threading.Lock` does NOT help. **Prevention:** All GUI updates go through EventBus → `after()` poll → main thread execution. Never call widget methods directly from other threads.

3. **PyInstaller build blocker** (Pitfalls #3 + #4, CRITICAL) — `coach.spec` excludes tkinter AND CustomTkinter assets aren't auto-detected by PyInstaller. Built .exe launches, pystray works, then crashes silently on first `import customtkinter` (because `console=False`). **Prevention:** Remove tkinter from excludes, add CTk package to `datas`, add hidden imports. Test the BUILT .exe, not the dev environment.

4. **Config race condition** (Pitfall #5, CRITICAL) — Adding a GUI settings panel creates a 3rd writer to `config.json` with zero locking. Read-modify-write from 3 threads = lost writes or corrupted JSON. **Prevention:** Add `threading.Lock` to `app_config.py` + atomic writes via `os.replace()`.

5. **GUI window captured in minimap screenshots** (Pitfall #6, CRITICAL) — `mss` captures whatever is on screen. If the GUI overlaps the minimap region, captures are corrupted and AI analysis receives garbage. **Prevention:** Auto-withdraw window during `"recording"` state. Position window away from minimap region on launch.

**Additional moderate pitfalls to address:** Window close kills app instead of minimizing (#7), shutdown coordination across 3 components (#8), DPI scaling mismatch (#9), dual update paths for tray + GUI (#10), `after()` may behave differently when window is withdrawn (#11), activity log memory growth (#12), focus stealing during gameplay (#16).

## Implications for Roadmap

### Phase 1: Threading Foundation + Event Bus
**Rationale:** The threading model is the highest-risk integration. Every GUI feature depends on the 3-thread architecture working correctly. The EventBus must exist before anything can communicate cross-thread. Build this first, validate it in isolation.
**Delivers:** `event_bus.py` (new), `coach_app.py` restructured `main()` with 3-thread startup, `app_config.py` with threading.Lock, clean shutdown sequence (stop_event → SHUTDOWN message → destroy → join).
**Addresses features:** Minimize-to-tray foundation, threading infrastructure.
**Avoids pitfalls:** #1 (main thread war), #2 (cross-thread updates), #5 (config race condition), #8 (shutdown coordination).

### Phase 2: GUI Shell + Tray Integration
**Rationale:** The basic window must exist and correctly coexist with pystray before any content panels make sense. Show/hide, close-to-tray, and tray double-click are the user-facing proof that the threading model works.
**Delivers:** `gui_window.py` basic shell (CTk window, dark theme, hide-on-close, bus polling skeleton), `tray_icon.py` modified with "Open CoachApp" menu item, show/hide via EventBus.
**Addresses features:** Window shell, minimize to system tray, tray double-click.
**Avoids pitfalls:** #7 (close kills app), #14 (tray double-click expectation), #16 (focus stealing — don't force focus during game).

### Phase 3: Content Panels — Status + How-It-Works + Settings
**Rationale:** These are independent UI panels that need only the window shell and the event bus. Status display consumes STATUS_CHANGE messages. Settings wires to existing `app_config.py`. "How it works" is static content. They can be built together because they share no dependencies beyond the shell.
**Delivers:** Status bar with 4-state indicator + champion name detail, "How it works" panel (3-4 step explanation), settings panel (minimap position toggle, size toggle with "Recommended for AI" label).
**Addresses features:** Status display, first-run explanation, minimap position setting, minimap size setting, "Recommended for AI" badge, champion name in status.
**Avoids pitfalls:** #10 (dual update paths — status goes through unified EventBus), #6 (auto-withdraw window on recording state change).

### Phase 4: Activity Log + Event Bridge
**Rationale:** The showcase feature — the thing that makes users say "oh, it actually works." Depends on the event bus (Phase 1) and the window shell (Phase 2). The async-to-thread bridge task connects `LiveCoachSession.events_queue` (currently unconsumed) to the GUI. Color coding and timestamps make it scannable.
**Delivers:** CTkTextbox activity log with color-coded events (12 event types mapped to colors), game-time timestamps, emoji prefixes, auto-scroll, 500-entry cap. Event bridge asyncio task. Upload progress feedback in log.
**Addresses features:** Activity log, color coding, timestamps, upload progress feedback.
**Avoids pitfalls:** #12 (memory growth — deque/maxlen from day one), #11 (after() polling when withdrawn — test and handle catch-up on show).

### Phase 5: Build Configuration + Validation
**Rationale:** PyInstaller config can only be validated when all GUI features work. This is the gating step for producing a distributable .exe. Must be a separate phase because the failure mode (silent crash in built .exe, works fine in dev) requires dedicated testing.
**Delivers:** Updated `coach.spec` (remove tkinter exclusion, add CTk datas + hiddenimports), verified built .exe with all GUI features working, documented bundle size increase.
**Addresses features:** Distributable build.
**Avoids pitfalls:** #3 (tkinter excluded), #4 (assets missing), #17 (sys.frozen path resolution), #15 (size increase — document, don't fight it), #9 (DPI scaling — test on 125%+ displays).

### Phase Ordering Rationale

- **Phase 1 must be first** — the threading model is foundational. If CTk can't coexist with pystray and asyncio, nothing else matters. Config thread-safety belongs here because it's a prerequisite for safe multi-thread access.
- **Phase 2 before content** — the window shell must exist and correctly show/hide before panels make sense. Tray integration validates the EventBus pattern end-to-end.
- **Phase 3 groups naturally** — status, settings, and how-it-works are all "content inside the window shell." They depend on Phase 2 but not on each other. Settings depends on config thread-safety from Phase 1.
- **Phase 4 after status** — the activity log's event bridge reuses the same EventBus polling established in Phase 2. Status display in Phase 3 proves the pattern works before the more complex log feature.
- **Phase 5 must be last** — can only validate when everything is integrated. Testing must happen on the BUILT .exe, not the dev environment.

### Research Flags

**Phases needing careful implementation/testing (but patterns are well-documented):**
- **Phase 1:** Threading model is highest-risk. The pattern is well-known, but test startup, shutdown, sleep/wake, alt-tab exhaustively. `run_detached()` verified via PoC but integration with full coach_loop needs testing.
- **Phase 4:** `after()` polling behavior when window is `withdraw()`'d needs empirical testing. If it stops firing, workaround is catch-up sync on `deiconify()`.
- **Phase 5:** CustomTkinter PyInstaller bundling has known gotchas. Test the built .exe on a clean machine (no Python installed). Test on high-DPI displays.

**Phases with standard patterns (low risk, skip deep research):**
- **Phase 2:** Window lifecycle (`withdraw`/`deiconify`/`WM_DELETE_WINDOW`) is standard tkinter. pystray menu items are well-documented.
- **Phase 3:** UI layout with CustomTkinter widgets is straightforward. Config read/write to `app_config.py` is already proven in tray menu. Status display is a label that updates via callback.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | customtkinter 5.2.2 + darkdetect 0.8.0 verified via `pip install` + source inspection. pystray 0.19.5 `run_detached()` verified via source + live PoC. All CTk widgets instantiated and tested. |
| Features | HIGH | Feature list derived from PROJECT.md decisions + direct codebase analysis. Event types from `live_coach.py`. Widget mapping verified against CTk 5.2.2 API. |
| Architecture | HIGH | 3-thread model is a well-understood Python pattern. All integration points verified in code with specific line references. EventBus pattern uses stdlib `queue.Queue` with guaranteed thread safety. |
| Pitfalls | HIGH | 17 pitfalls identified from direct code analysis, all with concrete line references and prevention strategies. Critical pitfalls (#1-#6) have HIGH confidence; DPI pitfall (#9) and after()-when-withdrawn (#11) are MEDIUM. |

**Overall confidence: HIGH** — all critical findings verified via source inspection or live execution.

### Gaps to Address

- **`after()` behavior when window is `withdraw()`'d** (MEDIUM confidence): Pitfall #11 notes tkinter `after()` may deprioritize or stop firing for hidden windows on some Windows versions. Needs empirical testing in Phase 4. Workaround: catch-up sync on `deiconify()`, or use `iconify()` instead of `withdraw()`.
- **DPI scaling interaction** (MEDIUM confidence): Pitfall #9 — CustomTkinter sets `SetProcessDpiAwareness(2)` which is process-global. If this changes how `mss` interprets screen coordinates, minimap capture region will be offset. Test on 125% and 150% scaling in Phase 5.
- **pystray daemon thread startup timing**: When `Icon.run()` runs on a daemon thread, the tray icon may not be immediately visible. The `Icon.run(setup=callback)` pattern can signal readiness, but timing relative to CTk window appearance needs integration testing in Phase 2.
- **`LiveCoachSession` lifetime vs event bridge**: The `events_queue` belongs to a `LiveCoachSession` instance that is created per game and destroyed after upload. The bridge task must handle session creation/destruction gracefully (no reference to a dead session's queue). Needs attention in Phase 4.

## Sources

### Primary (HIGH confidence)
- Direct code analysis: `coach_app.py`, `tray_icon.py`, `live_coach.py`, `minimap_capture.py`, `app_config.py`, `live_game_client.py`, `coach.spec` — all line references verified
- Live package verification: `customtkinter==5.2.2`, `darkdetect==0.8.0`, `pystray==0.19.5` — installed and inspected
- Proof-of-concept execution: `run_detached()` frees main thread for CTk mainloop
- CustomTkinter source inspection: `theme_manager.py` lines 16-20, `font/__init__.py` lines 10-18 for asset path resolution
- Widget API verification: CTkTextbox, CTkSwitch, CTkSegmentedButton, CTkTabview instantiated with methods tested
- Python stdlib: `queue.Queue` thread safety, `threading.Lock`, `threading.Event` semantics
- tkinter/Tcl documentation: main thread requirement, `after()` scheduling, `WM_DELETE_WINDOW` protocol, `withdraw()`/`deiconify()`
- pystray source: `_win32.py` backend — `Shell_NotifyIconW` via `ctypes.windll.shell32`, independent message pump

### Secondary (MEDIUM confidence)
- Gaming companion UX patterns: Discord, Overwolf, Blitz.gg, Mobalytics desktop — established conventions for tray behavior, status display, activity logging
- DPI awareness interaction between CustomTkinter and mss — depends on exact mss version + Windows version
- `after()` callback behavior for withdrawn windows — generally works on Windows, but edge cases may exist

---
*Research completed: 2025-07-17 — v1.1 CoachApp Desktop GUI milestone*
*Ready for roadmap: yes*
