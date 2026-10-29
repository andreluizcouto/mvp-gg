import { useState } from "react"
import { META_TIERS, championIcon } from "../services/constants"

// O mapa visto de cima, desenhado em linhas: é o motivo gráfico do site.
// Top e bot nas bordas, a mid em ouro na diagonal, o rio cruzando e as torres em pontos.
export function RiftLanes({ className = "" }) {
  const turrets = [
    [70, 330], [70, 230], [70, 130], [130, 70], [230, 70], [330, 70],
    [130, 330], [230, 330], [330, 330], [330, 230], [330, 130],
    [140, 260], [200, 200], [260, 140],
  ]
  return (
    <svg viewBox="0 0 400 400" className={className} aria-hidden="true">
      <defs>
        <linearGradient id="mid-lane" x1="0" y1="1" x2="1" y2="0">
          <stop offset="0" stopColor="#33D1C1" />
          <stop offset="0.5" stopColor="#E2B95E" />
          <stop offset="1" stopColor="#FF5A6E" />
        </linearGradient>
        <filter id="lane-glow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="6" />
        </filter>
      </defs>
      <rect x="40" y="40" width="320" height="320" rx="56" fill="none" stroke="rgba(255,255,255,0.05)" />
      {/* Rio */}
      <path d="M70 70 L330 330" stroke="rgba(51,209,193,0.10)" strokeWidth="26" strokeLinecap="round" />
      {/* Top e bot */}
      <path d="M70 330 V70 H330" fill="none" stroke="rgba(197,204,217,0.28)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"
        pathLength="1" strokeDasharray="1" className="animate-lane-draw" />
      <path d="M70 330 H330 V70" fill="none" stroke="rgba(197,204,217,0.18)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"
        pathLength="1" strokeDasharray="1" className="animate-lane-draw" style={{ animationDelay: "150ms" }} />
      {/* Mid */}
      <path d="M70 330 L330 70" stroke="url(#mid-lane)" strokeWidth="10" strokeLinecap="round" opacity="0.35" filter="url(#lane-glow)" />
      <path d="M70 330 L330 70" stroke="url(#mid-lane)" strokeWidth="3.5" strokeLinecap="round"
        pathLength="1" strokeDasharray="1" className="animate-lane-draw" style={{ animationDelay: "300ms" }} />
      {turrets.map(([x, y]) => (
        <circle key={`${x}-${y}`} cx={x} cy={y} r="3.2" fill="#0D121A" stroke="rgba(197,204,217,0.45)" strokeWidth="1.5" />
      ))}
      <circle cx="70" cy="330" r="14" fill="#0D121A" stroke="#33D1C1" strokeWidth="3" />
      <circle cx="330" cy="70" r="14" fill="#0D121A" stroke="#FF5A6E" strokeWidth="3" />
    </svg>
  )
}

export function TierBadge({ tier, size = "md" }) {
  const meta = META_TIERS[tier] ?? { label: "?", color: "#6E778A" }
  const box = size === "sm" ? "h-7 w-7 text-bs" : "h-8 w-8 text-bm"
  return (
    <span
      className={`inline-flex ${box} items-center justify-center rounded-lg font-display font-bold`}
      style={{ color: meta.color, backgroundColor: `${meta.color}1A`, boxShadow: `inset 0 0 0 1px ${meta.color}40` }}
      title={`Tier ${tier} no OP.GG`}
    >
      {meta.label}
    </span>
  )
}

export function ChampionAvatar({ championKey, name, version, className = "h-9 w-9" }) {
  const [failed, setFailed] = useState(false)
  if (!championKey || failed) {
    return (
      <span className={`${className} inline-flex items-center justify-center rounded-xl bg-black-500 font-display text-bxs text-black-300`}>
        {String(name || "?").slice(0, 2)}
      </span>
    )
  }
  return (
    <img
      src={championIcon(championKey, version)}
      alt=""
      loading="lazy"
      onError={() => setFailed(true)}
      className={`${className} rounded-xl object-cover ring-1 ring-white/10`}
    />
  )
}

// Seta de tendência: compara a posição atual com a do período anterior.
export function RankTrend({ rank, previous }) {
  if (!previous || !rank || previous === rank) {
    return <span className="text-bxs text-black-400" aria-label="Sem mudança">—</span>
  }
  const up = previous > rank
  const delta = Math.abs(previous - rank)
  return (
    <span className={`tabular inline-flex items-center gap-0.5 text-bxs font-semibold ${up ? "text-green-600" : "text-red-500"}`}
      aria-label={up ? `Subiu ${delta}` : `Caiu ${delta}`}>
      <svg viewBox="0 0 12 12" className={`h-3 w-3 ${up ? "" : "rotate-180"}`} aria-hidden="true">
        <path d="M6 2.5 10 8H2z" fill="currentColor" />
      </svg>
      {delta}
    </span>
  )
}

export function SkeletonRows({ rows = 5, className = "h-12" }) {
  return (
    <div className="grid gap-2" aria-hidden="true">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className={`shimmer-bg ${className} rounded-xl`} />
      ))}
    </div>
  )
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-2xl border border-white/[0.06] bg-black-600/50 px-6 py-10 text-center">
      <p className="text-bm text-black-200">{message}</p>
      {onRetry && (
        <button type="button" onClick={onRetry} className="btn-ghost text-bs">
          Tentar de novo
        </button>
      )}
    </div>
  )
}
