import { useState } from "react"
import { DDV } from "../services/constants"

const LANE_LABELS = {
  TOP: "TOP",
  JUNGLE: "JG",
  MIDDLE: "MID",
  BOTTOM: "BOT",
  UTILITY: "SUP",
}

const TIER_COLORS = {
  "S+": "#FF7043",
  S: "#7989EC",
  A: "#4AC97E",
  B: "#FFD147",
  C: "#9B9C9E",
  D: "#F03A38",
}

const MOCK_CHAMPIONS = [
  { rank: 1, name: "Nami", lane: "UTILITY", tier: "S+", winRate: 51.8, pickRate: 17.0 },
  { rank: 2, name: "Jinx", lane: "BOTTOM", tier: "S+", winRate: 51.6, pickRate: 15.1 },
  { rank: 3, name: "Graves", lane: "JUNGLE", tier: "S+", winRate: 50.6, pickRate: 13.1 },
  { rank: 4, name: "Ahri", lane: "MIDDLE", tier: "S+", winRate: 52.1, pickRate: 11.8 },
  { rank: 5, name: "Jax", lane: "TOP", tier: "S+", winRate: 51.3, pickRate: 10.5 },
  { rank: 6, name: "Thresh", lane: "UTILITY", tier: "S", winRate: 50.9, pickRate: 14.2 },
  { rank: 7, name: "Kaisa", lane: "BOTTOM", tier: "S", winRate: 50.7, pickRate: 16.3 },
  { rank: 8, name: "LeeSin", lane: "JUNGLE", tier: "S", winRate: 49.8, pickRate: 18.7 },
  { rank: 9, name: "Syndra", lane: "MIDDLE", tier: "S", winRate: 50.4, pickRate: 9.6 },
  { rank: 10, name: "Camille", lane: "TOP", tier: "S", winRate: 51.0, pickRate: 7.8 },
  { rank: 11, name: "Lulu", lane: "UTILITY", tier: "S", winRate: 50.5, pickRate: 12.1 },
  { rank: 12, name: "Lucian", lane: "BOTTOM", tier: "S", winRate: 49.9, pickRate: 13.4 },
  { rank: 13, name: "Viego", lane: "JUNGLE", tier: "A", winRate: 50.2, pickRate: 11.0 },
  { rank: 14, name: "Orianna", lane: "MIDDLE", tier: "A", winRate: 50.8, pickRate: 6.5 },
  { rank: 15, name: "Darius", lane: "TOP", tier: "A", winRate: 51.2, pickRate: 8.9 },
  { rank: 16, name: "Nautilus", lane: "UTILITY", tier: "A", winRate: 50.1, pickRate: 9.3 },
  { rank: 17, name: "Ezreal", lane: "BOTTOM", tier: "A", winRate: 49.5, pickRate: 19.2 },
  { rank: 18, name: "Elise", lane: "JUNGLE", tier: "A", winRate: 51.4, pickRate: 5.7 },
  { rank: 19, name: "Zed", lane: "MIDDLE", tier: "A", winRate: 49.7, pickRate: 14.8 },
  { rank: 20, name: "Fiora", lane: "TOP", tier: "A", winRate: 50.3, pickRate: 7.1 },
  { rank: 21, name: "Senna", lane: "UTILITY", tier: "B", winRate: 49.8, pickRate: 10.4 },
  { rank: 22, name: "MissFortune", lane: "BOTTOM", tier: "B", winRate: 50.0, pickRate: 11.6 },
  { rank: 23, name: "Khazix", lane: "JUNGLE", tier: "B", winRate: 49.6, pickRate: 8.2 },
  { rank: 24, name: "Viktor", lane: "MIDDLE", tier: "B", winRate: 49.3, pickRate: 5.4 },
  { rank: 25, name: "Garen", lane: "TOP", tier: "B", winRate: 51.5, pickRate: 6.0 },
  { rank: 26, name: "Blitzcrank", lane: "UTILITY", tier: "C", winRate: 49.1, pickRate: 7.5 },
  { rank: 27, name: "Draven", lane: "BOTTOM", tier: "C", winRate: 49.0, pickRate: 5.8 },
  { rank: 28, name: "Nidalee", lane: "JUNGLE", tier: "C", winRate: 48.2, pickRate: 4.3 },
  { rank: 29, name: "Ryze", lane: "MIDDLE", tier: "D", winRate: 46.8, pickRate: 3.1 },
  { rank: 30, name: "KSante", lane: "TOP", tier: "D", winRate: 47.1, pickRate: 4.6 },
]

const RANK_FILTERS = ["EMERALD+", "DIAMOND+", "MASTER+", "GRANDMASTER+", "CHALLENGER"]
const REGION_FILTERS = ["ALL", "BR", "NA", "EUW", "KR"]
const MODE_TABS = ["Ranked", "Arena", "ARAM"]

function getChampionImage(name) {
  return `https://ddragon.leagueoflegends.com/cdn/${DDV}/img/champion/${name}.png`
}

export default function TierlistScreen() {
  const [activeRank] = useState("EMERALD+")
  const [activeRegion] = useState("ALL")
  const [activeMode] = useState("Ranked")

  return (
    <div className="max-w-[1200px] mx-auto px-4 py-8">
      {/* Hero Section */}
      <section
        className="animate-fade-up bg-black-800 rounded-xl shadow-[0_2px_8px_rgba(121,137,236,0.10)] p-6 lg:p-10 mb-6 flex flex-col lg:flex-row items-center gap-6 overflow-hidden"
      >
        <div className="flex-1 min-w-0">
          <h1 className="text-hxl text-black-0 font-semibold mb-1">Tierlist & Builds</h1>
          <p className="text-bm text-black-300 mb-4">Emerald+, Patch {DDV}</p>

          <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-lg px-3 py-1.5 mb-4">
            <span className="text-bxs text-blue-400 font-semibold tracking-wider uppercase">Champions Analyzed</span>
            <span className="text-bs text-black-0 font-semibold">21,927,120</span>
          </div>

          <p className="text-bs text-black-200 leading-relaxed max-w-xl">
            Explore a Tierlist do MVP.GG para League of Legends, atualizada ao vivo com os melhores campeões para cada role.
            Dados coletados de partidas ranqueadas Emerald+ em todos os servidores.
          </p>
        </div>

        <div className="hidden lg:block flex-shrink-0 w-48 h-48 relative">
          <img
            src={getChampionImage("Jinx")}
            alt="Decorative champion"
            className="w-full h-full object-cover rounded-xl opacity-60"
          />
          <div className="absolute inset-0 bg-gradient-to-l from-transparent to-black-800 rounded-xl" />
        </div>
      </section>

      {/* Filters Row */}
      <section
        className="animate-fade-up bg-black-800 rounded-xl shadow-[0_2px_8px_rgba(121,137,236,0.10)] p-4 mb-6 flex flex-col gap-4"
        style={{ animationDelay: "0.1s" }}
      >
        {/* Game Mode Tabs */}
        <div className="flex items-center gap-2">
          {MODE_TABS.map((mode) => (
            <button
              key={mode}
              className={`px-4 py-1.5 rounded-lg text-bs font-semibold transition-colors ${
                activeMode === mode
                  ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                  : "bg-black-600 text-black-300 border border-transparent hover:text-black-200"
              }`}
            >
              {mode}
            </button>
          ))}
        </div>

        {/* Rank + Region Filters */}
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-bxs text-black-400 uppercase tracking-wider mr-1">Rank</span>
          {RANK_FILTERS.map((rank) => (
            <button
              key={rank}
              className={`px-3 py-1 rounded-lg text-bxs font-semibold transition-colors ${
                activeRank === rank
                  ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                  : "bg-black-600 text-black-300 border border-transparent hover:text-black-200"
              }`}
            >
              {rank}
            </button>
          ))}

          <div className="w-px h-5 bg-black-500 mx-2 hidden lg:block" />

          <span className="text-bxs text-black-400 uppercase tracking-wider mr-1">Region</span>
          {REGION_FILTERS.map((region) => (
            <button
              key={region}
              className={`px-3 py-1 rounded-lg text-bxs font-semibold transition-colors ${
                activeRegion === region
                  ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                  : "bg-black-600 text-black-300 border border-transparent hover:text-black-200"
              }`}
            >
              {region}
            </button>
          ))}
        </div>
      </section>

      {/* Champions Table */}
      <section
        className="animate-fade-up bg-black-800 rounded-xl shadow-[0_2px_8px_rgba(121,137,236,0.10)] overflow-hidden"
        style={{ animationDelay: "0.2s" }}
      >
        <div className="overflow-x-auto">
          <table className="w-full min-w-[540px]">
            <thead>
              <tr className="border-b border-black-500/50">
                <th className="text-bxs text-black-400 font-semibold uppercase tracking-wider text-left py-3 px-4 w-12">#</th>
                <th className="text-bxs text-black-400 font-semibold uppercase tracking-wider text-left py-3 px-4">Champion</th>
                <th className="text-bxs text-black-400 font-semibold uppercase tracking-wider text-center py-3 px-4 w-16">Lane</th>
                <th className="text-bxs text-black-400 font-semibold uppercase tracking-wider text-center py-3 px-4 w-16">Tier</th>
                <th className="text-bxs text-black-400 font-semibold uppercase tracking-wider text-right py-3 px-4 w-24">Win Rate</th>
                <th className="text-bxs text-black-400 font-semibold uppercase tracking-wider text-right py-3 px-4 w-24 hidden lg:table-cell">Pick Rate</th>
              </tr>
            </thead>
            <tbody>
              {MOCK_CHAMPIONS.map((champ, i) => (
                <tr
                  key={champ.rank}
                  className={`border-b border-black-500/20 hover:bg-black-600/50 transition-colors ${
                    i % 2 === 0 ? "bg-black-800" : "bg-black-800/60"
                  }`}
                >
                  {/* Rank */}
                  <td className="py-2.5 px-4 text-bs text-black-300 font-semibold">{champ.rank}</td>

                  {/* Champion */}
                  <td className="py-2.5 px-4">
                    <div className="flex items-center gap-3">
                      <img
                        src={getChampionImage(champ.name)}
                        alt={champ.name}
                        className="w-8 h-8 rounded-lg"
                      />
                      <span className="text-bs text-black-0 font-semibold">
                        {champ.name === "MissFortune" ? "Miss Fortune" : champ.name === "LeeSin" ? "Lee Sin" : champ.name === "KSante" ? "K'Sante" : champ.name === "Khazix" ? "Kha'Zix" : champ.name}
                      </span>
                    </div>
                  </td>

                  {/* Lane */}
                  <td className="py-2.5 px-4 text-center">
                    <span className="inline-block bg-black-600 text-black-300 text-bxs font-semibold px-2 py-0.5 rounded">
                      {LANE_LABELS[champ.lane]}
                    </span>
                  </td>

                  {/* Tier */}
                  <td className="py-2.5 px-4 text-center">
                    <span
                      className="text-bs font-bold"
                      style={{ color: TIER_COLORS[champ.tier] }}
                    >
                      {champ.tier}
                    </span>
                  </td>

                  {/* Win Rate */}
                  <td className="py-2.5 px-4 text-right">
                    <span className={`text-bs font-semibold ${champ.winRate >= 51 ? "text-green-600" : champ.winRate >= 50 ? "text-black-200" : "text-red-600"}`}>
                      {champ.winRate.toFixed(1)}%
                    </span>
                  </td>

                  {/* Pick Rate */}
                  <td className="py-2.5 px-4 text-right hidden lg:table-cell">
                    <span className="text-bs text-black-300">{champ.pickRate.toFixed(1)}%</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
