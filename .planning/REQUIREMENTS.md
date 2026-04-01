# Requirements: mvp.gg

**Defined:** 2026-04-01
**Core Value:** The product must show a solo queue player meaningful errors and strengths they would not have identified alone, in a way they can trust and act on.

## v1 Requirements

### Analysis Quality

- [x] **ANLY-01**: User can open a match and receive an automated analysis that identifies concrete strengths, mistakes, and next actions from that specific game
- [x] **ANLY-02**: User sees coaching points tied to match evidence such as builds, runes, events, or timeline context instead of generic advice
- [x] **ANLY-03**: Similar matches produce analysis with consistent structure and quality instead of large unexplained variation
- [x] **ANLY-04**: User can revisit an analyzed match and receive the same validated coaching result unless the analysis is intentionally regenerated

### Data and Delivery

- [x] **DATA-01**: System can assemble a complete post-game evidence bundle from Riot data and localhost-derived context before AI analysis runs
- [x] **DATA-02**: System rejects, flags, or safely degrades when the evidence bundle is incomplete, corrupt, or insufficient for trustworthy coaching
- [ ] **DATA-03**: User can clearly tell whether coaching for a match is ready, pending, unavailable, or failed

### Security

- [ ] **SECU-01**: Backend validates sensitive requests and never relies on frontend-owned logic for security or business-critical decisions
- [ ] **SECU-02**: Secrets, tokens, and internal-only controls remain server-side and are protected from accidental exposure
- [ ] **SECU-03**: Server validates and rate-limits critical input paths such as Riot ID lookup, match fetches, and local upload payloads
- [ ] **SECU-04**: Core architecture is ready for future login and monetization without redesigning trust boundaries

### User Experience

- [ ] **UX-01**: User can search by Riot ID, browse recent matches, and reach the target match analysis page without confusion
- [ ] **UX-02**: Match analysis page presents stats and coaching in a polished, readable browser experience
- [ ] **UX-03**: Product presents enough trust signals that the user feels comfortable sharing the experience with the community

### Quality and Verification

- [ ] **QUAL-01**: Automated tests cover the critical search, ingestion, analysis, and rendering paths most likely to regress
- [x] **QUAL-02**: System performs explicit verification between ingestion, context building, AI output validation, and frontend delivery

## v1.1 Requirements — MVPApp Desktop GUI

### Desktop App Infrastructure

- [x] **APP-01**: App runs CustomTkinter GUI on main thread with pystray on detached thread and asyncio on daemon thread without deadlocks or crashes
- [x] **APP-02**: Cross-thread events flow from asyncio loop to GUI via EventBus (queue.Queue + after() polling)
- [x] **APP-03**: Config read/write is thread-safe with locking to prevent race conditions between GUI, tray, and capture threads
- [ ] **APP-04**: PyInstaller build bundles CustomTkinter assets and produces a working .exe

### Desktop App Window

- [ ] **WIN-01**: User sees a clean, dark-mode main window with app branding when launching MVPApp
- [ ] **WIN-02**: User can close the window and the app minimizes to system tray instead of exiting
- [ ] **WIN-03**: User can show the window again by double-clicking the tray icon
- [ ] **WIN-04**: Window auto-hides during active recording to prevent minimap capture interference

### Desktop App Content

- [ ] **CNT-01**: User sees a "How it works" panel explaining what the app does and how to use it
- [ ] **CNT-02**: User sees current app status (waiting for game, recording, uploading, ready) matching tray icon states
- [ ] **CNT-03**: User can toggle minimap position between left and right
- [ ] **CNT-04**: User can see minimap size recommendation ("Grande" labeled as recommended for AI accuracy)

### Desktop App Activity Log

- [ ] **LOG-01**: User sees a real-time feed of game events (deaths, kills, objectives, captures, uploads, errors) with timestamps
- [ ] **LOG-02**: Events are color-coded by type for quick visual scanning
- [ ] **LOG-03**: Log is RAM-only with bounded size to prevent memory growth — no sensitive data exposed

## v2 Requirements

### Advanced Coaching

- **ADV-01**: User can ask follow-up questions to the AI about a completed match
- **ADV-02**: User receives phase-of-game coaching broken down by lane phase, mid game, and late game
- **ADV-03**: User can compare a match against reference games or higher-ranked players on the same champion

### Expanded Product Surface

- **EXP-01**: User receives live coaching during an active match
- **EXP-02**: Coaches or teams can use the platform collaboratively
- **EXP-03**: User can access the product through a dedicated mobile app

## Out of Scope

| Feature | Reason |
|---------|--------|
| Live in-game coaching | Post-game trust and consistency come first |
| Coach and team workflows | Product is focused on solo queue improvement |
| Mobile app | Browser-first product for now |
| Dynamic AI chat | Deferred until core analysis is trusted |
| Reference-match comparison | Deferred until base coaching quality is stable |
| Deep phase-of-game coaching | Deferred to keep v1 focused and shippable |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SECU-01 | Phase 1 | Pending |
| SECU-02 | Phase 1 | Pending |
| SECU-03 | Phase 1 | Pending |
| SECU-04 | Phase 1 | Pending |
| DATA-01 | Phase 2 | Complete |
| DATA-02 | Phase 2 | Complete |
| QUAL-02 | Phase 2 | Complete |
| ANLY-01 | Phase 3 | Complete |
| ANLY-02 | Phase 3 | Complete |
| ANLY-03 | Phase 3 | Complete |
| ANLY-04 | Phase 3 | Complete |
| UX-01 | Phase 4 | Complete |
| UX-02 | Phase 4 | Complete |
| DATA-03 | Phase 4 | Complete |
| QUAL-01 | Phase 5 | Complete |
| UX-03 | Phase 6 | Pending |
| APP-01 | Phase 7 | Complete |
| APP-02 | Phase 7 | Complete |
| APP-03 | Phase 7 | Complete |
| WIN-01 | Phase 8 | Pending |
| WIN-02 | Phase 8 | Pending |
| WIN-03 | Phase 8 | Pending |
| CNT-01 | Phase 9 | Pending |
| CNT-02 | Phase 9 | Pending |
| CNT-03 | Phase 9 | Pending |
| CNT-04 | Phase 9 | Pending |
| WIN-04 | Phase 9 | Pending |
| LOG-01 | Phase 10 | Pending |
| LOG-02 | Phase 10 | Pending |
| LOG-03 | Phase 10 | Pending |
| APP-04 | Phase 11 | Pending |

**Coverage:**
- v1 requirements: 16 total
- Mapped to phases: 16
- Unmapped: 0
- v1.1 requirements: 15 total
- Mapped to phases: 15
- Unmapped: 0

---
*Requirements defined: 2026-04-01*
*Last updated: 2026-04-01 after v1.1 requirements definition*
