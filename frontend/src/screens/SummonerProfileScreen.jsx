import { useState, useEffect } from "react"
import { useParams, useNavigate, useLocation } from "react-router-dom"
import { fetchMatches, fetchCoachingStatus, refreshMatches, fetchScoreboard } from "../services/api"
import { DDV, QUEUE_FILTERS, TIER_LABELS, getPositionLabel, isArenaMatch, queueLabel, rankCrest } from "../services/constants"
import { LiveBadge, LiveGameCard } from "../components/LiveGame"
import { useLiveGame } from "../services/live"
import { TIER_COLORS, parseTier, calcScore, buildChampionPool, buildSummonerProfilePath, formatDateTime, timeAgo } from "../services/utils"

const MATCHES_PAGE_SIZE = 10

function mergeMatches(existing, incoming) {
  const seen = new Set(existing.map(match => match.match_id))
  const additions = incoming.filter(match => !seen.has(match.match_id))
  return [...existing, ...additions]
}

function getRankLabel(score) {
  if (score >= 100) return { label: "MVP", color: "#F4C874" }
  if (score >= 90)  return { label: "Top 3", color: "#73E4D8" }
  if (score >= 75)  return { label: "4º-5º", color: "#33D1C1" }
  if (score >= 60)  return { label: "6º-7º", color: "#97A0B3" }
  return { label: "8º-10º", color: "#6E778A" }
}

// No Arena a nota de desempenho não faz sentido (sem farm nem visão): mostramos a colocação.
function PlacementBadge({ placement, win }) {
  const color = placement === 1 ? "#E2B95E" : win ? "#3DD68C" : "#97A0B3"
  return (
    <div
      className="flex h-[48px] min-w-[56px] flex-shrink-0 flex-col items-center justify-center rounded-lg"
      style={{ color, background: `${color}14`, border: `1px solid ${color}40` }}
    >
      <span className="font-display text-[16px] font-bold leading-none">{placement}º</span>
      <span className="mt-0.5 text-bxs uppercase tracking-wider opacity-80">lugar</span>
    </div>
  )
}

function ScoreBadge({ score }) {
  const isElite = score >= 90
  const isGood  = score >= 75
  const isFair  = score >= 60
  const color  = isElite ? "#73E4D8" : isGood ? "#33D1C1" : isFair ? "#97A0B3" : "#6E778A"
  const bg     = isElite ? "#33D1C120" : isGood ? "#16B2A412" : isFair ? "#33D1C10A" : "#262E3D08"
  const border = isElite ? "#33D1C155" : isGood ? "#33D1C133" : "transparent"
  const rank   = getRankLabel(score)

  return (
    <div
      className={`min-w-[56px] h-[48px] rounded-lg flex flex-col items-center justify-center flex-shrink-0 ${isElite ? "scoreGlow" : ""}`}
      style={{ color, background: bg, border: `1px solid ${border}` }}
    >
      <span className="text-[16px] font-extrabold leading-none">{score}</span>
      <span className="text-bxs tracking-wide mt-0.5" style={{ color: rank.color, opacity: 0.85 }}>{rank.label}</span>
    </div>
  )
}

function StatCard({ label, value, delay = 0 }) {
  return (
    <div
      className="bg-black-800 rounded-xl p-4 min-w-[120px] flex-shrink-0 border border-white/5 animate-fade-up"
      style={{ animationDelay: `${delay}ms`, animationFillMode: "both" }}
    >
      <p className="text-bxs text-black-400 uppercase mb-1">{label}</p>
      <p className="text-hxs text-black-0 font-bold">{value}</p>
    </div>
  )
}

function InlineScoreboard({ data, fallbackTag }) {
  if (!data?.teams) return null

  return (
    <div className="rounded-lg border border-black-800/40 w-full max-w-[1320px] mx-auto overflow-hidden">
      <div className="w-full">
        {data.teams.map((team, ti) => {
          const isBlue = team.side === "blue"
          const isWin = team.win
          const teamColor = isWin ? "#3DD68C" : "#FF5A6E"
          const teamBg = isWin ? "rgba(74,201,126,0.08)" : "rgba(240,58,56,0.08)"
          const barColor = isWin ? "rgba(74,201,126,0.7)" : "rgba(240,58,56,0.7)"
          const sideLabel = team.side === "arena" ? "Time" : isBlue ? "Lado Azul" : "Lado Vermelho"
          const resultLabel = team.placement ? `${team.placement}º lugar` : isWin ? "Vitória" : "Derrota"
          const maxDmg = Math.max(...team.players.map(p => p.total_damage), 1)
          const teamKills = team.players.reduce((sum, p) => sum + (p.kills || 0), 0)
          const teamDeaths = team.players.reduce((sum, p) => sum + (p.deaths || 0), 0)
          const teamAssists = team.players.reduce((sum, p) => sum + (p.assists || 0), 0)

          return (
            <div key={ti}>
              <div className="flex items-center justify-between px-4 py-2.5" style={{ background: teamBg }}>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-[12px] uppercase tracking-wider" style={{ color: teamColor }}>
                    {resultLabel}
                  </span>
                  <span className="text-bxs text-black-400">({sideLabel})</span>
                </div>
                <span className="font-mono text-[12px] text-black-200">{teamKills} / {teamDeaths} / {teamAssists}</span>
              </div>

              <div className="w-full h-[1.5px] bg-gradient-to-r from-black-800/0 via-blue-400/15 to-black-800/0 scoreboard-divider" />

              <div className="grid grid-cols-[minmax(220px,1.5fr)_86px_54px_54px_minmax(120px,1fr)_52px_116px] items-center gap-1 px-3 py-1.5 bg-black-900/30">
                <div className="text-bxs text-black-400 uppercase tracking-wider">Jogador</div>
                <div className="text-center text-bxs text-black-400 uppercase tracking-wider">KDA</div>
                <div className="text-center text-bxs text-black-400 uppercase tracking-wider">KP</div>
                <div className="text-center text-bxs text-black-400 uppercase tracking-wider">CS</div>
                <div className="text-bxs text-black-400 uppercase tracking-wider">Dano</div>
                <div className="text-center text-bxs text-black-400 uppercase tracking-wider">Vis</div>
                <div className="text-left text-bxs text-black-400 uppercase tracking-wider">Items</div>
              </div>

              <div className="w-full h-[1.5px] bg-gradient-to-r from-black-800/0 via-blue-400/15 to-black-800/0 scoreboard-divider" />

              {team.players.map((player, pi) => {
                const isTarget = player.is_target
                const dmgPct = ((player.total_damage / maxDmg) * 100).toFixed(0)
                const isTopDmg = player.total_damage === maxDmg
                const profilePath = buildSummonerProfilePath(player.summoner_name, fallbackTag)
                const rawKp = Number(player.kill_participation_pct)
                const computedKp = teamKills > 0
                  ? Math.round(((Number(player.kills) || 0) + (Number(player.assists) || 0)) / teamKills * 100)
                  : null
                const kpValue = Number.isFinite(rawKp) ? Math.round(rawKp) : computedKp

                return (
                  <div
                    key={pi}
                    className="grid grid-cols-[minmax(220px,1.5fr)_86px_54px_54px_minmax(120px,1fr)_52px_116px] items-center gap-1 px-3 py-2 hover:bg-white/[0.02] transition-colors"
                    style={isTarget ? { background: "rgba(200,155,60,0.08)", borderLeft: "2px solid rgba(200,155,60,0.5)" } : {}}
                  >
                    <div className="min-w-0 flex items-start gap-1.5">
                      <div className="w-7 h-7 rounded overflow-hidden border border-white/10 bg-black-600 flex-shrink-0">
                        <img
                          src={`https://ddragon.leagueoflegends.com/cdn/${DDV}/img/champion/${player.champion}.png`}
                          alt={player.champion}
                          className="w-full h-full object-cover"
                          onError={e => { e.target.style.display = "none" }}
                        />
                      </div>

                      <div className="min-w-0 flex-1">
                        {profilePath ? (
                          <a
                            href={profilePath}
                            className="text-bxs text-white/85 truncate hover:text-blue-400 hover:underline cursor-pointer transition-colors block max-w-full text-left"
                            onClick={e => e.stopPropagation()}
                          >
                            {player.summoner_name || player.champion}
                          </a>
                        ) : (
                          <p className="text-bxs text-white/85 truncate">{player.summoner_name || player.champion}</p>
                        )}

                        {player.position && (
                          <div className="mt-0.5">
                            <span className="text-bxs text-black-400 bg-black-600/80 rounded px-1 py-0.5 inline-block">
                              {getPositionLabel(player.position, "short")}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="text-center">
                      <span className="text-bxs text-white/90">{player.kills}</span>
                      <span className="text-bxs text-white/25"> / </span>
                      <span className="text-bxs text-red-400">{player.deaths}</span>
                      <span className="text-bxs text-white/25"> / </span>
                      <span className="text-bxs text-white/90">{player.assists}</span>
                    </div>

                    <div className="text-center">
                      {kpValue != null
                        ? <span className="text-bxs text-black-300">{kpValue}%</span>
                        : <span className="text-bxs text-black-500">—</span>}
                    </div>

                    <div className="text-center">
                      {player.cs_per_min
                        ? <span className="text-bxs text-black-300">{player.cs_per_min}</span>
                        : player.cs != null
                          ? <span className="text-bxs text-black-300">{player.cs}</span>
                          : <span className="text-bxs text-black-500">—</span>}
                    </div>

                    <div className="min-w-0">
                      <div className="h-2 bg-white/5 rounded-full overflow-hidden mb-1">
                        <div
                          className={`h-full rounded-full transition-all ${isTopDmg ? "shadow-[0_0_6px_1px_currentColor]" : ""}`}
                          style={{
                            width: `${dmgPct}%`,
                            background: isTopDmg ? (isWin ? "rgba(74,201,126,1)" : "rgba(240,58,56,1)") : barColor,
                            color: isWin ? "rgba(74,201,126,0.6)" : "rgba(240,58,56,0.6)",
                          }}
                        />
                      </div>
                      <div className={`text-bxs text-right ${isTopDmg ? "text-black-100 font-bold" : "text-black-400"}`}>
                        {player.total_damage >= 1000 ? `${(player.total_damage / 1000).toFixed(1)}k` : player.total_damage}
                      </div>
                    </div>

                    <div className="text-center">
                      {player.vision_score != null
                        ? <span className="text-bxs text-black-400">{player.vision_score}</span>
                        : <span className="text-bxs text-black-500">—</span>}
                    </div>

                    <div className="flex flex-col items-start gap-0.5">
                      <div className="flex items-center gap-1">
                        {[0, 1, 2, 6].map((slotIdx) => {
                          const itemId = player.items?.[slotIdx] ?? 0
                          return (
                            <div key={`top-${slotIdx}`} className="w-[20px] h-[20px] rounded bg-black-600/50 overflow-hidden flex-shrink-0">
                              {itemId > 0 && (
                                <img
                                  src={`https://ddragon.leagueoflegends.com/cdn/${DDV}/img/item/${itemId}.png`}
                                  alt=""
                                  className="w-full h-full object-cover"
                                  onError={e => { e.target.style.display = "none" }}
                                />
                              )}
                            </div>
                          )
                        })}
                      </div>
                      <div className="flex items-center gap-1">
                        {[3, 4, 5].map((slotIdx) => {
                          const itemId = player.items?.[slotIdx] ?? 0
                          return (
                            <div key={`bot-${slotIdx}`} className="w-[20px] h-[20px] rounded bg-black-600/50 overflow-hidden flex-shrink-0">
                              {itemId > 0 && (
                                <img
                                  src={`https://ddragon.leagueoflegends.com/cdn/${DDV}/img/item/${itemId}.png`}
                                  alt=""
                                  className="w-full h-full object-cover"
                                  onError={e => { e.target.style.display = "none" }}
                                />
                              )}
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function MatchRow({ match, index, onSelect, hasCoaching, puuid, fallbackTag }) {
  const win   = match.win === true || match.win === 1
  const score = calcScore(match)
  const arena = isArenaMatch(match) && match.placement
  const mode  = queueLabel(match)
  const [imgFailed, setImgFailed] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const [activeTab, setActiveTab] = useState("geral")
  const [scoreboardData, setScoreboardData] = useState(null)
  const [scoreboardLoading, setScoreboardLoading] = useState(false)

  function handleToggleExpand(e) {
    e.stopPropagation()
    const willExpand = !expanded
    setExpanded(willExpand)

    if (willExpand && !scoreboardData && !scoreboardLoading) {
      setScoreboardLoading(true)
      fetchScoreboard(match.match_id, puuid)
        .then(data => setScoreboardData(data))
        .catch(() => setScoreboardData(null))
        .finally(() => setScoreboardLoading(false))
    }
  }

  const TABS = [
    { key: "geral", label: "Geral" },
    { key: "detalhes", label: "Detalhes" },
    { key: "runas", label: "Runas" },
  ]

  return (
    <div
      style={{ animationDelay: `${index * 40}ms`, animationFillMode: "both" }}
      className={`w-full rounded-md border-l-[3px] animate-fade-up ${
        win ? "bg-accent-green/[0.06] border-accent-green/50" : "bg-accent-red/[0.06] border-accent-red/50"
      }`}
    >
      <div className="flex items-center gap-3 px-3 py-3 group">
        <div
          onClick={onSelect}
          className="flex items-center gap-3 flex-1 min-w-0 cursor-pointer transition-all duration-200 hover:brightness-110 active:scale-[0.995]"
        >
          <div className="w-11 h-11 rounded-lg overflow-hidden border border-white/10 flex-shrink-0 bg-black-600">
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

          <div className="flex-1 min-w-0">
            <div className="flex flex-col gap-0.5">
              <span className="flex items-center gap-2 leading-tight">
                <span className={`text-bxs font-bold uppercase ${win ? "text-accent-green" : "text-accent-red"}`}>
                  {arena ? `${match.placement}º lugar` : win ? "Vitória" : "Derrota"}
                </span>
                {mode && <span className="text-bxs font-semibold text-black-300">· {mode}</span>}
              </span>
              <div className="flex items-center gap-2 flex-wrap">
              <span className="text-bs font-semibold text-black-0 truncate">{match.champion}</span>
              {match.position && (
                <span className="text-bxs text-black-300 border border-black-500 rounded px-1 py-0.5 bg-black-600">
                  {getPositionLabel(match.position, "abbrev")}
                </span>
              )}
              </div>
              {hasCoaching && (
                <span className="text-bxs font-bold text-gold-400 bg-gold-400/15 border border-gold-400/25 px-1.5 py-0.5 rounded w-fit tracking-wide">
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
              {match.ended_at && (
                <time dateTime={new Date(match.ended_at).toISOString()} title={formatDateTime(match.ended_at)} className="text-bxs text-black-400">
                  · {timeAgo(match.ended_at)}
                </time>
              )}
            </div>
          </div>

          <div className="hidden sm:flex gap-0.5 flex-shrink-0">
            {(match.items?.length ? match.items : Array(7).fill(0)).map((itemId, i) => (
              <div key={i} className="w-[24px] h-[24px] rounded bg-black-600 overflow-hidden flex-shrink-0">
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

          <div className="hidden md:flex flex-col items-end gap-0.5 flex-shrink-0 w-16">
            {match.cs_per_min > 0 && <span className="text-bxs text-black-300">{match.cs_per_min} cs/m</span>}
            {match.vision_score > 0 && <span className="text-bxs text-black-400">{match.vision_score} vis</span>}
          </div>

          {arena ? <PlacementBadge placement={match.placement} win={win} /> : <ScoreBadge score={score} />}
        </div>

        <button
          onClick={handleToggleExpand}
          className="p-1.5 rounded hover:bg-white/5 transition-colors flex-shrink-0 ml-1"
          aria-label={expanded ? "Recolher scoreboard" : "Expandir scoreboard"}
        >
          <svg
            className={`w-4 h-4 text-black-400 group-hover:text-black-200 transition-transform duration-300 ${expanded ? "rotate-180" : ""}`}
            viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </button>
      </div>

      <div
        className={`overflow-hidden transition-[max-height] duration-300 ease-in-out ${expanded ? "max-h-[1700px]" : "max-h-0"}`}
      >
        <div className="px-3 pb-5 pt-1">
          <div className="flex justify-start gap-6 mb-3">
            {TABS.map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`pb-3 text-bs font-semibold transition-colors ${
                  activeTab === tab.key
                    ? "text-black-0" // Removido border-b
                    : "text-black-400 hover:text-black-200"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
          {/* Gradiente divisor sutil entre abas e conteúdo */}
          <div className="w-full h-[1.5px] bg-gradient-to-r from-black-800/0 via-blue-400/15 to-black-800/0 scoreboard-divider mb-5" />

          {activeTab === "geral" && (
            <>
              {scoreboardLoading && (
                <div className="space-y-1.5">
                  {Array.from({ length: 10 }).map((_, i) => (
                    <div key={i} className="h-9 shimmer-bg rounded" />
                  ))}
                </div>
              )}
              {!scoreboardLoading && scoreboardData && (
                <div className="flex justify-center">
                  <InlineScoreboard data={scoreboardData} fallbackTag={fallbackTag} />
                </div>
              )}
              {!scoreboardLoading && !scoreboardData && (
                <p className="text-bxs text-black-400 text-center py-4">Não foi possível carregar o scoreboard.</p>
              )}
            </>
          )}

          {activeTab === "detalhes" && (
            <p className="text-bxs text-black-400 text-center py-6">Em breve...</p>
          )}

          {activeTab === "runas" && (
            <p className="text-bxs text-black-400 text-center py-6">Em breve...</p>
          )}
        </div>
      </div>
    </div>
  )
}

const SEASON_QUEUES = [
  { queue: "RANKED_SOLO_5x5", label: "Solo/Duo" },
  { queue: "RANKED_FLEX_SR",  label: "Flex" },
]

// Tiers acima de Diamante não têm divisão (Mestre, Grão-Mestre, Desafiante)
function tierName(entry) {
  const name = TIER_LABELS[entry.tier] ?? entry.tier
  return ["MASTER", "GRANDMASTER", "CHALLENGER"].includes(entry.tier) ? name : `${name} ${entry.division}`
}

function WinRateBar({ wins, losses, color = "#33D1C1" }) {
  const total = wins + losses
  const pct = total ? (wins / total) * 100 : 0
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-red-500/25" aria-hidden="true">
      <div className="h-full rounded-full" style={{ width: `${pct}%`, background: color }} />
    </div>
  )
}

// Temporada inteira, direto da league-v4 (não depende das partidas carregadas na página)
function SeasonRankCard({ ranked }) {
  return (
    <section className="card p-4" aria-label="Ranqueada na temporada">
      <p className="eyebrow">Temporada</p>
      <div className="mt-3 grid gap-3">
        {SEASON_QUEUES.map(({ queue, label }) => {
          const entry = ranked.find(r => r.queue === queue)
          if (!entry) {
            return (
              <div key={queue} className="flex items-center gap-3 rounded-xl bg-white/[0.02] px-3 py-3">
                <img src={rankCrest("unranked")} alt="" className="h-10 w-10 opacity-40" />
                <div>
                  <p className="text-bxs font-semibold uppercase tracking-wider text-black-400">{label}</p>
                  <p className="text-bs text-black-300">Sem ranqueada nesta temporada</p>
                </div>
              </div>
            )
          }
          const color = TIER_COLORS[entry.tier] ?? TIER_COLORS.UNRANKED
          return (
            <div key={queue} className="rounded-xl bg-white/[0.02] px-3 py-3">
              <div className="flex items-center gap-3">
                <img src={rankCrest(entry.tier)} alt="" className="h-11 w-11 flex-shrink-0" />
                <div className="min-w-0 flex-1">
                  <p className="text-bxs font-semibold uppercase tracking-wider text-black-400">{label}</p>
                  <p className="truncate text-bm font-bold" style={{ color }}>
                    {tierName(entry)} <span className="tabular font-semibold text-black-200">· {entry.lp} PDL</span>
                  </p>
                </div>
                <div className="text-right">
                  <p className="tabular text-bm font-bold text-black-0">{Number(entry.win_rate).toFixed(1)}%</p>
                  <p className="text-bxs text-black-400">vitórias</p>
                </div>
              </div>
              <div className="mt-3 flex items-center gap-3">
                <WinRateBar wins={entry.wins} losses={entry.losses} color={color} />
                <span className="tabular whitespace-nowrap text-bxs text-black-300">{entry.wins}V {entry.losses}D</span>
              </div>
              {entry.hot_streak && <p className="mt-2 text-bxs font-semibold text-red-400">Em sequência de vitórias</p>}
            </div>
          )
        })}
      </div>
    </section>
  )
}

// Forma recente: só as partidas carregadas abaixo (respeita o filtro de modo)
function RecentFormCard({ matches, modeLabel }) {
  if (!matches.length) return null
  const wins = matches.filter(m => m.win).length
  const losses = matches.length - wins
  const wr = Math.round((wins / matches.length) * 100)
  return (
    <section className="card p-4" aria-label="Partidas recentes">
      <div className="flex items-baseline justify-between gap-3">
        <p className="eyebrow">Últimas {matches.length} partidas</p>
        <span className="text-bxs text-black-400">{modeLabel}</span>
      </div>
      <div className="mt-3 flex items-end justify-between">
        <p className="tabular text-hxs font-bold text-black-0">{wr}%</p>
        <p className="tabular text-bs text-black-300">{wins}V {losses}D</p>
      </div>
      <div className="mt-2"><WinRateBar wins={wins} losses={losses} /></div>
      <div className="mt-3 flex gap-1" aria-hidden="true">
        {matches.slice(0, 20).map(m => (
          <span key={m.match_id} className={`h-2 flex-1 rounded-full ${m.win ? "bg-green-600/80" : "bg-red-500/70"}`} />
        ))}
      </div>
    </section>
  )
}

function ChampionPoolCard({ champPool }) {
  if (!champPool.length) return null
  return (
    <div className="bg-purple-200/5 rounded-md overflow-hidden w-full lg:max-w-[500px]">
      <div className="w-full h-[1.5px] bg-gradient-to-r from-black-800/0 via-blue-400/15 to-black-800/0" />
      <div className="px-4 py-4 w-full">
        <p className="text-bm font-semibold text-black-200 mb-4 px-1">Desempenho do Campeão</p>

        {/* Header das colunas */}
        <div className="flex items-center gap-3 px-1 mb-2">
          <div className="w-10 flex-shrink-0" />
          <div className="flex-1 min-w-0" />
          <span className="w-12 text-center text-bxs text-black-400 uppercase tracking-wider">KDA</span>
          <span className="w-12 text-center text-bxs text-black-400 uppercase tracking-wider">CS/m</span>
          <span className="w-14 text-center text-bxs text-black-400 uppercase tracking-wider">Partidas</span>
          <span className="w-12 text-center text-bxs text-black-400 uppercase tracking-wider">WR</span>
        </div>

        <div className="w-full h-[1px] bg-gradient-to-r from-black-800/0 via-white/5 to-black-800/0 mb-1" />

        <div className="flex flex-col w-full">
          {champPool.map(champ => {
            const wrColor = champ.wr >= 60 ? "#3DD68C" : champ.wr >= 50 ? "#FFD147" : "#FF5A6E"
            const killsAvg = (champ.kills / champ.games).toFixed(1)
            const deathsAvg = (champ.deaths / champ.games).toFixed(1)
            const assistsAvg = (champ.assists / champ.games).toFixed(1)
            return (
              <div key={champ.champion} className="flex items-center gap-3 px-1 py-3 hover:bg-white/[0.02] transition-colors rounded champion-pool-row">
                <div className="w-10 h-10 rounded overflow-hidden border border-white/10 flex-shrink-0 bg-black-600">
                  <img
                    src={`https://ddragon.leagueoflegends.com/cdn/${DDV}/img/champion/${champ.champion}.png`}
                    alt={champ.champion} className="w-full h-full object-cover"
                    onError={e => { e.target.style.display = "none" }}
                  />
                </div>
                <div className="flex-1 min-w-0 pl-1">
                  <p className="text-[14px] font-bold text-black-100 leading-tight">{champ.kda}</p>
                  <p className="text-bxs text-black-400 leading-tight mt-0.5 truncate">{killsAvg} / {deathsAvg} / {assistsAvg}</p>
                </div>
                <span className="w-12 text-center text-[13px] text-black-200">{champ.cs_per_min}</span>
                <span className="w-14 text-center text-[13px] text-black-200">{champ.games}</span>
                <span className="w-12 text-center text-[13px] font-bold" style={{ color: wrColor }}>{champ.wr}%</span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default function SummonerProfileScreen() {
  const { name, tag } = useParams()
  const navigate      = useNavigate()
  const location      = useLocation()
  const [data, setData]               = useState(null)
  const [loading, setLoading]         = useState(true)
  const [refreshing, setRefreshing]   = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [coachingStatus, setCoachingStatus] = useState({})
  const [queue, setQueue]             = useState("all")
  const [listLoading, setListLoading] = useState(false)
  const [listError, setListError]     = useState("")

  const nick = `${decodeURIComponent(name)}#${decodeURIComponent(tag)}`
  const live = useLiveGame(nick)
  const [liveOpen, setLiveOpen] = useState(false)

  useEffect(() => {
    setLoading(true)
    setQueue("all")
    setListError("")
    fetchMatches(nick, { start: 0, count: MATCHES_PAGE_SIZE })
      .then(d => {
        setData(d)
        setLoading(false)
        const matchIds = (d.matches ?? []).map(m => m.match_id)
        fetchCoachingStatus(matchIds, nick).then(setCoachingStatus).catch(error => {
          console.error("Erro ao buscar status de coaching:", error)
        })
      })
      .catch(e => {
        navigate("/", { replace: true, state: { error: e.message || "Invocador nao encontrado." } })
      })
  }, [navigate, nick])

  if (loading) return <ProfileSkeleton />

  const matches   = Array.isArray(data) ? data : (data?.matches ?? [])
  const rawSummoner = data?.summoner ?? nick
  const summonerName = rawSummoner.includes("#") ? rawSummoner.split("#")[0] : rawSummoner
  const rankStr   = data?.rank ?? "Unranked"
  const ranked    = data?.ranked ?? []
  const soloEntry = ranked.find(r => r.queue === "RANKED_SOLO_5x5")
  const rankChip  = soloEntry ? `${tierName(soloEntry)} · ${soloEntry.lp} PDL` : (rankStr === "Unranked" ? "Sem ranking" : rankStr)
  const modeLabel = QUEUE_FILTERS.find(f => f.id === queue)?.label ?? "Todas"
  const tier      = parseTier(rankStr)
  const tierColor = TIER_COLORS[tier] ?? TIER_COLORS.UNRANKED
  const champPool = buildChampionPool(matches)
  const topChamp  = champPool.length > 0 ? champPool[0].champion : null

  const avgKDA    = matches.length > 0 ? (matches.reduce((sum, m) => sum + (m.kills + m.assists) / Math.max(m.deaths, 1), 0) / matches.length).toFixed(1) : "0.0"
  const avgScore  = matches.length > 0 ? Math.round(matches.reduce((sum, m) => sum + calcScore(m), 0) / matches.length) : 0
  const avgKP     = matches.length > 0 ? Math.round(matches.reduce((sum, m) => sum + (m.kill_participation_pct ?? 0), 0) / matches.length) : 0
  const avgCS     = matches.length > 0 ? (matches.reduce((sum, m) => sum + (m.cs_per_min ?? 0), 0) / matches.length).toFixed(1) : "0.0"
  const avgVision = matches.length > 0 ? Math.round(matches.reduce((sum, m) => sum + (m.vision_score ?? 0), 0) / matches.length) : 0

  function handleSelect(match, index) {
    const puuid = data?.puuid ?? ""
    const url = `/match/${encodeURIComponent(match.match_id)}${puuid ? `?puuid=${encodeURIComponent(puuid)}` : ""}`
    navigate(url, {
      state: { player: { nick }, rank: rankStr, matchStats: match, matchIndex: index, puuid, from: location.pathname },
    })
  }

  function handleQueueChange(nextQueue) {
    if (nextQueue === queue || listLoading) return
    setQueue(nextQueue)
    setListLoading(true)
    setListError("")
    fetchMatches(nick, { start: 0, count: MATCHES_PAGE_SIZE, queue: nextQueue })
      .then(d => {
        setData(d)
        const matchIds = (d.matches ?? []).map(m => m.match_id)
        fetchCoachingStatus(matchIds, nick).then(status => setCoachingStatus(prev => ({ ...prev, ...status }))).catch(() => {})
      })
      .catch(e => setListError(e.message || "Não foi possível carregar as partidas."))
      .finally(() => setListLoading(false))
  }

  function handleRefresh() {
    setRefreshing(true)
    refreshMatches(nick, { start: 0, count: MATCHES_PAGE_SIZE, queue })
      .then(d => {
        setData(d)
        const matchIds = (d.matches ?? []).map(m => m.match_id)
        fetchCoachingStatus(matchIds, nick).then(setCoachingStatus).catch(error => {
          console.error("Erro ao atualizar status de coaching:", error)
        })
      })
      .catch(error => {
        console.error("Erro ao atualizar partidas:", error)
      })
      .finally(() => setRefreshing(false))
  }

  function handleLoadMore() {
    if (loadingMore || !data?.has_more) return

    setLoadingMore(true)
    fetchMatches(nick, { start: data?.next_offset ?? matches.length, count: MATCHES_PAGE_SIZE, queue })
      .then(d => {
        setData(prev => {
          if (!prev) return d
          return {
            ...prev,
            ...d,
            matches: mergeMatches(prev.matches ?? [], d.matches ?? []),
          }
        })

        const matchIds = (d.matches ?? []).map(m => m.match_id)
        if (matchIds.length > 0) {
          fetchCoachingStatus(matchIds, nick)
            .then(status => setCoachingStatus(prev => ({ ...prev, ...status })))
            .catch(error => {
              console.error("Erro ao buscar status de coaching das partidas antigas:", error)
            })
        }
      })
      .catch(error => {
        console.error("Erro ao carregar mais partidas:", error)
      })
      .finally(() => setLoadingMore(false))
  }

  return (
    <div>
      <div className="relative mb-6 overflow-hidden border-b border-white/[0.06] bg-black-800">
        {topChamp && (
          <div className="absolute inset-0 overflow-hidden">
            <img
              src={`https://ddragon.leagueoflegends.com/cdn/img/champion/splash/${topChamp}_0.jpg`}
              alt=""
              className="h-full w-full object-cover object-[center_20%] opacity-35"
              onError={e => { e.target.style.display = "none" }}
            />
            <div className="absolute inset-0 bg-gradient-to-r from-black-800 via-black-800/80 to-black-800/30" />
            <div className="absolute inset-0 bg-gradient-to-t from-black-700 via-transparent to-transparent" />
          </div>
        )}
        <div className="relative z-10 mx-auto max-w-[1200px] px-4 pb-8 pt-10 md:pt-14">
          <div className="flex items-center gap-4 sm:gap-6">
            <div className="relative flex-shrink-0">
              <div className="h-[72px] w-[72px] overflow-hidden rounded-2xl ring-2 ring-white/10 sm:h-[92px] sm:w-[92px]">
                <img
                  src={`https://ddragon.leagueoflegends.com/cdn/${DDV}/img/profileicon/${data?.profile_icon ?? 29}.png`}
                  alt=""
                  className="h-full w-full object-cover"
                />
              </div>
              {tier !== "UNRANKED" && (
                <img src={rankCrest(tier)} alt="" className="absolute -bottom-2 -right-2 h-9 w-9 drop-shadow-lg" />
              )}
            </div>

            <div className="min-w-0 flex-1">
              <p className="eyebrow">Perfil · BR</p>
              <h1 className="mt-1 truncate font-display text-[24px] font-bold leading-tight text-black-0 sm:text-[34px]">
                {summonerName}<span className="font-medium text-black-400">#{decodeURIComponent(tag)}</span>
              </h1>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <span className="rounded-full px-3 py-1 text-bxs font-bold uppercase tracking-wider" style={{ color: tierColor, backgroundColor: `${tierColor}1F` }}>
                  {rankChip}
                </span>
                <LiveBadge live={live} open={liveOpen} onToggle={() => setLiveOpen(open => !open)} />
                <button
                  onClick={handleRefresh}
                  disabled={refreshing}
                  className="inline-flex min-h-[32px] items-center gap-2 rounded-full border border-white/10 px-3 text-bxs font-semibold text-black-100 transition hover:border-white/25 disabled:opacity-50"
                >
                  <span className={`h-1.5 w-1.5 rounded-full bg-purple-400 ${refreshing ? "animate-spin" : "animate-pulse-dot"}`} />
                  {refreshing ? "Atualizando..." : "Atualizar partidas"}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-[1200px] mx-auto px-4 pb-12">
        {liveOpen && <LiveGameCard live={live} />}
        {matches.length > 0 && (
          <div className="flex gap-3 overflow-x-auto pb-2 mb-4 scrollbar-hide">
            <StatCard label="KDA" value={avgKDA} delay={0} />
            <StatCard label="MVP Score" value={avgScore} delay={50} />
            <StatCard label="KP" value={`${avgKP}%`} delay={100} />
            <StatCard label="CS/min" value={avgCS} delay={150} />
            <StatCard label="Visão" value={avgVision} delay={200} />
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          <div className="lg:col-span-4 flex flex-col gap-3">
            <SeasonRankCard ranked={ranked} />
            <RecentFormCard matches={matches} modeLabel={modeLabel} />
            <ChampionPoolCard champPool={champPool} />
          </div>

          <div className="lg:col-span-8 flex flex-col gap-1.5">
            <div className="mb-2 flex flex-wrap gap-1.5" role="tablist" aria-label="Modo de jogo">
              {QUEUE_FILTERS.map(f => (
                <button
                  key={f.id}
                  type="button"
                  role="tab"
                  aria-selected={queue === f.id}
                  onClick={() => handleQueueChange(f.id)}
                  disabled={listLoading}
                  className={`chip ${queue === f.id ? "chip-active" : ""} disabled:cursor-wait`}
                >
                  {f.label}
                </button>
              ))}
            </div>
            {listLoading && (
              <div className="space-y-1.5" aria-busy="true">
                {Array.from({ length: 6 }).map((_, i) => <div key={i} className="h-[72px] shimmer-bg rounded-md" />)}
              </div>
            )}
            {!listLoading && listError && (
              <p className="py-10 text-center text-bs text-red-400">{listError}</p>
            )}
            {!listLoading && !listError && matches.map((match, i) => (
              <MatchRow
                key={match.match_id}
                match={match}
                index={i}
                onSelect={() => handleSelect(match, i)}
                hasCoaching={coachingStatus[match.match_id]?.status === "ready"}
                puuid={data?.puuid}
                fallbackTag={decodeURIComponent(tag)}
              />
            ))}
            {!listLoading && !listError && matches.length === 0 && (
              <div className="text-center py-12 text-black-400 text-bs">
                {queue === "all" ? "Nenhuma partida encontrada." : `Nenhuma partida recente de ${modeLabel}.`}
              </div>
            )}
            {!listLoading && matches.length > 0 && data?.has_more && (
              <div className="pt-3 flex justify-center">
                <button
                  onClick={handleLoadMore}
                  disabled={loadingMore}
                  className="rounded-full border border-white/10 bg-black-800 px-4 py-2 text-sm font-semibold text-blue-300 transition-colors hover:bg-black-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {loadingMore ? "Carregando..." : "Ver mais partidas"}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    {/* Ajuste para telas muito pequenas */}
    <style>{`
      @media (max-width: 350px) {
        .scoreboard-player-row > div, .scoreboard-player-row { gap: 2vw !important; padding-left: 2vw !important; padding-right: 2vw !important; }
        .scoreboard-player-row p, .scoreboard-player-row span { font-size: 10px !important; }
        .scoreboard-items-row { max-width: 100vw !important; gap: 1vw !important; }
      }
      @media (max-width: 330px) {
        .scoreboard-player-row { flex-wrap: wrap !important; gap: 1vw !important; }
        .scoreboard-player-row > div { min-width: 40px !important; }
        .scoreboard-items-row { max-width: 98vw !important; }
      }
      @media (max-width: 320px) {
        .scoreboard-player-row > div, .scoreboard-player-row { gap: 1vw !important; padding-left: 1vw !important; padding-right: 1vw !important; }
        .scoreboard-player-row p, .scoreboard-player-row span { font-size: 9px !important; }
        .scoreboard-items-row { max-width: 96vw !important; gap: 0.5vw !important; }
      }
      /* Scrollbar horizontal mais visível */
      .champion-pool-row::-webkit-scrollbar {
        height: 10px;
      }
      .champion-pool-row::-webkit-scrollbar-thumb {
        background: #33D1C188;
        border-radius: 6px;
      }
      .champion-pool-row::-webkit-scrollbar-track {
        background: #090D13;
      }
    `}</style>
    </div>
  )
}

function ProfileSkeleton() {
  return (
    <div>
      <div className="bg-black-800 rounded-b-[32px] border-b border-white/5 glow-purple mb-4">
        <div className="max-w-[1200px] mx-auto px-4 py-6">
          <div className="flex items-center gap-5">
            <div className="w-[70px] h-[70px] rounded-lg shimmer-bg" />
            <div className="flex-1 space-y-2">
              <div className="h-5 w-48 shimmer-bg rounded" />
              <div className="h-3 w-24 shimmer-bg rounded" />
            </div>
          </div>
        </div>
      </div>
      <div className="max-w-[1200px] mx-auto px-4">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          <div className="lg:col-span-4 space-y-3">
            <div className="h-32 shimmer-bg rounded-md" />
            <div className="h-48 shimmer-bg rounded-md" />
          </div>
          <div className="lg:col-span-8 space-y-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-16 shimmer-bg rounded-md" />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
