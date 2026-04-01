import React from "react"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { render, screen, waitFor } from "@testing-library/react"
import { describe, expect, it, vi, beforeEach } from "vitest"
import ResultsScreen from "../screens/ResultsScreen"

vi.mock("../services/constants", () => ({
  DDV: "15.1.1",
  getPositionLabel: () => "MID",
}))

vi.mock("../services/utils", () => ({
  calcScore: () => 95,
  buildSummonerProfilePath: () => "",
}))

const fetchMatchDetailsMock = vi.fn()
const fetchCoachingAnalysisMock = vi.fn()
const fetchScoreboardMock = vi.fn()

vi.mock("../services/api", () => ({
  fetchMatchDetails: (...args) => fetchMatchDetailsMock(...args),
  fetchCoachingAnalysis: (...args) => fetchCoachingAnalysisMock(...args),
  fetchScoreboard: (...args) => fetchScoreboardMock(...args),
}))

function renderWithPath(path) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/match/:matchId" element={<ResultsScreen />} />
      </Routes>
    </MemoryRouter>,
  )
}

const baseMatch = {
  match_id: "BR1_1",
  riot_id: "owner#BR1",
  summoner_name: "owner#BR1",
  champion: "Ahri",
  position: "MIDDLE",
  kills: 10,
  deaths: 2,
  assists: 8,
  win: true,
  duration_min: 30,
  cs_per_min: 7.2,
  vision_score: 20,
  items: [1056, 3020, 0, 0, 0, 0, 0],
}

describe("ResultsScreen status rendering", () => {
  beforeEach(() => {
    fetchMatchDetailsMock.mockReset()
    fetchCoachingAnalysisMock.mockReset()
    fetchScoreboardMock.mockReset()
  })

  it("shows private-safe block for direct-link without owner context", async () => {
    fetchMatchDetailsMock.mockResolvedValue({
      ...baseMatch,
      riot_id: "",
      summoner_name: "",
    })
    fetchScoreboardMock.mockResolvedValue({
      teams: [
        {
          side: "blue",
          win: true,
          players: [
            {
              puuid: "other-puuid",
              is_target: false,
              summoner_name: "other#BR1",
              champion: "Ahri",
              position: "MIDDLE",
              kills: 1,
              deaths: 1,
              assists: 1,
              cs: 100,
              cs_per_min: 6.0,
              total_damage: 10000,
              damage_share_pct: 30,
              gold_earned: 10000,
              vision_score: 10,
              items: [0, 0, 0, 0, 0, 0, 0],
              summoner1_id: 4,
              summoner2_id: 14,
            },
          ],
        },
      ],
    })

    renderWithPath("/match/BR1_1")

    expect(await screen.findByText("Análise privada para este jogador")).toBeInTheDocument()
    expect(screen.queryByText("COACHING IA")).toBeInTheDocument()
    expect(screen.queryByText("analise privada do dono")).not.toBeInTheDocument()
  })

  it("shows ready coaching state when analysis is available via owner flow", async () => {
    fetchScoreboardMock.mockResolvedValue({ teams: [] })
    fetchCoachingAnalysisMock.mockResolvedValue({
      has_analysis: true,
      analysis: "## 1. Força\nVocê controlou bem as waves.",
      status: "ready",
    })

    const state = {
      matchStats: baseMatch,
      player: { nick: "owner#BR1" },
      rank: "GOLD IV",
      puuid: "owner-puuid",
      from: "/summoner/owner/BR1",
    }

    render(
      <MemoryRouter initialEntries={[{ pathname: "/match/BR1_1", state }]}>
        <Routes>
          <Route path="/match/:matchId" element={<ResultsScreen />} />
        </Routes>
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(fetchCoachingAnalysisMock).toHaveBeenCalled()
    })

    expect(await screen.findAllByText("Estado da análise:")).not.toHaveLength(0)
    expect(screen.getByText("Análise pronta")).toBeInTheDocument()
    expect(screen.getAllByText("COACHING IA")).not.toHaveLength(0)
  })
})
