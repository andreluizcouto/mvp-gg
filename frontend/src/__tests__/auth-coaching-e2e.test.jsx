import React from "react"
import { render, screen, waitFor } from "@testing-library/react"
import { describe, expect, it, vi, beforeEach } from "vitest"

import App from "../App"

const loginMock = vi.fn()
const getSessionMock = vi.fn()
const fetchAuthMeMock = vi.fn()
const fetchAuthorizedCoachingStatusMock = vi.fn()

vi.mock("../services/auth", async () => {
  const actual = await vi.importActual("../services/auth")
  return {
    ...actual,
    login: (...args) => loginMock(...args),
    getSession: (...args) => getSessionMock(...args),
  }
})

vi.mock("../services/api", async () => {
  const actual = await vi.importActual("../services/api")
  return {
    ...actual,
    fetchAuthMe: (...args) => fetchAuthMeMock(...args),
    fetchAuthorizedCoachingStatus: (...args) => fetchAuthorizedCoachingStatusMock(...args),
  }
})

describe("login_to_coaching_protected_flow", () => {
  beforeEach(() => {
    getSessionMock.mockReset()
    fetchAuthMeMock.mockReset()
    fetchAuthorizedCoachingStatusMock.mockReset()
  })

  it("redirects unauthorized users to login for protected dashboard", async () => {
    window.history.pushState({}, "", "/dashboard")
    getSessionMock.mockReturnValue(null)

    render(<App />)

    expect(await screen.findByText("Login")).toBeInTheDocument()
  })

  it("shows protected coaching dashboard data when authorized", async () => {
    window.history.pushState({}, "", "/dashboard")
    getSessionMock.mockReturnValue({ access_token: "at", refresh_token: "rt" })
    fetchAuthMeMock.mockResolvedValue({
      email: "user@test.com",
      analyses_consumed: 2,
      analyses_performed: 5,
    })
    fetchAuthorizedCoachingStatusMock.mockResolvedValue({
      BR1_123: { status: "ready", has_analysis: true },
    })

    render(<App />)

    await waitFor(() => {
      expect(screen.getByText("Dashboard")).toBeInTheDocument()
      expect(screen.getByText("BR1_123")).toBeInTheDocument()
    })
  })
})
