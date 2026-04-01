import { useState } from "react"
import { useNavigate, useLocation } from "react-router-dom"

const NAV_LINKS = [
  { label: "Tierlist & Builds", path: "/tierlist" },
  { label: "Classificacoes", path: "/leaderboard" },
  { label: "Download", path: "/download" },
]

export default function Navbar() {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const [query, setQuery] = useState("")

  function handleSearch(e) {
    e.preventDefault()
    const raw = query.trim()
    if (!raw) return
    const hashIdx = raw.lastIndexOf("#")
    if (hashIdx < 1) return
    const nick = raw.slice(0, hashIdx).trim()
    const tag = raw.slice(hashIdx + 1).trim()
    if (!nick || !tag) return
    setQuery("")
    navigate(`/summoner/${encodeURIComponent(nick)}/${encodeURIComponent(tag)}`)
  }

  return (
    <header className="bg-black-800 grid grid-cols-[1fr_auto_1fr] sticky top-0 z-30 h-[50px] items-center px-5 lg:px-6 gap-4 shadow-[0_8px_9px_0px_rgba(121,137,236,0.10)]">
      <div className="flex items-center gap-6">
        <a
          href="/"
          onClick={(e) => {
            e.preventDefault()
            navigate("/")
          }}
          className="flex-shrink-0 text-bxl font-extrabold tracking-tight text-black-0 hover:text-purple-200 transition-colors cursor-pointer"
        >
          MVP.GG
        </a>

        <nav className="hidden lg:flex items-center gap-5">
          {NAV_LINKS.map(({ label, path }) => (
            <button
              key={path}
              onClick={() => navigate(path)}
              className={`text-bs font-medium transition-colors ${
                pathname.startsWith(path) ? "text-blue-400" : "text-black-300 hover:text-black-100"
              }`}
            >
              {label}
            </button>
          ))}
        </nav>
      </div>

      <form
        onSubmit={handleSearch}
        className="bg-black-600 hover:bg-black-500/40 duration-200 border border-black-500 text-bs gap-2 font-medium flex items-center rounded-full px-3 py-1.5 shadow-[0_0px_10px_0px_rgba(121,137,236,0.10)] w-[280px] lg:w-[320px]"
      >
        <svg className="w-4 h-4 text-black-300 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.3-4.3" />
        </svg>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Buscar Invocador..."
          className="bg-transparent outline-none text-black-100 placeholder-black-300 w-full text-bs"
        />
      </form>

      <div />
    </header>
  )
}
