const API_TIMEOUT_MS = 12000
const SUMMONER_TIMEOUT_MS = 30000
const MATCH_ID_RE = /^[A-Za-z0-9_:-]{3,80}$/
const GAME_NAME_RE = /^[^\r\n#]{1,32}$/
const TAG_LINE_RE = /^[^#\s]{1,16}$/

function normalizeBaseUrl(value) {
  return value.replace(/\/+$/, "")
}

function resolveBaseUrl() {
  const configured = (import.meta.env.VITE_API_URL || "").trim()
  const fallback = "https://lol-coach-backend-z4b7.onrender.com"
  const resolved = configured ? configured : fallback

  if (typeof window !== "undefined" && window.location.protocol === "https:" && resolved.startsWith("http://")) {
    throw new Error("VITE_API_URL insegura: use HTTPS em produção.")
  }

  return normalizeBaseUrl(resolved)
}

function newRequestId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID()
  }
  return `req-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function validateMatchId(matchId) {
  const value = String(matchId || "").trim()
  if (!MATCH_ID_RE.test(value)) {
    throw new Error("matchId inválido.")
  }
  return value
}

function parseRiotId(nick) {
  const value = String(nick || "").trim()
  const hashIdx = value.lastIndexOf("#")
  if (hashIdx < 1 || hashIdx >= value.length - 1) {
    throw new Error("riotId inválido. Use o formato nome#tag.")
  }

  const gameName = value.slice(0, hashIdx).trim()
  const tagLine = value.slice(hashIdx + 1).trim()

  if (!GAME_NAME_RE.test(gameName) || !TAG_LINE_RE.test(tagLine)) {
    throw new Error("riotId inválido. Use o formato nome#tag.")
  }

  return { value: `${gameName}#${tagLine}`, gameName, tagLine }
}

function normalizeOptionalRiotId(riotId) {
  if (!riotId) return ""
  try {
    return parseRiotId(riotId).value
  } catch {
    return ""
  }
}

async function requestJson(path, { timeoutMs = API_TIMEOUT_MS, includeRequestId = false } = {}) {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), timeoutMs)
  const headers = {
    Accept: "application/json",
  }

  // Keep public GET requests "simple" by default so browsers skip the CORS preflight.
  if (includeRequestId) {
    headers["X-Request-ID"] = newRequestId()
  }

  try {
    const response = await fetch(`${BASE_URL}${path}`, {
      method: "GET",
      mode: "cors",
      credentials: "omit",
      cache: "no-store",
      redirect: "error",
      referrerPolicy: "no-referrer",
      signal: controller.signal,
      headers,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.detail || `Erro ${response.status}`)
    }

    return response.json()
  } catch (error) {
    if (error?.name === "AbortError") {
      throw new Error("Timeout ao consultar a API.")
    }
    throw error
  } finally {
    clearTimeout(timeout)
  }
}

export const BASE_URL = resolveBaseUrl()
export const APP_DOWNLOAD_URL = `${BASE_URL}/downloads/app`

export async function fetchMatchDetails(matchId) {
  const safeMatchId = validateMatchId(matchId)
  return requestJson(`/match/${encodeURIComponent(safeMatchId)}`)
}

export async function fetchMatches(nick, { start = 0, count = 10 } = {}) {
  const { gameName, tagLine } = parseRiotId(nick)
  const params = new URLSearchParams({
    start: String(start),
    count: String(count),
  })
  return requestJson(`/summoner/${encodeURIComponent(gameName)}/${encodeURIComponent(tagLine)}?${params.toString()}`, {
    timeoutMs: SUMMONER_TIMEOUT_MS,
  })
}

export async function refreshMatches(nick, { start = 0, count = 10 } = {}) {
  const { gameName, tagLine } = parseRiotId(nick)
  const params = new URLSearchParams({
    start: String(start),
    count: String(count),
  })
  return requestJson(`/summoner/${encodeURIComponent(gameName)}/${encodeURIComponent(tagLine)}/refresh?${params.toString()}`, {
    timeoutMs: SUMMONER_TIMEOUT_MS,
  })
}

export async function fetchCoachingAnalysis(matchId, riotId = "") {
  const safeMatchId = validateMatchId(matchId)
  const safeRiotId = normalizeOptionalRiotId(riotId)
  const params = safeRiotId ? `?riot_id=${encodeURIComponent(safeRiotId)}` : ""

  try {
    return await requestJson(`/coaching/${encodeURIComponent(safeMatchId)}${params}`)
  } catch {
    return { match_id: safeMatchId, has_analysis: false, analysis: null }
  }
}

export async function fetchCoachingStatus(matchIds, riotId = "") {
  if (!Array.isArray(matchIds) || matchIds.length === 0) return {}

  const safeIds = matchIds.slice(0, 50).map(validateMatchId)
  const ids = safeIds.join(",")
  const safeRiotId = normalizeOptionalRiotId(riotId)
  const riotParam = safeRiotId ? `&riot_id=${encodeURIComponent(safeRiotId)}` : ""

  try {
    return await requestJson(`/coaching/status?ids=${encodeURIComponent(ids)}${riotParam}`)
  } catch {
    return {}
  }
}

export async function fetchScoreboard(matchId, puuid = "") {
  const safeMatchId = validateMatchId(matchId)
  const safePuuid = String(puuid || "").trim().slice(0, 120)
  const params = safePuuid ? `?puuid=${encodeURIComponent(safePuuid)}` : ""

  try {
    return await requestJson(`/match/${encodeURIComponent(safeMatchId)}/scoreboard${params}`)
  } catch {
    return null
  }
}
