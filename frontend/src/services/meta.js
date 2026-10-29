import { useEffect, useState } from "react"
import { fetchLeaderboard, fetchTierlist } from "./api"

// Cache em memória por sessão: a home e as telas usam os mesmos dados sem buscar duas vezes.
const memory = new Map()

function useCachedRequest(key, request) {
  const [attempt, setAttempt] = useState(0)
  const [state, setState] = useState(() => {
    const data = memory.get(key)?.data
    return data ? { data, loading: false, error: "" } : { data: null, loading: true, error: "" }
  })

  useEffect(() => {
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
  }, [key, attempt]) // eslint-disable-line react-hooks/exhaustive-deps

  return { ...state, retry: () => setAttempt((n) => n + 1) }
}

export function useTierlist() {
  return useCachedRequest("tierlist", fetchTierlist)
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
