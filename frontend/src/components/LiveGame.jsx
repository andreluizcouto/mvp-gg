import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { championIcon, queueLabel, spellIcon } from "../services/constants"
import { buildSummonerProfilePath } from "../services/utils"

function useElapsed(startedAt) {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    if (!startedAt) return undefined
    const timer = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(timer)
  }, [startedAt])
  if (!startedAt) return ""
  const total = Math.max(0, Math.floor((now - startedAt) / 1000))
  const min = Math.floor(total / 60)
  const sec = String(total % 60).padStart(2, "0")
  return `${min}:${sec}`
}

// Botão "Ao vivo": abre e fecha o cartão da partida em andamento (começa fechado).
export function LiveBadge({ live, open, onToggle }) {
  const elapsed = useElapsed(live?.started_at)
  if (!live) return null
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-expanded={open}
      aria-controls="ao-vivo"
      className={`inline-flex min-h-[32px] items-center gap-2 rounded-full px-3 text-bxs font-bold uppercase tracking-wider text-red-400 ring-1 transition ${open ? "bg-red-500/25 ring-red-500/60" : "bg-red-500/15 ring-red-500/40 hover:bg-red-500/25"}`}
    >
      <span className="relative flex h-2 w-2" aria-hidden="true">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-500 opacity-75" />
        <span className="relative inline-flex h-2 w-2 rounded-full bg-red-500" />
      </span>
      Ao vivo{elapsed && <span className="tabular font-semibold normal-case text-red-300">· {elapsed}</span>}
      <svg viewBox="0 0 24 24" className={`h-3.5 w-3.5 transition-transform duration-200 ${open ? "rotate-180" : ""}`} fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <polyline points="6 9 12 15 18 9" />
      </svg>
      <span className="sr-only">{open ? "Esconder partida ao vivo" : "Ver partida ao vivo"}</span>
    </button>
  )
}

const TEAM_STYLES = {
  100: { label: "Time azul", color: "#33D1C1" },
  200: { label: "Time vermelho", color: "#FF5A6E" },
}

function LivePlayer({ player }) {
  const [name, tag] = String(player.riot_id || "").split("#")
  const path = tag ? buildSummonerProfilePath(player.riot_id) : ""
  const content = (
    <>
      <img src={championIcon(player.champion_key)} alt={player.champion_key} className="h-10 w-10 flex-shrink-0 rounded-xl ring-1 ring-white/10" />
      <span className="flex flex-shrink-0 flex-col gap-0.5">
        {player.spells.map((spell, i) => spell
          ? <img key={i} src={spellIcon(spell)} alt="" className="h-[19px] w-[19px] rounded" />
          : <span key={i} className="h-[19px] w-[19px] rounded bg-black-500" />)}
      </span>
      <span className="min-w-0">
        <span className={`block truncate text-bs font-semibold ${player.is_target ? "text-purple-300" : "text-black-0"}`}>
          {name || player.champion_key}
        </span>
        <span className="block truncate text-bxs text-black-400">
          {tag ? `#${tag}` : player.is_bot ? "Bot" : "Nome oculto"}
        </span>
      </span>
    </>
  )
  const className = `flex min-w-0 items-center gap-2.5 rounded-xl px-2 py-1.5 ${player.is_target ? "bg-purple-400/10 ring-1 ring-purple-400/40" : ""}`
  return path && !player.is_target
    ? <Link to={path} className={`${className} transition hover:bg-white/[0.04]`}>{content}</Link>
    : <div className={className}>{content}</div>
}

export function LiveGameCard({ live }) {
  const elapsed = useElapsed(live?.started_at)
  if (!live) return null

  const teamIds = [...new Set(live.participants.map(p => p.team_id))].sort((a, b) => a - b)
  const mode = queueLabel({ queue_id: live.queue_id, queue_name: live.queue_name, game_mode: live.game_mode })

  return (
    <section id="ao-vivo" className="card mb-6 overflow-hidden border-red-500/25 p-5" aria-label="Partida ao vivo">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <span className="relative flex h-3 w-3" aria-hidden="true">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-500 opacity-75" />
            <span className="relative inline-flex h-3 w-3 rounded-full bg-red-500" />
          </span>
          <h2 className="whitespace-nowrap font-display text-bxl font-bold text-black-0">Jogando agora</h2>
          {mode && <span className="whitespace-nowrap text-bs font-semibold text-black-300">{mode}</span>}
        </div>
        <span className="tabular text-bm font-semibold text-red-300">
          {elapsed ? `${elapsed} de jogo` : "Carregando a partida…"}
        </span>
      </div>

      {live.game_mode === "KIWI" && (
        <p className="mt-3 rounded-xl bg-yellow-400/10 px-3 py-2 text-bxs text-yellow-400">
          A Riot ainda não libera o histórico de ARAM: Desordem na API, então esta partida aparece só ao vivo
          e não vai entrar na lista de partidas depois.
        </p>
      )}

      <div className={`mt-4 grid grid-cols-1 gap-4 ${teamIds.length === 2 ? "md:grid-cols-2" : "md:grid-cols-3"}`}>
        {teamIds.map((teamId, index) => {
          const style = TEAM_STYLES[teamId] ?? { label: `Time ${index + 1}`, color: "#97A0B3" }
          const bans = live.bans.filter(b => b.team_id === teamId && b.champion_key)
          return (
            <div key={teamId} className="rounded-2xl bg-white/[0.02] p-2">
              <div className="flex items-center justify-between px-2 pb-2 pt-1">
                <span className="text-bxs font-bold uppercase tracking-wider" style={{ color: style.color }}>{style.label}</span>
                {bans.length > 0 && (
                  <span className="flex items-center gap-1" aria-label="Bans">
                    <span className="mr-1 text-bxs text-black-400">Bans</span>
                    {bans.map((b, i) => (
                      <img key={i} src={championIcon(b.champion_key)} alt={b.champion_key} className="h-5 w-5 rounded grayscale opacity-60" />
                    ))}
                  </span>
                )}
              </div>
              <div className="grid gap-1">
                {live.participants.filter(p => p.team_id === teamId).map((p, i) => <LivePlayer key={`${p.riot_id}-${i}`} player={p} />)}
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
