export const DDV = "16.21.1"

export const POSITION_MAPS = {
  label:  { TOP: "Top", JUNGLE: "Jungle", MIDDLE: "Mid", BOTTOM: "ADC", UTILITY: "Suporte" },
  short:  { TOP: "TOP", JUNGLE: "JGL",    MIDDLE: "MID", BOTTOM: "ADC", UTILITY: "SUP" },
  abbrev: { TOP: "TOP", JUNGLE: "JG",     MIDDLE: "MID", BOTTOM: "ADC", UTILITY: "SUP" },
}

export function getPositionLabel(position, type = "label") {
  const key = position?.toUpperCase()
  if (!key) return ""
  return POSITION_MAPS[type]?.[key] ?? position
}

// ── Imagens públicas (Data Dragon e CommunityDragon) ──

const CDRAGON = "https://raw.communitydragon.org/latest/plugins"

export function championIcon(key, version = DDV) {
  return `https://ddragon.leagueoflegends.com/cdn/${version}/img/champion/${key}.png`
}

export function spellIcon(key, version = DDV) {
  return `https://ddragon.leagueoflegends.com/cdn/${version}/img/spell/${key}.png`
}

export function championSplash(key) {
  return `https://ddragon.leagueoflegends.com/cdn/img/champion/splash/${key}_0.jpg`
}

export function championCentered(key) {
  return `https://ddragon.leagueoflegends.com/cdn/img/champion/centered/${key}_0.jpg`
}

// Emblema grande (tem bastante margem transparente: usar com zoom)
export function rankEmblem(tier) {
  const safe = String(tier || "unranked").toLowerCase()
  return `${CDRAGON}/rcp-fe-lol-static-assets/global/default/images/ranked-emblem/emblem-${safe}.png`
}

// Brasão pequeno e recortado, bom para listas
export function rankCrest(tier) {
  const safe = String(tier || "unranked").toLowerCase()
  return `${CDRAGON}/rcp-fe-lol-static-assets/global/default/images/ranked-mini-crests/${safe}.svg`
}

// Chaves de rota do OP.GG → ícone oficial da posição
const POSITION_ICON_KEYS = { top: "top", jungle: "jungle", mid: "middle", adc: "bottom", support: "utility" }

export function positionIcon(position) {
  const key = POSITION_ICON_KEYS[position] ?? String(position || "").toLowerCase()
  return `${CDRAGON}/rcp-fe-lol-clash/global/default/assets/images/position-selector/positions/icon-position-${key}.png`
}

export const LANES = [
  { id: "top",     label: "Top" },
  { id: "jungle",  label: "Jungle" },
  { id: "mid",     label: "Mid" },
  { id: "adc",     label: "ADC" },
  { id: "support", label: "Suporte" },
]

// Elos do seletor da tier list (os mesmos do OP.GG). Esmeralda+ é o padrão do OP.GG.
export const DEFAULT_ELO = "emerald_plus"
export const TIERLIST_ELOS = [
  { id: "all",           label: "Todos os elos" },
  { id: "challenger",    label: "Desafiante" },
  { id: "grandmaster",   label: "Grão-Mestre" },
  { id: "master_plus",   label: "Mestre+" },
  { id: "master",        label: "Mestre" },
  { id: "diamond_plus",  label: "Diamante+" },
  { id: "diamond",       label: "Diamante" },
  { id: "emerald_plus",  label: "Esmeralda+" },
  { id: "emerald",       label: "Esmeralda" },
  { id: "platinum_plus", label: "Platina+" },
  { id: "platinum",      label: "Platina" },
  { id: "gold_plus",     label: "Ouro+" },
  { id: "gold",          label: "Ouro" },
  { id: "silver",        label: "Prata" },
  { id: "bronze",        label: "Bronze" },
  { id: "iron",          label: "Ferro" },
]

export function eloLabel(id) {
  return TIERLIST_ELOS.find(e => e.id === id)?.label ?? "Esmeralda+"
}

// Tiers do OP.GG vão de 1 (OP) a 5. Mostramos na escala de letras que o jogador conhece.
export const META_TIERS = {
  1: { label: "S", color: "#E2B95E" },
  2: { label: "A", color: "#33D1C1" },
  3: { label: "B", color: "#7FA8FF" },
  4: { label: "C", color: "#97A0B3" },
  5: { label: "D", color: "#6E778A" },
}

// ── Modos de jogo ──

// Filtros do perfil (o backend traduz cada um para as filas da Riot)
// O backend também aceita "normal" e "aram", mas o perfil só oferece estes.
export const QUEUE_FILTERS = [
  { id: "all",    label: "Todas" },
  { id: "solo",   label: "Solo/Duo" },
  { id: "flex",   label: "Flex" },
  { id: "arena",  label: "Arena" },
]

// Nomes curtos para as filas mais comuns; as demais usam o nome oficial que vem do backend
// (lista de filas do cliente, em português), então modos novos já aparecem com o nome certo.
const QUEUE_LABELS = {
  420: "Solo/Duo", 440: "Flex", 710: "Ranqueada-5",
  400: "Normal", 430: "Normal", 480: "Jogo Dinâmico", 490: "Jogo Rápido",
  450: "ARAM", 2400: "ARAM: Desordem", 2401: "ARAM: Desordem", 2403: "ARAM: Desordem", 2405: "ARAM: Desordem",
  2450: "ARAM: Desordem Raiz",
  1700: "Arena", 1710: "Arena", 1740: "Arena da Bravura", 1750: "Arena 3x6",
  900: "URF", 1900: "URF", 1020: "Um por Todos", 1300: "Nexus Blitz",
}
// KIWI é o nome interno do ARAM: Desordem
const MODE_LABELS = { CLASSIC: "Normal", ARAM: "ARAM", KIWI: "ARAM: Desordem", CHERRY: "Arena", URF: "URF", NEXUSBLITZ: "Nexus Blitz" }

export function queueLabel(match) {
  return QUEUE_LABELS[match?.queue_id]
    ?? (match?.queue_name || undefined)
    ?? MODE_LABELS[match?.game_mode]
    ?? (match?.game_mode ? String(match.game_mode).toLowerCase() : "")
}

export function isArenaMatch(match) {
  return match?.game_mode === "CHERRY" || (match?.queue_id >= 1700 && match?.queue_id < 1800)
}

export const TIER_LABELS = {
  IRON: "Ferro", BRONZE: "Bronze", SILVER: "Prata", GOLD: "Ouro", PLATINUM: "Platina", EMERALD: "Esmeralda",
  DIAMOND: "Diamante", MASTER: "Mestre", GRANDMASTER: "Grão-Mestre", CHALLENGER: "Desafiante",
}

// Links externos para a build completa de cada campeão
export function opggBuildUrl(championKey, lane) {
  return `https://op.gg/lol/champions/${String(championKey).toLowerCase()}/build/${lane}`
}

export function uggBuildUrl(championKey, lane) {
  return `https://u.gg/lol/champions/${String(championKey).toLowerCase()}/build?role=${lane}`
}
