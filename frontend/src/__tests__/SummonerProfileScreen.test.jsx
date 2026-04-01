import React from "react"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { render, screen, waitFor } from "@testing-library/react"
import { describe, expect, it, vi, beforeEach } from "vitest"
import SummonerProfileScreen from "../screens/SummonerProfileScreen"

vi.mock("../services/constants", () => ({
  DDV: "15.1.1",
  getPositionLabel: () => "MID",
}))

vi.mock("../services/utils", () => ({
  TIER_COLORS: {
    UNRANKED: "#fff",
    GOLD: "#f0c040",
  },
  parseTier: () => "GOLD",
  calcScore: () => 90,
  buildChampionPool: () => [],
  buildSummonerProfilePath: () => "",
}))

const fetchMatchesMock = vi.fn()
const fetchCoachingStatusMock = vi.fn()

vi.mock("../services/api", () => ({
  fetchMatches: (...args) => fetchMatchesMock(...args),
  fetchCoachingStatus: (...args) => fetchCoachingStatusMock(...args),
  refreshMatches: vi.fn(),
  fetchScoreboard: vi.fn(),
}))

function renderScreen() {
  return render(
    <MemoryRouter initialEntries={["/summoner/tester/BR1"]}>
      <Routes>
        <Route path="/summoner/:name/:tag" element={<SummonerProfileScreen />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("SummonerProfileScreen IA badge gating", () => {
  beforeEach(() => {
    fetchMatchesMock.mockReset()
    fetchCoachingStatusMock.mockReset()
  })

  it("shows IA badge only when status is ready", async () => {
    fetchMatchesMock.mockResolvedValue({
      summoner: "tester#BR1",
      rank: "GOLD IV",
      puuid: "puuid-1",
      matches: [
        {
          match_id: "BR1_1",
          champion: "Ahri",
          kills: 10,
          deaths: 2,
          assists: 8,
          duration_min: 30,
          cs_per_min: 7.2,
          vision_score: 20,
          win: true,
          position: "MIDDLE",
          items: [1056, 0, 0, 0, 0, 0, 0],
          kill_participation_pct: 60,
        },
        {
          match_id: "BR1_2",
          champion: "Lux",
          kills: 4,
          deaths: 7,
          assists: 9,
          duration_min: 28,
          cs_per_min: 6.0,
          vision_score: 14,
          win: false,
          position: "MIDDLE",
          items: [1056, 0, 0, 0, 0, 0, 0],
          kill_participation_pct: 45,
        },
      ],
      wins: 1,
      losses: 1,
      has_more: false,
      next_offset: 2,
    })
    fetchCoachingStatusMock.mockResolvedValue({
      BR1_1: { status: "ready" },
      BR1_2: { status: "pending" },
    })

    renderScreen()

    await waitFor(() => {
      expect(fetchMatchesMock).toHaveBeenCalled()
      expect(fetchCoachingStatusMock).toHaveBeenCalled()
    })

    const badges = await screen.findAllByText("IA")
    expect(badges).toHaveLength(1)
  })
})
