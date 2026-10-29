import { useMemo, useState } from "react"
import { useSearchParams } from "react-router-dom"
import { LANES, META_TIERS, opggBuildUrl, positionIcon, uggBuildUrl } from "../services/constants"
import { formatNumber, formatPercent, patchLabel, useTierlist, winRateColor } from "../services/meta"
import { ChampionAvatar, ErrorState, RankTrend, SkeletonRows, TierBadge } from "../components/MetaBits"

const SORTS = {
  rank:  { label: "#",        value: (r) => r.rank,      dir: 1 },
  win:   { label: "Vitória",  value: (r) => r.win_rate,  dir: -1 },
  pick:  { label: "Escolha",  value: (r) => r.pick_rate, dir: -1 },
  ban:   { label: "Ban",      value: (r) => r.ban_rate,  dir: -1 },
  games: { label: "Partidas", value: (r) => r.play,      dir: -1 },
}

const VALID_LANES = new Set(LANES.map((l) => l.id))

function timeAgo(epochSeconds) {
  if (!epochSeconds) return ""
  const minutes = Math.max(0, Math.round((Date.now() / 1000 - epochSeconds) / 60))
  if (minutes < 1) return "agora"
  if (minutes < 60) return `há ${minutes} min`
  const hours = Math.round(minutes / 60)
  return `há ${hours} h`
}

function SortHeader({ id, sort, onSort, className = "" }) {
  const active = sort === id
  return (
    <button
      type="button"
      onClick={() => onSort(id)}
      className={`inline-flex items-center justify-end gap-1 text-bxs font-semibold uppercase tracking-wider transition ${active ? "text-purple-300" : "text-black-400 hover:text-black-200"} ${className}`}
      aria-pressed={active}
    >
      {SORTS[id].label}
      {active && <span aria-hidden="true">{SORTS[id].dir === 1 ? "↑" : "↓"}</span>}
    </button>
  )
}

export default function TierlistScreen() {
  const [params, setParams] = useSearchParams()
  const laneParam = params.get("lane")
  const lane = VALID_LANES.has(laneParam) ? laneParam : "mid"
  const [sort, setSort] = useState("rank")
  const [query, setQuery] = useState("")
  const [hideOffMeta, setHideOffMeta] = useState(true)
  const { data, loading, error, retry } = useTierlist()

  const version = data?.ddragon_version
  const patch = patchLabel(version)

  const rows = useMemo(() => {
    const list = data?.positions?.[lane] ?? []
    const term = query.trim().toLowerCase()
    const { value, dir } = SORTS[sort]
    return list
      .filter((r) => !hideOffMeta || !r.is_rip)
      .filter((r) => !term || String(r.champion).toLowerCase().includes(term))
      .slice()
      .sort((a, b) => (value(a) - value(b)) * dir)
  }, [data, lane, query, sort, hideOffMeta])

  const tierCounts = useMemo(() => {
    const counts = {}
    for (const r of data?.positions?.[lane] ?? []) counts[r.tier] = (counts[r.tier] ?? 0) + 1
    return counts
  }, [data, lane])

  function selectLane(id) {
    const next = new URLSearchParams(params)
    next.set("lane", id)
    setParams(next, { replace: true })
  }

  return (
    <div className="mx-auto max-w-[1200px] px-4 py-10">
      <header className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="eyebrow">Tier list {patch && `· patch ${patch}`}</p>
          <h1 className="mt-3 font-display text-[30px] font-bold leading-tight text-black-0 sm:text-[40px]">Quem está forte agora</h1>
          <p className="mt-3 max-w-xl text-bm text-black-300">
            Força de cada campeão por rota na ranqueada solo/duo, com dados do OP.GG
            {data?.updated_at ? `, atualizados ${timeAgo(data.updated_at)}` : ""}. Para a build completa, abra o campeão no OP.GG ou no U.GG.
          </p>
        </div>
        <div className="flex flex-wrap gap-2" aria-label="Escala de tiers">
          {Object.entries(META_TIERS).map(([tier, meta]) => (
            <span key={tier} className="inline-flex items-center gap-2 rounded-full border border-white/[0.06] px-3 py-1.5 text-bxs text-black-300">
              <TierBadge tier={Number(tier)} size="sm" />
              <span className="tabular">{tierCounts[tier] ?? 0}</span>
              <span className="sr-only">campeões no tier {meta.label}</span>
            </span>
          ))}
        </div>
      </header>

      <div className="mt-8 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-wrap gap-1.5" role="tablist" aria-label="Rota">
          {LANES.map(({ id, label }) => (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={lane === id}
              onClick={() => selectLane(id)}
              className={`chip flex-shrink-0 ${lane === id ? "chip-active" : ""}`}
            >
              <img src={positionIcon(id)} alt="" className="h-4 w-4" />
              {label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <label className="flex h-10 flex-1 items-center gap-2 rounded-full border border-white/[0.08] bg-black-600/80 px-4 focus-within:border-purple-400/60 md:w-[240px] md:flex-none">
            <svg className="h-4 w-4 text-black-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <circle cx="11" cy="11" r="7.5" />
              <path d="m20.5 20.5-4.2-4.2" strokeLinecap="round" />
            </svg>
            <span className="sr-only">Filtrar campeão</span>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Filtrar campeão"
              className="w-full bg-transparent text-bs text-black-100 placeholder-black-400 outline-none"
            />
          </label>
          <label className="flex flex-shrink-0 cursor-pointer items-center gap-2 text-bs text-black-300">
            <input type="checkbox" checked={hideOffMeta} onChange={(e) => setHideOffMeta(e.target.checked)} className="h-4 w-4 accent-[#E2B95E]" />
            Só da meta
          </label>
        </div>
      </div>

      <section className="card mt-5 overflow-hidden">
        {/* Cabeçalho (desktop) */}
        <div className="hidden grid-cols-[48px_minmax(180px,1fr)_64px_84px_84px_84px_64px_96px_120px] items-center gap-3 border-b border-white/[0.06] px-5 py-3 md:grid">
          <SortHeader id="rank" sort={sort} onSort={setSort} className="justify-start" />
          <span className="text-bxs font-semibold uppercase tracking-wider text-black-400">Campeão</span>
          <span className="text-center text-bxs font-semibold uppercase tracking-wider text-black-400">Tier</span>
          <SortHeader id="win" sort={sort} onSort={setSort} />
          <SortHeader id="pick" sort={sort} onSort={setSort} />
          <SortHeader id="ban" sort={sort} onSort={setSort} />
          <span className="text-right text-bxs font-semibold uppercase tracking-wider text-black-400">KDA</span>
          <SortHeader id="games" sort={sort} onSort={setSort} />
          <span className="text-right text-bxs font-semibold uppercase tracking-wider text-black-400">Build</span>
        </div>

        {/* Ordenação (celular) */}
        <div className="flex gap-1.5 overflow-x-auto border-b border-white/[0.06] px-4 py-3 md:hidden">
          {Object.keys(SORTS).map((id) => (
            <button key={id} type="button" onClick={() => setSort(id)} className={`chip flex-shrink-0 ${sort === id ? "chip-active" : ""}`}>
              {SORTS[id].label}
            </button>
          ))}
        </div>

        <div className="p-2 md:p-3">
          {loading && <SkeletonRows rows={10} className="h-14" />}
          {error && <ErrorState message="Não deu para carregar a tier list agora." onRetry={retry} />}
          {!loading && !error && rows.length === 0 && (
            <p className="px-4 py-10 text-center text-bm text-black-300">Nenhum campeão com esse nome nesta rota.</p>
          )}

          <ol className="grid gap-0.5">
            {rows.map((row) => (
              <li
                key={row.champion}
                className={`grid grid-cols-[32px_1fr_auto_64px] items-center gap-3 rounded-xl px-2 py-2.5 transition hover:bg-white/[0.03] md:grid-cols-[48px_minmax(180px,1fr)_64px_84px_84px_84px_64px_96px_120px] md:px-3 ${row.is_rip ? "opacity-50" : ""}`}
              >
                <span className="flex flex-col items-start">
                  <span className="tabular text-bm font-semibold text-black-200">{row.rank}</span>
                  <RankTrend rank={row.rank} previous={row.rank_prev} />
                </span>
                <span className="flex min-w-0 items-center gap-3">
                  <ChampionAvatar championKey={row.champion_key} name={row.champion} version={version} className="h-10 w-10" />
                  <span className="min-w-0">
                    <span className="block truncate text-bm font-semibold text-black-0">{row.champion}</span>
                    <span className="tabular block text-bxs text-black-400 md:hidden">
                      {formatPercent(row.pick_rate)} escolha · {formatPercent(row.ban_rate)} ban
                    </span>
                  </span>
                </span>
                <span className="flex justify-center"><TierBadge tier={row.tier} /></span>
                <span className={`tabular text-right text-bm font-semibold ${winRateColor(row.win_rate)}`}>{formatPercent(row.win_rate)}</span>
                <span className="tabular hidden text-right text-bs text-black-200 md:block">{formatPercent(row.pick_rate)}</span>
                <span className="tabular hidden text-right text-bs text-black-200 md:block">{formatPercent(row.ban_rate)}</span>
                <span className="tabular hidden text-right text-bs text-black-200 md:block">{Number(row.kda || 0).toFixed(2)}</span>
                <span className="tabular hidden text-right text-bs text-black-300 md:block">{formatNumber(row.play)}</span>
                <span className="hidden justify-end gap-1.5 md:flex">
                  <a href={opggBuildUrl(row.champion_key, lane)} target="_blank" rel="noreferrer noopener"
                    className="rounded-full border border-white/[0.08] px-2.5 py-1 text-bxs font-semibold text-black-200 transition hover:border-white/25 hover:text-black-0">
                    OP.GG
                  </a>
                  <a href={uggBuildUrl(row.champion_key, lane)} target="_blank" rel="noreferrer noopener"
                    className="rounded-full border border-white/[0.08] px-2.5 py-1 text-bxs font-semibold text-black-200 transition hover:border-white/25 hover:text-black-0">
                    U.GG
                  </a>
                </span>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <p className="mt-4 text-bxs text-black-400">
        Dados de tier, vitória, escolha, ban, KDA e partidas fornecidos pelo{" "}
        <a href="https://op.gg/lol/champions" target="_blank" rel="noreferrer noopener" className="underline hover:text-black-200">OP.GG</a>.
        Os tiers 1 a 5 do OP.GG aparecem aqui como S, A, B, C e D. Campeões fora da meta ficam escondidos com o filtro ligado.
      </p>
    </div>
  )
}
