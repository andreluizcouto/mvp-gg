import { useEffect, useState } from "react"
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom"
import Logo from "./Logo"

const NAV_LINKS = [
  { label: "Tier list", path: "/tierlist" },
  { label: "Ranking", path: "/leaderboard" },
  { label: "Como funciona", path: "/how-it-works" },
  { label: "App", path: "/download" },
]

function parseRiotId(raw) {
  const value = raw.trim()
  const hashIdx = value.lastIndexOf("#")
  if (hashIdx < 1) return null
  const nick = value.slice(0, hashIdx).trim()
  const tag = value.slice(hashIdx + 1).trim()
  return nick && tag ? { nick, tag } : null
}

function SearchIcon({ className = "h-4 w-4" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <circle cx="11" cy="11" r="7.5" />
      <path d="m20.5 20.5-4.2-4.2" strokeLinecap="round" />
    </svg>
  )
}

function NavSearch({ onDone, autoFocus = false, className = "" }) {
  const navigate = useNavigate()
  const [query, setQuery] = useState("")
  const [invalid, setInvalid] = useState(false)

  function handleSubmit(e) {
    e.preventDefault()
    const parsed = parseRiotId(query)
    if (!parsed) { setInvalid(true); return }
    setQuery("")
    setInvalid(false)
    onDone?.()
    navigate(`/summoner/${encodeURIComponent(parsed.nick)}/${encodeURIComponent(parsed.tag)}`)
  }

  return (
    <form onSubmit={handleSubmit} role="search" className={className}>
      <label className={`flex h-10 items-center gap-2 rounded-full border bg-black-600/80 px-4 transition focus-within:border-purple-400/60 ${invalid ? "border-red-500/60" : "border-white/[0.08] hover:border-white/20"}`}>
        <SearchIcon className="h-4 w-4 flex-shrink-0 text-black-300" />
        <span className="sr-only">Buscar invocador</span>
        <input
          type="text"
          value={query}
          autoFocus={autoFocus}
          onChange={(e) => { setQuery(e.target.value); setInvalid(false) }}
          placeholder={invalid ? "Use Nick#TAG" : "Buscar Nick#TAG"}
          className="w-full bg-transparent text-bs text-black-100 placeholder-black-400 outline-none"
        />
      </label>
    </form>
  )
}

export default function Navbar() {
  const { pathname } = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)
  const isHome = pathname === "/"

  useEffect(() => { setMenuOpen(false) }, [pathname])

  return (
    <header className="sticky top-0 z-40 border-b border-white/[0.06] bg-black-800/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-[1200px] items-center gap-6 px-4">
        <Link to="/" aria-label="mvp.gg, página inicial" className="flex-shrink-0">
          <Logo />
        </Link>

        <nav className="hidden items-center gap-1 md:flex" aria-label="Principal">
          {NAV_LINKS.map(({ label, path }) => (
            <NavLink
              key={path}
              to={path}
              className={({ isActive }) =>
                `rounded-full px-3.5 py-2 text-bs font-semibold transition ${isActive ? "bg-white/[0.06] text-black-0" : "text-black-300 hover:text-black-0"}`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-2">
          {!isHome && <NavSearch className="hidden w-[260px] md:block lg:w-[300px]" />}
          <button
            type="button"
            onClick={() => setMenuOpen((open) => !open)}
            className="flex h-10 w-10 items-center justify-center rounded-full border border-white/[0.08] text-black-100 md:hidden"
            aria-expanded={menuOpen}
            aria-controls="menu-mobile"
            aria-label={menuOpen ? "Fechar menu" : "Abrir menu"}
          >
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
              {menuOpen ? <path d="M6 6l12 12M18 6 6 18" /> : <path d="M4 7h16M4 12h16M4 17h10" />}
            </svg>
          </button>
        </div>
      </div>

      {menuOpen && (
        <div id="menu-mobile" className="border-t border-white/[0.06] bg-black-800 px-4 pb-5 pt-4 md:hidden">
          <NavSearch autoFocus onDone={() => setMenuOpen(false)} />
          <nav className="mt-3 grid gap-1" aria-label="Principal">
            {NAV_LINKS.map(({ label, path }) => (
              <NavLink
                key={path}
                to={path}
                className={({ isActive }) =>
                  `flex min-h-[44px] items-center rounded-xl px-3 text-bm font-semibold ${isActive ? "bg-white/[0.06] text-black-0" : "text-black-200"}`
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
      )}
    </header>
  )
}
