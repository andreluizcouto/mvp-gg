import { useState } from "react"
import { DDV } from "../services/constants"
import { TIER_COLORS } from "../services/utils"

const MOCK_PLAYERS = [
  { rank: 1, name: "Kojima", tag: "BR1", lp: 3321, games: 264, winRate: 65, tier: "CHALLENGER", profileIcon: 29, topChampions: ["Riven", "MasterYi", "Vayne", "Lucian"], kda: "3.8" },
  { rank: 2, name: "Tinowns", tag: "MID1", lp: 3198, games: 312, winRate: 62, tier: "CHALLENGER", profileIcon: 685, topChampions: ["Azir", "Orianna", "Syndra", "Viktor"], kda: "4.2" },
  { rank: 3, name: "Robo", tag: "SUP1", lp: 3045, games: 289, winRate: 61, tier: "CHALLENGER", profileIcon: 4568, topChampions: ["Thresh", "Nautilus", "Leona", "Alistar"], kda: "3.5" },
  { rank: 4, name: "Cblol", tag: "TOP1", lp: 2987, games: 245, winRate: 60, tier: "CHALLENGER", profileIcon: 5367, topChampions: ["Gnar", "Renekton", "Jayce", "Camille"], kda: "3.1" },
  { rank: 5, name: "Aegis", tag: "JG01", lp: 2876, games: 302, winRate: 58, tier: "CHALLENGER", profileIcon: 4405, topChampions: ["LeeSin", "Viego", "Graves", "Nidalee"], kda: "3.6" },
  { rank: 6, name: "Titan", tag: "ADC1", lp: 2801, games: 278, winRate: 59, tier: "CHALLENGER", profileIcon: 5066, topChampions: ["Jinx", "Kaisa", "Aphelios", "Ezreal"], kda: "4.0" },
  { rank: 7, name: "Dynamo", tag: "MID2", lp: 2745, games: 231, winRate: 57, tier: "CHALLENGER", profileIcon: 5317, topChampions: ["LeBlanc", "Akali", "Zed", "Ahri"], kda: "3.4" },
  { rank: 8, name: "Netuno", tag: "BR2", lp: 2690, games: 298, winRate: 56, tier: "CHALLENGER", profileIcon: 4898, topChampions: ["Rengar", "Khazix", "Elise", "RekSai"], kda: "3.2" },
  { rank: 9, name: "Parang", tag: "TOP2", lp: 2634, games: 256, winRate: 58, tier: "CHALLENGER", profileIcon: 5195, topChampions: ["Aatrox", "KSante", "Jax", "Fiora"], kda: "2.9" },
  { rank: 10, name: "Wizer", tag: "TOP3", lp: 2578, games: 287, winRate: 55, tier: "CHALLENGER", profileIcon: 4787, topChampions: ["Gangplank", "Gwen", "Rumble", "Gragas"], kda: "3.0" },
  { rank: 11, name: "Flare", tag: "SUP2", lp: 2501, games: 310, winRate: 54, tier: "GRANDMASTER", profileIcon: 29, topChampions: ["Rakan", "Lulu", "Karma", "Janna"], kda: "3.7" },
  { rank: 12, name: "Guigo", tag: "JG02", lp: 2456, games: 265, winRate: 56, tier: "GRANDMASTER", profileIcon: 685, topChampions: ["Jarvan", "Vi", "Sejuani", "Wukong"], kda: "3.3" },
  { rank: 13, name: "Spark", tag: "ADC2", lp: 2398, games: 241, winRate: 55, tier: "GRANDMASTER", profileIcon: 4568, topChampions: ["Xayah", "Tristana", "MissFortune", "Samira"], kda: "3.9" },
  { rank: 14, name: "Avenger", tag: "MID3", lp: 2345, games: 290, winRate: 53, tier: "GRANDMASTER", profileIcon: 5367, topChampions: ["Yasuo", "Yone", "Katarina", "Talon"], kda: "3.1" },
  { rank: 15, name: "Kami", tag: "MID4", lp: 2290, games: 318, winRate: 54, tier: "GRANDMASTER", profileIcon: 4405, topChampions: ["Cassiopeia", "Ryze", "Veigar", "Anivia"], kda: "3.5" },
  { rank: 16, name: "Disamis", tag: "SUP3", lp: 2234, games: 273, winRate: 52, tier: "GRANDMASTER", profileIcon: 5066, topChampions: ["Pyke", "Bard", "Senna", "Zyra"], kda: "3.0" },
  { rank: 17, name: "Envy", tag: "JG03", lp: 2189, games: 255, winRate: 53, tier: "GRANDMASTER", profileIcon: 5317, topChampions: ["Hecarim", "Lillia", "Diana", "Fiddlesticks"], kda: "3.2" },
  { rank: 18, name: "Grevthar", tag: "TOP4", lp: 2145, games: 248, winRate: 51, tier: "GRANDMASTER", profileIcon: 4898, topChampions: ["Sett", "Mordekaiser", "Darius", "Urgot"], kda: "2.8" },
  { rank: 19, name: "Tutsz", tag: "ADC3", lp: 2098, games: 300, winRate: 52, tier: "GRANDMASTER", profileIcon: 5195, topChampions: ["Draven", "Jhin", "Caitlyn", "Zeri"], kda: "3.6" },
  { rank: 20, name: "Yuri", tag: "MID5", lp: 2056, games: 268, winRate: 51, tier: "GRANDMASTER", profileIcon: 4787, topChampions: ["Corki", "Galio", "TwistedFate", "Malzahar"], kda: "2.9" },
  { rank: 21, name: "Ranger", tag: "JG04", lp: 1998, games: 285, winRate: 52, tier: "MASTER", profileIcon: 29, topChampions: ["Kindred", "Taliyah", "Ekko", "Zac"], kda: "3.1" },
  { rank: 22, name: "Hauz", tag: "SUP4", lp: 1956, games: 240, winRate: 50, tier: "MASTER", profileIcon: 685, topChampions: ["Renata", "Milio", "Soraka", "Nami"], kda: "3.4" },
  { rank: 23, name: "Croc", tag: "TOP5", lp: 1912, games: 261, winRate: 51, tier: "MASTER", profileIcon: 4568, topChampions: ["Ornn", "Malphite", "Sion", "Poppy"], kda: "2.7" },
  { rank: 24, name: "Luci", tag: "ADC4", lp: 1867, games: 292, winRate: 50, tier: "MASTER", profileIcon: 5367, topChampions: ["Lucian", "Vayne", "Kogmaw", "Varus"], kda: "3.5" },
  { rank: 25, name: "Damage", tag: "MID6", lp: 1823, games: 277, winRate: 49, tier: "MASTER", profileIcon: 4405, topChampions: ["Syndra", "Lux", "Xerath", "Ziggs"], kda: "3.0" },
  { rank: 26, name: "Bankai", tag: "JG05", lp: 1780, games: 253, winRate: 50, tier: "MASTER", profileIcon: 5066, topChampions: ["Nocturne", "Shyvana", "Volibear", "Udyr"], kda: "2.8" },
  { rank: 27, name: "NexusBR", tag: "TOP6", lp: 1745, games: 267, winRate: 49, tier: "MASTER", profileIcon: 5317, topChampions: ["Irelia", "Riven", "Tryndamere", "Nasus"], kda: "2.9" },
  { rank: 28, name: "Ignis", tag: "SUP5", lp: 1698, games: 244, winRate: 48, tier: "MASTER", profileIcon: 4898, topChampions: ["Thresh", "Blitzcrank", "Leona", "Braum"], kda: "3.3" },
  { rank: 29, name: "Astra", tag: "ADC5", lp: 1656, games: 306, winRate: 49, tier: "MASTER", profileIcon: 5195, topChampions: ["Jinx", "Aphelios", "Kaisa", "Sivir"], kda: "3.7" },
  { rank: 30, name: "Turbo", tag: "MID7", lp: 1612, games: 238, winRate: 48, tier: "MASTER", profileIcon: 4787, topChampions: ["Zed", "Qiyana", "Fizz", "Kassadin"], kda: "3.2" },
  { rank: 31, name: "Polaris", tag: "JG06", lp: 1578, games: 281, winRate: 48, tier: "MASTER", profileIcon: 29, topChampions: ["LeeSin", "Viego", "Belveth", "Kayn"], kda: "2.7" },
  { rank: 32, name: "ShenBR", tag: "TOP7", lp: 1534, games: 259, winRate: 47, tier: "MASTER", profileIcon: 685, topChampions: ["Shen", "TahmKench", "Chogath", "Maokai"], kda: "2.5" },
  { rank: 33, name: "Bardo", tag: "SUP6", lp: 1490, games: 295, winRate: 48, tier: "MASTER", profileIcon: 4568, topChampions: ["Bard", "Pyke", "Rakan", "Thresh"], kda: "3.1" },
  { rank: 34, name: "Crespo", tag: "ADC6", lp: 1445, games: 250, winRate: 47, tier: "MASTER", profileIcon: 5367, topChampions: ["Ezreal", "Xayah", "Tristana", "Jhin"], kda: "3.4" },
  { rank: 35, name: "Phantom", tag: "MID8", lp: 1412, games: 274, winRate: 46, tier: "MASTER", profileIcon: 4405, topChampions: ["Ahri", "Lissandra", "Neeko", "Annie"], kda: "2.8" },
  { rank: 36, name: "Hades", tag: "JG07", lp: 1378, games: 263, winRate: 47, tier: "MASTER", profileIcon: 5066, topChampions: ["Warwick", "Amumu", "Rammus", "Nunu"], kda: "2.6" },
  { rank: 37, name: "Rugal", tag: "TOP8", lp: 1334, games: 246, winRate: 46, tier: "MASTER", profileIcon: 5317, topChampions: ["Kennen", "Quinn", "Teemo", "Vayne"], kda: "2.9" },
  { rank: 38, name: "Zenith", tag: "SUP7", lp: 1298, games: 288, winRate: 46, tier: "MASTER", profileIcon: 4898, topChampions: ["Lulu", "Janna", "Yuumi", "Sona"], kda: "3.5" },
  { rank: 39, name: "ReiDaBala", tag: "ADC7", lp: 1256, games: 252, winRate: 47, tier: "MASTER", profileIcon: 5195, topChampions: ["MissFortune", "Samira", "Kalista", "Twitch"], kda: "3.0" },
  { rank: 40, name: "Arcano", tag: "MID9", lp: 1212, games: 269, winRate: 45, tier: "MASTER", profileIcon: 4787, topChampions: ["Viktor", "Azir", "Orianna", "Cassiopeia"], kda: "2.7" },
  { rank: 41, name: "Brutus", tag: "JG08", lp: 1178, games: 237, winRate: 46, tier: "MASTER", profileIcon: 29, topChampions: ["Xin", "JarvanIV", "Pantheon", "Vi"], kda: "2.5" },
  { rank: 42, name: "DarkSun", tag: "TOP9", lp: 1134, games: 258, winRate: 45, tier: "MASTER", profileIcon: 685, topChampions: ["Aatrox", "Renekton", "Gnar", "Jayce"], kda: "2.6" },
  { rank: 43, name: "Coral", tag: "SUP8", lp: 1098, games: 279, winRate: 45, tier: "MASTER", profileIcon: 4568, topChampions: ["Nautilus", "Alistar", "Rell", "Braum"], kda: "2.9" },
  { rank: 44, name: "Kross", tag: "ADC8", lp: 1056, games: 301, winRate: 46, tier: "MASTER", profileIcon: 5367, topChampions: ["Draven", "Lucian", "Caitlyn", "Zeri"], kda: "3.1" },
  { rank: 45, name: "Cipher", tag: "MID0", lp: 1023, games: 243, winRate: 44, tier: "MASTER", profileIcon: 4405, topChampions: ["Kassadin", "Fizz", "Ekko", "Diana"], kda: "2.8" },
  { rank: 46, name: "Vulkan", tag: "JG09", lp: 989, games: 266, winRate: 45, tier: "MASTER", profileIcon: 5066, topChampions: ["Graves", "Nidalee", "Kindred", "Lillia"], kda: "2.4" },
  { rank: 47, name: "Magma", tag: "TOP0", lp: 956, games: 248, winRate: 44, tier: "MASTER", profileIcon: 5317, topChampions: ["Darius", "Garen", "Illaoi", "Yorick"], kda: "2.3" },
  { rank: 48, name: "Glacial", tag: "SUP9", lp: 923, games: 282, winRate: 44, tier: "MASTER", profileIcon: 4898, topChampions: ["Senna", "Karma", "Zyra", "Morgana"], kda: "3.2" },
  { rank: 49, name: "Bolt", tag: "ADC9", lp: 890, games: 254, winRate: 43, tier: "MASTER", profileIcon: 5195, topChampions: ["Kogmaw", "Varus", "Ashe", "Sivir"], kda: "2.6" },
  { rank: 50, name: "Obelisk", tag: "MID1", lp: 867, games: 271, winRate: 43, tier: "MASTER", profileIcon: 4787, topChampions: ["Malzahar", "Veigar", "Lux", "Brand"], kda: "2.5" },
]

const MODE_TABS = ["SoloQ", "Flex", "OTPs", "Community"]
const REGIONS = ["ALL", "BR", "NA", "EUW", "KR"]

const ROLES = [
  { label: "TOP", pct: 15.2, color: "bg-blue-700" },
  { label: "JG",  pct: 22.7, color: "bg-blue-600" },
  { label: "MID", pct: 27.2, color: "bg-blue-500" },
  { label: "BOT", pct: 21.5, color: "bg-blue-400" },
  { label: "SUP", pct: 13.4, color: "bg-purple-500" },
]

function TierBadge({ tier }) {
  const color = TIER_COLORS[tier] ?? TIER_COLORS.UNRANKED
  const label = tier.charAt(0) + tier.slice(1).toLowerCase()
  return (
    <span
      className="text-bxs font-bold uppercase tracking-wide px-2 py-0.5 rounded"
      style={{ color, background: `${color}20`, border: `1px solid ${color}33` }}
    >
      {label}
    </span>
  )
}

function TopPlayerCard({ player, index }) {
  const color = TIER_COLORS[player.tier] ?? TIER_COLORS.UNRANKED
  const medals = ["🥇", "🥈", "🥉"]

  return (
    <div
      style={{ animationDelay: `${index * 80}ms`, animationFillMode: "both" }}
      className="animate-fade-up bg-black-800 rounded-xl shadow-[0_2px_8px_rgba(121,137,236,0.10)] p-5 flex flex-col items-center gap-3 relative overflow-hidden"
    >
      <div className="absolute top-0 left-0 right-0 h-1 rounded-t-xl" style={{ background: color }} />

      <span className="text-2xl">{medals[index]}</span>

      <div className="w-16 h-16 rounded-full overflow-hidden border-2 bg-black-600" style={{ borderColor: color }}>
        <img
          src={`https://ddragon.leagueoflegends.com/cdn/${DDV}/img/profileicon/${player.profileIcon}.png`}
          alt={player.name}
          className="w-full h-full object-cover"
        />
      </div>

      <div className="text-center">
        <p className="text-bxl text-black-0">{player.name}</p>
        <p className="text-bxs text-black-300">#{player.tag}</p>
      </div>

      <div className="flex items-center gap-2">
        <TierBadge tier={player.tier} />
        <span className="text-bs font-bold text-black-0">{player.lp.toLocaleString()} LP</span>
      </div>

      <div className="flex items-center gap-2 text-bs text-black-200">
        <span>{player.games} jogos</span>
        <span className="text-black-500">•</span>
        <span className={player.winRate >= 55 ? "text-green-600 font-semibold" : "text-black-200"}>
          {player.winRate}% WR
        </span>
        <span className="text-black-500">•</span>
        <span>{player.kda} KDA</span>
      </div>

      <div className="flex gap-1.5">
        {player.topChampions.map((champ) => (
          <div key={champ} className="w-8 h-8 rounded-lg overflow-hidden border border-white/10 bg-black-600">
            <img
              src={`https://ddragon.leagueoflegends.com/cdn/${DDV}/img/champion/${champ}.png`}
              alt={champ}
              className="w-full h-full object-cover"
              onError={(e) => { e.target.style.display = "none" }}
            />
          </div>
        ))}
      </div>
    </div>
  )
}

function PlayerRow({ player, index }) {
  return (
    <tr
      style={{ animationDelay: `${(index + 3) * 30}ms`, animationFillMode: "both" }}
      className="animate-fade-up border-b border-white/5 hover:bg-white/[0.02] transition-colors"
    >
      <td className="py-2.5 px-3 text-bs text-black-300 font-semibold w-10">
        #{player.rank}
      </td>

      <td className="py-2.5 px-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full overflow-hidden border border-white/10 bg-black-600 flex-shrink-0">
            <img
              src={`https://ddragon.leagueoflegends.com/cdn/${DDV}/img/profileicon/${player.profileIcon}.png`}
              alt={player.name}
              className="w-full h-full object-cover"
            />
          </div>
          <div>
            <span className="text-bs font-semibold text-black-0">{player.name}</span>
            <span className="text-bxs text-black-400 ml-1">#{player.tag}</span>
          </div>
        </div>
      </td>

      <td className="py-2.5 px-3 hidden sm:table-cell">
        <TierBadge tier={player.tier} />
      </td>

      <td className="py-2.5 px-3 text-bs font-semibold text-black-0 text-right">
        {player.lp.toLocaleString()}
      </td>

      <td className="py-2.5 px-3 text-bs text-right">
        <span className={player.winRate >= 55 ? "text-green-600 font-semibold" : "text-black-200"}>
          {player.winRate}%
        </span>
      </td>

      <td className="py-2.5 px-3 hidden md:table-cell">
        <div className="flex gap-1 justify-end">
          {player.topChampions.slice(0, 3).map((champ) => (
            <div key={champ} className="w-6 h-6 rounded overflow-hidden border border-white/10 bg-black-600">
              <img
                src={`https://ddragon.leagueoflegends.com/cdn/${DDV}/img/champion/${champ}.png`}
                alt={champ}
                className="w-full h-full object-cover"
                onError={(e) => { e.target.style.display = "none" }}
              />
            </div>
          ))}
        </div>
      </td>

      <td className="py-2.5 px-3 text-bs text-black-300 text-right hidden md:table-cell">
        {player.kda}
      </td>
    </tr>
  )
}

export default function LeaderboardScreen() {
  const [activeTab, setActiveTab] = useState("SoloQ")
  const [activeRegion, setActiveRegion] = useState("BR")
  const [proOnly, setProOnly] = useState(false)

  const top3 = MOCK_PLAYERS.slice(0, 3)
  const rest = MOCK_PLAYERS.slice(3)

  return (
    <div className="max-w-[1200px] mx-auto px-4 pb-16">
      {/* Mode Tabs */}
      <div
        className="flex gap-1 pt-6 pb-4 animate-fade-up"
        style={{ animationDelay: "0ms", animationFillMode: "both" }}
      >
        {MODE_TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg text-bs font-semibold transition-colors ${
              activeTab === tab
                ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                : "text-black-300 hover:text-black-100 hover:bg-white/5"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Hero Section */}
      <div
        className="flex items-center justify-between gap-6 py-8 animate-fade-up"
        style={{ animationDelay: "60ms", animationFillMode: "both" }}
      >
        <div className="flex-1">
          <h1 className="text-hxl text-black-0 mb-3">
            Leaderboard {activeTab}
          </h1>
          <p className="text-bm text-black-300 max-w-xl leading-relaxed">
            Descubra o Leaderboard Ranked {activeTab} do MVP.GG, onde você encontra os melhores jogadores Challenger
            e Grandmaster do servidor. Acompanhe quem está no topo e inspire-se para subir no ranking.
          </p>
        </div>
        <div className="hidden lg:block w-32 h-32 rounded-xl overflow-hidden border border-white/10 bg-black-800 flex-shrink-0">
          <img
            src={`https://ddragon.leagueoflegends.com/cdn/img/champion/splash/Jinx_0.jpg`}
            alt="Champion decoration"
            className="w-full h-full object-cover object-top opacity-70"
          />
        </div>
      </div>

      {/* Role Distribution Bar */}
      <div
        className="mb-6 animate-fade-up"
        style={{ animationDelay: "120ms", animationFillMode: "both" }}
      >
        <p className="text-bxs text-black-400 mb-2 uppercase tracking-wider font-semibold">Distribuição por Role</p>
        <div className="flex rounded-lg overflow-hidden h-8">
          {ROLES.map((role) => (
            <div
              key={role.label}
              className={`${role.color} flex items-center justify-center gap-1 transition-all`}
              style={{ width: `${role.pct}%` }}
            >
              <span className="text-bxs font-bold text-white/90">{role.label}</span>
              <span className="text-bxs text-white/60 hidden sm:inline">{role.pct}%</span>
            </div>
          ))}
        </div>
      </div>

      {/* Region Filter */}
      <div
        className="flex items-center gap-2 flex-wrap mb-8 animate-fade-up"
        style={{ animationDelay: "180ms", animationFillMode: "both" }}
      >
        {REGIONS.map((region) => (
          <button
            key={region}
            onClick={() => setActiveRegion(region)}
            className={`px-3 py-1.5 rounded-lg text-bs font-semibold transition-colors ${
              activeRegion === region
                ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                : "text-black-300 hover:text-black-100 hover:bg-white/5 border border-transparent"
            }`}
          >
            {region}
          </button>
        ))}
        <div className="w-px h-5 bg-white/10 mx-1" />
        <button
          onClick={() => setProOnly(!proOnly)}
          className={`px-3 py-1.5 rounded-lg text-bs font-semibold transition-colors ${
            proOnly
              ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
              : "text-black-300 hover:text-black-100 hover:bg-white/5 border border-transparent"
          }`}
        >
          PRO
        </button>
      </div>

      {/* Top 3 Featured Players */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {top3.map((player, i) => (
          <TopPlayerCard key={player.rank} player={player} index={i} />
        ))}
      </div>

      {/* Rest of Players Table */}
      <div
        className="bg-black-800 rounded-xl shadow-[0_2px_8px_rgba(121,137,236,0.10)] overflow-hidden animate-fade-up"
        style={{ animationDelay: "300ms", animationFillMode: "both" }}
      >
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/10">
              <th className="py-3 px-3 text-bxs text-black-400 font-semibold text-left uppercase tracking-wider w-10">#</th>
              <th className="py-3 px-3 text-bxs text-black-400 font-semibold text-left uppercase tracking-wider">Jogador</th>
              <th className="py-3 px-3 text-bxs text-black-400 font-semibold text-left uppercase tracking-wider hidden sm:table-cell">Rank</th>
              <th className="py-3 px-3 text-bxs text-black-400 font-semibold text-right uppercase tracking-wider">LP</th>
              <th className="py-3 px-3 text-bxs text-black-400 font-semibold text-right uppercase tracking-wider">WR</th>
              <th className="py-3 px-3 text-bxs text-black-400 font-semibold text-right uppercase tracking-wider hidden md:table-cell">Campeões</th>
              <th className="py-3 px-3 text-bxs text-black-400 font-semibold text-right uppercase tracking-wider hidden md:table-cell">KDA</th>
            </tr>
          </thead>
          <tbody>
            {rest.map((player, i) => (
              <PlayerRow key={player.rank} player={player} index={i} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
