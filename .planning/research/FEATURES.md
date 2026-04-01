# Feature Landscape — CoachApp Desktop GUI (v1.1)

**Domain:** Desktop gaming companion app GUI (League of Legends post-game coaching)
**Researched:** 2025-07-14
**Overall confidence:** HIGH — based on direct codebase analysis + established gaming companion UX patterns

## Table Stakes

Features users expect from a desktop companion app with a GUI. Missing any of these makes the product feel broken or unfinished.

| Feature | Why Expected | Complexity | Dependencies | Notes |
|---------|--------------|------------|--------------|-------|
| **Status display — prominent, always visible** | Users launch the app and immediately need to know: is it working? Is it looking for a game? Is it recording? Every gaming companion (Overwolf apps, Blitz, Mobalytics desktop) shows state prominently. Without it, users alt-tab mid-game to check if the app crashed. | Low | Existing `TrayIcon.set_state()` already tracks 4 states: waiting/recording/uploading/ready. GUI just needs to consume the same state. | Map the 4 existing states to visual indicators: color + icon + label. Use the same `_COLORS` and `_STATUS_LABELS` dicts from `tray_icon.py` for consistency. |
| **Settings panel: minimap position (left/right)** | LoL lets players move minimap to either side. If capture region is wrong, the entire product is broken — every screenshot misses the minimap. This is the #1 config that MUST be right. | Low | Existing `app_config.get_config()`/`save_config()` with `minimap_left` bool. `minimap_capture.py` already reads it at capture time. | Binary toggle (left/right). Currently a checkbox in tray menu — upgrade to a visual toggle or segmented control in the GUI. |
| **Settings panel: minimap size** | Similar to position — wrong size means capture is cropped or includes HUD chrome. Currently `minimap_large` is a bool (factor 0.37 vs 0.43). Users don't know which to pick without guidance. | Low | Existing `minimap_large` bool in `app_config.py`. Factor used in `minimap_capture.py` line 30-31. | Add a "Recommended for AI" label on the large option (per PROJECT.md: ~43% screen height gives enough resolution for champion/icon recognition). Simple toggle, not a slider. |
| **Minimize to system tray on window close** | Gaming companions MUST not clutter the taskbar during gameplay. Users close windows instinctively; the app must keep running in the tray. Every serious gaming companion does this (Discord, Overwolf, Blitz). If closing the window kills the app mid-game, users lose their entire match's capture data. | Medium | Requires coordinating CustomTkinter window lifecycle with existing `pystray.Icon` from `tray_icon.py`. Need to intercept `WM_DELETE_WINDOW`, hide the window, and restore on tray double-click/menu item. | The hard part is coexisting two event loops: CustomTkinter's `mainloop()` and pystray's `run()`. pystray typically blocks the main thread. Solution: run pystray in a background thread (it supports this on Windows via `Icon.run_detached()` or `Icon(setup=callback)` pattern). |
| **First-run explanation ("How it works")** | Users download a .exe that captures their screen and sends data to the cloud. Without explaining what it does, users will distrust it, think it's spyware, or not understand the value. Trust is the #1 barrier for a screen-capture companion app. | Low | Static content. No dependencies on existing code. | 3-4 step explanation: (1) app detects LoL game, (2) captures minimap at key moments (deaths, kills, objectives), (3) sends to cloud for AI analysis, (4) view coaching on mvpgg.vercel.app. Keep it under 100 words total. Visual steps > paragraphs. |
| **Activity log — basic event feed** | Users need proof the app is doing something during a game. "Did it capture my death at 12:30?" Without a log, the app is a black box. Users will check the log when analysis seems wrong or missing. | Medium | `LiveCoachSession.events_queue` (asyncio.Queue) already emits `LiveEvent` objects with event_type, timestamp_sec, champion, detail, minimap_path. Need a bridge from asyncio thread → GUI thread. | The async→GUI bridge is the core technical challenge. Options: (1) `window.after()` polling a thread-safe queue every 200-500ms, (2) a callback registered on the session that posts to GUI. Option 1 is simpler and proven with tkinter. Color-code by event type using the existing event type constants. |

## Differentiators

Features that set the app apart from "yet another companion app." Not expected, but significantly improve the user experience.

| Feature | Value Proposition | Complexity | Dependencies | Notes |
|---------|-------------------|------------|--------------|-------|
| **Color-coded activity log** | Deaths in red, kills in green, objectives in gold/blue, errors in orange, uploads in blue. Makes the log scannable at a glance — users alt-tab for 2 seconds and can see "3 deaths, 2 dragons" without reading text. No gaming companion does this well for event-level logging. | Low (incremental over basic log) | Basic activity log must exist first. Map `EVENT_DEATH`→red, `EVENT_KILL`→green, `EVENT_MULTIKILL`→purple, `EVENT_DRAGON`/`EVENT_BARON`/`EVENT_HERALD`→gold, `EVENT_TURRET`→blue, errors→orange, uploads→teal. | CustomTkinter's `CTkTextbox` supports tag-based coloring (wraps tkinter.Text which has `tag_config`). Each log line gets a tag matching its event type. |
| **Timestamps on every log entry** | `[14:32] 💀 Death — killed by Zed (assisted by Lee Sin)` reads naturally and maps to game time. Users can cross-reference with their VOD or replay. | Low (incremental over basic log) | `LiveEvent.game_time_str()` already returns `"MM:SS"` format. Just prefix each log line. | Use game time (from event) for in-game events, not wall-clock time. Game time is what players think in. Add wall-clock for non-game events (upload started, error occurred). |
| **"Recommended for AI" badge on minimap size** | No other app tells users "this setting makes the AI work better." It builds trust: the app isn't just capturing blindly, the size matters for analysis quality. Users feel guided, not abandoned. | Trivial | Static label next to the minimap_large toggle. | Per PROJECT.md decision: large minimap (~43% screen height, ~464px on 1080p) gives enough resolution for champion/icon recognition. Label it as a recommendation, not a requirement — users who prefer smaller minimap should still be able to use the app. |
| **Upload progress feedback in log** | `[POST-GAME] ⬆️ Uploading 7 events to cloud...` → `[POST-GAME] ✅ Upload complete — analysis processing` → `[POST-GAME] 🎯 Analysis ready! View at mvpgg.vercel.app`. Turns the opaque upload phase into a narrative. | Low-Medium | Requires injecting log events from `coach_app._upload()` and `coach_app._poll_status()` into the GUI log. These functions already use `logger.info()` — could tap into logging or add explicit callbacks. | The upload/poll functions are in coach_app.py (lines 53-147). They already log to Python's logging module. Simplest approach: add a custom logging handler that pushes formatted messages to the GUI's event queue. |
| **Champion name in status during recording** | During recording, show "Recording — Jinx" with the champion name. Players feel the app "knows" their game. | Low | `coach_app.py` line 167 already passes `champion` to `tray.set_state("recording", detail=champion)`. GUI just needs to display the detail string. | Text-only is fine for v1.1. Champion icons via Data Dragon CDN can come later. |

## Anti-Features

Features to explicitly NOT build in this milestone. Each has a clear reason.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **In-game overlay** | Requires DirectX/Vulkan hooking or Windows Game Bar integration. High risk of anti-cheat flags (Vanguard). Massive complexity. Players already have their HUD — another overlay is noise. | Keep the app as a background companion. Users check it between games or after match. The tray icon color is the only in-game signal. |
| **Auto-start with Windows** | Registry/startup folder manipulation requires elevated permissions on some systems. Users are suspicious of apps that auto-start. Adds uninstall complexity. | Add in a later milestone only if users request it. For now, users launch manually or pin to taskbar. |
| **Sound notifications** | Gamers have carefully tuned audio (Discord, Spotify, game audio). An unexpected notification sound mid-teamfight is rage-inducing. | Visual-only feedback through tray icon color changes and log entries. |
| **Minimap size slider (continuous)** | The capture formula uses two discrete factors (0.37 and 0.43). A continuous slider would require recalibrating the capture math AND the AI model's expectations. Over-engineering for two valid options. | Keep it as a binary toggle (normal/large). The AI is tuned for these two sizes. |
| **Log persistence / log file viewer** | `coach_app.log` already exists on disk for debugging. The GUI log is for real-time trust, not forensic analysis. Persisting GUI log adds file I/O, rotation, and UI for loading old logs — all unnecessary. | RAM-only log (per PROJECT.md decision). Clear on app restart. Power users can check `coach_app.log` directly. |
| **Settings for backend URL or auth token** | Exposing these in the GUI is a security risk and confusing for users. The `.env` file already handles this for developers. | Keep backend URL and token in `.env` only. If token is missing, show a clear error in the activity log ("Authentication not configured"). |
| **Dark/light theme toggle** | Gaming apps are dark-themed. Period. Adding a toggle doubles the design work for a feature almost no gamer will use. CustomTkinter defaults to dark. | Ship dark mode only. Use CustomTkinter's built-in dark theme (`set_appearance_mode("dark")`). |
| **Multi-monitor / capture region preview** | `mss` captures from `monitors[1]` (primary). Supporting multi-monitor with a visual preview of the capture region is significant complexity. | Capture from primary monitor only. Document this limitation. Address only if users report issues. |
| **Localization / i18n** | The codebase mixes Portuguese logging and English labels. Full i18n is a project in itself. | English-only GUI for v1.1. Standardize all user-facing strings to English. |

## Feature Dependencies

```
┌─────────────────────────────┐
│  CustomTkinter Window Shell │ ← Everything depends on this
│  (window create, show/hide) │
└──────────┬──────────────────┘
           │
     ┌─────┴──────────────────────────────────────┐
     │                                            │
     ▼                                            ▼
┌─────────────────┐                    ┌─────────────────────┐
│ "How it works"  │                    │ Minimize-to-tray    │
│ (static panel)  │                    │ (pystray + CTk      │
│ No deps beyond  │                    │  coexistence)       │
│ the window      │                    │                     │
└─────────────────┘                    └─────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────┐
│ Settings Panel                                  │
│ - Reads/writes via app_config.py                │
│ - minimap_left toggle                           │
│ - minimap_large toggle + "Recommended" label    │
│ No runtime deps (config read at capture time)   │
└─────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────┐
│ Status Display                                  │
│ - Consumes state from coach_loop                │
│ - Needs event bridge: async thread → GUI        │
│ DEPENDS ON: window shell + event bridge         │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│ Activity Log (real-time)                        │
│ - Consumes LiveEvent from events_queue          │
│ - Consumes upload/poll status from logging      │
│ - Color coding per event type                   │
│ - Timestamps from LiveEvent.game_time_str()     │
│ DEPENDS ON: event bridge (same as status)       │
└─────────────────────────────────────────────────┘
```

**Key dependency insight:** The event bridge (async thread → GUI thread) is the single critical integration point. Status display and activity log both depend on it. Build the bridge first, then both features flow naturally.

## MVP Recommendation

**Prioritize (in build order):**

1. **CustomTkinter window shell + minimize-to-tray** — This is the foundation. Without a window that coexists with pystray, nothing else works. Solve the threading model first: CustomTkinter mainloop on main thread, pystray in a background thread (or via `Icon(setup=...)` pattern), asyncio coach_loop in its own daemon thread. This is the highest-risk integration.

2. **Status display + event bridge** — Build the thread-safe bridge (asyncio → GUI via `window.after()` polling). Display the current state prominently. Once this works, the app already feels alive and useful.

3. **"How it works" panel + settings panel** — Low complexity, high trust value. Static content for explanation, two toggles for settings. These are quick wins after the window shell exists.

4. **Activity log with color coding and timestamps** — The showcase feature. Depends on the event bridge from step 2. Adds LiveEvent consumption, log formatting, and color tags. This is what makes users say "oh, it actually works."

5. **Upload progress feedback in log** — Polish. Tap into existing Python logging or add callbacks from `_upload()`/`_poll_status()`. Makes the post-game phase transparent.

**Defer to future milestones:**
- **Champion icons in activity log** — Requires bundling Data Dragon assets or CDN fetching. Text names are sufficient for v1.1.
- **Minimap capture preview** — Would let users verify the capture region visually. Nice-to-have but adds complexity.
- **Auto-start with Windows** — Only if user feedback requests it.

## Complexity Assessment

| Feature | Estimated Effort | Risk | Notes |
|---------|-----------------|------|-------|
| Window shell + tray coexistence | Medium | **HIGH** — This is the threading integration that can go wrong. pystray + CustomTkinter + asyncio = 3 event loops. | Test on Windows 10 and 11. pystray's `Icon.run_detached()` or `Icon(setup=callback)` are the integration paths. |
| Event bridge (async → GUI) | Medium | Medium — Pattern is well-known (`after()` polling) but must handle queue draining without blocking GUI. | Poll every 250ms. Drain all available events per tick (not just one). |
| Status display | Low | Low | Just a label + colored indicator that updates via the event bridge. |
| "How it works" panel | Low | Low | Static CustomTkinter frames/labels. |
| Settings panel | Low | Low | Two toggles wired to `app_config.py`. Already proven in tray menu. |
| Activity log | Medium | Low-Medium — Scrolling performance if hundreds of events. | Cap at ~500 visible entries. Auto-scroll to bottom. CustomTkinter's CTkTextbox handles this. |
| Minimize to tray | Medium | Medium — Window hide/show must be reliable. Some Windows versions handle `withdraw()`/`deiconify()` differently. | Test thoroughly. Handle edge case: user clicks tray icon while window is already visible → bring to front, don't hide. |

## Event Types Available for the Activity Log

Based on `live_coach.py` analysis, these are the concrete events the GUI log will display:

| Event Constant | Source | Log Display Example | Suggested Color |
|---------------|--------|---------------------|-----------------|
| `EVENT_DEATH` | `_handle_death()` | `[12:30] 💀 Death — killed by Zed (Lee Sin)` | Red |
| `EVENT_KILL` | `_handle_kill()` | `[14:02] ⚔️ Kill — Jinx killed Ezreal` | Green |
| `EVENT_MULTIKILL` | `_handle_multikill()` | `[14:05] 🔥 Triple Kill!` | Purple/Gold |
| `EVENT_DRAGON` | `_handle_objective()` | `[18:40] 🐉 Dragon Infernal (ally team)` | Gold |
| `EVENT_BARON` | `_handle_objective()` | `[24:10] 👑 Baron Nashor (enemy — STOLEN)` | Gold |
| `EVENT_HERALD` | `_handle_objective()` | `[10:15] 🦀 Rift Herald (ally team)` | Gold |
| `EVENT_TURRET` | `_handle_objective()` | `[16:50] 🏰 Turret destroyed` | Blue |
| (system) | `coach_loop()` | `[--:--] 🔍 Waiting for League of Legends...` | Gray |
| (system) | `coach_loop()` | `[00:00] 🎮 Game detected — Recording as Jinx` | White |
| (system) | `_upload()` | `[POST] ⬆️ Uploading 7 events...` | Teal |
| (system) | `_poll_status()` | `[POST] ✅ Analysis ready!` | Green |
| (error) | various | `[--:--] ⚠️ Upload failed — server timeout` | Orange |

## Sources

- **Direct codebase analysis** (HIGH confidence): `coach_app.py`, `live_coach.py`, `minimap_capture.py`, `tray_icon.py`, `app_config.py`, `config.json`
- **PROJECT.md** (HIGH confidence): Key decisions on CustomTkinter, RAM-only log, minimap size recommendation
- **Gaming companion UX patterns** (MEDIUM confidence): Based on established patterns from Discord, Overwolf, Blitz.gg, Mobalytics desktop apps — well-known desktop gaming companion conventions
- **CustomTkinter + pystray integration** (MEDIUM confidence): Threading model is a known pattern in the Python desktop app community, but specific edge cases depend on Windows version and pystray backend (win32)

---
*Research completed: 2025-07-14 — v1.1 CoachApp Desktop GUI milestone*
