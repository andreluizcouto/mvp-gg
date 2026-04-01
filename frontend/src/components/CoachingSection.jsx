import { useState } from "react"
import { APP_DOWNLOAD_URL } from "../services/api"

// ── Shared card shell ──────────────────────────────────────────────────────────
// All coaching states (locked or unlocked) use this outer wrapper for consistency.
function CoachingCard({ children, unlocked = false }) {
  return (
    <div className={`border rounded-xl overflow-hidden ${unlocked ? "border-blue-400/20 bg-black-800" : "border-white/7"}`}>
      {children}
    </div>
  )
}

function CoachingHeader({ label, active = false }) {
  return (
    <div className="bg-black-700 px-4 py-2.5 border-b border-white/6 flex items-center gap-2.5">
      <span className="text-base">🤖</span>
      <span className={`text-bxs font-bold uppercase tracking-widest ${active ? "text-blue-400" : "text-black-400"}`}>
        {label}
      </span>
      {active && (
        <span className="bg-blue-400/15 text-blue-400 text-[9px] px-2 py-0.5 rounded-full font-semibold tracking-wide">
          mvp.gg App
        </span>
      )}
    </div>
  )
}

// ── State: ready ───────────────────────────────────────────────────────────────
function parseAnalysisSections(text) {
  if (!text) return []
  const parts = text.split(/(?=##\s+\d+\.)/)
  return parts
    .filter(p => p.trim())
    .map(p => {
      const titleMatch = p.match(/##\s+\d+\.\s+(.+)/)
      return {
        title: titleMatch ? titleMatch[1].trim() : "Análise",
        content: p.replace(/##\s+\d+\.\s+.+\n?/, "").trim(),
      }
    })
}

function UnlockedCoaching({ analysis }) {
  const sections = parseAnalysisSections(analysis)
  const tabs = sections.length > 0 ? sections : [{ title: "Resumo", content: analysis }]
  const [activeTab, setActiveTab] = useState(0)

  return (
    <CoachingCard unlocked>
      <CoachingHeader label="COACHING IA" active />
      <div className="flex border-b border-white/6 overflow-x-auto">
        {tabs.map((tab, i) => (
          <button
            key={i}
            onClick={() => setActiveTab(i)}
            title={tab.title}
            className={`px-3.5 py-2 text-[11px] whitespace-nowrap border-b-2 transition-colors cursor-pointer ${
              activeTab === i
                ? "font-bold text-blue-400 border-blue-400"
                : "font-normal text-white/30 border-transparent hover:text-white/50"
            }`}
          >
            {tab.title.length > 20 ? tab.title.slice(0, 20) + "…" : tab.title}
          </button>
        ))}
      </div>
      <div className="p-4 max-h-[400px] overflow-y-auto">
        <p className="text-black-200 text-[13px] leading-[1.75] whitespace-pre-wrap">
          {tabs[activeTab]?.content}
        </p>
      </div>
    </CoachingCard>
  )
}

// ── State: pending (D-06) ──────────────────────────────────────────────────────
function PendingCoaching() {
  return (
    <CoachingCard>
      <CoachingHeader label="COACHING IA" active={false} />
      <div className="p-6 bg-black-800 text-center">
        <div className="flex items-center justify-center gap-2 mb-2">
          <span className="text-[28px]">🕐</span>
          <div className="w-1.5 h-1.5 rounded-full bg-yellow-400 animate-pulse-dot flex-shrink-0" />
        </div>
        <p className="text-bm text-black-200 font-bold mb-1">Análise em andamento</p>
        <p className="text-bxs text-black-400">Isso pode levar alguns segundos — recarregue a página em breve.</p>
      </div>
    </CoachingCard>
  )
}

// ── State: failed (D-06) ───────────────────────────────────────────────────────
function FailedCoaching() {
  return (
    <CoachingCard>
      <CoachingHeader label="COACHING IA" active={false} />
      <div className="p-6 bg-black-800 text-center">
        <span className="text-[28px] block mb-2">⚠️</span>
        <p className="text-bm text-black-200 font-bold mb-1">Não foi possível gerar a análise</p>
        <p className="text-bxs text-black-400">O sistema encontrou um problema ao processar esta partida.</p>
      </div>
    </CoachingCard>
  )
}

// ── State: unavailable / insufficient_data (D-07) ─────────────────────────────
// Fixed copy — do not alter per D-07.
function UnavailableCoaching() {
  return (
    <CoachingCard>
      <CoachingHeader label="COACHING IA" active={false} />
      <div className="p-6 bg-black-800 text-center">
        <span className="text-[22px] block mb-2">🔒</span>
        <p className="text-bxs text-black-300 mb-3">
          Coach indisponivel, baixe o app e jogue uma partida.
        </p>
        <a
          href={APP_DOWNLOAD_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block bg-blue-500 text-white text-[11px] font-bold px-5 py-1.5 rounded-md no-underline tracking-wide hover:bg-blue-600 transition-colors"
        >
          Baixar mvp.gg App — grátis
        </a>
      </div>
    </CoachingCard>
  )
}

// ── State: private / shared link without owner context (D-08) ─────────────────
// Fixed copy — do not alter per D-08.
function PrivateCoaching() {
  return (
    <CoachingCard>
      <CoachingHeader label="COACHING IA" active={false} />
      <div className="p-5 bg-black-800 text-center">
        <span className="text-[22px] block mb-2">🔒</span>
        <p className="text-bm text-black-200 font-bold">Análise privada para este jogador</p>
        <p className="text-bxs text-black-400 mt-1">Esta análise só está disponível para o dono da conta.</p>
      </div>
    </CoachingCard>
  )
}

// ── State: loading ─────────────────────────────────────────────────────────────
function LoadingCoaching() {
  return (
    <div className="border border-white/6 rounded-xl p-6 text-center text-black-400 text-bs">
      Carregando análise...
    </div>
  )
}

// ── Export ─────────────────────────────────────────────────────────────────────
// status prop: "ready" | "pending" | "failed" | "insufficient_data" | "private" | null
// When status is null/undefined and hasAnalysis is false, defaults to UnavailableCoaching.
export default function CoachingSection({ analysis, hasAnalysis, loading, status }) {
  if (loading) return <LoadingCoaching />
  if (hasAnalysis && analysis && status === "ready") return <UnlockedCoaching analysis={analysis} />
  if (status === "pending") return <PendingCoaching />
  if (status === "failed") return <FailedCoaching />
  if (status === "insufficient_data") return <UnavailableCoaching />
  if (status === "private") return <PrivateCoaching />
  // Default fallback for any unknown/null status without analysis
  return <UnavailableCoaching />
}
