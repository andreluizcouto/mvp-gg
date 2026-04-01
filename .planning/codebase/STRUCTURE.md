# Codebase Structure

**Analysis Date:** 2026-03-30

## Directory Layout

```
Coach-AI-Project/
├── ProjectB-frontend/    # React frontend
│   ├── src/             # Source code
│   │   ├── components/  # Shared UI components
│   │   ├── screens/     # Route-based screens
│   │   ├── services/    # API/data helpers
│   │   └── App.jsx      # Main app component
│   ├── package.json     # Frontend deps/scripts
│   └── ...
├── ProjectB/            # Python backend
│   ├── main.py          # FastAPI entry point
│   ├── requirements.txt # Backend deps
│   ├── coach_ai.py      # AI logic
│   ├── db.py            # DB logic
│   ├── riot_client.py   # Riot API
│   └── ...
└── .planning/codebase/  # Codebase analysis docs
```

## Directory Purposes

**ProjectB-frontend/src/components:**
- Purpose: Shared React UI components
- Contains: Navbar, Layout, Footer, etc.
- Key files: `Navbar.jsx`, `Layout.jsx`, `Footer.jsx`

**ProjectB-frontend/src/screens:**
- Purpose: Route-based UI screens
- Contains: Search, Profile, Results, etc.
- Key files: `SearchScreen.jsx`, `SummonerProfileScreen.jsx`, etc.

**ProjectB-frontend/src/services:**
- Purpose: API/data helpers
- Contains: API, constants, utils
- Key files: `api.js`, `constants.js`, `utils.js`

**ProjectB:**
- Purpose: Backend logic
- Contains: FastAPI app, domain modules
- Key files: `main.py`, `coach_ai.py`, `db.py`, `riot_client.py`

## Key File Locations

**Entry Points:**
- `ProjectB-frontend/src/main.jsx`: React app mount
- `ProjectB/main.py`: FastAPI app

**Configuration:**
- `ProjectB-frontend/package.json`: Frontend deps/scripts
- `ProjectB/requirements.txt`: Backend deps

**Core Logic:**
- `ProjectB-frontend/src/services/api.js`: API calls
- `ProjectB/coach_ai.py`: AI logic

**Testing:**
- `ProjectB/tests/`: Backend tests (pytest)

## Naming Conventions

**Files:**
- PascalCase for React components (e.g., `Navbar.jsx`)
- camelCase for JS helpers (e.g., `api.js`)
- snake_case for Python modules (e.g., `coach_ai.py`)

**Directories:**
- Lowercase, descriptive (e.g., `services`, `screens`)

## Where to Add New Code

**New Feature:**
- Primary code: `ProjectB-frontend/src/screens/` (UI), `ProjectB/` (backend)
- Tests: `ProjectB/tests/`

**New Component/Module:**
- Implementation: `ProjectB-frontend/src/components/` (UI), `ProjectB/` (backend)

**Utilities:**
- Shared helpers: `ProjectB-frontend/src/services/`

## Special Directories

**.planning/codebase:**
- Purpose: Codebase analysis docs
- Generated: Yes
- Committed: Yes

---

*Structure analysis: 2026-03-30*