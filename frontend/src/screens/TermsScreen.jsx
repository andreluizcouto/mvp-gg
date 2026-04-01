// Pagina "Terms of Service"
import React from "react"

const sections = [
  {
    title: "Uso do servico",
    body: [
      "O mvp.gg e uma plataforma independente de analise de partidas de League of Legends. O servico existe para exibir estatisticas, historico de partidas e, quando disponivel, analises automatizadas e recursos de coaching baseados nos dados enviados pelo usuario ou obtidos por integracoes permitidas.",
      "Ao usar o site ou o app local do projeto, voce concorda em utilizar a plataforma apenas para fins legitimos, sem tentar explorar falhas, contornar limites tecnicos, automatizar abuso de consultas ou acessar dados que nao estejam vinculados ao seu uso autorizado.",
    ],
  },
  {
    title: "Disponibilidade e limites",
    body: [
      "Partes do servico dependem de provedores terceiros, incluindo Riot API, infraestrutura de hospedagem e componentes de IA. Por isso, alguns recursos podem ficar indisponiveis, lentos, limitados ou ser alterados sem aviso previo.",
      "O projeto pode aplicar validacoes, autenticacao tecnica, limites de taxa e limites de upload para proteger a infraestrutura, reduzir abuso e preservar a disponibilidade para os demais usuarios.",
    ],
  },
  {
    title: "Conteudo enviado pelo usuario",
    body: [
      "Quando o app local envia dados para analise, o usuario declara que possui autorizacao para processar aquele conteudo dentro do contexto da propria partida. O projeto busca tratar apenas o minimo necessario para gerar estatisticas e coaching, incluindo identificadores de partida, Riot ID, eventos de jogo e, quando aplicavel, imagens temporarias do minimapa.",
      "Voce nao deve enviar conteudo ilicito, malicioso, adulterado para fraude ou projetado para degradar a plataforma, contornar controles de seguranca ou gerar custo indevido de processamento.",
    ],
  },
  {
    title: "Propriedade intelectual e relacao com a Riot",
    body: [
      "O mvp.gg nao e afiliado, endossado ou patrocinado pela Riot Games. Todos os nomes, marcas, personagens, elementos visuais e propriedades relacionadas a League of Legends pertencem aos seus respectivos titulares.",
      "O uso da plataforma nao transfere ao usuario qualquer direito sobre marcas, APIs, conteudo oficial ou ativos de terceiros exibidos por referencia, integracao ou compatibilidade.",
    ],
  },
  {
    title: "Isencao de responsabilidade",
    body: [
      "As analises, recomendacoes e textos de coaching oferecidos pelo projeto possuem carater informativo e experimental. Eles nao constituem promessa de resultado, ranking, melhoria competitiva garantida ou avaliacao oficial da Riot Games.",
      "Na extensao permitida pela legislacao aplicavel, o servico e fornecido no estado em que se encontra, sem garantias absolutas de disponibilidade, precisao, continuidade ou adequacao a um objetivo especifico.",
    ],
  },
]

export default function TermsScreen() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-blue-400 mb-3">Termos de Servico</h1>
        <p className="text-black-200 leading-7">
          Estes termos descrevem as regras gerais de uso do mvp.gg e do app local associado ao projeto.
          Ao continuar utilizando a plataforma, voce concorda com estas condicoes.
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

      <p className="text-[11px] leading-6 text-black-400 mt-8">
        Ultima atualizacao: marco de 2026.
      </p>
    </div>
  )
}
