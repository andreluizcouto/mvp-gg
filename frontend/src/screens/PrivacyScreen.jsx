// Pagina "Privacy Policy"
import React from "react"

const sections = [
  {
    title: "Quais dados podem ser tratados",
    body: [
      "O mvp.gg busca tratar apenas os dados necessarios para operar o servico. Isso pode incluir Riot ID, match ID, estatisticas da partida, dados publicos retornados por integracoes permitidas e, no caso do app local, eventos da partida e imagens temporarias do minimapa usadas para analise pos-jogo.",
      "O projeto nao depende de criacao de conta tradicional no site para consulta publica e evita coletar dados pessoais sensiveis que nao tenham relacao direta com a funcionalidade do produto.",
    ],
  },
  {
    title: "Como os dados sao usados",
    body: [
      "Os dados tratados sao usados para carregar historico de partidas, montar scoreboards, disponibilizar analises salvas, exibir coaching quando existente e melhorar a confiabilidade tecnica do servico.",
      "Tambem podem ser usados para seguranca operacional, incluindo autenticacao tecnica entre componentes, controle de abuso, limitacao de taxa, rastreabilidade por requisicao e investigacao de falhas.",
    ],
  },
  {
    title: "Armazenamento e minimizacao",
    body: [
      "O projeto procura adotar minimizacao de dados e armazenamento restrito ao que e util para a experiencia do usuario e para a operacao da plataforma. Imagens temporarias usadas no fluxo de upload local sao tratadas de forma temporaria e o backend busca remove-las ao final do processamento, inclusive em cenarios de erro.",
      "Analises de coaching e metadados vinculados a partidas podem ser persistidos para consulta posterior, respeitando o escopo tecnico do recurso e os filtros aplicaveis do sistema.",
    ],
  },
  {
    title: "Seguranca",
    body: [
      "O projeto utiliza medidas tecnicas proporcionais ao seu estagio atual, incluindo validacao de entrada, autenticacao por token em rotas internas, separacao entre token interno e token do app local, limitacao de taxa e controles para reduzir uploads maliciosos ou acesso indevido.",
      "Nenhum sistema e absolutamente invulneravel. Por isso, o servico pode evoluir seus controles de seguranca, politicas de retencao e fluxos de acesso sempre que necessario para reduzir risco e proteger melhor os usuarios.",
    ],
  },
]

export default function PrivacyScreen() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-blue-400 mb-3">Politica de Privacidade</h1>
        <p className="text-black-200 leading-7">
          Esta pagina resume como o mvp.gg trata dados tecnicos e informacoes relacionadas a partidas.
          A proposta do projeto e operar com o minimo necessario para entregar estatisticas e analises.
        </p>
      </div>

      <div className="space-y-6">
        {sections.map((section) => (
          <section key={section.title} className="rounded-xl border border-white/5 bg-black-800/40 p-5">
            <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-black-100 mb-3">
              {section.title}
            </h2>
            <div className="space-y-3">
              {section.body.map((paragraph) => (
                <p key={paragraph} className="text-sm leading-7 text-black-200">
                  {paragraph}
                </p>
              ))}
            </div>
          </section>
        ))}
      </div>

      <p className="text-bxs leading-6 text-black-400 mt-8">
        Ultima atualizacao: marco de 2026.
      </p>
    </div>
  )
}
