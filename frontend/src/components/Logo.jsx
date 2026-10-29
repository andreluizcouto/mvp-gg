// Marca do mvp.gg: o mapa visto de cima.
// As bordas são o top e o bot, a diagonal dourada é a mid, e as bolinhas são as duas bases.
export function RiftMark({ className = "h-7 w-7" }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true">
      <rect x="1" y="1" width="30" height="30" rx="9" fill="#161C27" stroke="rgba(255,255,255,0.10)" />
      <path d="M8 24V8h16" fill="none" stroke="#97A0B3" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M8 24h16V8" fill="none" stroke="#97A0B3" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" opacity="0.55" />
      <path d="M8.5 23.5 23.5 8.5" fill="none" stroke="#E2B95E" strokeWidth="2.6" strokeLinecap="round" />
      <circle cx="8" cy="24" r="2.6" fill="#33D1C1" />
      <circle cx="24" cy="8" r="2.6" fill="#FF5A6E" />
    </svg>
  )
}

export default function Logo({ className = "", markClassName = "h-7 w-7" }) {
  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <RiftMark className={markClassName} />
      <span className="font-display text-[17px] font-bold tracking-tight text-black-0">
        mvp<span className="text-purple-400">.gg</span>
      </span>
    </span>
  )
}
