import { describe, expect, it } from "vitest"
import { timeAgo } from "../services/utils"

const NOW = Date.UTC(2026, 9, 29, 12, 0)
const ago = (minutes) => NOW - minutes * 60000

describe("timeAgo", () => {
  it("usa horas, dias, semanas, meses e anos no singular e no plural", () => {
    expect(timeAgo(ago(0), NOW)).toBe("agora há pouco")
    expect(timeAgo(ago(5), NOW)).toBe("há 5 minutos")
    expect(timeAgo(ago(60), NOW)).toBe("há 1 hora")
    expect(timeAgo(ago(60 * 5), NOW)).toBe("há 5 horas")
    expect(timeAgo(ago(60 * 24), NOW)).toBe("há 1 dia")
    expect(timeAgo(ago(60 * 24 * 6), NOW)).toBe("há 6 dias")
    expect(timeAgo(ago(60 * 24 * 7), NOW)).toBe("há 1 semana")
    expect(timeAgo(ago(60 * 24 * 20), NOW)).toBe("há 2 semanas")
    expect(timeAgo(ago(60 * 24 * 30), NOW)).toBe("há 1 mês")
    expect(timeAgo(ago(60 * 24 * 95), NOW)).toBe("há 3 meses")
    expect(timeAgo(ago(60 * 24 * 400), NOW)).toBe("há 1 ano")
  })

  it("devolve vazio sem data", () => {
    expect(timeAgo(null, NOW)).toBe("")
  })
})
