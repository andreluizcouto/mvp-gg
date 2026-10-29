import React from "react"
import { APP_DOWNLOAD_URL } from "../services/api"

export default function DownloadScreen() {
  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      <h1 className="text-2xl font-bold text-blue-400 mb-4">Download</h1>
      <p className="text-black-200 mb-4">
        Baixe o mvp.gg App para desbloquear o coaching de IA completo e receber dicas exclusivas após cada partida.
      </p>
      <a
        href={APP_DOWNLOAD_URL}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-block bg-blue-500 text-white font-bold px-6 py-2 rounded hover:bg-blue-600 transition-colors"
      >
        Baixar mvp.gg App - grátis
      </a>
      <p className="text-black-300 text-xs mt-4">Disponível para Windows. Versão Mac em breve.</p>
    </div>
  )
}
