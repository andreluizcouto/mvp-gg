// Pagina "How it Works"
import React from "react"

const steps = [
  {
    title: "1. Consulte o site normalmente",
    body:
      "No mvp.gg voce pode pesquisar um invocador, ver historico recente, scoreboards e estatisticas publicas da partida sem precisar instalar nada.",
  },
  {
    title: "2. Use o app local para coaching expandido",
    body:
      "Se quiser uma leitura pos-jogo mais detalhada, o app local acompanha a partida, detecta eventos relevantes e coleta apenas o minimapa em momentos especificos do jogo.",
  },
  {
    title: "3. O processamento acontece no fim da partida",
    body:
      "Quando a partida termina, o app envia os dados necessarios para o backend e a analise de coaching pode ser salva para consulta posterior no site.",
  },
  {
    title: "4. Os arquivos temporarios nao ficam parados",
    body:
      "As imagens usadas nesse fluxo sao temporarias e o backend busca remove-las ao final do processamento, inclusive em cenarios de erro, para reduzir exposicao desnecessaria.",
  },
]

const highlights = [
  "O app nao precisa capturar a tela inteira para operar o fluxo atual de coaching.",
  "O backend aplica autenticacao tecnica, validacao de entrada e limitacao de taxa para reduzir abuso.",
  "Os tokens do app local e das rotas internas agora ficam separados, o que melhora o isolamento de acesso.",
]

export default function HowItWorksScreen() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-blue-400 mb-3">Como funciona o mvp.gg</h1>
        <p className="text-black-200 leading-7">
          O projeto combina leitura de estatisticas publicas com um fluxo opcional de coaching expandido
          via app local. A ideia e manter a consulta simples no site e deixar o processamento adicional
          restrito ao momento em que ele realmente faz sentido.
        </p>
      </div>

      <div className="space-y-4 mb-8">
        {steps.map((step) => (
          <section key={step.title} className="rounded-xl border border-white/5 bg-black-800/40 p-5">
            <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-black-100 mb-3">
              {step.title}
            </h2>
            <p className="text-sm leading-7 text-black-200">{step.body}</p>
          </section>
        ))}
      </div>

      <section className="rounded-xl border border-blue-400/15 bg-blue-400/[0.04] p-5">
        <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-blue-300 mb-3">
          Pontos importantes
        </h2>
        <ul className="space-y-3 text-sm leading-7 text-black-200">
          {highlights.map((item) => (
            <li key={item} className="flex gap-3">
              <span className="mt-2 h-1.5 w-1.5 rounded-full bg-blue-400 flex-shrink-0" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
