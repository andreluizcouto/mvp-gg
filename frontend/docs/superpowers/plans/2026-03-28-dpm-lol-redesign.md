# MVP.GG Frontend Redesign (dpm.lol Style) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the mvp.gg frontend to match dpm.lol's visual style (dark purple/blue theme, sidebar layout, clean modern aesthetic) while keeping mvp.gg's unique features (ScoreBadge, coaching IA, damage bar).

**Architecture:** Rewrite all 4 screens + shared layout (Navbar/Footer) using dpm.lol's design system: custom black scale (black-0 to black-800), purple/blue accents, Plus Jakarta Sans font, 4-column grid (1 sidebar + 3 main). Shared layout wraps all routes. Each screen is a focused file.

**Tech Stack:** React 19 + Vite 8 + Tailwind 3.4 + React Router 7. No new dependencies.

---

## File Structure

```
src/
├── App.jsx                          (modify) — add Layout wrapper
├── main.jsx                         (no change)
├── index.css                        (rewrite) — new theme, animations, utilities
├── components/
│   ├── Layout.jsx                   (create) — Navbar + Footer + main slot
│   ├── CoachingSection.jsx          (modify) — restyle to match new theme
│   └── Navbar.jsx                   (create) — sticky header with logo, search, nav
├── screens/
│   ├── SearchScreen.jsx             (rewrite) — dpm.lol homepage style
│   ├── SummonerProfileScreen.jsx    (rewrite) — sidebar ranked + match history rows
│   ├── ResultsScreen.jsx            (modify) — restyle to match new theme
│   └── LoadingScreen.jsx            (modify) — restyle skeleton
├── services/
│   ├── api.js                       (no change)
│   └── constants.js                 (no change)
tailwind.config.js                   (rewrite) — dpm.lol color scale + typography
index.html                           (modify) — swap fonts to Plus Jakarta Sans
```

---

## Design System Reference

### Color Palette (from dpm.lol + ui-ux-pro-max Gaming palette)

```
Black Scale (backgrounds):
  black-900: #050506    (deepest, body)
  black-800: #0a0a0c    (header, profile banner, cards)
  black-700: #0f0f23    (body background)
  black-600: #1a1c2e    (search bar, buttons)
  black-500: #252840    (borders, hover)

Text Scale:
  black-0:   #FFFFFF    (brightest text)
  black-100: #E2E8F0    (body text)
  black-200: #94A3B8    (secondary text)
  black-300: #64748B    (muted text)
  black-400: #475569    (dimmest text)

Accents:
  purple-200: #A78BFA   (secondary accent, text)
  purple-300: #7C3AED   (primary accent)
  purple-500: #6D28D9   (CTA buttons)
  blue-300:   #7989EC   (active tab indicator)
  blue-100:   #C4B5FD   (update button text)

Semantic:
  win:    #22C55E (green-500)
  loss:   #EF4444 (red-500)
  lime:   #84CC16 (region badge)
  gold:   #c89b3c (coaching IA accent — kept from mvp.gg)
```

### Typography
- **Font:** Plus Jakarta Sans (loaded from Google Fonts)
- **Sizes (custom tokens):**
  - `text-hxs`: 20px (summoner name lg)
  - `text-bxl`: 18px (summoner name base)
  - `text-bm`: 14px (nav, tabs)
  - `text-bs`: 12px (labels, stats)
  - `text-bxs`: 10px (small labels)

### Layout
- Max content width: `max-w-5xl` (1024px)
- Main grid: `grid-cols-1 lg:grid-cols-4` (1 sidebar + 3 main)
- Header height: `h-[50px]`
- Profile banner: `rounded-b-[32px]` with purple glow shadow
- Gap scale: 4, 8, 12, 16, 20

---

### Task 1: Tailwind Config + CSS Foundation

**Files:**
- Rewrite: `tailwind.config.js`
- Rewrite: `src/index.css`
- Modify: `index.html`

- [ ] **Step 1: Rewrite tailwind.config.js with dpm.lol design tokens**

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        black: {
          0:   '#FFFFFF',
          100: '#E2E8F0',
          200: '#94A3B8',
          300: '#64748B',
          400: '#475569',
          500: '#252840',
          600: '#1a1c2e',
          700: '#0f0f23',
          800: '#0a0a0c',
          900: '#050506',
        },
        purple: {
          200: '#A78BFA',
          300: '#7C3AED',
          500: '#6D28D9',
          600: '#5B21B6',
        },
        blue: {
          100: '#C4B5FD',
          300: '#7989EC',
          400: '#6366F1',
        },
        lime: {
          800: '#3f6212',
        },
        gold: {
          300: '#f0d080',
          400: '#c89b3c',
          500: '#a47d2e',
        },
        accent: {
          red:   '#EF4444',
          green: '#22C55E',
        },
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'hxl': ['32px', { lineHeight: '1.1', fontWeight: '600' }],
        'hxs': ['20px', { lineHeight: '1.2', fontWeight: '600' }],
        'bxl': ['18px', { lineHeight: '1.3', fontWeight: '600' }],
        'bm':  ['14px', { lineHeight: '1.4', fontWeight: '500' }],
        'bs':  ['12px', { lineHeight: '1.5', fontWeight: '500' }],
        'bxs': ['10px', { lineHeight: '1.5', fontWeight: '500' }],
      },
      animation: {
        'fade-up':    'fadeUp 0.4s ease forwards',
        'fade-in':    'fadeIn 0.3s ease forwards',
        'pulse-dot':  'pulseDot 2s ease-in-out infinite',
      },
      keyframes: {
        fadeUp: {
          '0%':   { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        pulseDot: {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0.4' },
        },
      },
    },
  },
  plugins: [],
}
```

- [ ] **Step 2: Rewrite src/index.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

* { box-sizing: border-box; }

html, body {
  background-color: #0f0f23;
  color: #E2E8F0;
  font-family: "Plus Jakarta Sans", system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
}

::-webkit-scrollbar            { width: 6px; }
::-webkit-scrollbar-track      { background: #0a0a0c; }
::-webkit-scrollbar-thumb      { background: #7C3AED44; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover{ background: #7C3AED88; }

@layer utilities {
  .text-gold-gradient {
    background: linear-gradient(135deg, #f0d080 0%, #c89b3c 50%, #a47d2e 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .text-premium {
    background: linear-gradient(135deg, #A78BFA, #7C3AED);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .shimmer-bg {
    background: linear-gradient(90deg, #1a1c2e 0%, #252840 30%, #2a2e52 50%, #252840 70%, #1a1c2e 100%);
    background-size: 200% 100%;
    animation: shimmer 2s linear infinite;
  }
  .glow-purple {
    box-shadow: 0 8px 9px 0px rgba(121,137,236,0.10);
  }
  .scoreGlow {
    animation: scoreGlow 1.8s ease-in-out infinite;
  }
}

@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

@keyframes scoreGlow {
  0%, 100% { box-shadow: 0 0 10px #c89b3cbb, 0 0 20px #c89b3c55; }
  50%       { box-shadow: 0 0 20px #f0d080ee, 0 0 40px #c89b3c99; }
}
```

- [ ] **Step 3: Update index.html fonts**

Replace the Google Fonts link with:
```html
<link
  href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap"
  rel="stylesheet"
/>
```

- [ ] **Step 4: Verify dev server starts**

Run: `cd ProjectB-frontend && npm run dev`
Expected: Vite dev server starts, page loads with new dark background (#0f0f23)

- [ ] **Step 5: Commit**

```bash
git add tailwind.config.js src/index.css index.html
git commit -m "feat: new design system — dpm.lol dark purple theme"
```

---

### Task 2: Shared Layout (Navbar + Footer)

**Files:**
- Create: `src/components/Navbar.jsx`
- Create: `src/components/Layout.jsx`
- Modify: `src/App.jsx`

- [ ] **Step 1: Create src/components/Navbar.jsx**

```jsx
import { useNavigate } from "react-router-dom"

export default function Navbar() {
  const navigate = useNavigate()

  return (
    <header className="bg-black-800 flex sticky top-0 z-30 h-[50px] items-center justify-between px-5 lg:px-6 gap-4 border-b border-white/5">
      {/* Logo */}
      <a
        href="/"
        onClick={e => { e.preventDefault(); navigate("/") }}
        className="flex-shrink-0 text-bxl font-extrabold tracking-tight text-black-0 hover:text-purple-200 transition-colors cursor-pointer"
      >
        MVP.GG
      </a>

      {/* Search bar (pill) */}
      <div
        onClick={() => navigate("/")}
        className="cursor-pointer bg-black-600 hover:bg-black-500/40 duration-200 border border-black-500 text-black-300 text-bs gap-3 font-medium flex items-center justify-start rounded-full px-3 py-1.5 shadow-[0_0px_10px_0px_rgba(121,137,236,0.10)] max-w-[320px] flex-1"
      >
        <svg className="w-4 h-4 text-black-300 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.3-4.3" />
        </svg>
        <span className="truncate">Buscar Invocador...</span>
      </div>

      {/* Right section */}
      <div className="flex items-center gap-3">
        <a
          href="#"
          className="hidden sm:flex items-center gap-2 bg-purple-200/[0.15] hover:bg-purple-200/30 duration-200 px-2 py-1 rounded text-bxs font-extrabold uppercase text-premium"
        >
          Coach IA
        </a>
      </div>
    </header>
  )
}
```

- [ ] **Step 2: Create src/components/Layout.jsx**

```jsx
import { Outlet } from "react-router-dom"
import Navbar from "./Navbar"

export default function Layout() {
  return (
    <div className="bg-black-700 text-black-100 flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}

function Footer() {
  return (
    <footer className="border-t border-white/5 flex flex-col items-center justify-between px-8 py-2 lg:flex-row">
      <p className="text-black-400 text-[10px] lg:text-[11px] text-center lg:text-left">
        MVP.GG is not endorsed by Riot Games. Game content and materials are trademarks of Riot Games.
      </p>
      <div className="flex items-center gap-4 mt-2 lg:mt-0">
        <a href="/privacy" className="text-black-400 hover:text-black-300 text-[10px] transition-colors">Privacidade</a>
        <a href="/tos" className="text-black-400 hover:text-black-300 text-[10px] transition-colors">Termos</a>
      </div>
    </footer>
  )
}
```

- [ ] **Step 3: Modify src/App.jsx to use Layout**

```jsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import Layout                from "./components/Layout"
import SearchScreen          from "./screens/SearchScreen"
import SummonerProfileScreen from "./screens/SummonerProfileScreen"
import ResultsScreen         from "./screens/ResultsScreen"

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/"                    element={<SearchScreen />} />
          <Route path="/summoner/:name/:tag" element={<SummonerProfileScreen />} />
          <Route path="/match/:matchId"      element={<ResultsScreen />} />
          <Route path="*"                    element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
```

- [ ] **Step 4: Verify layout renders**

Run: `npm run dev`
Expected: Page shows sticky dark header with "MVP.GG" logo, search pill, footer at bottom

- [ ] **Step 5: Commit**

```bash
git add src/components/Navbar.jsx src/components/Layout.jsx src/App.jsx
git commit -m "feat: shared Layout with Navbar and Footer (dpm.lol style)"
```

---

### Task 3: SearchScreen Redesign

**Files:**
- Rewrite: `src/screens/SearchScreen.jsx`

- [ ] **Step 1: Rewrite SearchScreen.jsx**

```jsx
import { useState, useRef } from "react"
import { useNavigate, useLocation } from "react-router-dom"

const CHAMPIONS = [
  { name: "Jinx" },
  { name: "Ahri" },
  { name: "Yasuo" },
  { name: "Thresh" },
  { name: "Zed" },
  { name: "Caitlyn" },
]

export default function SearchScreen() {
  const navigate        = useNavigate()
  const { state }       = useLocation()
  const [query, setQuery] = useState("")
  const [error, setError] = useState(state?.error ?? "")
  const inputRef          = useRef(null)

  function handleSubmit(e) {
    e.preventDefault()
    const raw = query.trim()
    if (!raw) { setError("Digite Nick#TAG para buscar."); return }
    const hashIdx = raw.lastIndexOf("#")
    if (hashIdx < 1) { setError("Use o formato Nick#TAG — ex: natus vincere#navi1"); return }
    const nick = raw.slice(0, hashIdx).trim()
    const tag  = raw.slice(hashIdx + 1).trim()
    if (!nick || !tag) { setError("Nick ou TAG inválidos."); return }
    setError("")
    navigate(`/summoner/${encodeURIComponent(nick)}/${encodeURIComponent(tag)}`)
  }

  return (
    <div className="relative min-h-[calc(100vh-50px)] overflow-hidden">
      {/* Background gradient blob */}
      <div className="fixed inset-0 pointer-events-none opacity-30 -top-72 flex justify-center">
        <svg width="900" height="600" viewBox="0 0 900 600" className="blur-3xl">
          <defs>
            <radialGradient id="bg-grad" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#6248FF" stopOpacity="0.4" />
              <stop offset="37%" stopColor="#E5FF48" stopOpacity="0.15" />
              <stop offset="59%" stopColor="#FF48ED" stopOpacity="0.2" />
              <stop offset="71%" stopColor="#48BDFF" stopOpacity="0.15" />
              <stop offset="93%" stopColor="#6248FF" stopOpacity="0.1" />
            </radialGradient>
          </defs>
          <ellipse cx="450" cy="300" rx="450" ry="300" fill="url(#bg-grad)" />
        </svg>
      </div>

      <div className="relative z-10 flex flex-col items-center px-4 pt-[15vh] pb-16">
        {/* Hero */}
        <div className="text-center mb-8 animate-fade-up">
          <h1 className="text-hxl md:text-[42px] font-extrabold text-black-0 leading-none tracking-tight mb-3">
            MVP.GG
          </h1>
          <p className="text-bs text-black-300 tracking-wide">
            Seu Coach de League of Legends com IA
          </p>
        </div>

        {/* Search */}
        <form
          onSubmit={handleSubmit}
          className="w-full max-w-[500px] mb-3 animate-fade-up"
          style={{ animationDelay: "80ms", animationFillMode: "both" }}
        >
          <div className="relative flex items-center bg-black-600 border border-black-500 rounded-full overflow-hidden shadow-[0_0px_10px_0px_rgba(121,137,236,0.10)] hover:bg-black-500/40 transition-colors duration-200">
            <svg className="absolute left-4 w-4 h-4 text-black-300 pointer-events-none" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.3-4.3" />
            </svg>
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={e => { setQuery(e.target.value); setError("") }}
              placeholder="Buscar Invocador... Nick#TAG"
              className="flex-1 bg-transparent py-3 pl-11 pr-4 text-bs text-black-100 placeholder-black-400 focus:outline-none"
              autoFocus
            />
            <button
              type="submit"
              className="mr-1.5 flex-shrink-0 px-5 py-2 rounded-full font-bold text-bs uppercase tracking-wider transition-all duration-200 active:scale-95 bg-purple-300 hover:bg-purple-500 text-white"
            >
              Buscar
            </button>
          </div>
        </form>

        {error
          ? <p className="text-bxs text-accent-red mb-1 animate-fade-in">! {error}</p>
          : <p className="text-bxs text-black-400 mb-1">Ex: natus vincere#navi1</p>
        }

        {/* Champion cards */}
        <div
          className="w-full max-w-xl mt-16 animate-fade-up"
          style={{ animationDelay: "160ms", animationFillMode: "both" }}
        >
          <p className="text-bxs font-bold uppercase tracking-widest text-black-400 mb-4 text-center">
            Campeoes populares
          </p>
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
            {CHAMPIONS.map(champ => (
              <div
                key={champ.name}
                className="relative rounded-lg overflow-hidden aspect-[2/3] border border-white/5 hover:border-purple-300/40 transition-all duration-200 hover:scale-[1.03] cursor-default"
              >
                <img
                  src={`https://ddragon.leagueoflegends.com/cdn/img/champion/loading/${champ.name}_0.jpg`}
                  alt={champ.name}
                  className="w-full h-full object-cover object-top"
                  onError={e => { e.target.style.display = "none" }}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black-900/95 via-black-900/20 to-transparent" />
                <div className="absolute bottom-2 left-0 right-0 text-center">
                  <span className="text-bxs font-bold text-black-100">{champ.name}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verify search screen renders**

Run: `npm run dev`, navigate to `/`
Expected: Dark page with purple gradient blob, centered search with pill shape, champion cards at bottom

- [ ] **Step 3: Test search flow**

Enter "natus vincere#navi1" and submit.
Expected: Navigates to `/summoner/natus%20vincere/navi1`

- [ ] **Step 4: Commit**

```bash
git add src/screens/SearchScreen.jsx
git commit -m "feat: SearchScreen redesign — dpm.lol style with purple gradient"
```

---

### Task 4: SummonerProfileScreen Redesign (Profile Banner + Sidebar + Match Rows)

**Files:**
- Rewrite: `src/screens/SummonerProfileScreen.jsx`

This is the largest task. The new layout has:
1. Profile banner (dark bg, rounded-b-32, summoner icon + name + rank + tabs)
2. 4-column grid: sidebar (ranked card) + main (match history)
3. Match rows are horizontal compact rows (not cards)

- [ ] **Step 1: Rewrite SummonerProfileScreen.jsx**

```jsx
import { useState, useEffect } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { fetchMatches, fetchCoachingStatus } from "../services/api"
import { DDV } from "../services/constants"

// ── constants ─────────────────────────────────────────────
const POS_LABEL = { TOP: "TOP", JUNGLE: "JG", MIDDLE: "MID", BOTTOM: "BOT", UTILITY: "SUP" }
const posLabel  = pos => POS_LABEL[pos?.toUpperCase()] ?? ""

const TIER_COLORS = {
  CHALLENGER:  "#F4C874", GRANDMASTER: "#CD4535", MASTER: "#9D48E0",
  DIAMOND:     "#57A0D2", EMERALD:     "#56B675", PLATINUM: "#5BBFB5",
  GOLD:        "#C89B3C", SILVER:      "#8A9BB4", BRONZE:   "#AE704B",
  IRON:        "#7C7F84", UNRANKED:    "#555",
}

// ── helpers ───────────────────────────────────────────────
function parseTier(rankStr) {
  if (!rankStr || rankStr === "Unranked") return "UNRANKED"
  return rankStr.split(" ")[0].toUpperCase()
}

function calcScore(match) {
  const { kills = 0, deaths = 0, assists = 0, win, cs_per_min = 0, vision_score = 0, kill_participation_pct = 0, damage_share_pct = 0 } = match
  const kda = (kills + assists) / Math.max(deaths, 1)
  const s = Math.min(kda / 8 * 30, 30) + (win ? 20 : 0) + Math.min(cs_per_min / 8 * 15, 15) + Math.min(vision_score / 60 * 10, 10) + Math.min(kill_participation_pct / 100 * 15, 15) + Math.min(damage_share_pct / 35 * 10, 10)
  return Math.round(Math.min(s, 100))
}

function buildChampionPool(matches) {
  const pool = {}
  for (const m of matches) {
    const c = m.champion
    if (!pool[c]) pool[c] = { champion: c, wins: 0, games: 0, kills: 0, deaths: 0, assists: 0 }
    pool[c].games++
    if (m.win) pool[c].wins++
    pool[c].kills += m.kills; pool[c].deaths += m.deaths; pool[c].assists += m.assists
  }
  return Object.values(pool).sort((a, b) => b.games - a.games).slice(0, 5).map(c => ({
    ...c,
    wr: Math.round(c.wins / c.games * 100),
    kda: c.deaths === 0 ? "Perfect" : ((c.kills + c.assists) / c.deaths).toFixed(1),
  }))
}

// ── ScoreBadge ────────────────────────────────────────────
function ScoreBadge({ score }) {
  const isElite = score >= 90
  const isGood  = score >= 75
  const isFair  = score >= 60
  const color = isElite ? "#f0d080" : isGood ? "#c89b3c" : isFair ? "#94A3B8" : "#475569"
  const bg    = isElite ? "#c89b3c20" : isGood ? "#c89b3c12" : isFair ? "#94A3B810" : "#47556908"
  const border = isElite ? "#c89b3c55" : isGood ? "#c89b3c33" : "transparent"

  return (
    <div
      className={`min-w-[40px] h-[40px] rounded-lg flex flex-col items-center justify-center flex-shrink-0 ${isElite ? "scoreGlow" : ""}`}
      style={{ color, background: bg, border: `1px solid ${border}` }}
    >
      <span className="text-[15px] font-extrabold leading-none">{score}</span>
      <span className="text-[7px] tracking-wider opacity-50 uppercase">score</span>
    </div>
  )
}

// ── MatchRow ──────────────────────────────────────────────
function MatchRow({ match, index, onSelect, hasCoaching }) {
  const win   = match.win === true || match.win === 1
  const score = calcScore(match)
  const [imgFailed, setImgFailed] = useState(false)

  return (
    <button
      onClick={onSelect}
      style={{ animationDelay: `${index * 40}ms`, animationFillMode: "both" }}
      className={`w-full text-left rounded-md border-l-[3px] transition-all duration-200 hover:brightness-110 active:scale-[0.995] animate-fade-up group ${
        win ? "bg-accent-green/[0.06] border-accent-green/50" : "bg-accent-red/[0.06] border-accent-red/50"
      }`}
    >
      <div className="flex items-center gap-3 px-3 py-2.5">
        {/* Champion icon */}
        <div className="w-10 h-10 rounded-lg overflow-hidden border border-white/10 flex-shrink-0 bg-black-600">
          {!imgFailed ? (
            <img
              src={`https://ddragon.leagueoflegends.com/cdn/${DDV}/img/champion/${match.champion}.png`}
              alt={match.champion}
              onError={() => setImgFailed(true)}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-black-400 text-xs">?</div>
          )}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-0.5">
            <span className={`text-bxs font-bold uppercase ${win ? "text-accent-green" : "text-accent-red"}`}>
              {win ? "Vitoria" : "Derrota"}
            </span>
            <span className="text-bs font-semibold text-black-0 truncate">{match.champion}</span>
            {match.position && (
              <span className="text-[9px] text-black-300 border border-black-500 rounded px-1 py-0.5 bg-black-600">
                {posLabel(match.position)}
              </span>
            )}
            {hasCoaching && (
              <span className="text-[9px] font-bold text-gold-400 bg-gold-400/15 px-1.5 py-0.5 rounded">
                IA
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-bs">
              <span className="text-black-100">{match.kills}</span>
              <span className="text-black-400"> / </span>
              <span className="text-accent-red">{match.deaths}</span>
              <span className="text-black-400"> / </span>
              <span className="text-black-100">{match.assists}</span>
            </span>
            <span className="text-bxs text-black-400">{match.duration_min}min</span>
          </div>
        </div>

        {/* Items */}
        <div className="hidden sm:flex gap-0.5 flex-shrink-0">
          {(match.items?.length ? match.items : Array(7).fill(0)).map((itemId, i) => (
            <div key={i} className="w-[20px] h-[20px] rounded bg-black-600 border border-white/5 overflow-hidden flex-shrink-0">
              {itemId > 0 && (
                <img
                  src={`https://ddragon.leagueoflegends.com/cdn/${DDV}/img/item/${itemId}.png`}
                  alt="" className="w-full h-full object-cover"
                  onError={e => { e.target.style.display = "none" }}
                />
              )}
            </div>
          ))}
        </div>

        {/* CS + Vision */}
        <div className="hidden md:flex flex-col items-end gap-0.5 flex-shrink-0 w-16">
          {match.cs_per_min > 0 && <span className="text-bxs text-black-300">{match.cs_per_min} cs/m</span>}
          {match.vision_score > 0 && <span className="text-bxs text-black-400">{match.vision_score} vis</span>}
        </div>

        {/* Score */}
        <ScoreBadge score={score} />
      </div>
    </button>
  )
}

// ── RankedCard (sidebar) ──────────────────────────────────
function RankedCard({ rankStr, wins, losses, tier, tierColor }) {
  const total = wins + losses
  const wr    = total > 0 ? Math.round(wins / total * 100) : 0

  return (
    <div className="bg-purple-200/5 border-t border-white/5 rounded-md overflow-hidden relative">
      {/* Glow effects */}
      <div className="absolute -top-0 -right-3 w-[120px] h-[120px] rounded-full blur-xl opacity-20" style={{ background: tierColor }} />
      <div className="absolute -top-0 -left-3 w-[100px] h-[100px] rounded-full blur-xl opacity-10" style={{ background: tierColor }} />

      <div className="relative p-4">
        <div className="flex items-center gap-2 mb-3">
          <svg className="w-[18px] h-[18px] text-black-200" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="8" r="6" /><path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11" />
          </svg>
          <span className="text-bs font-semibold text-black-200">Ranked Solo</span>
        </div>

        <div className="flex items-center justify-between mb-2">
          <img
            src={`https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-shared-components/global/default/images/${tier.toLowerCase()}.png`}
            alt={tier}
            className="w-10 object-cover"
            style={{ filter: "brightness(0.9) contrast(1.15)" }}
            onError={e => { e.target.style.display = "none" }}
          />
          <div className="text-right">
            <p className="text-bm font-bold uppercase" style={{ color: tierColor }}>
              {rankStr === "Unranked" ? "Sem Ranking" : rankStr}
            </p>
            <p className="text-bs font-semibold" style={{ color: `${tierColor}CC` }}>
              {wins}W - {losses}L ({wr}%)
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── ChampionPoolCard (sidebar) ────────────────────────────
function ChampionPoolCard({ champPool }) {
  if (!champPool.length) return null
  return (
    <div className="bg-purple-200/5 border-t border-white/5 rounded-md p-4">
      <p className="text-bs font-semibold text-black-200 mb-3">Campeoes mais jogados</p>
      <div className="space-y-2">
        {champPool.map(champ => {
          const wrColor = champ.wr >= 60 ? "#22C55E" : champ.wr >= 50 ? "#c89b3c" : "#EF4444"
          return (
            <div key={champ.champion} className="flex items-center gap-2">
              <div className="w-7 h-7 rounded overflow-hidden border border-white/10 flex-shrink-0 bg-black-600">
                <img
                  src={`https://ddragon.leagueoflegends.com/cdn/${DDV}/img/champion/${champ.champion}.png`}
                  alt={champ.champion} className="w-full h-full object-cover"
                  onError={e => { e.target.style.display = "none" }}
                />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-bs font-semibold text-black-100 truncate">{champ.champion}</p>
                <p className="text-bxs text-black-400">{champ.games}j · KDA {champ.kda}</p>
              </div>
              <span className="text-bs font-bold" style={{ color: wrColor }}>{champ.wr}%</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── SummonerProfileScreen ─────────────────────────────────
export default function SummonerProfileScreen() {
  const { name, tag } = useParams()
  const navigate      = useNavigate()
  const [data, setData]               = useState(null)
  const [loading, setLoading]         = useState(true)
  const [coachingStatus, setCoachingStatus] = useState({})

  const nick = `${decodeURIComponent(name)}#${decodeURIComponent(tag)}`

  useEffect(() => {
    setLoading(true)
    fetchMatches(nick)
      .then(d => {
        setData(d)
        setLoading(false)
        const matchIds = (d.matches ?? []).map(m => m.match_id)
        fetchCoachingStatus(matchIds).then(setCoachingStatus).catch(() => {})
      })
      .catch(e => {
        navigate("/", { replace: true, state: { error: e.message || "Invocador nao encontrado." } })
      })
  }, [nick])

  if (loading) return <ProfileSkeleton />

  const matches   = Array.isArray(data) ? data : (data?.matches ?? [])
  const summoner  = data?.summoner ?? nick
  const rankStr   = data?.rank ?? "Unranked"
  const wins      = data?.wins   ?? matches.filter(m => m.win).length
  const losses    = data?.losses ?? matches.filter(m => !m.win).length
  const tier      = parseTier(rankStr)
  const tierColor = TIER_COLORS[tier] ?? TIER_COLORS.UNRANKED
  const champPool = buildChampionPool(matches)

  function handleSelect(match, index) {
    navigate(`/match/${encodeURIComponent(match.match_id)}`, {
      state: { player: { nick }, rank: rankStr, matchStats: match, matchIndex: index, puuid: data?.puuid ?? "" },
    })
  }

  return (
    <div>
      {/* ── Profile Banner ───────────────── */}
      <div className="bg-black-800 rounded-b-[32px] border-b border-white/5 overflow-hidden glow-purple relative mb-4 md:pt-2">
        <div className="max-w-5xl mx-auto px-4 py-4">
          <div className="flex items-center gap-5">
            {/* Summoner icon */}
            <div className="flex flex-col items-center gap-1 flex-shrink-0">
              <div className="w-[70px] h-[70px] rounded-lg border-2 border-black-500 overflow-hidden">
                <img
                  src={`https://ddragon.leagueoflegends.com/cdn/${DDV}/img/profileicon/${data?.profile_icon ?? 29}.png`}
                  alt="Profile Icon"
                  className="w-full h-full object-cover"
                />
              </div>
              {data?.level && (
                <div className="text-[9px] font-extrabold bg-black-700 border border-white/10 rounded px-1.5 py-0.5 -mt-3 relative z-10">
                  {data.level}
                </div>
              )}
            </div>

            {/* Name + rank */}
            <div className="flex-1 min-w-0">
              <div className="flex items-end gap-2 mb-1">
                <span className="text-bxl lg:text-hxs text-black-0 font-semibold truncate max-w-[280px]">
                  {summoner}
                </span>
                <span className="text-bm text-black-200 font-medium">#{tag}</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="text-bxs font-extrabold rounded-md px-1.5 py-0.5 bg-lime-800 text-black-100">BR</div>
              </div>
            </div>

            {/* Update button */}
            <button className="hidden sm:flex items-center gap-2 rounded-md px-3 py-2 text-bs font-semibold text-blue-100/90 border-t border-white/5 bg-purple-200/10 hover:bg-purple-200/[0.15] transition-all duration-200 shadow-[0_0px_5px_0px_rgba(255,235,173,0.1)]">
              <div className="h-2 w-2 bg-yellow-400 rounded-full animate-pulse-dot" />
              Atualizar
            </button>
          </div>

          {/* Tabs */}
          <div className="flex items-center gap-1 mt-4 border-t border-white/5 pt-2">
            <TabItem active label="Partidas" />
            <TabItem label="Campeoes" />
            <TabItem label="Live" dot />
          </div>
        </div>
      </div>

      {/* ── Main Content (Grid) ─────────── */}
      <div className="max-w-5xl mx-auto px-4 pb-12">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          {/* Sidebar */}
          <div className="flex flex-col gap-3">
            <RankedCard rankStr={rankStr} wins={wins} losses={losses} tier={tier} tierColor={tierColor} />
            <ChampionPoolCard champPool={champPool} />
          </div>

          {/* Match history */}
          <div className="lg:col-span-3 flex flex-col gap-1.5">
            {matches.map((match, i) => (
              <MatchRow
                key={match.match_id}
                match={match}
                index={i}
                onSelect={() => handleSelect(match, i)}
                hasCoaching={!!coachingStatus[match.match_id]}
              />
            ))}
            {matches.length === 0 && (
              <div className="text-center py-12 text-black-400 text-bs">
                Nenhuma partida encontrada.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Sub-components ────────────────────────────────────────

function TabItem({ active, label, dot }) {
  return (
    <button className={`px-4 py-2 text-bs font-semibold transition-all ${
      active ? "text-black-0" : "text-black-300 hover:text-black-200"
    } flex items-center gap-2`}>
      {dot && <div className="w-2 h-2 rounded-full bg-black-300" />}
      {label}
      {active && (
        <div className="absolute -bottom-0.5 left-1/4 right-1/4 h-0.5 rounded-full bg-blue-300 shadow-[0_0px_12px_0px_rgba(222,204,251,0.32)]" />
      )}
    </button>
  )
}

function ProfileSkeleton() {
  return (
    <div>
      <div className="bg-black-800 rounded-b-[32px] border-b border-white/5 glow-purple mb-4">
        <div className="max-w-5xl mx-auto px-4 py-6">
          <div className="flex items-center gap-5">
            <div className="w-[70px] h-[70px] rounded-lg shimmer-bg" />
            <div className="flex-1 space-y-2">
              <div className="h-5 w-48 shimmer-bg rounded" />
              <div className="h-3 w-24 shimmer-bg rounded" />
            </div>
          </div>
        </div>
      </div>
      <div className="max-w-5xl mx-auto px-4">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          <div className="space-y-3">
            <div className="h-32 shimmer-bg rounded-md" />
            <div className="h-48 shimmer-bg rounded-md" />
          </div>
          <div className="lg:col-span-3 space-y-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-16 shimmer-bg rounded-md" />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verify profile page renders**

Run: `npm run dev`, search for "natus vincere#navi1"
Expected: Profile banner with icon + name + rank, grid layout with sidebar ranked card + match rows

- [ ] **Step 3: Test match navigation**

Click any match row.
Expected: Navigates to `/match/{matchId}` with state

- [ ] **Step 4: Commit**

```bash
git add src/screens/SummonerProfileScreen.jsx
git commit -m "feat: SummonerProfile redesign — dpm.lol layout with sidebar + match rows"
```

---

### Task 5: ResultsScreen + CoachingSection Restyle

**Files:**
- Modify: `src/screens/ResultsScreen.jsx`
- Modify: `src/components/CoachingSection.jsx`

- [ ] **Step 1: Update ResultsScreen header and styling**

In `src/screens/ResultsScreen.jsx`, replace the `<header>` section (lines 242-257) with:

```jsx
{/* Top bar removed — Layout provides Navbar */}
```

Replace `bg-surface-900/80` with `bg-black-800/80`, `text-gold-gradient` with `text-black-0`, `border-gold-400/10` with `border-white/5`, and `max-w-3xl` with `max-w-5xl` across the file.

Specifically update the header and main:

```jsx
<div className="min-h-screen">
  <main className="max-w-5xl mx-auto px-4 py-8 space-y-6">
```

Remove the entire `<header>` block since Layout now provides navigation.

Update `SectionLabel` to use purple instead of gold:

```jsx
function SectionLabel({ children, noBorder }) {
  return (
    <div className="flex items-center gap-3 mb-3">
      <span className="text-bs font-bold uppercase tracking-widest text-black-300">{children}</span>
      {!noBorder && <div className="flex-1 h-px bg-gradient-to-r from-purple-300/20 to-transparent" />}
    </div>
  )
}
```

Update `StatPill`:

```jsx
function StatPill({ label, value, sub }) {
  return (
    <div className="bg-purple-200/5 border border-white/5 rounded-lg p-4 flex flex-col gap-1">
      <p className="text-bxs font-bold uppercase tracking-widest text-black-400">{label}</p>
      <p className="text-hxs font-extrabold text-black-0 leading-none">{value}</p>
      {sub && <p className="text-bxs text-black-300">{sub}</p>}
    </div>
  )
}
```

- [ ] **Step 2: Update CoachingSection.jsx to new theme**

Replace emoji icons with SVG, update colors from gold to purple accent:

In the `UnlockedCoaching` component, change:
- Header background: `"linear-gradient(90deg, rgba(26,20,0,0.8), rgba(13,13,32,0.8))"` → `"rgba(124,58,237,0.08)"`
- Header border: `"rgba(200,155,60,0.15)"` → `"rgba(255,255,255,0.06)"`
- Label color: `"#c89b3c"` → `"#A78BFA"` (purple-200)
- Badge background: `"rgba(200,155,60,0.15)"` → `"rgba(124,58,237,0.15)"`
- Badge color: `"#c89b3c"` → `"#A78BFA"`
- Active tab color: `"#c89b3c"` → `"#7989EC"` (blue-300)
- Active tab border: `"2px solid #c89b3c"` → `"2px solid #7989EC"`

In `LockedCoaching`, update the CTA button:
- background: `"linear-gradient(135deg, #c89b3c, #f0d080)"` → `"linear-gradient(135deg, #7C3AED, #A78BFA)"`
- color: `"#080a14"` → `"#FFFFFF"`
- Lock text color: `"#c89b3c"` → `"#A78BFA"`

Replace `<span style={{ fontSize: "16px" }}>🤖</span>` with:
```jsx
<svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
  <path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="m2 14 2-2-2-2"/><path d="m22 14-2-2 2-2"/>
</svg>
```

Replace `<span style={{ fontSize: "22px" }}>🔒</span>` with:
```jsx
<svg className="w-6 h-6 text-purple-200" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
  <rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
</svg>
```

- [ ] **Step 3: Verify results page and coaching section**

Navigate to a match. Expected: Purple-themed stats, coaching section with purple accents, no emoji icons.

- [ ] **Step 4: Commit**

```bash
git add src/screens/ResultsScreen.jsx src/components/CoachingSection.jsx
git commit -m "feat: ResultsScreen + CoachingSection restyle — purple theme, SVG icons"
```

---

### Task 6: LoadingScreen Restyle + Final Polish

**Files:**
- Modify: `src/screens/LoadingScreen.jsx`

- [ ] **Step 1: Update LoadingScreen**

Read current LoadingScreen.jsx and replace gold references with purple:
- Replace any `gold-400` with `purple-300`
- Replace any `#c89b3c` with `#7C3AED`
- Replace any `text-gold-gradient` with `text-black-0`
- Update background to `bg-black-700`

- [ ] **Step 2: Full visual regression check**

Navigate through all flows:
1. `/` — Search page with purple gradient
2. Search "natus vincere#navi1" — Profile with sidebar
3. Click a match — Results page with purple stats
4. Check coaching section locked/unlocked states

Expected: Consistent dark purple theme throughout, no gold remnants except in ScoreBadge (intentional)

- [ ] **Step 3: Run build**

Run: `npm run build`
Expected: Builds successfully with no errors

- [ ] **Step 4: Commit**

```bash
git add src/screens/LoadingScreen.jsx
git commit -m "feat: LoadingScreen restyle + final polish — dpm.lol redesign complete"
```

---

## Summary

| Task | What | Files |
|------|------|-------|
| 1 | Design tokens (Tailwind + CSS + fonts) | tailwind.config.js, index.css, index.html |
| 2 | Shared Layout (Navbar + Footer) | Layout.jsx, Navbar.jsx, App.jsx |
| 3 | SearchScreen redesign | SearchScreen.jsx |
| 4 | SummonerProfile (banner + sidebar + match rows) | SummonerProfileScreen.jsx |
| 5 | ResultsScreen + CoachingSection restyle | ResultsScreen.jsx, CoachingSection.jsx |
| 6 | LoadingScreen + final polish | LoadingScreen.jsx |
