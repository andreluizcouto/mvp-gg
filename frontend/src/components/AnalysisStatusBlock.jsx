/**
 * AnalysisStatusBlock — short coaching trust signal (D-12).
 * Displays a colored dot + state label + reason for the current coaching status.
 * Position: between match header card and CoachingSection in ResultsScreen.
 *
 * status prop: "ready" | "pending" | "failed" | "insufficient_data" | "private" | null
 */

// State → display config mapping per UI-SPEC D-12
const STATUS_CONFIG = {
  ready: {
    dot: "bg-green-600",
    label: "Análise pronta",
    reason: "Coaching disponível para esta partida",
  },
  pending: {
    dot: "bg-yellow-400 animate-pulse-dot",
    label: "Análise em andamento",
    reason: "Aguarde alguns instantes e recarregue",
  },
  failed: {
    dot: "bg-red-500",
    label: "Análise falhou",
    reason: "Não foi possível processar esta partida",
  },
  insufficient_data: {
    dot: "bg-black-400",
    label: "Coach indisponível",
    reason: "Baixe o app e jogue uma partida",
  },
  private: {
    dot: "bg-black-400",
    label: "Análise privada",
    reason: "Disponível apenas para o dono da conta",
  },
}

const DEFAULT_CONFIG = {
  dot: "bg-black-500",
  label: "Status desconhecido",
  reason: "Não foi possível verificar a análise",
}

export default function AnalysisStatusBlock({ status }) {
  const config = STATUS_CONFIG[status] ?? DEFAULT_CONFIG

  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-black-800/60 border border-white/5 mt-3 mb-3 animate-fade-in">
      <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${config.dot}`} />
      <span className="text-bxs text-black-400 font-medium uppercase tracking-wider">
        Estado da análise:
      </span>
      <span className="text-bxs text-black-200 font-bold">{config.label}</span>
      <span className="text-bxs text-black-500"> — </span>
      <span className="text-bxs text-black-400">{config.reason}</span>
    </div>
  )
}
