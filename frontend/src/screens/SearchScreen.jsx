import { useEffect, useMemo, useState } from "react"
import { Link, useLocation, useNavigate } from "react-router-dom"
import { LANES, championCentered, positionIcon, rankCrest } from "../services/constants"
import { formatNumber, formatPercent, patchLabel, strongestElos, useLeaderboard, useTierlist, useTierlistElos, winRateColor } from "../services/meta"
import { ChampionAvatar, EloStrip, RiftLanes, SkeletonRows, TierBadge } from "../components/MetaBits"

function parseRiotId(raw) {
  const value = raw.trim()
  if (!value) return { error: "Digite Nick#TAG para buscar." }
  const hashIdx = value.lastIndexOf("#")
  if (hashIdx < 1) return { error: "Use o formato Nick#TAG, por exemplo Faker#BR1." }
  const nick = value.slice(0, hashIdx).trim()
  const tag = value.slice(hashIdx + 1).trim()
  if (!nick || !tag) return { error: "Nick ou TAG inválidos." }
  return { nick, tag }
}

function profilePath(nick, tag) {
  return `/summoner/${encodeURIComponent(nick)}/${encodeURIComponent(tag)}`
}

const STEPS = [
  {
    title: "Busque seu Riot ID",
    body: "Digite Nick#TAG e veja o histórico recente, o elo e cada partida com KDA, farm, visão e dano.",
  },
  {
    title: "Entenda cada partida",
    body: "Cada jogo ganha uma nota de desempenho e um placar completo, com você destacado entre os dez jogadores.",
  },
  {
    title: "Receba o coaching",
    body: "Com o app no PC, a IA lê a partida e aponta os erros e acertos que fizeram diferença no resultado.",
  },
]

export default function SearchScreen() {
  const navigate = useNavigate()
  const { state } = useLocation()
  const [query, setQuery] = useState("")
  const [error, setError] = useState(state?.error ?? "")
  const [lane, setLane] = useState("mid")
  const tierlist = useTierlist()
  const ladder = useLeaderboard(50)
  const elos = useTierlistElos(lane)

  useEffect(() => {
    if (!error) return undefined
    const timer = setTimeout(() => setError(""), 4000)
    return () => clearTimeout(timer)
  }, [error])

  function handleSubmit(e) {
    e.preventDefault()
    const parsed = parseRiotId(query)
    if (parsed.error) { setError(parsed.error); return }
    setError("")
    navigate(profilePath(parsed.nick, parsed.tag))
  }

  const version = tierlist.data?.ddragon_version
  const patch = patchLabel(version)
  const laneLeaders = useMemo(() => {
    const positions = tierlist.data?.positions ?? {}
    return LANES.map(({ id, label }) => ({ id, label, champion: positions[id]?.[0] })).filter((l) => l.champion)
  }, [tierlist.data])
  const laneRows = (tierlist.data?.positions?.[lane] ?? []).slice(0, 6)
  const topPlayers = (ladder.data?.players ?? []).slice(0, 6)
  const suggestions = (ladder.data?.players ?? []).slice(0, 3)

  return (
    <div className="relative overflow-hidden">
      {/* ───── Hero ───── */}
      <section className="relative">
        <div className="rift-grid pointer-events-none absolute inset-0" />
        <div className="pointer-events-none absolute -top-40 left-1/2 h-[520px] w-[920px] -translate-x-1/2 rounded-full bg-purple-400/[0.07] blur-3xl" />

        <div className="relative mx-auto grid max-w-[1200px] grid-cols-1 items-center gap-10 px-4 pb-16 pt-10 md:pt-16 lg:grid-cols-[1.15fr_0.85fr] lg:pb-24 lg:pt-20">
          <div>
            <p className="eyebrow animate-fade-up">Coach de LoL com IA · servidor BR</p>
            <h1
              className="mt-4 font-display text-[34px] font-bold leading-[1.05] tracking-tight text-black-0 sm:text-[46px] lg:text-[58px] animate-fade-up"
              style={{ animationDelay: "60ms" }}
            >
              Descubra o que separa você do <span className="text-gold-gradient">MVP</span>.
            </h1>
            <p className="mt-5 max-w-[520px] text-bm text-black-300 sm:text-[17px] animate-fade-up" style={{ animationDelay: "120ms" }}>
              Busque qualquer invocador e veja cada partida de perto: desempenho, placar completo e coaching com IA.
              Grátis, sem login.
            </p>

            <form onSubmit={handleSubmit} role="search" className="mt-8 max-w-[560px] animate-fade-up" style={{ animationDelay: "180ms" }}>
              <div className={`flex items-center gap-2 rounded-2xl border bg-black-600/90 p-2 shadow-card transition focus-within:border-purple-400/60 ${error ? "border-red-500/60" : "border-white/[0.08]"}`}>
                <svg className="ml-3 h-5 w-5 flex-shrink-0 text-black-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <circle cx="11" cy="11" r="7.5" />
                  <path d="m20.5 20.5-4.2-4.2" strokeLinecap="round" />
                </svg>
                <label htmlFor="busca-home" className="sr-only">Riot ID do invocador</label>
                <input
                  id="busca-home"
                  type="text"
                  value={query}
                  onChange={(e) => { setQuery(e.target.value); setError("") }}
                  placeholder="Nick#TAG"
                  autoComplete="off"
                  className="h-12 min-w-0 flex-1 bg-transparent text-[16px] text-black-0 placeholder-black-400 outline-none"
                />
                <button type="submit" className="btn-gold h-12 px-6 text-bm">
                  Analisar
                </button>
              </div>
              <p className={`mt-3 min-h-[20px] text-bs ${error ? "text-red-400" : "text-black-400"}`} role={error ? "alert" : undefined}>
                {error || (suggestions.length > 0 ? "Ou experimente um Challenger do BR:" : "")}
              </p>
              {!error && suggestions.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {suggestions.map((p) => (
                    <Link key={`${p.game_name}#${p.tag_line}`} to={profilePath(p.game_name, p.tag_line)} className="chip max-w-full">
                      <span className="truncate">{p.game_name}</span>
                      <span className="text-black-400">#{p.tag_line}</span>
                    </Link>
                  ))}
                </div>
              )}
            </form>
          </div>

          {/* Mapa + líderes de cada rota */}
          <div className="relative hidden lg:block">
            <RiftLanes className="absolute -inset-10 h-[calc(100%+80px)] w-[calc(100%+80px)] opacity-90" />
            <div className="card relative ml-auto mt-24 w-[330px] p-5">
              <div className="flex items-center justify-between">
                <p className="eyebrow">Donos das rotas</p>
                {patch && <span className="text-bxs text-black-400">Patch {patch}</span>}
              </div>
              <div className="mt-4 grid gap-2">
                {tierlist.loading && <SkeletonRows rows={5} className="h-11" />}
                {laneLeaders.map(({ id, label, champion }) => (
                  <Link key={id} to={`/tierlist?lane=${id}`} className="flex items-center gap-3 rounded-xl px-2 py-1.5 transition hover:bg-white/[0.04]">
                    <img src={positionIcon(id)} alt="" className="h-5 w-5 opacity-70" />
                    <ChampionAvatar championKey={champion.champion_key} name={champion.champion} version={version} className="h-9 w-9" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-bs font-semibold text-black-0">{champion.champion}</p>
                      <p className="text-bxs text-black-400">{label}</p>
                    </div>
                    <span className={`tabular text-bs font-semibold ${winRateColor(champion.win_rate)}`}>{formatPercent(champion.win_rate, 0)}</span>
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ───── Em alta: o nº 1 de cada rota ───── */}
      {laneLeaders.length > 0 && (
        <section className="mx-auto max-w-[1200px] px-4 pb-16">
          <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="eyebrow">Em alta no patch {patch}</p>
              <h2 className="mt-2 font-display text-[24px] font-bold text-black-0 sm:text-[30px]">O mais forte de cada rota</h2>
            </div>
            <Link to="/tierlist" className="text-bs font-semibold text-purple-300 hover:text-purple-200">Ver tier list completa →</Link>
          </div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            {laneLeaders.map(({ id, label, champion }, index) => (
              <Link
                key={id}
                to={`/tierlist?lane=${id}`}
                className={`group relative overflow-hidden rounded-card border border-white/[0.06] bg-black-600 ${index === 4 ? "col-span-2 sm:col-span-1" : ""}`}
              >
                <img
                  src={championCentered(champion.champion_key)}
                  alt=""
                  loading="lazy"
                  className="aspect-[4/5] w-full object-cover object-center opacity-80 transition duration-500 group-hover:scale-105 group-hover:opacity-100"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black-900 via-black-900/30 to-transparent" />
                <div className="absolute inset-x-0 bottom-0 p-4">
                  <div className="mb-2 flex items-center gap-2">
                    <img src={positionIcon(id)} alt="" className="h-4 w-4 opacity-80" />
                    <span className="text-bxs font-semibold uppercase tracking-wider text-black-200">{label}</span>
                  </div>
                  <p className="font-display text-bxl font-bold text-black-0">{champion.champion}</p>
                  <p className="tabular mt-1 text-bxs text-black-300">
                    {formatPercent(champion.win_rate, 0)} vitórias · {formatPercent(champion.pick_rate, 0)} escolha
                  </p>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* ───── Tier list + Ranking ───── */}
      <section className="mx-auto grid max-w-[1200px] grid-cols-1 gap-5 px-4 pb-16 lg:grid-cols-2">
        <div className="card p-5">
          <div className="flex items-center justify-between gap-3">
            <h2 className="font-display text-bxl font-bold text-black-0">Tier list {patch && <span className="text-black-400">· {patch}</span>}</h2>
            <Link to={`/tierlist?lane=${lane}`} className="text-bs font-semibold text-purple-300 hover:text-purple-200">Ver tudo →</Link>
          </div>
          <div className="mt-4 flex flex-wrap gap-1.5" role="tablist" aria-label="Rota">
            {LANES.map(({ id, label }) => (
              <button
                key={id}
                type="button"
                role="tab"
                aria-selected={lane === id}
                onClick={() => setLane(id)}
                className={`chip flex-shrink-0 ${lane === id ? "chip-active" : ""}`}
              >
                <img src={positionIcon(id)} alt="" className="h-4 w-4" />
                {label}
              </button>
            ))}
          </div>
          <div className="mt-4 flex items-center justify-between gap-3 px-2 text-bxs text-black-400">
            <span>Força por elo: Ferro → Mestre+</span>
            <span>Tier · vitória em Esmeralda+</span>
          </div>
          <div className="mt-2 grid gap-1">
            {tierlist.loading && <SkeletonRows rows={6} className="h-16" />}
            {tierlist.error && <p className="py-6 text-center text-bs text-black-300">Tier list indisponível agora.</p>}
            {laneRows.map((row) => {
              const entries = elos.data?.champions?.[row.champion_key]
              const strongest = entries ? strongestElos(entries, elos.data.elos) : ""
              return (
                <div key={row.champion} className="grid grid-cols-[24px_1fr_auto_56px] items-center gap-3 rounded-xl px-2 py-2 hover:bg-white/[0.03]">
                  <span className="tabular text-bs font-semibold text-black-400">{row.rank}</span>
                  <div className="flex min-w-0 items-center gap-3">
                    <ChampionAvatar championKey={row.champion_key} name={row.champion} version={version} className="h-10 w-10 flex-shrink-0" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-bs font-semibold text-black-0">{row.champion}</p>
                      <div className="mt-1">
                        {entries
                          ? <EloStrip entries={entries} elos={elos.data.elos} />
                          : <span className={`block h-5 w-full max-w-[200px] rounded-[5px] ${elos.error ? "bg-white/[0.03]" : "shimmer-bg"}`} aria-hidden="true" />}
                      </div>
                      <p className="mt-1 truncate text-bxs text-black-400">
                        {strongest ? <>Mais forte em <span className="font-semibold text-black-200">{strongest}</span></> : elos.loading ? "Calculando força por elo…" : " "}
                      </p>
                    </div>
                  </div>
                  <TierBadge tier={row.tier} size="sm" />
                  <span className={`tabular text-right text-bs font-semibold ${winRateColor(row.win_rate)}`}>{formatPercent(row.win_rate)}</span>
                </div>
              )
            })}
          </div>
          <p className="mt-3 text-bxs text-black-400">Dados: OP.GG · ranqueada solo/duo</p>
        </div>

        <div className="card p-5">
          <div className="flex items-center justify-between gap-3">
            <h2 className="font-display text-bxl font-bold text-black-0">Challenger <span className="text-black-400">· BR</span></h2>
            <Link to="/leaderboard" className="text-bs font-semibold text-purple-300 hover:text-purple-200">Ver ranking →</Link>
          </div>
          <div className="mt-4 grid gap-1">
            {ladder.loading && <SkeletonRows rows={6} className="h-12" />}
            {ladder.error && <p className="py-6 text-center text-bs text-black-300">Ranking indisponível agora.</p>}
            {topPlayers.map((p) => (
              <Link
                key={`${p.game_name}#${p.tag_line}`}
                to={profilePath(p.game_name, p.tag_line)}
                className="grid grid-cols-[24px_36px_1fr_auto] items-center gap-3 rounded-xl px-2 py-2 transition hover:bg-white/[0.03]"
              >
                <span className={`tabular text-bs font-bold ${p.position <= 3 ? "text-purple-300" : "text-black-400"}`}>{p.position}</span>
                <img src={rankCrest(p.tier)} alt="" className="h-8 w-8 object-contain" loading="lazy" />
                <span className="min-w-0">
                  <span className="block truncate text-bs font-semibold text-black-0">{p.game_name}</span>
                  <span className="block text-bxs text-black-400">#{p.tag_line} · {Number(p.win_rate).toFixed(1)}% vitórias</span>
                </span>
                <span className="tabular text-bs font-semibold text-black-100">{formatNumber(p.lp)} PDL</span>
              </Link>
            ))}
          </div>
          <p className="mt-3 text-bxs text-black-400">Dados: Riot Games · fila solo/duo</p>
        </div>
      </section>

      {/* ───── Como funciona ───── */}
      <section className="mx-auto max-w-[1200px] px-4 pb-8">
        <div className="card relative overflow-hidden p-6 sm:p-10">
          <RiftLanes className="pointer-events-none absolute -right-44 -top-40 hidden h-[420px] w-[420px] opacity-20 lg:block" />
          <p className="eyebrow">Como funciona</p>
          <h2 className="mt-2 max-w-xl font-display text-[24px] font-bold text-black-0 sm:text-[30px]">Do placar à próxima vitória em três passos</h2>
          <ol className="relative mt-8 grid grid-cols-1 gap-6 md:grid-cols-3">
            {STEPS.map((step, i) => (
              <li key={step.title} className="flex gap-4">
                <span className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full border border-purple-400/40 font-display text-bm font-bold text-purple-300">
                  {i + 1}
                </span>
                <div>
                  <h3 className="text-bm font-semibold text-black-0">{step.title}</h3>
                  <p className="mt-1 text-bs text-black-300">{step.body}</p>
                </div>
              </li>
            ))}
          </ol>
          <div className="relative mt-8 flex flex-wrap gap-3">
            <Link to="/download" className="btn-gold text-bs">Baixar o app de coaching</Link>
            <Link to="/how-it-works" className="btn-ghost text-bs">Entenda os detalhes</Link>
          </div>
        </div>
      </section>
    </div>
  )
}
