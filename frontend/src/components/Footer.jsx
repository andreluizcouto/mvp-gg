// Rodapé institucional com links e o aviso obrigatório da Riot
import { Link } from "react-router-dom"
import Logo from "./Logo"

const LINKS = [
  { label: "Tier list", path: "/tierlist" },
  { label: "Ranking", path: "/leaderboard" },
  { label: "Como funciona", path: "/how-it-works" },
  { label: "App", path: "/download" },
  { label: "Termos de serviço", path: "/terms" },
  { label: "Privacidade", path: "/privacy" },
]

export default function Footer() {
  return (
    <footer className="mt-16 border-t border-white/[0.06] bg-black-800">
      <div className="mx-auto grid max-w-[1200px] grid-cols-1 gap-8 px-4 py-10 md:grid-cols-[1fr_2fr]">
        <div>
          <Logo />
          <p className="mt-3 max-w-xs text-bs text-black-300">
            Estatísticas, tier list da meta e coaching com IA para cada partida de League of Legends.
          </p>
        </div>

        <div className="grid gap-6">
          <nav className="flex flex-wrap gap-x-6 gap-y-3" aria-label="Rodapé">
            {LINKS.map(({ label, path }) => (
              <Link key={path} to={path} className="text-bs font-semibold text-black-200 transition hover:text-purple-300">
                {label}
              </Link>
            ))}
          </nav>
          <p className="text-bxs leading-5 text-black-400">
            mvp.gg não é endossado pela Riot Games e não reflete as opiniões ou visões da Riot Games ou de qualquer
            pessoa oficialmente envolvida na produção ou gerenciamento das propriedades da Riot Games. Riot Games,
            League of Legends e todas as propriedades associadas são marcas registradas ou marcas comerciais da
            Riot Games, Inc. Dados da tier list fornecidos pelo OP.GG.
          </p>
        </div>
      </div>
    </footer>
  )
}
