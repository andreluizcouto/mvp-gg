import React from "react"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react"
import { afterEach, describe, expect, it, vi, beforeEach } from "vitest"

import DashboardScreen from "../screens/DashboardScreen"

const navigateMock = vi.fn()
const getSessionMock = vi.fn()
const logoutMock = vi.fn()
const fetchAuthMeMock = vi.fn()
const fetchAuthorizedCoachingStatusMock = vi.fn()

vi.mock("../services/auth", () => ({
  getSession: (...args) => getSessionMock(...args),
  logout: (...args) => logoutMock(...args),
}))

vi.mock("../services/api", () => ({
  BASE_URL: "https://api.test",
  fetchAuthMe: (...args) => fetchAuthMeMock(...args),
  fetchAuthorizedCoachingStatus: (...args) => fetchAuthorizedCoachingStatusMock(...args),
}))

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom")
  return {
    ...actual,
    useNavigate: () => navigateMock,
  }
})

describe("DashboardScreen", () => {
  afterEach(() => {
    cleanup()
  })

  beforeEach(() => {
    navigateMock.mockReset()
    getSessionMock.mockReset()
    logoutMock.mockReset()
    fetchAuthMeMock.mockReset()
    fetchAuthorizedCoachingStatusMock.mockReset()
  })

  it("shows analyses counters and only ready matches", async () => {
    getSessionMock.mockReturnValue({ access_token: "at", refresh_token: "rt" })
    fetchAuthMeMock.mockResolvedValue({
      email: "user@test.com",
      analyses_consumed: 3,
      analyses_performed: 9,
      matches_with_analysis: ["BR1_123", "BR1_124"],
    })
    fetchAuthorizedCoachingStatusMock.mockResolvedValue({
      BR1_123: { status: "ready", has_analysis: true },
      BR1_124: { status: "pending", has_analysis: false },
    })

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <Routes>
          <Route path="/dashboard" element={<DashboardScreen />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(await screen.findByText("3")).toBeInTheDocument()
    expect(screen.getByText("9")).toBeInTheDocument()
    expect(screen.getByText("BR1_123")).toBeInTheDocument()
    expect(screen.queryByText("BR1_124")).not.toBeInTheDocument()
  })

  it("redirects to login on unauthorized response", async () => {
    getSessionMock.mockReturnValue({ access_token: "at", refresh_token: "rt" })
    const unauthorized = new Error("unauthorized")
    unauthorized.status = 401
    fetchAuthMeMock.mockRejectedValue(unauthorized)

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <Routes>
          <Route path="/dashboard" element={<DashboardScreen />} />
        </Routes>
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(navigateMock).toHaveBeenCalledWith("/login", { replace: true })
    })
  })

  it("logs out and redirects", async () => {
    getSessionMock.mockReturnValue({ access_token: "at", refresh_token: "rt" })
    fetchAuthMeMock.mockResolvedValue({
      email: "user@test.com",
      analyses_consumed: 0,
      analyses_performed: 0,
      matches_with_analysis: [],
    })
    fetchAuthorizedCoachingStatusMock.mockResolvedValue({})
    logoutMock.mockResolvedValue(undefined)

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <Routes>
          <Route path="/dashboard" element={<DashboardScreen />} />
        </Routes>
      </MemoryRouter>,
    )

    await screen.findByText("Dashboard")
    fireEvent.click(screen.getByRole("button", { name: "Sair" }))
    await waitFor(() => {
      expect(logoutMock).toHaveBeenCalled()
      expect(navigateMock).toHaveBeenCalledWith("/login", { replace: true })
    })
  })
})
