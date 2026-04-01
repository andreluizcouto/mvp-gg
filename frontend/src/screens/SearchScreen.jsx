import { useState, useRef, useEffect } from "react"
import { useNavigate, useLocation } from "react-router-dom"
import { DDV } from "../services/constants"

const TIERLIST_PREVIEW = [
  { name: "Nami",  tier: "S+", winRate: "51.8%", pickRate: "17.0%" },
  { name: "Jinx",  tier: "S+", winRate: "51.6%", pickRate: "15.1%" },
  { name: "Graves", tier: "S+", winRate: "50.6%", pickRate: "13.1%" },
  { name: "Ahri",  tier: "S+", winRate: "51.0%", pickRate: "12.6%" },
  { name: "Garen", tier: "S+", winRate: "51.6%", pickRate: "9.3%" },
]

const LEADERBOARD_PREVIEW = [
  { rank: 1, name: "Odysseus", tier: "CHALLENGER", lp: 2993, winRate: "56%", profileIcon: 29 },
  { rank: 2, name: "Caliste",  tier: "CHALLENGER", lp: 2982, winRate: "67%", profileIcon: 588 },
  { rank: 3, name: "RaiderGO", tier: "CHALLENGER", lp: 2964, winRate: "65%", profileIcon: 4833 },
  { rank: 4, name: "Parus",    tier: "CHALLENGER", lp: 2856, winRate: "62%", profileIcon: 5367 },
  { rank: 5, name: "Mercy9",   tier: "CHALLENGER", lp: 2810, winRate: "56%", profileIcon: 7 },
]

const POPULAR_CHAMPIONS = [
  { name: "Nami",    displayName: "Nami",    desc: "Descubra as melhores builds para Nami..." },
  { name: "Ezreal",  displayName: "Ezreal",  desc: "Descubra as melhores builds para Ezreal..." },
  { name: "Caitlyn", displayName: "Caitlyn", desc: "Descubra as melhores builds para Caitlyn..." },
]

export default function SearchScreen() {
  const navigate        = useNavigate()
  const { state }       = useLocation()
  const [query, setQuery] = useState("")
  const [error, setError] = useState(state?.error ?? "")
  const inputRef          = useRef(null)

  const [fading, setFading] = useState(false)

  useEffect(() => {
    if (error) {
      setFading(false)
      const fadeTimer = setTimeout(() => setFading(true), 2000)
      const clearTimer = setTimeout(() => setError(""), 3000)
      return () => { clearTimeout(fadeTimer); clearTimeout(clearTimer) }
    }
  }, [error])

  function handleSubmit(e) {
    e.preventDefault()
    const raw = query.trim()
    if (!raw) { setError("Digite Nick#TAG para buscar."); return }
    const hashIdx = raw.lastIndexOf("#")
    if (hashIdx < 1) { setError("Use o formato Nick#TAG — ex: Faker#BR1"); return }
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
              <stop offset="0%" stopColor="#4D62E5" stopOpacity="0.35" />
              <stop offset="40%" stopColor="#7C35F1" stopOpacity="0.15" />
              <stop offset="70%" stopColor="#7989EC" stopOpacity="0.20" />
              <stop offset="93%" stopColor="#4D62E5" stopOpacity="0.08" />
            </radialGradient>
          </defs>
          <ellipse cx="450" cy="300" rx="450" ry="300" fill="url(#bg-grad)" />
        </svg>
      </div>

      <div className="relative z-10">
        {/* ───── Hero Section ───── */}
        <section className="max-w-[1200px] mx-auto px-4 pt-16 lg:pt-24 pb-16">
          <div className="flex flex-col lg:flex-row items-center lg:items-start gap-8 lg:gap-12">
            {/* Left: title + search */}
            <div className="flex-1 text-center lg:text-left">
              <h1
                className="text-[28px] lg:text-[42px] font-extrabold text-black-0 leading-tight tracking-tight mb-4 animate-fade-up"
              >
                DESCUBRA O QUE SEPARA<br />
                VOCÊ DO{" "}
                <span className="text-blue-400">MVP</span>
              </h1>
              <p
                className="text-bs lg:text-bm text-black-300 mb-8 animate-fade-up"
                style={{ animationDelay: "60ms", animationFillMode: "both" }}
              >
                Estatísticas, coaching com IA e análise personalizada para cada partida
              </p>

              {/* Search */}
              <form
                onSubmit={handleSubmit}
                className="w-full max-w-[500px] mx-auto lg:mx-0 mb-3 animate-fade-up"
                style={{ animationDelay: "120ms", animationFillMode: "both" }}
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
                    className="mr-1.5 flex-shrink-0 px-5 py-2 rounded-full font-bold text-bs uppercase tracking-wider transition-all duration-200 active:scale-95 bg-blue-500 hover:bg-blue-600 text-white"
                  >
                    Buscar
                  </button>
                </div>
              </form>

              <div className="max-w-[500px] mx-auto lg:mx-0">
                {error
                  ? <p className={`text-bxs text-accent-red mb-1 transition-opacity duration-1000 ${fading ? "opacity-0" : "opacity-100"}`}>{error}</p>
                  : <p className="text-bxs text-black-400 mb-1 animate-fade-in">Ex: Faker#BR1</p>
                }
              </div>
            </div>

            {/* Right: decorative champion splash */}
            <div
              className="hidden lg:block w-[260px] flex-shrink-0 animate-fade-up"
              style={{ animationDelay: "180ms", animationFillMode: "both" }}
            >
              <div className="relative rounded-xl overflow-hidden aspect-[3/4] border border-white/5 shadow-[0_2px_8px_rgba(121,137,236,0.10)]">
                <img
                  src="https://ddragon.leagueoflegends.com/cdn/img/champion/loading/Zaahen_0.jpg"
                  alt="Zaahen"
                  className="w-full h-full object-cover object-top"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black-900/80 via-transparent to-transparent" />
              </div>
            </div>
          </div>
        </section>

        {/* ───── Tierlist + Leaderboard (2 cols) ───── */}
        <section
          className="max-w-[1200px] mx-auto px-4 pb-16 animate-fade-up"
          style={{ animationDelay: "240ms", animationFillMode: "both" }}
        >
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Tierlist Preview */}
            <div className="bg-black-800 rounded-xl p-5 shadow-[0_2px_8px_rgba(121,137,236,0.10)]">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-bm font-semibold text-black-0">
                  {DDV} Tierlist &amp; Builds
                </h2>
                <button
                  onClick={() => navigate("/tierlist")}
                  className="text-bxs font-semibold text-blue-400 hover:text-blue-300 transition-colors"
                >
                  Ver tudo →
                </button>
              </div>

              {/* Table header */}
              <div className="grid grid-cols-[1fr_48px_64px_64px] gap-2 text-bxs text-black-400 uppercase tracking-wider mb-2 px-2">
                <span>Campeão</span>
                <span className="text-center">Tier</span>
                <span className="text-right">Win%</span>
                <span className="text-right">Pick%</span>
              </div>

              {/* Rows */}
              <div className="space-y-1">
                {TIERLIST_PREVIEW.map((c) => (
                  <div
                    key={c.name}
                    className="grid grid-cols-[1fr_48px_64px_64px] gap-2 items-center px-2 py-2 rounded-lg hover:bg-black-600/50 transition-colors"
                  >
                    <div className="flex items-center gap-2.5">
                      <img
                        src={`https://ddragon.leagueoflegends.com/cdn/${DDV}/img/champion/${c.name}.png`}
                        alt={c.name}
                        className="w-7 h-7 rounded-md"
                      />
                      <span className="text-bs text-black-100 font-medium">{c.name}</span>
                    </div>
                    <span className="text-bs font-bold text-center" style={{ color: "#FF7043" }}>
                      {c.tier}
                    </span>
                    <span className="text-bs text-green-600 text-right">{c.winRate}</span>
                    <span className="text-bs text-black-300 text-right">{c.pickRate}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Leaderboard Preview */}
            <div className="bg-black-800 rounded-xl p-5 shadow-[0_2px_8px_rgba(121,137,236,0.10)]">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-bm font-semibold text-black-0">Leaderboard</h2>
                <button
                  onClick={() => navigate("/leaderboard")}
                  className="text-bxs font-semibold text-blue-400 hover:text-blue-300 transition-colors"
                >
                  Ver tudo →
                </button>
              </div>

              {/* Region tabs (decorative) */}
              <div className="flex gap-2 mb-4">
                {["BR", "NA", "EUW", "KR"].map((region, i) => (
                  <span
                    key={region}
                    className={`text-bxs font-semibold px-3 py-1 rounded-full cursor-default transition-colors ${
                      i === 0
                        ? "bg-blue-500/20 text-blue-400"
                        : "bg-black-600 text-black-400 hover:text-black-300"
                    }`}
                  >
                    {region}
                  </span>
                ))}
              </div>

              {/* Rows */}
              <div className="space-y-1">
                {LEADERBOARD_PREVIEW.map((p) => (
                  <div
                    key={p.rank}
                    className="flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-black-600/50 transition-colors"
                  >
                    <span className="text-bs font-bold text-black-400 w-5 text-center">
                      {p.rank}
                    </span>
                    <img
                      src={`https://ddragon.leagueoflegends.com/cdn/${DDV}/img/profileicon/${p.profileIcon}.png`}
                      alt=""
                      className="w-7 h-7 rounded-md"
                    />
                    <span className="text-bs text-black-100 font-medium flex-1 truncate">
                      {p.name}
                    </span>
                    <span
                      className="text-bxs font-bold"
                      style={{ color: "#F4C874" }}
                    >
                      {p.tier}
                    </span>
                    <span className="text-bs text-black-200 w-14 text-right">{p.lp} LP</span>
                    <span className="text-bs text-green-600 w-10 text-right">{p.winRate}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* ───── Popular Champions Section ───── */}
        <section
          className="max-w-[1200px] mx-auto px-4 pb-20 animate-fade-up"
          style={{ animationDelay: "320ms", animationFillMode: "both" }}
        >
          <div className="text-center mb-8">
            <h2 className="text-hxs font-semibold text-black-0 mb-2">
              Campeões mais populares
            </h2>
            <p className="text-bs text-black-300">
              Explore as melhores builds, matchups e mais
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
            {POPULAR_CHAMPIONS.map((champ) => (
              <div
                key={champ.name}
                className="relative group rounded-xl overflow-hidden aspect-[3/4] border border-white/5 hover:border-purple-300/30 transition-all duration-300 cursor-default"
              >
                <img
                  src={`https://ddragon.leagueoflegends.com/cdn/img/champion/loading/${champ.name}_0.jpg`}
                  alt={champ.displayName}
                  className="w-full h-full object-cover object-top group-hover:scale-105 transition-transform duration-500"
                  onError={e => { e.target.style.display = "none" }}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black-900/95 via-black-900/30 to-transparent" />
                <div className="absolute bottom-0 left-0 right-0 p-4">
                  <h3 className="text-bm font-bold text-black-0 mb-1">{champ.displayName}</h3>
                  <p className="text-bxs text-black-300">{champ.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
