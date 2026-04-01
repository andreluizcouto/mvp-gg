import { useState, useEffect } from "react"
import { useParams, useLocation, useNavigate, useSearchParams } from "react-router-dom"
import CoachingSection from "../components/CoachingSection"
import AnalysisStatusBlock from "../components/AnalysisStatusBlock"
import { fetchCoachingAnalysis, fetchScoreboard, fetchMatchDetails } from "../services/api"
import { DDV, getPositionLabel } from "../services/constants"
import { calcScore, buildSummonerProfilePath } from "../services/utils"

// ── ScoreBadge (identical to SummonerProfileScreen) ────────
function getRankLabel(score) {
  if (score >= 100) return { label: "MVP",     color: "#F4C874" }
  if (score >= 90)  return { label: "Top 3",   color: "#A6B0F2" }
  if (score >= 75)  return { label: "4th-5th", color: "#7989EC" }
  if (score >= 60)  return { label: "6th-7th", color: "#9B9C9E" }
  return              { label: "8th-10th",     color: "#686B6E" }
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

// ── InlineScoreboard (identical to SummonerProfileScreen) ──
function InlineScoreboard({ data, fallbackTag }) {
  if (!data?.teams) return null

  return (
    <div className="rounded-lg overflow-x-auto border border-black-800/40">
      <div className="min-w-[900px]">
      {data.teams.map((team, ti) => {
        const isWin      = team.win
        const teamColor  = isWin ? "#4AC97E" : "#F03A38"
        const teamBg     = isWin ? "rgba(74,201,126,0.08)" : "rgba(240,58,56,0.08)"
        const barColor   = isWin ? "rgba(74,201,126,0.7)"  : "rgba(240,58,56,0.7)"
        const sideLabel  = team.side === "blue" ? "Lado Azul" : "Lado Vermelho"
        const maxDmg     = Math.max(...team.players.map(p => p.total_damage), 1)
        const teamKills  = team.players.reduce((s, p) => s + (p.kills   || 0), 0)
        const teamDeaths = team.players.reduce((s, p) => s + (p.deaths  || 0), 0)
        const teamAssist = team.players.reduce((s, p) => s + (p.assists || 0), 0)

        return (
          <div key={ti}>
            <div className="flex items-center justify-between px-4 py-2" style={{ background: teamBg }}>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-[11px] uppercase tracking-wider" style={{ color: teamColor }}>
                  {isWin ? "Vitória" : "Derrota"}
                </span>
                <span className="text-[10px] text-black-400">({sideLabel})</span>
              </div>
              <span className="font-mono text-[11px] text-black-200">
                {teamKills} / {teamDeaths} / {teamAssist}
              </span>
            </div>

            <div className="w-full h-[1.5px] bg-gradient-to-r from-black-800/0 via-blue-400/15 to-black-800/0 scoreboard-divider" />

            <div className="grid grid-cols-[32px_112px_80px_48px_56px_minmax(180px,1fr)_40px_180px] items-center gap-2 px-3 py-1 bg-black-900/30">
              <div />
              <div className="text-[9px] text-black-400 uppercase tracking-wider">Jogador</div>
              <div className="text-center text-[9px] text-black-400 uppercase tracking-wider">KDA</div>
              <div className="text-center text-[9px] text-black-400 uppercase tracking-wider">KP</div>
              <div className="text-center text-[9px] text-black-400 uppercase tracking-wider">CS</div>
              <div className="text-[9px] text-black-400 uppercase tracking-wider">Dano</div>
              <div className="text-center text-[9px] text-black-400 uppercase tracking-wider">Vis</div>
              <div className="text-center text-[9px] text-black-400 uppercase tracking-wider">Items</div>
            </div>

            <div className="w-full h-[1.5px] bg-gradient-to-r from-black-800/0 via-blue-400/15 to-black-800/0 scoreboard-divider" />

            {team.players.map((player, pi) => {
              const isTarget = player.is_target
              const dmgPct   = ((player.total_damage / maxDmg) * 100).toFixed(0)
              const isTopDmg = player.total_damage === maxDmg
              const profilePath = buildSummonerProfilePath(player.summoner_name, fallbackTag)

              return (
                <div
                  key={pi}
                  className="grid grid-cols-[32px_112px_80px_48px_56px_minmax(180px,1fr)_40px_180px] items-center gap-2 px-3 py-2 hover:bg-white/[0.02] transition-colors"
                  style={isTarget ? { background: "rgba(200,155,60,0.08)", borderLeft: "2px solid rgba(200,155,60,0.5)" } : {}}
                >
                  <div className="w-8 h-8 rounded overflow-hidden border border-white/10 flex-shrink-0 bg-black-600">
                    <img
                      src={`https://ddragon.leagueoflegends.com/cdn/${DDV}/img/champion/${player.champion}.png`}
                      alt={player.champion}
                      className="w-full h-full object-cover"
                      onError={e => { e.target.style.display = "none" }}
                    />
                  </div>

                  <div className="min-w-0">
                    {profilePath ? (
                      <a
                        href={profilePath}
                        className="text-[11px] text-white/80 truncate hover:text-blue-400 hover:underline cursor-pointer transition-colors block max-w-full text-left"
                        onClick={e => e.stopPropagation()}
                      >
                        {player.summoner_name || player.champion}
                      </a>
                    ) : (
                      <p className="text-[11px] text-white/80 truncate">
                        {player.summoner_name || player.champion}
                      </p>
                    )}
                    {player.position && (
                      <span className="text-[9px] text-black-400 bg-black-600/80 rounded px-1 py-0.5 inline-block mt-0.5">
                        {getPositionLabel(player.position, "short")}
                      </span>
                    )}
                  </div>

                  <div className="text-center">
                    <span className="text-[11px] text-white/90">{player.kills}</span>
                    <span className="text-[10px] text-white/25"> / </span>
                    <span className="text-[11px] text-red-400">{player.deaths}</span>
                    <span className="text-[10px] text-white/25"> / </span>
                    <span className="text-[11px] text-white/90">{player.assists}</span>
                  </div>

                  <div className="text-center">
                    {player.kill_participation_pct != null
                      ? <span className="text-[10px] text-black-300">{player.kill_participation_pct}%</span>
                      : <span className="text-[10px] text-black-500">—</span>}
                  </div>

                  <div className="text-center">
                    {player.cs_per_min
                      ? <span className="text-[10px] text-black-300">{player.cs_per_min} cs/m</span>
                      : player.cs != null
                        ? <span className="text-[10px] text-black-300">{player.cs} cs</span>
                        : <span className="text-[10px] text-black-500">—</span>}
                  </div>

                  <div className="flex items-center gap-1.5">
                    <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${isTopDmg ? "shadow-[0_0_8px_2px_currentColor]" : ""}`}
                        style={{
                          width: `${dmgPct}%`,
                          background: isTopDmg ? (isWin ? "rgba(74,201,126,1)" : "rgba(240,58,56,1)") : barColor,
                          color: isWin ? "rgba(74,201,126,0.6)" : "rgba(240,58,56,0.6)",
                        }}
                      />
                    </div>
                    <span className={`text-[9px] w-9 text-right flex-shrink-0 ${isTopDmg ? "text-black-100 font-bold" : "text-black-400"}`}>
                      {player.total_damage >= 1000
                        ? `${(player.total_damage / 1000).toFixed(1)}k`
                        : player.total_damage}
                    </span>
                  </div>

                  <div className="text-center">
                    {player.vision_score != null
                      ? <span className="text-[10px] text-black-400">{player.vision_score}</span>
                      : <span className="text-[10px] text-black-500">—</span>}
                  </div>

                  <div className="flex justify-center gap-0.5">
                    {(player.items ?? []).map((itemId, ii) => (
                      <div key={ii} className="w-6 h-6 rounded bg-black-600/50 overflow-hidden flex-shrink-0">
                        {itemId > 0 && (
                          <img
                            src={`https://ddragon.leagueoflegends.com/cdn/${DDV}/img/item/${itemId}.png`}
                            alt=""
                            className="w-full h-full object-cover"
                            onError={e => { e.target.style.display = "none" }}
                          />
                        )}
                      </div>
                    ))}
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

// ── champion combo helper ───────────────────────────────────
// Note: COMBO_ROLE and getComboAlly removed — Detalhes tab is disabled (D-11)

const TABS = [
  { key: "geral",    label: "Geral",     disabled: false },
  { key: "detalhes", label: "Detalhes",  disabled: true  },
  { key: "runas",    label: "Runas",     disabled: true  },
]

function buildMockMatchPayload(matchId, puuid) {
  const safeMatchId = matchId || "BR1_MOCK_0001"
  const safePuuid = puuid || "mock-puuid-target"
  const targetNick = "natus vincere#navi3"

  const bluePlayers = [
    { puuid: safePuuid, summoner_name: targetNick, champion: "Jinx", position: "BOTTOM", kills: 14, deaths: 5, assists: 7, cs: 208, cs_per_min: 8.0, total_damage: 33600, gold_earned: 15100, vision_score: 7, items: [6671, 3094, 3031, 3036, 3006, 3072, 3363], kill_participation_pct: 64, is_target: true },
    { puuid: "mock-blue-2", summoner_name: "just me#ana", champion: "Ahri", position: "MIDDLE", kills: 8, deaths: 7, assists: 17, cs: 146, cs_per_min: 5.6, total_damage: 27100, gold_earned: 12900, vision_score: 25, items: [6655, 3020, 3165, 4645, 3089, 3102, 3363], kill_participation_pct: 58, is_target: false },
    { puuid: "mock-blue-3", summoner_name: "Sirena#l1l", champion: "Nami", position: "UTILITY", kills: 2, deaths: 3, assists: 22, cs: 29, cs_per_min: 1.1, total_damage: 4700, gold_earned: 9300, vision_score: 65, items: [2065, 3222, 6617, 3107, 3504, 3190, 3364], kill_participation_pct: 56, is_target: false },
  ]

  const redPlayers = [
    { puuid: "mock-red-1", summoner_name: "DAVI O GRANDE#BR1", champion: "Aatrox", position: "TOP", kills: 3, deaths: 9, assists: 7, cs: 165, cs_per_min: 6.3, total_damage: 20500, gold_earned: 11100, vision_score: 7, items: [3153, 3046, 3071, 3053, 6333, 0, 3363], kill_participation_pct: 41, is_target: false },
    { puuid: "mock-red-2", summoner_name: "VkGhost#br1", champion: "Vex", position: "MIDDLE", kills: 7, deaths: 7, assists: 11, cs: 200, cs_per_min: 7.7, total_damage: 23600, gold_earned: 12100, vision_score: 28, items: [6655, 3020, 4645, 3089, 3135, 3157, 3363], kill_participation_pct: 51, is_target: false },
    { puuid: "mock-red-3", summoner_name: "Krauss#sup", champion: "Pyke", position: "UTILITY", kills: 2, deaths: 8, assists: 9, cs: 26, cs_per_min: 1.0, total_damage: 11000, gold_earned: 8900, vision_score: 52, items: [6692, 3117, 3179, 3857, 3814, 0, 3364], kill_participation_pct: 38, is_target: false },
  ]

  const addShare = players => {
    const teamDamage = players.reduce((sum, p) => sum + p.total_damage, 0) || 1
    return players.map(p => ({ ...p, damage_share_pct: Number(((p.total_damage / teamDamage) * 100).toFixed(1)) }))
  }

  return {
    playerNick: targetNick,
    rank: "DIAMOND II",
    puuid: safePuuid,
    matchStats: {
      match_id: safeMatchId,
      riot_id: targetNick,
      summoner_name: targetNick,
      champion: "Jinx",
      position: "BOTTOM",
      kills: 14,
      deaths: 5,
      assists: 7,
      win: true,
      duration_min: 26,
      cs_per_min: 8.0,
      vision_score: 7,
      kill_participation_pct: 64,
      damage_share_pct: 33.6,
      items: [6671, 3094, 3031, 3036, 3006, 3072, 3363],
      allies: [
        { champion: "Nami", position: "UTILITY" },
        { champion: "Ahri", position: "MIDDLE" },
      ],
    },
    scoreboard: {
      match_id: safeMatchId,
      duration_min: 26,
      teams: [
        { side: "blue", win: true, players: addShare(bluePlayers) },
        { side: "red", win: false, players: addShare(redPlayers) },
      ],
    },
  }
}

// ── ResultsScreen ──────────────────────────────────────────
export default function ResultsScreen() {
  const { matchId } = useParams()
  const location        = useLocation()
  const state           = location.state
  const hasRouteMatchStats = Boolean(state?.matchStats)
  const isDirectLink       = !hasRouteMatchStats
  const navigate    = useNavigate()
  const [searchParams] = useSearchParams()
  const isMockMode = searchParams.get("mock") === "1"

  const [activeTab,       setActiveTab]       = useState("geral")
  const [coachingLoading, setCoachingLoading] = useState(!isDirectLink)
  const [hasAnalysis,     setHasAnalysis]     = useState(false)
  const [analysis,        setAnalysis]        = useState(null)
  const [coachingApiStatus, setCoachingApiStatus] = useState(null)
  const [scoreboard,      setScoreboard]      = useState(null)
  const [scoreboardLoading, setScoreboardLoading] = useState(false)


  // Novo: Suporte a acesso direto via URL
  const [matchStats, setMatchStats] = useState(state?.matchStats ?? null)
  const [playerNick, setPlayerNick] = useState(state?.player?.nick ?? "")
  const [_rank, setRank] = useState(state?.rank ?? "")
  const [puuid, setPuuid] = useState(state?.puuid ?? searchParams.get("puuid") ?? "")
  const [loadingMatch, setLoadingMatch] = useState(false)
  const [errorMatch, setErrorMatch] = useState("")
  const [retryCount, setRetryCount] = useState(0)

  useEffect(() => {
    if (!isMockMode) return
    const mock = buildMockMatchPayload(matchId, puuid)
    setErrorMatch("")
    setLoadingMatch(false)
    setMatchStats(mock.matchStats)
    setScoreboard(mock.scoreboard)
    setPlayerNick(mock.playerNick)
    setRank(mock.rank)
    setPuuid(prev => prev || mock.puuid)
    setHasAnalysis(false)
    setAnalysis(null)
    setCoachingLoading(false)
  }, [isMockMode, matchId, puuid])

  useEffect(() => {
    if (isMockMode) return
    if (matchStats) return
    if (!matchId) return
    setLoadingMatch(true)
    setErrorMatch("")
    fetchMatchDetails(matchId)
      .then(data => {
        setMatchStats(data)
        setPlayerNick(data.summoner_name || "")
        setRank(data.rank || "")
        setPuuid(data.puuid || "")
      })
      .catch(() => {
        setErrorMatch("Partida não encontrada ou erro ao carregar.")
      })
      .finally(() => setLoadingMatch(false))
  }, [isMockMode, matchId, matchStats, retryCount])

  useEffect(() => {
    if (isMockMode) return
    if (isDirectLink) return
    if (!matchId) return
    if (!playerNick) return
    let cancelled = false
    fetchCoachingAnalysis(matchId, playerNick)
      .then(data => {
        if (cancelled) return
        setHasAnalysis(data.has_analysis)
        setAnalysis(data.analysis ?? null)
        setCoachingApiStatus(data.status ?? null)
      })
      .catch(() => { if (!cancelled) { setHasAnalysis(false); setAnalysis(null); setCoachingApiStatus(null) } })
      .finally(() => { if (!cancelled) setCoachingLoading(false) })
    return () => { cancelled = true }
  }, [isMockMode, matchId, playerNick, hasRouteMatchStats])

  useEffect(() => {
    if (isMockMode) return
    if (!matchId || !matchStats) return
    setScoreboardLoading(true)
    fetchScoreboard(matchId, puuid)
      .then(data => {
        if (data) {
          setScoreboard(data)
        } else {
          setScoreboard(null)
        }
      })
      .catch(() => {
        // Fallback: usa o riot_id do banco se o scoreboard falhar
        setPlayerNick(prev => prev || matchStats?.riot_id || "")
        setScoreboard(null)
      })
      .finally(() => setScoreboardLoading(false))
  }, [isMockMode, matchId, matchStats, puuid])

  // Acesso via URL: extrai o nome do jogador correto pelo is_target do scoreboard
  useEffect(() => {
    if (isMockMode) return
    if (playerNick || !scoreboard) return
    const allPlayers = scoreboard.teams?.flatMap(t => t.players) ?? []
    const target = allPlayers.find(p => p.is_target)
    setPlayerNick(target?.summoner_name || matchStats?.riot_id || "")
  }, [isMockMode, scoreboard, playerNick, matchStats])

  const win     = matchStats?.win === true || matchStats?.win === 1
  const score   = matchStats ? calcScore(matchStats) : 0
  const fallbackTag = String(playerNick || matchStats?.riot_id || "")
    .split("#")
    .slice(1)
    .join("#")
    .trim() || "BR1"
  const playerProfilePath = buildSummonerProfilePath(playerNick, fallbackTag)
  const [imgFailed, setImgFailed] = useState(false)

  // Derives the coaching display status for CoachingSection and AnalysisStatusBlock.
  // "private" is a frontend-only state: direct URL access with no playerNick context resolved.
  function getCoachingDisplayStatus() {
    if (coachingLoading) return null
    if (hasAnalysis && coachingApiStatus === "ready") return "ready"
    if (coachingApiStatus === "pending") return "pending"
    if (coachingApiStatus === "failed") return "failed"
    if (coachingApiStatus === "insufficient_data") return "insufficient_data"
    // Direct URL access with no player context (shared link viewer): show private state.
    if (!hasRouteMatchStats && !playerNick && !coachingLoading) return "private"
    return "insufficient_data"
  }
  const coachingDisplayStatus = getCoachingDisplayStatus()

  if (loadingMatch) {
    return <div className="max-w-2xl mx-auto px-4 py-10 text-center text-black-300 text-bs">Carregando partida...</div>
  }
  if (errorMatch) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-10 text-center">
        <svg
          className="w-8 h-8 text-red-500 mx-auto mb-3"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
        <p className="text-bxs text-black-300">Partida não encontrada ou erro ao carregar.</p>
        <div className="flex items-center justify-center gap-3 mt-4">
          <button
            onClick={() => { setErrorMatch(""); setRetryCount(c => c + 1) }}
            className="bg-black-700 border border-black-500 text-black-100 text-bxs font-bold px-4 py-2 rounded-md hover:bg-black-600 transition-colors"
          >
            Tentar novamente
          </button>
          <button
            onClick={() => navigate("/")}
            className="text-blue-400 text-bxs font-bold hover:underline transition-colors"
          >
            Ir para home
          </button>
        </div>
      </div>
    )
  }
  if (!matchStats) return null

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      {/* ── Back button ──────────────────────────────── */}
      <button
        aria-label="Voltar para a home"
        onClick={() =>
          window.history.length <= 2 || !location.state?.from
            ? navigate("/")
            : navigate(-1)
        }
        className="text-bxs text-black-300 hover:text-black-100 font-medium transition-colors flex items-center gap-1 mb-3"
      >
        ← Voltar
      </button>

      {/* ── Match row (identical style to MatchRow in SummonerProfileScreen) ── */}
      <div className={`w-full rounded-md border-l-[3px] ${
        win ? "bg-accent-green/[0.06] border-accent-green/50" : "bg-accent-red/[0.06] border-accent-red/50"
      }`}>
        {/* Summary header */}
        <div className="flex items-center gap-3 px-3 py-2.5">
          <div className="w-10 h-10 rounded-lg overflow-hidden border border-white/10 flex-shrink-0 bg-black-600">
            {!imgFailed ? (
              <img
                src={`https://ddragon.leagueoflegends.com/cdn/${DDV}/img/champion/${matchStats.champion}.png`}
                alt={matchStats.champion}
                onError={() => setImgFailed(true)}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-black-400 text-xs">?</div>
            )}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-0.5">
              <span className={`text-bxs font-bold uppercase ${win ? "text-accent-green" : "text-accent-red"}`}>
                {win ? "Vitoria" : "Derrota"}
              </span>
              <span className="text-bs font-semibold text-black-0 truncate">{matchStats.champion}</span>
              {matchStats.position && (
                <span className="text-[9px] text-black-300 border border-black-500 rounded px-1 py-0.5 bg-black-600">
                  {getPositionLabel(matchStats.position, "abbrev")}
                </span>
              )}
              {hasAnalysis && (
                <span className="text-[9px] font-bold text-gold-400 bg-gold-400/15 px-1.5 py-0.5 rounded">
                  IA
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-bs">
                <span className="text-black-100">{matchStats.kills}</span>
                <span className="text-black-400"> / </span>
                <span className="text-accent-red">{matchStats.deaths}</span>
                <span className="text-black-400"> / </span>
                <span className="text-black-100">{matchStats.assists}</span>
              </span>
              <span className="text-bxs text-black-400">{matchStats.duration_min}min</span>
            </div>
            {playerNick && (
              playerProfilePath ? (
                <a
                  href={playerProfilePath}
                  className="text-bxs text-blue-300 hover:text-blue-200 hover:underline transition-colors mt-1"
                >
                  {playerNick}
                </a>
              ) : (
                <span className="text-bxs text-black-300 mt-1 block">{playerNick}</span>
              )
            )}
          </div>

          <div className="hidden sm:flex gap-0.5 flex-shrink-0">
            {(matchStats.items?.length ? matchStats.items : Array(7).fill(0)).map((itemId, i) => (
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
            {matchStats.cs_per_min > 0 && <span className="text-bxs text-black-300">{matchStats.cs_per_min} cs/m</span>}
            {matchStats.vision_score > 0 && <span className="text-bxs text-black-400">{matchStats.vision_score} vis</span>}
          </div>

          <ScoreBadge score={score} />
        </div>
      </div>

      {/* ── Scoreboard section — below the fold (D-09) ──────────────────────── */}
      <div className="mt-6">
        <div className="flex gap-6 mb-2">
          {TABS.map(tab =>
            tab.disabled ? (
              <button
                key={tab.key}
                disabled
                title={`${tab.label} — Em breve`}
                className="pb-3 text-bxs font-medium text-black-500 cursor-not-allowed"
              >
                {tab.label}
                <span className="ml-1.5 text-[9px] text-black-500 font-medium tracking-wide">Em breve</span>
              </button>
            ) : (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`pb-3 text-bxs font-semibold transition-colors ${
                  activeTab === tab.key
                    ? "text-black-0 border-b-2 border-blue-400"
                    : "text-black-400 hover:text-black-200"
                }`}
              >
                {tab.label}
              </button>
            )
          )}
        </div>
        <div className="w-full h-[1.5px] bg-gradient-to-r from-black-800/0 via-blue-400/15 to-black-800/0 scoreboard-divider mb-4" />

        {/* Geral tab: scoreboard */}
        {activeTab === "geral" && (
          <>
            {scoreboardLoading ? (
              <div className="space-y-1.5">
                {Array.from({ length: 10 }).map((_, i) => (
                  <div key={i} className="h-9 shimmer-bg rounded" />
                ))}
              </div>
            ) : !scoreboard ? (
              <div className="rounded-lg border border-white/6 bg-black-800/60 px-4 py-6 text-center text-sm text-black-400">
                Não foi possível carregar o scoreboard desta partida agora. Tente recarregar a página.
              </div>
            ) : (
              <InlineScoreboard data={scoreboard} fallbackTag={fallbackTag} />
            )}
          </>
        )}
      </div>

      {/* ── Analysis Status + Coaching IA (somente via perfil, não link direto) ── */}
      {!isDirectLink && (
        <>
          <AnalysisStatusBlock status={coachingDisplayStatus} />
          <CoachingSection
            analysis={analysis}
            hasAnalysis={hasAnalysis}
            loading={coachingLoading}
            status={coachingDisplayStatus}
          />
        </>
      )}

    </div>
  )
}

