import { useEffect, useState } from "react"

const STEPS = [
  { icon: "⚔️",  text: "Buscando histórico de partidas..." },
  { icon: "📊",  text: "Calculando geometria das waves..." },
  { icon: "🗺️",  text: "Analisando controle de visão..." },
  { icon: "🎯",  text: "Avaliando participação em objetivos..." },
  { icon: "🤖",  text: "Gerando análise com IA..." },
  { icon: "✅",  text: "Finalizando relatório de análise..." },
]

export default function LoadingScreen({ player, title }) {
  const [stepIndex, setStepIndex] = useState(0)
  const [progress,  setProgress]  = useState(0)
  const [dots,      setDots]      = useState("")

  useEffect(() => {
    const i = setInterval(() => setStepIndex(s => (s + 1) % STEPS.length), 600)
    return () => clearInterval(i)
  }, [])

  useEffect(() => {
    const i = setInterval(() => setProgress(p => p >= 88 ? p : p + (88 - p) * 0.04 + 0.3), 180)
    return () => clearInterval(i)
  }, [])

  useEffect(() => {
    const i = setInterval(() => setDots(d => d.length >= 3 ? "" : d + "."), 400)
    return () => clearInterval(i)
  }, [])

  const currentStep = STEPS[stepIndex]

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4 relative overflow-hidden">
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        {[0,1,2].map(i => (
          <div key={i} className="absolute rounded-full border border-blue-400/10"
            style={{ width: `${320+i*140}px`, height: `${320+i*140}px`, animation: `pulseDot ${2+i*0.6}s ease-in-out ${i*0.4}s infinite` }} />
        ))}
      </div>

      <div className="relative z-10 w-full max-w-sm text-center">
        <div className="flex items-center justify-center mb-8">
          <div className="relative w-24 h-24">
            <svg className="absolute inset-0 animate-spin-slow" viewBox="0 0 96 96">
              <polygon points="48,4 92,26 92,70 48,92 4,70 4,26" fill="none" stroke="#33D1C1" strokeWidth="1.5" strokeDasharray="8 4" opacity="0.6"/>
            </svg>
            <svg className="absolute inset-0" style={{ animation: "spin 4s linear infinite reverse" }} viewBox="0 0 96 96">
              <polygon points="48,16 74,30 74,58 48,72 22,58 22,30" fill="none" stroke="#33D1C1" strokeWidth="1" opacity="0.35"/>
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-2xl select-none">{currentStep.icon}</span>
            </div>
          </div>
        </div>

        {player && <p className="font-mono text-xs text-blue-400/80 tracking-widest uppercase mb-1">{player.nick}</p>}

        <h2 className="font-extrabold text-2xl uppercase tracking-wide text-white/90 mb-6">
          {title ?? "Analisando Invocador"}{dots}
        </h2>

        <div className="h-6 mb-6 overflow-hidden">
          <p key={stepIndex} className="text-sm text-white/45 animate-fade-up">{currentStep.text}</p>
        </div>

        <div className="w-full bg-black-600 rounded-full h-1.5 overflow-hidden border border-blue-400/10">
          <div className="h-full rounded-full transition-all duration-300"
            style={{ width: `${progress}%`, background: "linear-gradient(90deg, #243497, #16B2A4, #33D1C1)", boxShadow: "0 0 10px #33D1C188" }} />
        </div>
        <div className="flex justify-between mt-1.5">
          <span className="font-mono text-bxs text-white/25">0%</span>
          <span className="font-mono text-bxs text-blue-400/60">{Math.round(progress)}%</span>
        </div>

        <p className="mt-8 text-xs text-white/20 leading-relaxed">
          A análise pode levar até 30 segundos.<br/>
          Calculando geometria de wave e gerando insights com IA.
        </p>
      </div>
    </div>
  )
}
