import React from "react"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { describe, expect, it, vi, beforeEach } from "vitest"

import LoginScreen from "../screens/LoginScreen"

const loginMock = vi.fn()
const navigateMock = vi.fn()

vi.mock("../services/auth", () => ({
  login: (...args) => loginMock(...args),
  getSession: vi.fn(),
}))

vi.mock("../services/api", () => ({
  BASE_URL: "https://api.test",
}))

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom")
  return {
    ...actual,
    useNavigate: () => navigateMock,
  }
})

describe("LoginScreen", () => {
  beforeEach(() => {
    loginMock.mockReset()
    navigateMock.mockReset()
  })

  it("submits credentials and redirects on success", async () => {
    loginMock.mockResolvedValue({ access_token: "at", refresh_token: "rt" })

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="/login" element={<LoginScreen />} />
        </Routes>
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "user@test.com" } })
    fireEvent.change(screen.getByLabelText("Senha"), { target: { value: "password-123" } })
    fireEvent.click(screen.getByRole("button", { name: "Entrar" }))

    await waitFor(() => {
      expect(loginMock).toHaveBeenCalled()
      expect(navigateMock).toHaveBeenCalledWith("/dashboard", { replace: true })
    })
  })
})
