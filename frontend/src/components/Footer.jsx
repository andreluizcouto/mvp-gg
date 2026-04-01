// Footer institucional com links e disclaimer Riot
import React from "react"
import { useNavigate } from "react-router-dom"

export default function Footer() {
  const navigate = useNavigate()

  return (
    <footer className="bg-black-800 border-t border-black-600 text-black-300 text-xs py-6 px-4 mt-10">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center md:items-start justify-between gap-4 md:gap-8">
        <div className="flex flex-wrap gap-4 mb-1 md:mb-0">
          <button onClick={() => navigate("/how-it-works")} className="hover:text-blue-400 underline">
            Como funciona
          </button>
          <button onClick={() => navigate("/download")} className="hover:text-blue-400 underline">
            Download
          </button>
          <button onClick={() => navigate("/terms")} className="hover:text-blue-400 underline">
            Termos de Servico
          </button>
          <button onClick={() => navigate("/privacy")} className="hover:text-blue-400 underline">
            Privacidade
          </button>
        </div>

        <div className="w-full max-w-3xl">
          <p className="text-left text-[10px] leading-4 text-black-400 md:text-[11px]">
            mvp.gg nao e endossado pela Riot Games e nao reflete as opinioes ou visoes da Riot Games ou
            de qualquer pessoa oficialmente envolvida na producao ou gerenciamento das propriedades da
            Riot Games. Riot Games, League of Legends e todas as propriedades associadas sao marcas
            registradas ou marcas comerciais da Riot Games, Inc.
          </p>
        </div>
      </div>
    </footer>
  )
}
