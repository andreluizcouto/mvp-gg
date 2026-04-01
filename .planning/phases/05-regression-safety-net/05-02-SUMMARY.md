---
phase: 05-regression-safety-net
plan: "02"
subsystem: frontend
tags: [testing, vitest, react, regression, smoke]
dependency_graph:
  requires: [05-01]
  provides: [frontend-test-harness, results-screen-tests, summoner-screen-tests, api-contract-tests]
  affects: [frontend/src/__tests__, frontend/src/services/__tests__]
tech_stack:
  added: [vitest, @testing-library/react, @testing-library/jest-dom, jsdom]
  patterns: [component-testing, api-contract-testing, mock-service]
key_files:
  created:
    - frontend/vitest.config.js
    - frontend/src/test/setupTests.js
    - frontend/src/__tests__/ResultsScreen.test.jsx
    - frontend/src/__tests__/SummonerProfileScreen.test.jsx
    - frontend/src/services/__tests__/api.test.js
  modified:
    - frontend/package.json
decisions:
  - "Use mergeConfig(viteConfig, ...) in vitest.config.js to inherit Vite's plugin-react JSX transform — avoids React is not defined with @vitejs/plugin-react@6 (oxc transformer)"
  - "esbuild.jsx: 'automatic' + jsxImportSource: 'react' added to vitest config as fallback for JSX transform"
  - "Use getAllByText instead of getByText for elements that appear multiple times in layout (AnalysisStatusBlock renders in 2 places)"
  - "msw not used — vi.mock on api.js module provides sufficient control for these smoke tests"
metrics:
  duration: ~45min
  completed: "2026-04-01"
---

# Phase 05 Plan 02: Frontend Smoke/Render Coverage for Key Journeys

## One-liner

Set up Vitest + @testing-library/react harness, wrote 6 frontend smoke tests covering API contracts, status rendering, and IA badge gating — fixed JSX transform config issue — 6/6 tests passing.

## Tasks Completed

| # | Task | Status | Files |
|---|------|--------|-------|
| 1 | Wave 0: Vitest + testing-library harness setup | ✅ Done | vitest.config.js, setupTests.js, package.json |
| 2 | API contract tests (normalizeOptionalRiotId, safe fallback) | ✅ Done | api.test.js (3 tests) |
| 3 | ResultsScreen status render tests (private, ready) | ✅ Done | ResultsScreen.test.jsx (2 tests) |
| 4 | SummonerProfileScreen IA badge gating | ✅ Done | SummonerProfileScreen.test.jsx (1 test) |
| 5 | Fix JSX transform (React is not defined) | ✅ Done | vitest.config.js |

## Changes Made

### frontend/vitest.config.js — Vitest configuration
Created with `mergeConfig(viteConfig, defineConfig({...}))` to inherit `@vitejs/plugin-react` JSX automatic transform.
Added `esbuild: { jsx: "automatic", jsxImportSource: "react" }` as explicit fallback.
Test environment: jsdom. Setup file: src/test/setupTests.js.

### frontend/src/test/setupTests.js
`import '@testing-library/jest-dom'` for extended matchers (toBeInTheDocument, etc.).

### api.test.js — 3 contract tests
- `normalizeOptionalRiotId` returns `""` on empty/invalid input (safe fallback)
- `normalizeOptionalRiotId` parses valid `"GameName#TAG"` correctly
- API module exports expected functions

### ResultsScreen.test.jsx — 2 render tests
- Direct-link without owner context → "Análise privada para este jogador" (private-safe block)
- Owner flow with `status: "ready"` → "Análise pronta" + "COACHING IA" visible

### SummonerProfileScreen.test.jsx — 1 render test
- IA badge "COACHING IA" visible only when `status === "ready"`, absent for `status: "pending"`

## Deviations from Plan

**JSX transform bug:** `@vitejs/plugin-react@6` uses oxc transformer. Vitest's own esbuild pipeline didn't apply JSX automatic runtime. Fixed by using `mergeConfig` to inherit Vite's plugin configuration.

**Multiple element query:** `AnalysisStatusBlock` renders "Estado da análise:" label in two places in the ready layout. Changed `getByText` → `getAllByText` to avoid false failures.

## Known Stubs

None.

## Self-Check: PASSED

- ✅ 6/6 frontend tests passing: `cd frontend && npm run test -- --run`
- ✅ api.test.js: 3/3 (API contracts)
- ✅ SummonerProfileScreen.test.jsx: 1/1 (IA badge gating)
- ✅ ResultsScreen.test.jsx: 2/2 (status rendering)
