import { useEffect, useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"
import { BASE_URL, fetchAuthMe, fetchAuthorizedCoachingStatus } from "../services/api"
import { getSession, logout } from "../services/auth"

export default function DashboardScreen() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [me, setMe] = useState(null)
  const [statusMap, setStatusMap] = useState({})

  const session = useMemo(() => getSession(), [])

  useEffect(() => {
    let cancelled = false
    async function load() {
      if (!session?.access_token) {
        navigate("/login", { replace: true })
        return
      }
      setLoading(true)
      try {
        const mePayload = await fetchAuthMe(session.access_token)
        if (cancelled) return
        setMe(mePayload)
        const samples = ["BR1_123", "BR1_124", "BR1_125"]
        const statuses = await fetchAuthorizedCoachingStatus(samples, session.access_token)
        if (!cancelled) setStatusMap(statuses || {})
      } catch (err) {
        if (err?.status === 401 || err?.status === 403) {
          navigate("/login", { replace: true })
          return
        }
        if (!cancelled) setError(err?.message || "Falha ao carregar dashboard.")
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [navigate, session?.access_token])

  async function handleLogout() {
    try {
      if (session?.refresh_token && session?.access_token) {
        await logout(BASE_URL, session.refresh_token, session.access_token)
      }
    } finally {
      navigate("/login", { replace: true })
    }
  }

  const analyzedMatches = Object.entries(statusMap)
    .filter(([, value]) => value?.status === "ready" || value?.has_analysis === true)
    .map(([matchId]) => matchId)

  if (loading) {
    return <div className="mx-auto max-w-4xl px-4 py-12 text-black-300">Carregando dashboard...</div>
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-hxs font-bold text-black-0">Dashboard</h1>
          <p className="text-bs text-black-300">{me?.email || "Conta autenticada"}</p>
        </div>
        <button onClick={handleLogout} className="rounded-lg border border-black-500 px-3 py-2 text-bs text-black-200 hover:text-black-0">
          Sair
        </button>
      </div>

      {error ? <p role="alert" className="mb-4 text-bxs text-accent-red">{error}</p> : null}

      <div className="grid gap-4 sm:grid-cols-2 mb-6">
        <div className="rounded-xl border border-black-500 bg-black-800 p-4">
          <p className="text-bxs uppercase text-black-400">Análises consumidas</p>
          <p className="text-hxs font-bold text-black-0">{me?.analyses_consumed ?? 0}</p>
        </div>
        <div className="rounded-xl border border-black-500 bg-black-800 p-4">
          <p className="text-bxs uppercase text-black-400">Análises realizadas</p>
          <p className="text-hxs font-bold text-black-0">{me?.analyses_performed ?? 0}</p>
        </div>
      </div>

      <div className="rounded-xl border border-black-500 bg-black-800 p-4">
        <h2 className="text-bm font-semibold text-black-100 mb-3">Partidas com análise disponível</h2>
        {analyzedMatches.length === 0 ? (
          <p className="text-bs text-black-300">Nenhuma análise pronta no momento.</p>
        ) : (
          <ul className="space-y-2">
            {analyzedMatches.map((matchId) => (
              <li key={matchId} className="rounded-lg border border-black-600 bg-black-700 px-3 py-2 text-bs text-black-100">
                {matchId}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
