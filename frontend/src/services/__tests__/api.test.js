import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

describe("api service safety contracts", () => {
  beforeEach(() => {
    vi.resetModules()
    vi.unstubAllGlobals()
    vi.stubEnv("VITE_API_URL", "https://api.example.com")
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("fetchCoachingAnalysis returns safe fallback on network error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network")))
    const api = await import("../api.js")

    await expect(api.fetchCoachingAnalysis("BR1_123", "owner#BR1")).resolves.toEqual({
      match_id: "BR1_123",
      has_analysis: false,
      analysis: null,
    })
  })

  it("fetchCoachingStatus returns empty object on fetch error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network")))
    const api = await import("../api.js")

    await expect(api.fetchCoachingStatus(["BR1_123"], "owner#BR1")).resolves.toEqual({})
  })

  it("omits invalid riot_id query param in coaching endpoints", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({}),
    })
    vi.stubGlobal("fetch", fetchMock)
    const api = await import("../api.js")

    await api.fetchCoachingStatus(["BR1_123"], "invalid riot id")
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(fetchMock.mock.calls[0][0]).toContain("/coaching/status")
    expect(fetchMock.mock.calls[0][0]).not.toContain("riot_id=")

    fetchMock.mockClear()
    await api.fetchCoachingAnalysis("BR1_123", "invalid riot id")
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(fetchMock.mock.calls[0][0]).toContain("/coaching/BR1_123")
    expect(fetchMock.mock.calls[0][0]).not.toContain("riot_id=")
  })
})
