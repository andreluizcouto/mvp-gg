export const DDV = "16.7.1"

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
