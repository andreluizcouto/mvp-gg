import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { BASE_URL } from "../services/api"
import { login } from "../services/auth"

export default function LoginScreen() {
  const navigate = useNavigate()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  async function handleSubmit(event) {
    event.preventDefault()
    setError("")
    setLoading(true)
    try {
      await login(BASE_URL, { email, password })
      navigate("/dashboard", { replace: true })
    } catch (err) {
      setError(err?.message || "Falha no login.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-md px-4 py-16">
      <div className="rounded-xl border border-black-500 bg-black-800 p-6 shadow-[0_0px_10px_0px_rgba(121,137,236,0.10)]">
        <h1 className="text-hxs font-bold text-black-0 mb-2">Login</h1>
        <p className="text-bs text-black-300 mb-6">Acesse suas análises IA e consumo do plano.</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block">
            <span className="text-bxs text-black-300">Email</span>
            <input
              aria-label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-lg border border-black-500 bg-black-700 px-3 py-2 text-black-100 outline-none"
              required
            />
          </label>
          <label className="block">
            <span className="text-bxs text-black-300">Senha</span>
            <input
              aria-label="Senha"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-lg border border-black-500 bg-black-700 px-3 py-2 text-black-100 outline-none"
              required
            />
          </label>
          {error ? <p role="alert" className="text-bxs text-accent-red">{error}</p> : null}
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-blue-500 py-2 text-white font-semibold hover:bg-blue-600 disabled:opacity-60"
          >
            {loading ? "Entrando..." : "Entrar"}
          </button>
        </form>
      </div>
    </div>
  )
}
