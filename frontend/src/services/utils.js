export const TIER_COLORS = {
  CHALLENGER: "#F4C874", GRANDMASTER: "#CD4535", MASTER: "#9D48E0",
  DIAMOND: "#57A0D2", EMERALD: "#56B675", PLATINUM: "#5BBFB5",
  GOLD: "#C89B3C", SILVER: "#8A9BB4", BRONZE: "#AE704B",
  IRON: "#7C7F84", UNRANKED: "#555",
}

export function parseTier(rankStr) {
  if (!rankStr || rankStr === "Unranked") return "UNRANKED"
  return rankStr.split(" ")[0].toUpperCase()
}

export function buildSummonerProfilePath(summonerName, fallbackTag = "") {
  const value = String(summonerName || "").trim()
  const hashIdx = value.lastIndexOf("#")
  if (hashIdx > 0 && hashIdx < value.length - 1) {
    const pName = value.slice(0, hashIdx).trim()
    const pTag = value.slice(hashIdx + 1).trim()
    if (!pName || !pTag) return ""
    return `/summoner/${encodeURIComponent(pName)}/${encodeURIComponent(pTag)}`
  }

  const pName = value
  const pTag = String(fallbackTag || "").trim()
  if (!pName || !pTag) return ""

  return `/summoner/${encodeURIComponent(pName)}/${encodeURIComponent(pTag)}`
}

export function calcScore(match) {
  const {
    kills = 0, deaths = 0, assists = 0, win,
    cs_per_min = 0, vision_score = 0,
    kill_participation_pct = 0, damage_share_pct = 0,
  } = match
  const kda = (kills + assists) / Math.max(deaths, 1)
  const s =
    Math.min(kda / 8 * 30, 30) +
    (win ? 20 : 0) +
    Math.min(cs_per_min / 8 * 15, 15) +
    Math.min(vision_score / 60 * 10, 10) +
    Math.min(kill_participation_pct / 100 * 15, 15) +
    Math.min(damage_share_pct / 35 * 10, 10)
  return Math.round(Math.min(s, 100))
}

export function buildChampionPool(matches) {
  const pool = {}
  for (const m of matches) {
    const c = m.champion
    if (!pool[c]) pool[c] = { champion: c, wins: 0, games: 0, kills: 0, deaths: 0, assists: 0, cs_per_min_total: 0 }
    pool[c].games++
    if (m.win) pool[c].wins++
    pool[c].kills += m.kills
    pool[c].deaths += m.deaths
    pool[c].assists += m.assists
    pool[c].cs_per_min_total += (m.cs_per_min ?? 0)
  }
  return Object.values(pool)
    .sort((a, b) => b.games - a.games)
    .slice(0, 5)
    .map(c => ({
      ...c,
      wr: Math.round(c.wins / c.games * 100),
      kda: c.deaths === 0 ? "Perfect" : ((c.kills + c.assists) / c.deaths).toFixed(1),
      cs_per_min: (c.cs_per_min_total / c.games).toFixed(1),
    }))
}

export function formatKDA(kdaStr) {
  const [k, d, a] = (kdaStr ?? "0/0/0").split("/").map(Number)
  const ratio = d === 0 ? "Perfect" : ((k + a) / d).toFixed(2)
  return { k, d, a, ratio }
}

// "há 3 horas", "há 2 dias", "há 1 semana", "há 5 meses"…
const RELATIVE_STEPS = [
  { limit: 60,        size: 1,        one: "minuto", many: "minutos" },
  { limit: 60 * 24,   size: 60,       one: "hora",   many: "horas" },
  { limit: 60 * 24 * 7,  size: 60 * 24,      one: "dia",    many: "dias" },
  { limit: 60 * 24 * 30, size: 60 * 24 * 7,  one: "semana", many: "semanas" },
  { limit: 60 * 24 * 365, size: 60 * 24 * 30, one: "mês",   many: "meses" },
  { limit: Infinity,  size: 60 * 24 * 365, one: "ano",    many: "anos" },
]

export function timeAgo(timestampMs, now = Date.now()) {
  const value = Number(timestampMs)
  if (!value) return ""
  const minutes = Math.max(0, Math.floor((now - value) / 60000))
  if (minutes < 1) return "agora há pouco"
  const step = RELATIVE_STEPS.find(s => minutes < s.limit)
  const amount = Math.max(1, Math.floor(minutes / step.size))
  return `há ${amount} ${amount === 1 ? step.one : step.many}`
}

export function formatDateTime(timestampMs) {
  const value = Number(timestampMs)
  if (!value) return ""
  return new Date(value).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" })
}
