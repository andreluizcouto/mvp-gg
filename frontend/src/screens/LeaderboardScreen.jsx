import { useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { rankCrest, rankEmblem } from "../services/constants"
import { formatNumber, useLeaderboard } from "../services/meta"
import { ErrorState, SkeletonRows } from "../components/MetaBits"

function profilePath(p) {
  return `/summoner/${encodeURIComponent(p.game_name)}/${encodeURIComponent(p.tag_line)}`
}

function WinLossBar({ wins, losses }) {
  const total = wins + losses
  const pct = total ? (wins / total) * 100 : 0
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-red-500/30" aria-hidden="true">
        <div className="h-full rounded-full bg-blue-400" style={{ width: `${pct}%` }} />
      </div>
      <span className="tabular whitespace-nowrap text-bxs text-black-300">
        {wins}V {losses}D
      </span>
    </div>
  )
}

function Badges({ player }) {
  return (
    <span className="flex flex-wrap gap-1">
      {player.hot_streak && <span className="rounded-full bg-red-500/15 px-2 py-0.5 text-bxs font-semibold text-red-400">Em sequência</span>}
      {player.fresh_blood && <span className="rounded-full bg-blue-400/15 px-2 py-0.5 text-bxs font-semibold text-blue-300">Novo no elo</span>}
      {player.veteran && <span className="rounded-full bg-purple-400/15 px-2 py-0.5 text-bxs font-semibold text-purple-300">Veterano</span>}
    </span>
  )
}

const PODIUM_STYLES = [
  "border-purple-400/40 shadow-glow lg:-translate-y-3",
  "border-white/[0.10]",
  "border-white/[0.10]",
]

export default function LeaderboardScreen() {
  const { data, loading, error, retry } = useLeaderboard(50)
  const [query, setQuery] = useState("")
  const players = useMemo(() => data?.players ?? [], [data])

  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase()
    if (!term) return players
    return players.filter((p) => `${p.game_name}#${p.tag_line}`.toLowerCase().includes(term))
  }, [players, query])

  const podium = query ? [] : players.slice(0, 3)
  const rest = query ? filtered : filtered.slice(3)

  return (
    <div className="mx-auto max-w-[1200px] px-4 py-10">
      <header className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="eyebrow">Ranking · servidor BR</p>
          <h1 className="mt-3 font-display text-[30px] font-bold leading-tight text-black-0 sm:text-[40px]">Os melhores do Brasil</h1>
          <p className="mt-3 max-w-xl text-bm text-black-300">
            Top 50 do Challenger na fila solo/duo, direto da Riot. Toque num jogador para ver as partidas dele.
          </p>
        </div>
        <label className="flex h-10 items-center gap-2 rounded-full border border-white/[0.08] bg-black-600/80 px-4 focus-within:border-purple-400/60 md:w-[280px]">
          <svg className="h-4 w-4 text-black-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <circle cx="11" cy="11" r="7.5" />
            <path d="m20.5 20.5-4.2-4.2" strokeLinecap="round" />
          </svg>
          <span className="sr-only">Filtrar jogador</span>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filtrar jogador"
            className="w-full bg-transparent text-bs text-black-100 placeholder-black-400 outline-none"
          />
        </label>
      </header>

      {loading && <div className="mt-8"><SkeletonRows rows={8} className="h-16" /></div>}
      {error && <div className="mt-8"><ErrorState message="Não deu para carregar o ranking agora." onRetry={retry} /></div>}

      {podium.length > 0 && (
        <section className="mt-10 grid grid-cols-1 gap-4 lg:grid-cols-3" aria-label="Top 3">
          {[podium[1], podium[0], podium[2]].filter(Boolean).map((p) => (
            <Link
              key={`${p.game_name}#${p.tag_line}`}
              to={profilePath(p)}
              className={`card relative flex items-center gap-4 border p-5 transition hover:border-purple-400/50 lg:flex-col lg:text-center ${PODIUM_STYLES[p.position - 1]} ${p.position === 1 ? "order-first lg:order-none" : ""}`}
            >
              <span className={`absolute right-4 top-4 font-display text-[28px] font-bold lg:left-5 lg:right-auto ${p.position === 1 ? "text-gold-gradient" : "text-black-400"}`}>
                {p.position}
              </span>
              <span className="h-20 w-20 flex-shrink-0 overflow-hidden lg:h-28 lg:w-28"><img src={rankEmblem(p.tier)} alt="" className="h-full w-full scale-[2.5] object-contain" /></span>
              <div className="min-w-0 flex-1 pr-8 lg:w-full lg:pr-0">
                <p className="truncate font-display text-bxl font-bold text-black-0">{p.game_name}</p>
                <p className="text-bs text-black-400">#{p.tag_line}</p>
                <p className="tabular mt-2 text-bxl font-semibold text-purple-300">{formatNumber(p.lp)} PDL</p>
                <div className="mt-3 lg:mx-auto lg:max-w-[220px]"><WinLossBar wins={p.wins} losses={p.losses} /></div>
              </div>
            </Link>
          ))}
        </section>
      )}

      {rest.length > 0 && (
        <section className="card mt-6 overflow-hidden">
          <div className="hidden grid-cols-[56px_1fr_120px_220px_80px_200px] gap-4 border-b border-white/[0.06] px-5 py-3 text-bxs font-semibold uppercase tracking-wider text-black-400 md:grid">
            <span>#</span>
            <span>Jogador</span>
            <span className="text-right">PDL</span>
            <span>Vitórias e derrotas</span>
            <span className="text-right">Vitória</span>
            <span>Destaques</span>
          </div>
          <ol className="grid gap-0.5 p-2 md:p-3">
            {rest.map((p) => (
              <li key={`${p.game_name}#${p.tag_line}`}>
                <Link
                  to={profilePath(p)}
                  className="grid grid-cols-[36px_1fr_auto] items-center gap-3 rounded-xl px-2 py-2.5 transition hover:bg-white/[0.03] md:grid-cols-[56px_1fr_120px_220px_80px_200px] md:gap-4 md:px-3"
                >
                  <span className="tabular text-bm font-semibold text-black-400">{p.position}</span>
                  <span className="flex min-w-0 items-center gap-3">
                    <img src={rankCrest(p.tier)} alt="" className="h-8 w-8 flex-shrink-0 object-contain" loading="lazy" />
                    <span className="min-w-0">
                      <span className="block truncate text-bm font-semibold text-black-0">{p.game_name}</span>
                      <span className="block text-bxs text-black-400">#{p.tag_line}<span className="md:hidden"> · {Number(p.win_rate).toFixed(1)}% vitórias</span></span>
                    </span>
                  </span>
                  <span className="tabular text-right text-bm font-semibold text-black-100">{formatNumber(p.lp)}<span className="text-bxs text-black-400 md:hidden"> PDL</span></span>
                  <span className="hidden md:block"><WinLossBar wins={p.wins} losses={p.losses} /></span>
                  <span className="tabular hidden text-right text-bm font-semibold text-black-100 md:block">{Number(p.win_rate).toFixed(1)}%</span>
                  <span className="hidden md:block"><Badges player={p} /></span>
                </Link>
              </li>
            ))}
          </ol>
        </section>
      )}

      {!loading && !error && query && filtered.length === 0 && (
        <p className="mt-8 text-center text-bm text-black-300">Ninguém do top 50 com esse nome.</p>
      )}

      <p className="mt-4 text-bxs text-black-400">Dados: Riot Games (league-v4 e account-v1). O ranking é atualizado a cada 30 minutos.</p>
    </div>
  )
}
