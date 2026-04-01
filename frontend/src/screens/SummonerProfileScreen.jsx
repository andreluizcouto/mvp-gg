import { useState, useEffect } from "react"
import { useParams, useNavigate, useLocation } from "react-router-dom"
import { fetchMatches, fetchCoachingStatus, refreshMatches, fetchScoreboard } from "../services/api"
import { DDV, getPositionLabel } from "../services/constants"
import { TIER_COLORS, parseTier, calcScore, buildChampionPool, buildSummonerProfilePath } from "../services/utils"

const MATCHES_PAGE_SIZE = 10

function mergeMatches(existing, incoming) {
  const seen = new Set(existing.map(match => match.match_id))
  const additions = incoming.filter(match => !seen.has(match.match_id))
  return [...existing, ...additions]
}

function getRankLabel(score) {
  if (score >= 100) return { label: "MVP", color: "#F4C874" }
  if (score >= 90)  return { label: "Top 3", color: "#A6B0F2" }
  if (score >= 75)  return { label: "4th-5th", color: "#7989EC" }
  if (score >= 60)  return { label: "6th-7th", color: "#9B9C9E" }
  return { label: "8th-10th", color: "#686B6E" }
}

function ScoreBadge({ score }) {
  const isElite = score >= 90
  const isGood  = score >= 75
  const isFair  = score >= 60
  const color  = isElite ? "#A6B0F2" : isGood ? "#7989EC" : isFair ? "#9B9C9E" : "#686B6E"
  const bg     = isElite ? "#7989EC20" : isGood ? "#4D62E512" : isFair ? "#7989EC0A" : "#363A3D08"
  const border = isElite ? "#7989EC55" : isGood ? "#7989EC33" : "transparent"
  const rank   = getRankLabel(score)

  return (
    <div
      className={`min-w-[44px] h-[48px] rounded-lg flex flex-col items-center justify-center flex-shrink-0 ${isElite ? "scoreGlow" : ""}`}
      style={{ color, background: bg, border: `1px solid ${border}` }}
    >
      <span className="text-[15px] font-extrabold leading-none">{score}</span>
      <span className="text-[7px] tracking-wider uppercase mt-0.5" style={{ color: rank.color, opacity: 0.8 }}>{rank.label}</span>
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
          const teamColor = isWin ? "#4AC97E" : "#F03A38"
          const teamBg = isWin ? "rgba(74,201,126,0.08)" : "rgba(240,58,56,0.08)"
          const barColor = isWin ? "rgba(74,201,126,0.7)" : "rgba(240,58,56,0.7)"
          const sideLabel = isBlue ? "Lado Azul" : "Lado Vermelho"
          const resultLabel = isWin ? "Vitória" : "Derrota"
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
                  <span className="text-[11px] text-black-400">({sideLabel})</span>
                </div>
                <span className="font-mono text-[12px] text-black-200">{teamKills} / {teamDeaths} / {teamAssists}</span>
              </div>

              <div className="w-full h-[1.5px] bg-gradient-to-r from-black-800/0 via-blue-400/15 to-black-800/0 scoreboard-divider" />

              <div className="grid grid-cols-[minmax(170px,1fr)_88px_56px_56px_minmax(120px,1fr)_56px_120px] items-center gap-1.5 px-3 py-1.5 bg-black-900/30">
                <div className="text-[10px] text-black-400 uppercase tracking-wider">Jogador</div>
                <div className="text-center text-[10px] text-black-400 uppercase tracking-wider">KDA</div>
                <div className="text-center text-[10px] text-black-400 uppercase tracking-wider">KP</div>
                <div className="text-center text-[10px] text-black-400 uppercase tracking-wider">CS</div>
                <div className="text-[10px] text-black-400 uppercase tracking-wider">Dano</div>
                <div className="text-center text-[10px] text-black-400 uppercase tracking-wider">Vis</div>
                <div className="text-left text-[10px] text-black-400 uppercase tracking-wider">Items</div>
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
                    className="grid grid-cols-[minmax(170px,1fr)_88px_56px_56px_minmax(120px,1fr)_56px_120px] items-center gap-1.5 px-3 py-2 hover:bg-white/[0.02] transition-colors"
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
                            className="text-[11px] text-white/85 truncate hover:text-blue-400 hover:underline cursor-pointer transition-colors block max-w-full text-left"
                            onClick={e => e.stopPropagation()}
                          >
                            {player.summoner_name || player.champion}
                          </a>
                        ) : (
                          <p className="text-[11px] text-white/85 truncate">{player.summoner_name || player.champion}</p>
                        )}

                        {player.position && (
                          <div className="mt-0.5">
                            <span className="text-[9px] text-black-400 bg-black-600/80 rounded px-1 py-0.5 inline-block">
                              {getPositionLabel(player.position, "short")}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="text-center">
                      <span className="text-[11px] text-white/90">{player.kills}</span>
                      <span className="text-[10px] text-white/25"> / </span>
                      <span className="text-[11px] text-red-400">{player.deaths}</span>
                      <span className="text-[10px] text-white/25"> / </span>
                      <span className="text-[11px] text-white/90">{player.assists}</span>
                    </div>

                    <div className="text-center">
                      {kpValue != null
                        ? <span className="text-[10px] text-black-300">{kpValue}%</span>
                        : <span className="text-[10px] text-black-500">—</span>}
                    </div>

                    <div className="text-center">
                      {player.cs_per_min
                        ? <span className="text-[10px] text-black-300">{player.cs_per_min}</span>
                        : player.cs != null
                          ? <span className="text-[10px] text-black-300">{player.cs}</span>
                          : <span className="text-[10px] text-black-500">—</span>}
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
                      <div className={`text-[9px] text-right ${isTopDmg ? "text-black-100 font-bold" : "text-black-400"}`}>
                        {player.total_damage >= 1000 ? `${(player.total_damage / 1000).toFixed(1)}k` : player.total_damage}
                      </div>
                    </div>

                    <div className="text-center">
                      {player.vision_score != null
                        ? <span className="text-[10px] text-black-400">{player.vision_score}</span>
                        : <span className="text-[10px] text-black-500">—</span>}
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
              <span className={`text-bxs font-bold uppercase leading-tight ${win ? "text-accent-green" : "text-accent-red"}`}>
                {win ? "Vitoria" : "Derrota"}
              </span>
              <div className="flex items-center gap-2 flex-wrap">
              <span className="text-bs font-semibold text-black-0 truncate">{match.champion}</span>
              {match.position && (
                <span className="text-[9px] text-black-300 border border-black-500 rounded px-1 py-0.5 bg-black-600">
                  {getPositionLabel(match.position, "abbrev")}
                </span>
              )}
              </div>
              {hasCoaching && (
                <span className="text-[10px] font-bold text-gold-400 bg-gold-400/15 border border-gold-400/25 px-1.5 py-0.5 rounded w-fit tracking-wide">
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

          <ScoreBadge score={score} />
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

function RankedCard({ rankStr, wins, losses, tier, tierColor }) {
  const total = wins + losses
  const wr    = total > 0 ? Math.round(wins / total * 100) : 0

  return (
    <div className="bg-purple-200/5 rounded-md overflow-hidden relative">
      <div className="w-full h-[1.5px] bg-gradient-to-r from-black-800/0 via-blue-400/15 to-black-800/0" />
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
          <span className="w-12 text-center text-[9px] text-black-400 uppercase tracking-wider">KDA</span>
          <span className="w-12 text-center text-[9px] text-black-400 uppercase tracking-wider">CS/m</span>
          <span className="w-14 text-center text-[9px] text-black-400 uppercase tracking-wider">Partidas</span>
          <span className="w-12 text-center text-[9px] text-black-400 uppercase tracking-wider">WR</span>
        </div>

        <div className="w-full h-[1px] bg-gradient-to-r from-black-800/0 via-white/5 to-black-800/0 mb-1" />

        <div className="flex flex-col w-full">
          {champPool.map(champ => {
            const wrColor = champ.wr >= 60 ? "#4AC97E" : champ.wr >= 50 ? "#FFD147" : "#F03A38"
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
                  <p className="text-[10px] text-black-400 leading-tight mt-0.5">{killsAvg} / {deathsAvg} / {assistsAvg}</p>
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

  const nick = `${decodeURIComponent(name)}#${decodeURIComponent(tag)}`

  useEffect(() => {
    setLoading(true)
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
  const wins      = data?.wins   ?? matches.filter(m => m.win).length
  const losses    = data?.losses ?? matches.filter(m => !m.win).length
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

  function handleRefresh() {
    setRefreshing(true)
    refreshMatches(nick, { start: 0, count: MATCHES_PAGE_SIZE })
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
    fetchMatches(nick, { start: data?.next_offset ?? matches.length, count: MATCHES_PAGE_SIZE })
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
      <div className="bg-black-800 rounded-b-[32px] border-b border-white/5 overflow-hidden glow-purple relative mb-4 md:pt-2">
        {topChamp && (
          <div className="absolute inset-0 opacity-10 overflow-hidden">
            <img
              src={`https://ddragon.leagueoflegends.com/cdn/img/champion/splash/${topChamp}_0.jpg`}
              alt=""
              className="w-full h-full object-cover object-top"
              onError={e => { e.target.style.display = "none" }}
            />
          </div>
        )}
        <div className="max-w-[1600px] mx-auto px-4 py-4 relative z-10">
          <div className="flex items-center gap-5">
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

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <span className="text-bxl lg:text-hxs text-black-0 font-semibold truncate max-w-[280px]">
                  {summonerName}<span className="text-black-300 font-medium">#{tag}</span>
                </span>
                <div className="text-bxs font-extrabold rounded-md px-1.5 py-0.5 bg-lime-800 text-black-100">BR</div>
                <button
                  onClick={handleRefresh}
                  disabled={refreshing}
                  className="flex items-center gap-1.5 rounded-md px-2.5 py-1 text-bxs font-semibold text-blue-100/90 border border-white/5 bg-purple-200/10 hover:bg-purple-200/[0.15] transition-all duration-200 disabled:opacity-50"
                >
                  <div className={`h-1.5 w-1.5 bg-yellow-400 rounded-full ${refreshing ? "animate-spin" : "animate-pulse-dot"}`} />
                  {refreshing ? "Atualizando..." : "Atualizar"}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-[1600px] mx-auto px-4 pb-12">
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
          <div className="lg:col-span-3 flex flex-col gap-3">
            <RankedCard rankStr={rankStr} wins={wins} losses={losses} tier={tier} tierColor={tierColor} />
            <ChampionPoolCard champPool={champPool} />
          </div>

          <div className="lg:col-span-9 flex flex-col gap-1.5">
            {matches.map((match, i) => (
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
            {matches.length === 0 && (
              <div className="text-center py-12 text-black-400 text-bs">
                Nenhuma partida encontrada.
              </div>
            )}
            {matches.length > 0 && data?.has_more && (
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
        background: #7989EC88;
        border-radius: 6px;
      }
      .champion-pool-row::-webkit-scrollbar-track {
        background: #0D0F10;
      }
    `}</style>
    </div>
  )
}

function ProfileSkeleton() {
  return (
    <div>
      <div className="bg-black-800 rounded-b-[32px] border-b border-white/5 glow-purple mb-4">
        <div className="max-w-[1600px] mx-auto px-4 py-6">
          <div className="flex items-center gap-5">
            <div className="w-[70px] h-[70px] rounded-lg shimmer-bg" />
            <div className="flex-1 space-y-2">
              <div className="h-5 w-48 shimmer-bg rounded" />
              <div className="h-3 w-24 shimmer-bg rounded" />
            </div>
          </div>
        </div>
      </div>
      <div className="max-w-[1600px] mx-auto px-4">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          <div className="lg:col-span-3 space-y-3">
            <div className="h-32 shimmer-bg rounded-md" />
            <div className="h-48 shimmer-bg rounded-md" />
          </div>
          <div className="lg:col-span-9 space-y-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-16 shimmer-bg rounded-md" />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
