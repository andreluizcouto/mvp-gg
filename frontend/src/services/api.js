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

function getAuthHeaders(accessToken) {
  if (!accessToken) return {}
  return { Authorization: `Bearer ${accessToken}` }
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

async function requestJsonWithAuth(path, accessToken, { method = "GET", body, timeoutMs = API_TIMEOUT_MS } = {}) {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), timeoutMs)
  const headers = {
    Accept: "application/json",
    ...getAuthHeaders(accessToken),
  }
  if (body) headers["Content-Type"] = "application/json"

  try {
    const response = await fetch(`${BASE_URL}${path}`, {
      method,
      mode: "cors",
      credentials: "omit",
      cache: "no-store",
      redirect: "error",
      referrerPolicy: "no-referrer",
      signal: controller.signal,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) {
      const error = new Error(data.detail || `Erro ${response.status}`)
      error.status = response.status
      throw error
    }
    return data
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

export async function fetchMatchDetails(matchId, puuid = "") {
  const safeMatchId = validateMatchId(matchId)
  const safePuuid = String(puuid || "").trim().slice(0, 120)
  const params = safePuuid ? `?puuid=${encodeURIComponent(safePuuid)}` : ""
  return requestJson(`/match/${encodeURIComponent(safeMatchId)}${params}`)
}

const QUEUE_GROUPS = new Set(["all", "solo", "flex", "normal", "aram", "arena"])

function historyParams(start, count, queue) {
  const params = new URLSearchParams({
    start: String(start),
    count: String(count),
  })
  if (queue && queue !== "all" && QUEUE_GROUPS.has(queue)) params.set("queue", queue)
  return params
}

export async function fetchMatches(nick, { start = 0, count = 10, queue = "all" } = {}) {
  const { gameName, tagLine } = parseRiotId(nick)
  const params = historyParams(start, count, queue)
  return requestJson(`/summoner/${encodeURIComponent(gameName)}/${encodeURIComponent(tagLine)}?${params.toString()}`, {
    timeoutMs: SUMMONER_TIMEOUT_MS,
  })
}

export async function refreshMatches(nick, { start = 0, count = 10, queue = "all" } = {}) {
  const { gameName, tagLine } = parseRiotId(nick)
  const params = historyParams(start, count, queue)
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

export async function fetchAuthorizedCoachingAnalysis(matchId, accessToken, riotId = "") {
  const safeMatchId = validateMatchId(matchId)
  const safeRiotId = normalizeOptionalRiotId(riotId)
  const params = safeRiotId ? `?riot_id=${encodeURIComponent(safeRiotId)}` : ""
  return requestJsonWithAuth(`/coaching/${encodeURIComponent(safeMatchId)}${params}`, accessToken)
}

export async function fetchAuthorizedCoachingStatus(matchIds, accessToken, riotId = "") {
  if (!Array.isArray(matchIds) || matchIds.length === 0) return {}
  const safeIds = matchIds.slice(0, 50).map(validateMatchId)
  const ids = safeIds.join(",")
  const safeRiotId = normalizeOptionalRiotId(riotId)
  const riotParam = safeRiotId ? `&riot_id=${encodeURIComponent(safeRiotId)}` : ""
  return requestJsonWithAuth(`/coaching/status?ids=${encodeURIComponent(ids)}${riotParam}`, accessToken)
}

export async function fetchAuthMe(accessToken) {
  return requestJsonWithAuth("/auth/me", accessToken)
}

export async function fetchLiveGame(nick) {
  const { gameName, tagLine } = parseRiotId(nick)
  return requestJson(`/summoner/${encodeURIComponent(gameName)}/${encodeURIComponent(tagLine)}/live`)
}

export async function fetchTierlist() {
  return requestJson("/meta/tierlist", { timeoutMs: SUMMONER_TIMEOUT_MS })
}

const LANES_ALLOWED = new Set(["top", "jungle", "mid", "adc", "support"])

// Força por elo: com o servidor frio, o OP.GG leva até ~30s por rota (depois fica em cache).
export async function fetchTierlistElos(lane) {
  const safeLane = LANES_ALLOWED.has(lane) ? lane : "mid"
  return requestJson(`/meta/tierlist/elos?lane=${safeLane}`, { timeoutMs: 120000 })
}

export async function fetchLeaderboard({ limit = 50 } = {}) {
  const safeLimit = Math.max(1, Math.min(Number(limit) || 50, 100))
  return requestJson(`/leaderboard?limit=${safeLimit}`, { timeoutMs: SUMMONER_TIMEOUT_MS })
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
