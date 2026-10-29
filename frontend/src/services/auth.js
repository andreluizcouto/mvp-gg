const AUTH_STORAGE_KEY = "mvpgg.auth.session"

function readStoredSession() {
  if (typeof window === "undefined") return null
  try {
    const raw = window.sessionStorage.getItem(AUTH_STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function writeStoredSession(payload) {
  if (typeof window === "undefined") return null
  if (!payload) {
    window.sessionStorage.removeItem(AUTH_STORAGE_KEY)
    return null
  }
  window.sessionStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(payload))
  return payload
}

export function getSession() {
  return readStoredSession()
}

export function setSession(payload) {
  return writeStoredSession(payload)
}

export async function login(baseUrl, { email, password }) {
  const response = await fetch(`${baseUrl}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({ email, password }),
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.detail || "Falha no login.")
  return writeStoredSession(data)
}

export async function refreshSession(baseUrl, refreshToken) {
  const response = await fetch(`${baseUrl}/auth/refresh`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.detail || "Sessão expirada.")
  return writeStoredSession(data)
}

export async function logout(baseUrl, refreshToken, accessToken) {
  const response = await fetch(`${baseUrl}/auth/logout`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(data.detail || "Falha ao encerrar sessão.")
  }
  writeStoredSession(null)
}
