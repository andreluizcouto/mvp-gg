import { useEffect, useState } from "react"
import { fetchLeaderboard, fetchTierlist, fetchTierlistByElo, fetchTierlistSnapshot } from "./api"
import { DEFAULT_ELO, LANES } from "./constants"

// Cache em memória por sessão: a home e as telas usam os mesmos dados sem buscar duas vezes.
const memory = new Map()

// enabled = false: o hook não busca nada (hooks não podem ser chamados condicionalmente).
function useCachedRequest(key, request, enabled = true) {
  const [attempt, setAttempt] = useState(0)
  const [state, setState] = useState(() => {
    const data = memory.get(key)?.data
    return data ? { data, loading: false, error: "" } : { data: null, loading: enabled, error: "" }
  })

  useEffect(() => {
    if (!enabled) {
      setState({ data: null, loading: false, error: "" })
      return undefined
    }
    let entry = memory.get(key)
    if (entry?.data) {
      setState({ data: entry.data, loading: false, error: "" })
      return undefined
    }
    // Uma requisição só por chave, mesmo com várias telas montadas ao mesmo tempo.
    if (!entry?.promise) {
      entry = { promise: request() }
      memory.set(key, entry)
    }

    let alive = true
    setState((prev) => ({ ...prev, loading: true, error: "" }))
    entry.promise
      .then((data) => {
        memory.set(key, { data })
        if (alive) setState({ data, loading: false, error: "" })
      })
      .catch((error) => {
        memory.delete(key)
        if (alive) setState({ data: null, loading: false, error: error?.message || "Não foi possível carregar." })
      })
    return () => { alive = false }
  }, [key, attempt, enabled]) // eslint-disable-line react-hooks/exhaustive-deps

  return { ...state, retry: () => setAttempt((n) => n + 1) }
}

export function useTierlist() {
  return useCachedRequest("tierlist", fetchTierlist)
}

// Tier list de um elo com as 5 rotas de uma vez: primeiro o snapshot pré-calculado (instantâneo);
// se ele ainda não existir, o backend monta as 5 rotas em paralelo. Trocar de rota não busca de novo.
async function fetchEloAllLanes(elo) {
  try {
    return await fetchTierlistSnapshot(elo)
  } catch {
    const results = await Promise.all(LANES.map(({ id }) => fetchTierlistByElo(id, elo)))
    return {
      elo,
      ddragon_version: results[0]?.ddragon_version,
      updated_at: Math.min(...results.map(r => r.updated_at || Infinity)),
      positions: Object.fromEntries(LANES.map(({ id }, i) => [id, results[i]?.rows ?? []])),
    }
  }
}

// Linhas da tier list de uma rota num elo. Esmeralda+ reaproveita a tier list padrão (já carregada).
export function useTierlistRows(lane, elo) {
  const base = useTierlist()
  const custom = elo !== DEFAULT_ELO
  const byElo = useCachedRequest(`tierlist-elo:${elo}`, () => fetchEloAllLanes(elo), custom)
  const source = custom ? byElo : base
  return {
    rows: source.data?.positions?.[lane] ?? [],
    version: source.data?.ddragon_version ?? base.data?.ddragon_version,
    updatedAt: source.data?.updated_at,
    loading: source.loading,
    error: source.error,
    retry: source.retry,
  }
}

export function useLeaderboard(limit = 50) {
  return useCachedRequest(`leaderboard:${limit}`, () => fetchLeaderboard({ limit }))
}

// "16.21.1" → "16.21"
export function patchLabel(version) {
  return String(version || "").split(".").slice(0, 2).join(".")
}

export function formatPercent(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—"
  return `${(Number(value) * 100).toFixed(digits)}%`
}

export function winRateColor(rate) {
  if (rate >= 0.53) return "text-purple-300"
  if (rate >= 0.51) return "text-green-600"
  if (rate >= 0.49) return "text-black-100"
  return "text-red-400"
}

export function formatNumber(value) {
  return new Intl.NumberFormat("pt-BR").format(Number(value) || 0)
}
